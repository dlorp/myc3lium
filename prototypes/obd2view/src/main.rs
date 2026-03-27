use anyhow::Result;
use clap::Parser;
use std::path::PathBuf;

mod config;
mod data;
mod obd2;
mod protocol;
mod ui;

use config::Config;
use ui::App;

#[derive(Parser)]
#[command(name = "obd2view")]
#[command(about = "Terminal OBD2 diagnostic monitor", long_about = None)]
struct Cli {
    /// Serial device path (e.g., /dev/ttyUSB0)
    #[arg(short, long)]
    device: Option<String>,

    /// Config file path
    #[arg(short, long)]
    config: Option<PathBuf>,

    /// Enable debug logging
    #[arg(short, long)]
    debug: bool,

    /// List available serial devices
    #[arg(short, long)]
    list_devices: bool,
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();

    // Initialize logging
    if cli.debug {
        tracing_subscriber::fmt()
            .with_max_level(tracing::Level::DEBUG)
            .init();
    }

    // List devices mode
    if cli.list_devices {
        list_serial_devices()?;
        return Ok(());
    }

    // Load config
    let config = if let Some(path) = cli.config {
        Config::from_file(&path)?
    } else {
        Config::load_or_default()?
    };

    // Override device from CLI
    let config = if let Some(device) = cli.device {
        Config {
            device,
            ..config
        }
    } else {
        config
    };

    // Run TUI
    let mut app = App::new(config)?;
    app.run().await?;

    Ok(())
}

fn list_serial_devices() -> Result<()> {
    println!("Available serial devices:");
    let ports = tokio_serial::available_ports()?;
    
    if ports.is_empty() {
        println!("  (none found)");
    } else {
        for port in ports {
            println!("  - {}", port.port_name);
            if let tokio_serial::SerialPortType::UsbPort(info) = port.port_type {
                println!("    USB: {:04x}:{:04x}", info.vid, info.pid);
                if let Some(product) = info.product {
                    println!("    Product: {}", product);
                }
            }
        }
    }
    
    Ok(())
}
