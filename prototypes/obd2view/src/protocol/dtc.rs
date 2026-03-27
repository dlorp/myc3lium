use std::fmt;

/// Diagnostic Trouble Code
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DTC {
    pub code: String,
    pub description: String,
}

impl DTC {
    /// Parse DTC from 2-byte array
    pub fn from_bytes(bytes: [u8; 2]) -> Option<Self> {
        // Filter out empty codes (0x0000)
        if bytes[0] == 0x00 && bytes[1] == 0x00 {
            return None;
        }

        Some(Self::from_bytes_unchecked(bytes[0], bytes[1]))
    }

    /// Parse DTC from 2-byte hex value (unchecked)
    /// Format: First 2 bits = code type, next 2 bits = system, last 12 bits = number
    fn from_bytes_unchecked(b1: u8, b2: u8) -> Self {
        let code_type = (b1 >> 6) & 0x03;
        let system = (b1 >> 4) & 0x03;
        let number = ((b1 & 0x0F) as u16) << 8 | b2 as u16;

        let prefix = match code_type {
            0x00 => 'P', // Powertrain
            0x01 => 'C', // Chassis
            0x02 => 'B', // Body
            0x03 => 'U', // Network
            _ => '?',
        };

        let code = format!("{}{:04X}", prefix, (system << 12) | number);
        let description = Self::lookup_description(&code);

        Self { code, description }
    }

    /// Parse multiple DTCs from response bytes
    /// Response format: "43 NN XX XX YY YY ..." where NN = count, XX XX = first DTC, etc.
    pub fn parse_response(data: &[u8]) -> Vec<Self> {
        if data.len() < 2 || data[0] != 0x43 {
            return vec![];
        }

        let count = data[1] as usize;
        let mut dtcs = Vec::new();

        for i in 0..count {
            let offset = 2 + (i * 2);
            if offset + 1 < data.len() {
                let dtc = Self::from_bytes(data[offset], data[offset + 1]);
                // Filter out empty codes (0x0000)
                if data[offset] != 0x00 || data[offset + 1] != 0x00 {
                    dtcs.push(dtc);
                }
            }
        }

        dtcs
    }

    /// Lookup DTC description (common codes only)
    fn lookup_description(code: &str) -> String {
        match code {
            // Common P0xxx codes
            "P0100" => "Mass or Volume Air Flow Circuit Malfunction",
            "P0101" => "Mass or Volume Air Flow Circuit Range/Performance",
            "P0102" => "Mass or Volume Air Flow Circuit Low Input",
            "P0103" => "Mass or Volume Air Flow Circuit High Input",
            "P0104" => "Mass or Volume Air Flow Circuit Intermittent",
            "P0105" => "Manifold Absolute Pressure/Barometric Pressure Circuit",
            "P0106" => "Manifold Absolute Pressure/Barometric Pressure Circuit Range/Performance",
            "P0107" => "Manifold Absolute Pressure/Barometric Pressure Circuit Low Input",
            "P0108" => "Manifold Absolute Pressure/Barometric Pressure Circuit High Input",
            "P0109" => "Manifold Absolute Pressure/Barometric Pressure Circuit Intermittent",
            "P0110" => "Intake Air Temperature Circuit",
            "P0111" => "Intake Air Temperature Circuit Range/Performance",
            "P0112" => "Intake Air Temperature Circuit Low Input",
            "P0113" => "Intake Air Temperature Circuit High Input",
            "P0114" => "Intake Air Temperature Circuit Intermittent",
            "P0115" => "Engine Coolant Temperature Circuit",
            "P0116" => "Engine Coolant Temperature Circuit Range/Performance",
            "P0117" => "Engine Coolant Temperature Circuit Low Input",
            "P0118" => "Engine Coolant Temperature Circuit High Input",
            "P0119" => "Engine Coolant Temperature Circuit Intermittent",
            "P0120" => "Throttle Position Sensor/Switch A Circuit",
            "P0121" => "Throttle Position Sensor/Switch A Circuit Range/Performance",
            "P0122" => "Throttle Position Sensor/Switch A Circuit Low Input",
            "P0123" => "Throttle Position Sensor/Switch A Circuit High Input",
            "P0130" => "O2 Sensor Circuit (Bank 1, Sensor 1)",
            "P0131" => "O2 Sensor Circuit Low Voltage (Bank 1, Sensor 1)",
            "P0132" => "O2 Sensor Circuit High Voltage (Bank 1, Sensor 1)",
            "P0133" => "O2 Sensor Circuit Slow Response (Bank 1, Sensor 1)",
            "P0134" => "O2 Sensor Circuit No Activity Detected (Bank 1, Sensor 1)",
            "P0135" => "O2 Sensor Heater Circuit (Bank 1, Sensor 1)",
            "P0171" => "System Too Lean (Bank 1)",
            "P0172" => "System Too Rich (Bank 1)",
            "P0174" => "System Too Lean (Bank 2)",
            "P0175" => "System Too Rich (Bank 2)",
            "P0300" => "Random/Multiple Cylinder Misfire Detected",
            "P0301" => "Cylinder 1 Misfire Detected",
            "P0302" => "Cylinder 2 Misfire Detected",
            "P0303" => "Cylinder 3 Misfire Detected",
            "P0304" => "Cylinder 4 Misfire Detected",
            "P0305" => "Cylinder 5 Misfire Detected",
            "P0306" => "Cylinder 6 Misfire Detected",
            "P0325" => "Knock Sensor 1 Circuit (Bank 1 or Single Sensor)",
            "P0335" => "Crankshaft Position Sensor A Circuit",
            "P0340" => "Camshaft Position Sensor Circuit",
            "P0420" => "Catalyst System Efficiency Below Threshold (Bank 1)",
            "P0430" => "Catalyst System Efficiency Below Threshold (Bank 2)",
            "P0440" => "Evaporative Emission Control System",
            "P0441" => "Evaporative Emission Control System Incorrect Purge Flow",
            "P0442" => "Evaporative Emission Control System Leak Detected (Small Leak)",
            "P0443" => "Evaporative Emission Control System Purge Control Valve Circuit",
            "P0455" => "Evaporative Emission Control System Leak Detected (Large Leak)",
            "P0500" => "Vehicle Speed Sensor A",
            "P0505" => "Idle Control System",
            "P0506" => "Idle Control System RPM Lower Than Expected",
            "P0507" => "Idle Control System RPM Higher Than Expected",
            "P0700" => "Transmission Control System Malfunction",
            "P0705" => "Transmission Range Sensor Circuit (PRNDL Input)",
            "P0710" => "Transmission Fluid Temperature Sensor Circuit",
            "P0715" => "Input/Turbine Speed Sensor Circuit",
            "P0720" => "Output Speed Sensor Circuit",
            "P0725" => "Engine Speed Input Circuit",
            "P0730" => "Incorrect Gear Ratio",
            
            // Default for unknown codes
            _ => format!("Unknown code ({})", code),
        }.to_string()
    }
}

impl fmt::Display for DTC {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}: {}", self.code, self.description)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dtc_parsing() {
        // P0133 = 0x0133 → 0x01, 0x33
        let dtc = DTC::from_bytes(0x01, 0x33);
        assert_eq!(dtc.code, "P0133");
        assert!(dtc.description.contains("O2 Sensor"));
    }

    #[test]
    fn test_dtc_response() {
        // Response: 43 02 01 33 04 20 (2 codes: P0133, P0420)
        let data = vec![0x43, 0x02, 0x01, 0x33, 0x04, 0x20];
        let dtcs = DTC::parse_response(&data);
        assert_eq!(dtcs.len(), 2);
        assert_eq!(dtcs[0].code, "P0133");
        assert_eq!(dtcs[1].code, "P0420");
    }

    #[test]
    fn test_empty_dtc() {
        // Response: 43 00 (no codes)
        let data = vec![0x43, 0x00];
        let dtcs = DTC::parse_response(&data);
        assert_eq!(dtcs.len(), 0);
    }
}
