// Data layer - SQLite session storage and CSV export
// TODO: Implement database schema, session logging

use anyhow::Result;
use rusqlite::Connection;
use std::path::Path;

pub struct Database {
    conn: Connection,
}

impl Database {
    pub fn open(path: &Path) -> Result<Self> {
        // TODO: Open SQLite, create schema if needed
        unimplemented!("Database::open not yet implemented")
    }

    pub fn start_session(&mut self, vehicle_name: Option<&str>) -> Result<i64> {
        // TODO: Insert session record, return session_id
        unimplemented!("start_session not yet implemented")
    }

    pub fn log_reading(&mut self, session_id: i64, pid: &str, value: f64, unit: &str) -> Result<()> {
        // TODO: Insert reading into database
        unimplemented!("log_reading not yet implemented")
    }

    pub fn log_dtc(&mut self, session_id: i64, code: &str, description: &str) -> Result<()> {
        // TODO: Insert DTC into database
        unimplemented!("log_dtc not yet implemented")
    }

    pub fn end_session(&mut self, session_id: i64) -> Result<()> {
        // TODO: Update session end_time
        unimplemented!("end_session not yet implemented")
    }
}
