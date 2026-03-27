pub mod elm327;
pub mod pid;
pub mod dtc;

pub use elm327::ELM327;
pub use pid::{Pid, PidValue};
pub use dtc::DTC;

use thiserror::Error;

#[derive(Error, Debug)]
pub enum ProtocolError {
    #[error("Serial I/O error: {0}")]
    SerialError(#[from] std::io::Error),
    
    #[error("Invalid response: {0}")]
    InvalidResponse(String),
    
    #[error("Timeout waiting for response")]
    Timeout,
    
    #[error("Checksum mismatch")]
    ChecksumError,
    
    #[error("Unsupported protocol")]
    UnsupportedProtocol,
    
    #[error("ECU error: {0}")]
    EcuError(String),
    
    #[error("Connection failed: {0}")]
    ConnectionFailed(String),
}

pub type Result<T> = std::result::Result<T, ProtocolError>;
