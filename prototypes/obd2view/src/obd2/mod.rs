// OBD2 manager - high-level interface for vehicle communication
// Handles caching, batch queries, and connection lifecycle

use crate::config::Config;
use crate::protocol::{ELM327, Pid, PidValue, DTC};
use anyhow::Result;
use std::collections::HashMap;
use std::time::{Duration, Instant};

/// Default cache TTL: 200ms (5 Hz polling rate)
const DEFAULT_CACHE_DURATION: Duration = Duration::from_millis(200);

pub struct OBD2Manager {
    elm: ELM327,
    cache: HashMap<Pid, (PidValue, Instant)>,
    cache_duration: Duration,
}

impl OBD2Manager {
    /// Connect to ELM327 adapter and initialize
    pub async fn connect(config: &Config) -> Result<Self> {
        let elm = ELM327::new(&config.device, config.baud_rate).await?;

        Ok(Self {
            elm,
            cache: HashMap::new(),
            cache_duration: DEFAULT_CACHE_DURATION,
        })
    }

    /// Get PID value (uses cache if fresh)
    pub async fn get_pid(&mut self, pid: Pid) -> Result<PidValue> {
        // Check cache
        if let Some((value, timestamp)) = self.cache.get(&pid) {
            if timestamp.elapsed() < self.cache_duration {
                return Ok(value.clone());
            }
        }

        // Query ELM327
        let mode = 0x01; // Mode 01: Current data
        let pid_code = pid.code();
        
        let data = self.elm.query_pid(mode, pid_code).await?;
        let value = pid.parse(&data)?;

        // Update cache
        self.cache.insert(pid, (value.clone(), Instant::now()));

        Ok(value)
    }

    /// Batch query multiple PIDs (TODO: optimize with multi-PID requests)
    pub async fn get_pids(&mut self, pids: &[Pid]) -> Result<HashMap<Pid, PidValue>> {
        let mut results = HashMap::new();

        for pid in pids {
            match self.get_pid(*pid).await {
                Ok(value) => {
                    results.insert(*pid, value);
                }
                Err(e) => {
                    eprintln!("Failed to query {:?}: {}", pid, e);
                }
            }
        }

        Ok(results)
    }

    /// Read all Diagnostic Trouble Codes
    pub async fn read_dtcs(&mut self) -> Result<Vec<DTC>> {
        let data = self.elm.read_dtcs().await?;

        // Parse DTC data: [count, code1_hi, code1_lo, code2_hi, code2_lo, ...]
        if data.is_empty() {
            return Ok(Vec::new());
        }

        let count = data[0] as usize;
        let mut dtcs = Vec::new();

        for i in 0..count {
            let offset = 1 + (i * 2);
            if offset + 1 < data.len() {
                let code_bytes = [data[offset], data[offset + 1]];
                if let Some(dtc) = DTC::from_bytes(code_bytes) {
                    dtcs.push(dtc);
                }
            }
        }

        Ok(dtcs)
    }

    /// Clear all Diagnostic Trouble Codes
    pub async fn clear_dtcs(&mut self) -> Result<()> {
        self.elm.clear_dtcs().await?;
        Ok(())
    }

    /// Clear PID cache (force fresh reads)
    pub fn clear_cache(&mut self) {
        self.cache.clear();
    }

    /// Set cache duration
    pub fn set_cache_duration(&mut self, duration: Duration) {
        self.cache_duration = duration;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    #[ignore] // Requires hardware
    async fn test_manager_connect_and_query() {
        let config = Config::default();
        let mut manager = OBD2Manager::connect(&config)
            .await
            .expect("Failed to connect");

        let rpm = manager.get_pid(Pid::EngineRPM)
            .await
            .expect("Failed to get RPM");

        println!("RPM: {:?}", rpm);
    }

    #[tokio::test]
    #[ignore] // Requires hardware
    async fn test_cache_behavior() {
        let config = Config::default();
        let mut manager = OBD2Manager::connect(&config)
            .await
            .expect("Failed to connect");

        // First read (cache miss)
        let start = Instant::now();
        let _rpm1 = manager.get_pid(Pid::EngineRPM).await.unwrap();
        let first_duration = start.elapsed();

        // Second read (cache hit)
        let start = Instant::now();
        let _rpm2 = manager.get_pid(Pid::EngineRPM).await.unwrap();
        let second_duration = start.elapsed();

        // Cache hit should be significantly faster
        assert!(second_duration < first_duration / 10);
    }
}
