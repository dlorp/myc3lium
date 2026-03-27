use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub device: String,
    pub baud_rate: u32,
    pub protocol: String,
    pub theme: String,
    pub units: Units,
    pub refresh_rate: u8,
    pub logging_enabled: bool,
    pub log_path: PathBuf,
    pub vehicle_name: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Units {
    Imperial,
    Metric,
}

impl Default for Config {
    fn default() -> Self {
        let log_path = dirs::data_local_dir()
            .unwrap_or_else(|| PathBuf::from("."))
            .join("obd2view")
            .join("sessions");

        Config {
            device: "/dev/ttyUSB0".to_string(),
            baud_rate: 38400,
            protocol: "auto".to_string(),
            theme: "psx".to_string(),
            units: Units::Imperial,
            refresh_rate: 60,
            logging_enabled: true,
            log_path,
            vehicle_name: None,
        }
    }
}

impl Config {
    pub fn load_or_default() -> Result<Self> {
        let config_path = Self::default_config_path();
        
        if config_path.exists() {
            Self::from_file(&config_path)
        } else {
            Ok(Self::default())
        }
    }

    pub fn from_file(path: &Path) -> Result<Self> {
        let contents = fs::read_to_string(path)
            .with_context(|| format!("Failed to read config from {}", path.display()))?;
        
        toml::from_str(&contents)
            .with_context(|| format!("Failed to parse config from {}", path.display()))
    }

    pub fn save(&self, path: &Path) -> Result<()> {
        let contents = toml::to_string_pretty(self)
            .context("Failed to serialize config")?;
        
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)
                .context("Failed to create config directory")?;
        }
        
        fs::write(path, contents)
            .with_context(|| format!("Failed to write config to {}", path.display()))?;
        
        Ok(())
    }

    pub fn default_config_path() -> PathBuf {
        dirs::home_dir()
            .unwrap_or_else(|| PathBuf::from("."))
            .join(".obd2viewrc")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = Config::default();
        assert_eq!(config.baud_rate, 38400);
        assert_eq!(config.theme, "psx");
    }

    #[test]
    fn test_serialize_deserialize() {
        let config = Config::default();
        let toml = toml::to_string(&config).unwrap();
        let deserialized: Config = toml::from_str(&toml).unwrap();
        assert_eq!(deserialized.baud_rate, config.baud_rate);
    }
}
