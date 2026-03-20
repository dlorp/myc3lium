"""
MYC3LIUM Hardware Interfaces
Direct integration with LoRa, HaLow, WiFi, GPS sensors
"""

import asyncio
import time
from typing import Optional


class GPSInterface:
    """
    GPS interface (NMEA via serial or gpsd)
    Uses real driver with robust error handling
    """
    def __init__(self, port: str = "/dev/ttyAMA0", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.driver = None
        self.last_position = None

        # Try to use real driver
        try:
            from hardware_drivers_real import GPS_NMEA_Driver
            self.driver = GPS_NMEA_Driver(port, baudrate)
            self.driver.connect()
        except Exception as e:
            print(f"GPS real driver unavailable: {e}")
            self.driver = None

    def connect(self):
        """
        Connect to GPS module
        """
        if self.driver:
            return self.driver.connect()
        return False

    def read_nmea(self) -> Optional[dict]:
        """
        Read and parse NMEA sentence
        Returns position dict or None
        """
        if not self.serial:
            return None

        try:
            line = self.serial.readline().decode('ascii', errors='ignore').strip()

            # Parse GGA sentence (Global Positioning System Fix Data)
            if line.startswith('$GPGGA') or line.startswith('$GNGGA'):
                parts = line.split(',')

                if len(parts) < 10:
                    return None

                # Parse latitude
                lat_raw = parts[2]
                lat_dir = parts[3]
                if lat_raw and lat_dir:
                    lat_deg = float(lat_raw[:2])
                    lat_min = float(lat_raw[2:])
                    lat = lat_deg + (lat_min / 60.0)
                    if lat_dir == 'S':
                        lat = -lat
                else:
                    return None

                # Parse longitude
                lon_raw = parts[4]
                lon_dir = parts[5]
                if lon_raw and lon_dir:
                    lon_deg = float(lon_raw[:3])
                    lon_min = float(lon_raw[3:])
                    lon = lon_deg + (lon_min / 60.0)
                    if lon_dir == 'W':
                        lon = -lon
                else:
                    return None

                # Parse altitude
                alt = float(parts[9]) if parts[9] else 0.0

                # Quality indicator (0=invalid, 1=GPS, 2=DGPS)
                quality = int(parts[6]) if parts[6] else 0

                # Number of satellites
                num_sats = int(parts[7]) if parts[7] else 0

                # HDOP (horizontal dilution of precision)
                hdop = float(parts[8]) if parts[8] else 99.9

                # Estimate accuracy from HDOP
                # Rule of thumb: accuracy ≈ HDOP * UERE (UERE ≈ 5m for GPS)
                accuracy = hdop * 5.0

                position = {
                    'lat': lat,
                    'lon': lon,
                    'alt': alt,
                    'accuracy': accuracy,
                    'quality': quality,
                    'satellites': num_sats,
                    'timestamp': time.time()
                }

                self.last_position = position
                return position

        except Exception as e:
            print(f"NMEA parse error: {e}")
            return None

        return None

    def get_position(self) -> Optional[dict]:
        """
        Get current GPS position (blocking read with timeout)
        """
        if self.driver:
            pos = self.driver.get_position()
            if pos:
                self.last_position = pos
            return pos or self.last_position

        return self.last_position


class LoRaInterface:
    """
    LoRa HAT interface (SX1262 via SPI)
    Uses real driver when available, falls back to null
    """
    def __init__(self, spi_device: str = "/dev/spidev0.0"):
        self.spi_device = spi_device
        self.driver = None

        # Try to use real driver
        try:
            from hardware_drivers_real import SX1262LoRaDriver
            spi_bus, spi_dev = 0, 0  # Extract from spi_device path
            self.driver = SX1262LoRaDriver(spi_bus, spi_dev)
        except Exception as e:
            print(f"LoRa real driver unavailable: {e}")
            self.driver = None

    def get_rssi(self) -> float:
        """
        Get current RSSI from LoRa module
        """
        if self.driver:
            return self.driver.get_rssi()

        # No hardware available
        return -120.0

    def get_snr(self) -> float:
        """
        Get Signal-to-Noise Ratio
        """
        if self.driver:
            return self.driver.get_snr()

        return -10.0


class HaLowInterface:
    """
    HaLow (802.11ah) interface via USB adapter
    """
    def __init__(self, interface: str = "wlan1"):
        self.interface = interface

    def get_station_info(self) -> list[dict]:
        """
        Get connected station info (RSSI, signal quality)
        """
        import subprocess

        try:
            result = subprocess.run(
                ['iw', 'dev', self.interface, 'station', 'dump'],
                capture_output=True,
                text=True,
                timeout=2
            )

            stations = []
            current_station = None

            for line in result.stdout.split('\n'):
                if line.startswith('Station'):
                    if current_station:
                        stations.append(current_station)

                    mac = line.split()[1]
                    current_station = {'mac': mac, 'interface': self.interface}

                elif current_station:
                    if 'signal:' in line:
                        current_station['rssi'] = int(line.split()[1])
                    elif 'rx bitrate:' in line:
                        parts = line.split()
                        if len(parts) > 2:
                            current_station['rx_bitrate'] = float(parts[2])
                    elif 'tx bitrate:' in line:
                        parts = line.split()
                        if len(parts) > 2:
                            current_station['tx_bitrate'] = float(parts[2])

            if current_station:
                stations.append(current_station)

            return stations

        except Exception as e:
            print(f"HaLow station info error: {e}")
            return []


class WiFiInterface:
    """
    WiFi (2.4/5 GHz) interface
    """
    def __init__(self, interface: str = "wlan0"):
        self.interface = interface

    def get_station_info(self) -> list[dict]:
        """
        Get connected station info
        """
        # Same as HaLow but different interface
        halow = HaLowInterface(self.interface)
        return halow.get_station_info()


class IMUInterface:
    """
    IMU (Inertial Measurement Unit) interface
    For dead reckoning when GPS unavailable
    """
    def __init__(self, i2c_bus: int = 1, address: int = 0x68):
        self.i2c_bus = i2c_bus
        self.address = address
        self.driver = None

        # Try to use real driver
        try:
            from hardware_drivers_real import MPU6050_IMU_Driver
            self.driver = MPU6050_IMU_Driver(i2c_bus)
        except Exception as e:
            print(f"IMU real driver unavailable: {e}")
            self.driver = None

    def read_accel(self) -> tuple[float, float, float]:
        """
        Read accelerometer (m/s²)
        Returns (ax, ay, az)
        """
        if self.driver:
            return self.driver.read_accel()

        return (0.0, 0.0, 9.8)

    def read_gyro(self) -> tuple[float, float, float]:
        """
        Read gyroscope (rad/s)
        Returns (gx, gy, gz)
        """
        if self.driver:
            return self.driver.read_gyro()

        return (0.0, 0.0, 0.0)


class HardwareManager:
    """
    Unified hardware interface manager
    Automatically detects and initializes available sensors
    """
    def __init__(self):
        self.gps = None
        self.lora = None
        self.halow = None
        self.wifi = None
        self.imu = None

        self.detect_hardware()

    def detect_hardware(self):
        """
        Auto-detect available hardware
        """
        import os
        import subprocess

        # Detect GPS
        if os.path.exists('/dev/ttyAMA0'):
            self.gps = GPSInterface('/dev/ttyAMA0')
            print("✓ GPS detected on /dev/ttyAMA0")
        elif os.path.exists('/dev/ttyUSB0'):
            self.gps = GPSInterface('/dev/ttyUSB0')
            print("✓ GPS detected on /dev/ttyUSB0")
        else:
            print("✗ GPS not detected")

        # Detect LoRa (SPI)
        if os.path.exists('/dev/spidev0.0'):
            self.lora = LoRaInterface('/dev/spidev0.0')
            print("✓ LoRa HAT detected on SPI0")
        else:
            print("✗ LoRa HAT not detected")

        # Detect HaLow (check for wlan1)
        try:
            result = subprocess.run(
                ['iw', 'dev', 'wlan1', 'info'],
                capture_output=True,
                timeout=1
            )
            if result.returncode == 0:
                self.halow = HaLowInterface('wlan1')
                print("✓ HaLow detected on wlan1")
        except:
            print("✗ HaLow not detected")

        # Detect WiFi (wlan0 always present on Pi)
        try:
            result = subprocess.run(
                ['iw', 'dev', 'wlan0', 'info'],
                capture_output=True,
                timeout=1
            )
            if result.returncode == 0:
                self.wifi = WiFiInterface('wlan0')
                print("✓ WiFi detected on wlan0")
        except:
            print("✗ WiFi not detected")

        # Detect IMU (I2C)
        if os.path.exists('/dev/i2c-1'):
            self.imu = IMUInterface(i2c_bus=1)
            print("✓ IMU detected on I2C bus 1")
        else:
            print("✗ IMU not detected")

    def get_all_rssi(self) -> dict[str, list[dict]]:
        """
        Get RSSI from all available radios
        """
        rssi_data = {}

        if self.lora:
            rssi_data['lora'] = [{'rssi': self.lora.get_rssi(), 'snr': self.lora.get_snr()}]

        if self.halow:
            rssi_data['halow'] = self.halow.get_station_info()

        if self.wifi:
            rssi_data['wifi'] = self.wifi.get_station_info()

        return rssi_data

    def get_position(self) -> Optional[dict]:
        """
        Get GPS position
        """
        if self.gps:
            return self.gps.get_position()
        return None

    def get_imu_data(self) -> dict:
        """
        Get IMU accelerometer + gyroscope
        """
        if self.imu:
            accel = self.imu.read_accel()
            gyro = self.imu.read_gyro()

            return {
                'accel': {'x': accel[0], 'y': accel[1], 'z': accel[2]},
                'gyro': {'x': gyro[0], 'y': gyro[1], 'z': gyro[2]}
            }

        return {'accel': None, 'gyro': None}


# Async wrappers for FastAPI
async def async_get_position(hardware: HardwareManager) -> Optional[dict]:
    """
    Async wrapper for GPS position
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, hardware.get_position)


async def async_get_all_rssi(hardware: HardwareManager) -> dict:
    """
    Async wrapper for RSSI collection
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, hardware.get_all_rssi)


if __name__ == "__main__":
    # Test hardware detection
    print("Detecting hardware...")
    hw = HardwareManager()

    print("\nGPS position:")
    pos = hw.get_position()
    if pos:
        print(f"  Lat: {pos['lat']:.6f}, Lon: {pos['lon']:.6f}, Alt: {pos['alt']:.1f}m")
        print(f"  Accuracy: ±{pos['accuracy']:.1f}m, Sats: {pos['satellites']}")
    else:
        print("  No GPS fix")

    print("\nRSSI from all radios:")
    rssi = hw.get_all_rssi()
    for radio, data in rssi.items():
        print(f"  {radio.upper()}: {data}")

    print("\nIMU data:")
    imu = hw.get_imu_data()
    if imu['accel']:
        print(f"  Accel: {imu['accel']}")
        print(f"  Gyro: {imu['gyro']}")
    else:
        print("  No IMU data")
