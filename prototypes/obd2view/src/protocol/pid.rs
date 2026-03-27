use std::fmt;

/// OBD2 Parameter ID definition
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Pid {
    pub mode: u8,
    pub id: u8,
}

impl Pid {
    pub const fn new(mode: u8, id: u8) -> Self {
        Self { mode, id }
    }

    /// Format as OBD2 command (e.g., "01 0C" for RPM)
    pub fn as_command(&self) -> String {
        format!("{:02X} {:02X}", self.mode, self.id)
    }

    /// Parse from response prefix (e.g., "41 0C" → Mode 01, PID 0C)
    pub fn from_response(bytes: &[u8]) -> Option<Self> {
        if bytes.len() >= 2 {
            Some(Self {
                mode: bytes[0] - 0x40, // Response mode = request mode + 0x40
                id: bytes[1],
            })
        } else {
            None
        }
    }
}

// Common Mode 01 PIDs
impl Pid {
    pub const ENGINE_RPM: Self = Self::new(0x01, 0x0C);
    pub const VEHICLE_SPEED: Self = Self::new(0x01, 0x0D);
    pub const COOLANT_TEMP: Self = Self::new(0x01, 0x05);
    pub const INTAKE_TEMP: Self = Self::new(0x01, 0x0F);
    pub const THROTTLE_POS: Self = Self::new(0x01, 0x11);
    pub const ENGINE_LOAD: Self = Self::new(0x01, 0x04);
    pub const MAF_RATE: Self = Self::new(0x01, 0x10);
    pub const FUEL_PRESSURE: Self = Self::new(0x01, 0x0A);
    pub const O2_BANK1_S1: Self = Self::new(0x01, 0x14);
    pub const SHORT_FUEL_TRIM_1: Self = Self::new(0x01, 0x06);
    pub const LONG_FUEL_TRIM_1: Self = Self::new(0x01, 0x07);

    // Backward compatibility aliases
    pub const RPM: Self = Self::ENGINE_RPM;
    pub const SPEED: Self = Self::VEHICLE_SPEED;

    /// Get PID code (ID byte)
    pub fn code(&self) -> u8 {
        self.id
    }

    /// Parse raw data for this PID
    pub fn parse(&self, data: &[u8]) -> anyhow::Result<PidValue> {
        Ok(PidValue::parse(*self, data))
    }
}

impl fmt::Display for Pid {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:02X}{:02X}", self.mode, self.id)
    }
}

/// Parsed PID value with units
#[derive(Debug, Clone)]
pub enum PidValue {
    Rpm(u16),
    Speed(u8), // km/h
    Temperature(i16), // Celsius
    Percentage(f32),
    Voltage(f32),
    Pressure(f32), // kPa
    MassAirFlow(f32), // g/s
    Unknown(Vec<u8>),
}

impl PidValue {
    /// Parse raw bytes into a value based on PID
    pub fn parse(pid: Pid, data: &[u8]) -> Self {
        match pid {
            Pid::RPM => {
                if data.len() >= 2 {
                    let rpm = ((data[0] as u16) << 8 | data[1] as u16) / 4;
                    PidValue::Rpm(rpm)
                } else {
                    PidValue::Unknown(data.to_vec())
                }
            }
            Pid::SPEED => {
                if !data.is_empty() {
                    PidValue::Speed(data[0])
                } else {
                    PidValue::Unknown(data.to_vec())
                }
            }
            Pid::COOLANT_TEMP | Pid::INTAKE_TEMP => {
                if !data.is_empty() {
                    let temp = data[0] as i16 - 40;
                    PidValue::Temperature(temp)
                } else {
                    PidValue::Unknown(data.to_vec())
                }
            }
            Pid::THROTTLE_POS | Pid::ENGINE_LOAD => {
                if !data.is_empty() {
                    let percent = (data[0] as f32 * 100.0) / 255.0;
                    PidValue::Percentage(percent)
                } else {
                    PidValue::Unknown(data.to_vec())
                }
            }
            Pid::MAF_RATE => {
                if data.len() >= 2 {
                    let maf = ((data[0] as u16) << 8 | data[1] as u16) as f32 / 100.0;
                    PidValue::MassAirFlow(maf)
                } else {
                    PidValue::Unknown(data.to_vec())
                }
            }
            Pid::FUEL_PRESSURE => {
                if !data.is_empty() {
                    let pressure = data[0] as f32 * 3.0; // kPa
                    PidValue::Pressure(pressure)
                } else {
                    PidValue::Unknown(data.to_vec())
                }
            }
            Pid::O2_BANK1_S1 => {
                if !data.is_empty() {
                    let voltage = data[0] as f32 / 200.0; // Volts
                    PidValue::Voltage(voltage)
                } else {
                    PidValue::Unknown(data.to_vec())
                }
            }
            Pid::SHORT_FUEL_TRIM_1 | Pid::LONG_FUEL_TRIM_1 => {
                if !data.is_empty() {
                    let percent = ((data[0] as i16 - 128) as f32 * 100.0) / 128.0;
                    PidValue::Percentage(percent)
                } else {
                    PidValue::Unknown(data.to_vec())
                }
            }
            _ => PidValue::Unknown(data.to_vec()),
        }
    }

    pub fn display(&self, imperial: bool) -> String {
        match self {
            PidValue::Rpm(rpm) => format!("{} rpm", rpm),
            PidValue::Speed(kmh) => {
                if imperial {
                    format!("{} mph", (*kmh as f32 * 0.621371) as u8)
                } else {
                    format!("{} km/h", kmh)
                }
            }
            PidValue::Temperature(celsius) => {
                if imperial {
                    let fahrenheit = (*celsius as f32 * 9.0 / 5.0) + 32.0;
                    format!("{:.0}°F", fahrenheit)
                } else {
                    format!("{}°C", celsius)
                }
            }
            PidValue::Percentage(p) => format!("{:.1}%", p),
            PidValue::Voltage(v) => format!("{:.2}V", v),
            PidValue::Pressure(kpa) => {
                if imperial {
                    format!("{:.1} psi", kpa * 0.145038)
                } else {
                    format!("{:.1} kPa", kpa)
                }
            }
            PidValue::MassAirFlow(maf) => format!("{:.2} g/s", maf),
            PidValue::Unknown(_) => "N/A".to_string(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rpm_parsing() {
        let data = vec![0x26, 0x1A]; // (0x26 * 256 + 0x1A) / 4 = 2438
        let value = PidValue::parse(Pid::RPM, &data);
        match value {
            PidValue::Rpm(rpm) => assert_eq!(rpm, 2438),
            _ => panic!("Expected RPM value"),
        }
    }

    #[test]
    fn test_temperature_parsing() {
        let data = vec![0xE1]; // 225 - 40 = 185°C
        let value = PidValue::parse(Pid::COOLANT_TEMP, &data);
        match value {
            PidValue::Temperature(temp) => assert_eq!(temp, 185),
            _ => panic!("Expected temperature value"),
        }
    }

    #[test]
    fn test_speed_conversion() {
        let value = PidValue::Speed(100); // 100 km/h
        assert_eq!(value.display(false), "100 km/h");
        assert_eq!(value.display(true), "62 mph");
    }
}
