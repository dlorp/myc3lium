// elm327/connection.rs - Serial port communication for ELM327 adapters

use std::io;
use std::time::Duration;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio_serial::{SerialPort, SerialPortBuilderExt, SerialStream};

/// ELM327 connection manager
pub struct Elm327Connection {
    port: BufReader<SerialStream>,
    timeout: Duration,
}

/// Protocol detection result
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Protocol {
    Auto,
    Iso9141_2,      // ISO 9141-2 (older vehicles)
    Kwp2000Fast,    // KWP2000 Fast (5 baud init)
    Kwp2000Slow,    // KWP2000 Slow
    CanIso15765_11, // CAN 11-bit ID (500 kbps)
    CanIso15765_29, // CAN 29-bit ID (500 kbps)
    CanIso15765_11_250, // CAN 11-bit ID (250 kbps)
    CanIso15765_29_250, // CAN 29-bit ID (250 kbps)
}

impl Protocol {
    pub fn to_elm_command(&self) -> &'static str {
        match self {
            Protocol::Auto => "ATSP0",
            Protocol::Iso9141_2 => "ATSP3",
            Protocol::Kwp2000Fast => "ATSP4",
            Protocol::Kwp2000Slow => "ATSP5",
            Protocol::CanIso15765_11 => "ATSP6",
            Protocol::CanIso15765_29 => "ATSP7",
            Protocol::CanIso15765_11_250 => "ATSP8",
            Protocol::CanIso15765_29_250 => "ATSP9",
        }
    }
}

/// ELM327 response type
#[derive(Debug, Clone)]
pub enum Response {
    Ok,
    Data(String),
    Error(String),
    NoData,
    Searching,
}

impl Elm327Connection {
    /// Open serial connection to ELM327 adapter
    pub async fn open(port_name: &str, baud_rate: u32) -> io::Result<Self> {
        let port = tokio_serial::new(port_name, baud_rate)
            .timeout(Duration::from_millis(500))
            .open_native_async()?;

        let port = BufReader::new(port);

        let mut conn = Self {
            port,
            timeout: Duration::from_millis(500),
        };

        // Initialize ELM327
        conn.initialize().await?;

        Ok(conn)
    }

    /// Initialize ELM327 adapter with default settings
    async fn initialize(&mut self) -> io::Result<()> {
        // Reset adapter
        self.send_command("ATZ").await?;
        tokio::time::sleep(Duration::from_millis(500)).await;

        // Turn off echo (cleaner responses)
        self.send_command("ATE0").await?;

        // Turn off line feeds (use only \r)
        self.send_command("ATL0").await?;

        // Turn off spaces in responses (compact hex)
        self.send_command("ATS0").await?;

        // Set timeout to default
        self.send_command("ATST32").await?; // 32 * 4ms = 128ms timeout

        // Allow long messages (for multi-frame responses)
        self.send_command("ATAL").await?;

        Ok(())
    }

    /// Send AT or OBD command and read response
    pub async fn send_command(&mut self, cmd: &str) -> io::Result<Response> {
        // Write command with carriage return
        self.port.get_mut().write_all(cmd.as_bytes()).await?;
        self.port.get_mut().write_all(b"\r").await?;
        self.port.get_mut().flush().await?;

        // Read response line(s) until prompt
        let mut lines = Vec::new();
        let mut buffer = String::new();

        loop {
            buffer.clear();

            // Read with timeout
            let read_result = tokio::time::timeout(
                self.timeout,
                self.port.read_line(&mut buffer),
            )
            .await;

            match read_result {
                Ok(Ok(0)) => {
                    return Err(io::Error::new(
                        io::ErrorKind::UnexpectedEof,
                        "Connection closed",
                    ))
                }
                Ok(Ok(_)) => {
                    let line = buffer.trim();

                    // Prompt character indicates end of response
                    if line == ">" || line.is_empty() {
                        break;
                    }

                    // Skip echo of command
                    if line == cmd {
                        continue;
                    }

                    lines.push(line.to_string());
                }
                Ok(Err(e)) => return Err(e),
                Err(_) => {
                    return Err(io::Error::new(
                        io::ErrorKind::TimedOut,
                        "Command timeout",
                    ))
                }
            }
        }

        // Parse response
        Ok(self.parse_response(&lines))
    }

    /// Parse ELM327 response lines
    fn parse_response(&self, lines: &[String]) -> Response {
        if lines.is_empty() {
            return Response::NoData;
        }

        // Single line responses
        if lines.len() == 1 {
            let line = &lines[0];
            return match line.as_str() {
                "OK" => Response::Ok,
                "SEARCHING..." => Response::Searching,
                "NO DATA" | "?" => Response::NoData,
                "ERROR" | "UNABLE TO CONNECT" => Response::Error(line.clone()),
                _ if line.starts_with("ERROR") => Response::Error(line.clone()),
                _ => Response::Data(line.clone()),
            };
        }

        // Multi-line data response (join all lines)
        let data = lines.join(" ");
        Response::Data(data)
    }

    /// Detect vehicle protocol automatically
    pub async fn detect_protocol(&mut self) -> io::Result<Protocol> {
        // Set to auto-detect mode
        self.send_command("ATSP0").await?;

        // Try to read a PID to trigger detection
        match self.send_command("0100").await? {
            Response::Data(_) | Response::Ok => {
                // Query current protocol
                match self.send_command("ATDPN").await? {
                    Response::Data(proto_num) => {
                        let protocol = match proto_num.trim() {
                            "3" => Protocol::Iso9141_2,
                            "4" => Protocol::Kwp2000Fast,
                            "5" => Protocol::Kwp2000Slow,
                            "6" => Protocol::CanIso15765_11,
                            "7" => Protocol::CanIso15765_29,
                            "8" => Protocol::CanIso15765_11_250,
                            "9" => Protocol::CanIso15765_29_250,
                            _ => Protocol::Auto,
                        };
                        Ok(protocol)
                    }
                    _ => Ok(Protocol::Auto),
                }
            }
            _ => Err(io::Error::new(
                io::ErrorKind::Other,
                "Failed to detect protocol",
            )),
        }
    }

    /// Set specific protocol (useful for faster connection)
    pub async fn set_protocol(&mut self, protocol: Protocol) -> io::Result<()> {
        self.send_command(protocol.to_elm_command()).await?;
        Ok(())
    }

    /// Read supported PIDs (Mode 01, PID 00, 20, 40, 60, 80, A0, C0, E0)
    pub async fn get_supported_pids(&mut self) -> io::Result<Vec<u8>> {
        let mut supported = Vec::new();

        // PID 00 shows support for PIDs 01-20
        if let Response::Data(data) = self.send_command("0100").await? {
            if let Some(pids) = self.parse_pid_support(&data) {
                supported.extend(pids);
            }
        }

        // PID 20 shows support for PIDs 21-40
        if let Response::Data(data) = self.send_command("0120").await? {
            if let Some(pids) = self.parse_pid_support(&data) {
                supported.extend(pids.iter().map(|p| p + 0x20));
            }
        }

        // Continue for PIDs 40, 60, 80, etc. if needed

        Ok(supported)
    }

    /// Parse PID support bitfield from response
    fn parse_pid_support(&self, data: &str) -> Option<Vec<u8>> {
        // Response format: "41 00 BE 1F A8 13" (example)
        // Skip mode+PID bytes (41 00), then parse 4 bytes as bitfield

        let hex_bytes: Vec<&str> = data.split_whitespace().collect();
        if hex_bytes.len() < 6 {
            return None;
        }

        let mut supported = Vec::new();
        for (byte_idx, hex) in hex_bytes.iter().skip(2).take(4).enumerate() {
            if let Ok(byte_val) = u8::from_str_radix(hex, 16) {
                for bit in 0..8 {
                    if byte_val & (1 << (7 - bit)) != 0 {
                        let pid = (byte_idx * 8 + bit + 1) as u8;
                        supported.push(pid);
                    }
                }
            }
        }

        Some(supported)
    }

    /// Close connection gracefully
    pub async fn close(&mut self) -> io::Result<()> {
        // Optional: Send close protocol command
        let _ = self.send_command("ATPC").await;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_protocol_commands() {
        assert_eq!(Protocol::Auto.to_elm_command(), "ATSP0");
        assert_eq!(Protocol::CanIso15765_11.to_elm_command(), "ATSP6");
    }

    #[test]
    fn test_parse_pid_support() {
        let conn = Elm327Connection {
            port: BufReader::new(/* mock */),
            timeout: Duration::from_millis(500),
        };

        // Example: 41 00 BE 1F A8 13
        // Binary: 10111110 00011111 10101000 00010011
        let data = "41 00 BE 1F A8 13";
        let supported = conn.parse_pid_support(data).unwrap();

        // Should include PIDs like 01, 03, 04, 05, 06, 07...
        assert!(supported.contains(&0x01)); // PID 01
        assert!(supported.contains(&0x03)); // PID 03
        assert!(supported.contains(&0x04)); // PID 04
    }
}
