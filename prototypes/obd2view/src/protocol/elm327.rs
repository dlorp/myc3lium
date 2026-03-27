// ELM327 AT command protocol implementation
// Handles serial communication with ELM327 OBD2 adapters

use super::{Result, ProtocolError};
use tokio_serial::{SerialPort, SerialPortBuilderExt, SerialStream};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use std::time::Duration;

const DEFAULT_TIMEOUT: Duration = Duration::from_secs(2);
const PROMPT: u8 = b'>';

pub struct ELM327 {
    port: SerialStream,
    timeout: Duration,
}

impl ELM327 {
    /// Connect to ELM327 adapter and initialize
    pub async fn new(device: &str, baud_rate: u32) -> Result<Self> {
        // Open serial port
        let port = tokio_serial::new(device, baud_rate)
            .timeout(DEFAULT_TIMEOUT)
            .open_native_async()
            .map_err(|e| ProtocolError::ConnectionFailed(e.to_string()))?;

        let mut elm = Self {
            port,
            timeout: DEFAULT_TIMEOUT,
        };

        // Initialize ELM327
        elm.initialize().await?;

        Ok(elm)
    }

    /// Send initialization sequence
    async fn initialize(&mut self) -> Result<()> {
        // Reset adapter
        self.send_command("ATZ").await?;
        tokio::time::sleep(Duration::from_millis(500)).await;

        // Turn off echo (cleaner responses)
        self.send_command("ATE0").await?;

        // Turn off line feeds (compact responses)
        self.send_command("ATL0").await?;

        // Turn on headers (shows source ECU)
        self.send_command("ATH1").await?;

        // Auto protocol detection
        self.send_command("ATSP0").await?;

        Ok(())
    }

    /// Send AT command or OBD query, wait for ">" prompt
    pub async fn send_command(&mut self, cmd: &str) -> Result<String> {
        // Clear input buffer
        let mut discard = vec![0u8; 1024];
        let _ = self.port.try_read(&mut discard);

        // Send command + carriage return
        let mut cmd_bytes = cmd.as_bytes().to_vec();
        cmd_bytes.push(b'\r');
        
        self.port.write_all(&cmd_bytes).await
            .map_err(|e| ProtocolError::ConnectionFailed(e.to_string()))?;

        // Read until ">" prompt
        let mut response = Vec::new();
        let mut buf = [0u8; 1];
        
        let timeout = tokio::time::sleep(self.timeout);
        tokio::pin!(timeout);

        loop {
            tokio::select! {
                result = self.port.read(&mut buf) => {
                    match result {
                        Ok(0) => return Err(ProtocolError::ConnectionFailed("Port closed".into())),
                        Ok(_) => {
                            if buf[0] == PROMPT {
                                break;
                            }
                            response.push(buf[0]);
                        }
                        Err(e) => return Err(ProtocolError::ConnectionFailed(e.to_string())),
                    }
                }
                _ = &mut timeout => {
                    return Err(ProtocolError::Timeout);
                }
            }
        }

        // Convert to string, strip whitespace
        let response_str = String::from_utf8_lossy(&response)
            .trim()
            .to_string();

        // Check for error responses
        if response_str.contains("ERROR") || response_str.contains("?") {
            return Err(ProtocolError::InvalidResponse(response_str));
        }

        Ok(response_str)
    }

    /// Query OBD2 PID (Mode + PID)
    pub async fn query_pid(&mut self, mode: u8, pid: u8) -> Result<Vec<u8>> {
        let cmd = format!("{:02X}{:02X}", mode, pid);
        let response = self.send_command(&cmd).await?;

        // Parse hex response: "41 0C 1A 2B" → [0x41, 0x0C, 0x1A, 0x2B]
        let bytes: Result<Vec<u8>> = response
            .split_whitespace()
            .map(|hex| u8::from_str_radix(hex, 16)
                .map_err(|_| ProtocolError::InvalidResponse(response.clone())))
            .collect();

        let bytes = bytes?;

        // Verify response mode matches (response mode = request mode + 0x40)
        if bytes.is_empty() || bytes[0] != mode + 0x40 {
            return Err(ProtocolError::InvalidResponse(response));
        }

        // Verify PID matches
        if bytes.len() < 2 || bytes[1] != pid {
            return Err(ProtocolError::InvalidResponse(response));
        }

        // Return data bytes (skip mode + pid)
        Ok(bytes[2..].to_vec())
    }

    /// Read Diagnostic Trouble Codes (Mode 03)
    pub async fn read_dtcs(&mut self) -> Result<Vec<u8>> {
        let response = self.send_command("03").await?;

        // Parse multi-line DTC response
        // Format: "43 02 01 33 00 00" (2 codes: P0133, P0000)
        let bytes: Result<Vec<u8>> = response
            .split_whitespace()
            .map(|hex| u8::from_str_radix(hex, 16)
                .map_err(|_| ProtocolError::InvalidResponse(response.clone())))
            .collect();

        let bytes = bytes?;

        // Verify response mode (0x43 = Mode 03 response)
        if bytes.is_empty() || bytes[0] != 0x43 {
            return Err(ProtocolError::InvalidResponse(response));
        }

        // Return DTC data (skip mode byte)
        Ok(bytes[1..].to_vec())
    }

    /// Clear Diagnostic Trouble Codes (Mode 04)
    pub async fn clear_dtcs(&mut self) -> Result<()> {
        let response = self.send_command("04").await?;

        // Mode 04 response is "44" (success)
        if !response.contains("44") {
            return Err(ProtocolError::InvalidResponse(response));
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // Note: These are integration tests that require real hardware
    // For CI/CD, consider mocking SerialStream with a trait

    #[tokio::test]
    #[ignore] // Requires hardware
    async fn test_connect_and_query_rpm() {
        let mut elm = ELM327::new("/dev/ttyUSB0", 38400)
            .await
            .expect("Failed to connect to ELM327");

        let data = elm.query_pid(0x01, 0x0C)
            .await
            .expect("Failed to query RPM");

        assert_eq!(data.len(), 2, "RPM data should be 2 bytes");
        
        let rpm = ((data[0] as u16) << 8 | data[1] as u16) / 4;
        println!("RPM: {}", rpm);
    }

    #[tokio::test]
    #[ignore] // Requires hardware
    async fn test_read_dtcs() {
        let mut elm = ELM327::new("/dev/ttyUSB0", 38400)
            .await
            .expect("Failed to connect to ELM327");

        let dtc_data = elm.read_dtcs()
            .await
            .expect("Failed to read DTCs");

        println!("DTC data: {:?}", dtc_data);
    }
}
