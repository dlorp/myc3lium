// elm327/pid.rs - OBD-II PID definitions and decoders

use std::fmt;

/// Standard OBD-II Mode 01 PIDs
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
#[repr(u8)]
pub enum PidId {
    SupportedPids00 = 0x00,
    MonitorStatus = 0x01,
    FreezeDtc = 0x02,
    FuelSystemStatus = 0x03,
    EngineLoad = 0x04,
    CoolantTemp = 0x05,
    ShortFuelTrim1 = 0x06,
    LongFuelTrim1 = 0x07,
    ShortFuelTrim2 = 0x08,
    LongFuelTrim2 = 0x09,
    FuelPressure = 0x0A,
    IntakeManifoldPressure = 0x0B,
    EngineRpm = 0x0C,
    VehicleSpeed = 0x0D,
    TimingAdvance = 0x0E,
    IntakeAirTemp = 0x0F,
    MafAirFlow = 0x10,
    ThrottlePosition = 0x11,
    OxygenSensor1 = 0x14,
    OxygenSensor2 = 0x15,
    OxygenSensor3 = 0x16,
    OxygenSensor4 = 0x17,
    SupportedPids20 = 0x20,
    DistanceWithMil = 0x21,
    FuelRailPressure = 0x22,
    FuelRailGaugePressure = 0x23,
    CommandedEgr = 0x2C,
    EgrError = 0x2D,
    FuelLevel = 0x2F,
    DistanceSinceCodesClear = 0x31,
    BarometricPressure = 0x33,
    CatalystTempB1S1 = 0x3C,
    SupportedPids40 = 0x40,
    ControlModuleVoltage = 0x42,
    AbsoluteLoadValue = 0x43,
    AmbientAirTemp = 0x46,
    TimeWithMil = 0x4D,
    TimeSinceCodesClear = 0x4E,
    FuelType = 0x51,
    EthanolFuelPercent = 0x52,
    SupportedPids60 = 0x60,
    EngineFuelRate = 0x5E,
}

impl PidId {
    pub fn from_u8(value: u8) -> Option<Self> {
        match value {
            0x00 => Some(Self::SupportedPids00),
            0x01 => Some(Self::MonitorStatus),
            0x04 => Some(Self::EngineLoad),
            0x05 => Some(Self::CoolantTemp),
            0x0B => Some(Self::IntakeManifoldPressure),
            0x0C => Some(Self::EngineRpm),
            0x0D => Some(Self::VehicleSpeed),
            0x0E => Some(Self::TimingAdvance),
            0x0F => Some(Self::IntakeAirTemp),
            0x10 => Some(Self::MafAirFlow),
            0x11 => Some(Self::ThrottlePosition),
            0x14 => Some(Self::OxygenSensor1),
            0x15 => Some(Self::OxygenSensor2),
            0x2F => Some(Self::FuelLevel),
            0x42 => Some(Self::ControlModuleVoltage),
            0x46 => Some(Self::AmbientAirTemp),
            0x5E => Some(Self::EngineFuelRate),
            _ => None,
        }
    }

    pub fn name(&self) -> &'static str {
        match self {
            Self::EngineLoad => "Engine Load",
            Self::CoolantTemp => "Coolant Temp",
            Self::IntakeManifoldPressure => "Intake Pressure",
            Self::EngineRpm => "RPM",
            Self::VehicleSpeed => "Speed",
            Self::TimingAdvance => "Timing Advance",
            Self::IntakeAirTemp => "Intake Air Temp",
            Self::MafAirFlow => "MAF",
            Self::ThrottlePosition => "Throttle Position",
            Self::OxygenSensor1 => "O2 Sensor B1S1",
            Self::OxygenSensor2 => "O2 Sensor B1S2",
            Self::FuelLevel => "Fuel Level",
            Self::ControlModuleVoltage => "ECU Voltage",
            Self::AmbientAirTemp => "Ambient Temp",
            Self::EngineFuelRate => "Fuel Rate",
            _ => "Unknown",
        }
    }

    pub fn unit(&self) -> &'static str {
        match self {
            Self::EngineLoad => "%",
            Self::CoolantTemp => "°C",
            Self::IntakeManifoldPressure => "kPa",
            Self::EngineRpm => "rpm",
            Self::VehicleSpeed => "km/h",
            Self::TimingAdvance => "° BTDC",
            Self::IntakeAirTemp => "°C",
            Self::MafAirFlow => "g/s",
            Self::ThrottlePosition => "%",
            Self::OxygenSensor1 | Self::OxygenSensor2 => "V",
            Self::FuelLevel => "%",
            Self::ControlModuleVoltage => "V",
            Self::AmbientAirTemp => "°C",
            Self::EngineFuelRate => "L/h",
            _ => "",
        }
    }

    /// Decode raw bytes from OBD response
    pub fn decode(&self, bytes: &[u8]) -> Option<PidValue> {
        match self {
            // A (single byte, 0-100%)
            Self::EngineLoad | Self::ThrottlePosition | Self::FuelLevel => {
                Some(PidValue::Percentage(bytes.get(0)? * 100 / 255))
            }

            // A - 40 (temperature in Celsius)
            Self::CoolantTemp | Self::IntakeAirTemp | Self::AmbientAirTemp => {
                Some(PidValue::Temperature(*bytes.get(0)? as i16 - 40))
            }

            // ((A * 256) + B) / 4 (RPM)
            Self::EngineRpm => {
                let a = *bytes.get(0)? as u16;
                let b = *bytes.get(1)? as u16;
                Some(PidValue::Rpm(((a << 8) | b) / 4))
            }

            // A (speed in km/h)
            Self::VehicleSpeed => Some(PidValue::Speed(*bytes.get(0)? as u16)),

            // A (pressure in kPa)
            Self::IntakeManifoldPressure => {
                Some(PidValue::Pressure(*bytes.get(0)? as u16))
            }

            // (A - 128) / 2 (timing advance in degrees)
            Self::TimingAdvance => {
                let a = *bytes.get(0)? as i16;
                Some(PidValue::Angle((a - 128) as f32 / 2.0))
            }

            // ((A * 256) + B) / 100 (MAF in g/s)
            Self::MafAirFlow => {
                let a = *bytes.get(0)? as u16;
                let b = *bytes.get(1)? as u16;
                Some(PidValue::MassFlow(((a << 8) | b) as f32 / 100.0))
            }

            // A / 200 (O2 sensor voltage)
            Self::OxygenSensor1 | Self::OxygenSensor2 => {
                Some(PidValue::Voltage(*bytes.get(0)? as f32 / 200.0))
            }

            // ((A * 256) + B) / 1000 (ECU voltage)
            Self::ControlModuleVoltage => {
                let a = *bytes.get(0)? as u16;
                let b = *bytes.get(1)? as u16;
                Some(PidValue::Voltage(((a << 8) | b) as f32 / 1000.0))
            }

            // ((A * 256) + B) / 20 (fuel rate in L/h)
            Self::EngineFuelRate => {
                let a = *bytes.get(0)? as u16;
                let b = *bytes.get(1)? as u16;
                Some(PidValue::FuelRate(((a << 8) | b) as f32 / 20.0))
            }

            _ => None,
        }
    }
}

/// Decoded PID value with proper type
#[derive(Debug, Clone, PartialEq)]
pub enum PidValue {
    Percentage(u8),     // 0-100%
    Temperature(i16),   // Celsius
    Rpm(u16),           // Revolutions per minute
    Speed(u16),         // km/h
    Pressure(u16),      // kPa
    Angle(f32),         // Degrees
    MassFlow(f32),      // g/s
    Voltage(f32),       // Volts
    FuelRate(f32),      // L/h
}

impl PidValue {
    /// Convert to imperial units where applicable
    pub fn to_imperial(&self) -> String {
        match self {
            Self::Temperature(c) => {
                let f = (*c as f32 * 9.0 / 5.0) + 32.0;
                format!("{:.0}°F", f)
            }
            Self::Speed(kph) => {
                let mph = *kph as f32 * 0.621371;
                format!("{:.0} mph", mph)
            }
            Self::Pressure(kpa) => {
                let psi = *kpa as f32 * 0.145038;
                format!("{:.1} psi", psi)
            }
            _ => self.to_string(),
        }
    }

    /// Convert to metric display
    pub fn to_metric(&self) -> String {
        self.to_string()
    }

    /// Get numeric value (for graphing/logging)
    pub fn as_f32(&self) -> f32 {
        match self {
            Self::Percentage(v) => *v as f32,
            Self::Temperature(v) => *v as f32,
            Self::Rpm(v) => *v as f32,
            Self::Speed(v) => *v as f32,
            Self::Pressure(v) => *v as f32,
            Self::Angle(v) => *v,
            Self::MassFlow(v) => *v,
            Self::Voltage(v) => *v,
            Self::FuelRate(v) => *v,
        }
    }
}

impl fmt::Display for PidValue {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Percentage(v) => write!(f, "{}%", v),
            Self::Temperature(v) => write!(f, "{}°C", v),
            Self::Rpm(v) => write!(f, "{} rpm", v),
            Self::Speed(v) => write!(f, "{} km/h", v),
            Self::Pressure(v) => write!(f, "{} kPa", v),
            Self::Angle(v) => write!(f, "{:.1}° BTDC", v),
            Self::MassFlow(v) => write!(f, "{:.2} g/s", v),
            Self::Voltage(v) => write!(f, "{:.2}V", v),
            Self::FuelRate(v) => write!(f, "{:.2} L/h", v),
        }
    }
}

/// Parse OBD response hex string to bytes
pub fn parse_hex_response(response: &str) -> Option<(PidId, Vec<u8>)> {
    let parts: Vec<&str> = response.split_whitespace().collect();
    if parts.len() < 2 {
        return None;
    }

    // First byte should be 0x41 (response to Mode 01)
    if parts[0] != "41" {
        return None;
    }

    // Second byte is PID
    let pid_byte = u8::from_str_radix(parts[1], 16).ok()?;
    let pid = PidId::from_u8(pid_byte)?;

    // Remaining bytes are data
    let data: Vec<u8> = parts[2..]
        .iter()
        .filter_map(|s| u8::from_str_radix(s, 16).ok())
        .collect();

    Some((pid, data))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rpm_decode() {
        let pid = PidId::EngineRpm;
        let bytes = vec![0x1A, 0xF8]; // (0x1A << 8 | 0xF8) / 4 = 1726
        let value = pid.decode(&bytes).unwrap();
        assert_eq!(value, PidValue::Rpm(1726));
    }

    #[test]
    fn test_coolant_temp_decode() {
        let pid = PidId::CoolantTemp;
        let bytes = vec![0xB4]; // 180 - 40 = 140°C
        let value = pid.decode(&bytes).unwrap();
        assert_eq!(value, PidValue::Temperature(140));
    }

    #[test]
    fn test_maf_decode() {
        let pid = PidId::MafAirFlow;
        let bytes = vec![0x05, 0xF0]; // (0x05F0) / 100 = 15.2 g/s
        let value = pid.decode(&bytes).unwrap();
        match value {
            PidValue::MassFlow(v) => assert!((v - 15.2).abs() < 0.01),
            _ => panic!("Wrong type"),
        }
    }

    #[test]
    fn test_parse_response() {
        let response = "41 0C 1A F8";
        let (pid, data) = parse_hex_response(response).unwrap();
        assert_eq!(pid, PidId::EngineRpm);
        assert_eq!(data, vec![0x1A, 0xF8]);
    }

    #[test]
    fn test_imperial_conversion() {
        let temp = PidValue::Temperature(90); // 90°C
        assert_eq!(temp.to_imperial(), "194°F"); // Should be 194°F

        let speed = PidValue::Speed(100); // 100 km/h
        assert!(speed.to_imperial().starts_with("62")); // ~62 mph
    }
}
