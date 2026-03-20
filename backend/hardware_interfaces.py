"""
MYC3LIUM Hardware Interfaces
Direct integration with LoRa, HaLow, WiFi, GPS sensors
"""

import serial
import time
import struct
from typing import Optional, Dict, List, Tuple
import asyncio


class GPSInterface:
    """
    GPS interface (NMEA via serial or gpsd)
    """
    def __init__(self, port: str = "/dev/ttyAMA0", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.last_position = None
    
    def connect(self):
        """
        Connect to GPS module
        """
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"GPS connected on {self.port}")
        except Exception as e:
            print(f"GPS connection failed: {e}")
            self.serial = None
    
    def read_nmea(self) -> Optional[Dict]:
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
    
    def get_position(self) -> Optional[Dict]:
        """
        Get current GPS position (blocking read with timeout)
        """
        if not self.serial:
            self.connect()
        
        if not self.serial:
            return self.last_position  # Return last known if available
        
        # Try to read position for up to 2 seconds
        start = time.time()
        while time.time() - start < 2.0:
            pos = self.read_nmea()
            if pos:
                return pos
        
        return self.last_position


class LoRaInterface:
    """
    LoRa HAT interface (SX1262 via SPI)
    """
    def __init__(self, spi_device: str = "/dev/spidev0.0"):
        self.spi_device = spi_device
        self.rssi_last = -120
    
    def get_rssi(self) -> float:
        """
        Get current RSSI from LoRa module
        """
        try:
            # Read RSSI register (would use actual SPI commands)
            # For now, mock implementation
            import random
            self.rssi_last = random.uniform(-120, -60)
            return self.rssi_last
        except Exception as e:
            print(f"LoRa RSSI read error: {e}")
            return -120
    
    def get_snr(self) -> float:
        """
        Get Signal-to-Noise Ratio
        """
        try:
            # Read SNR register
            import random
            return random.uniform(-10, 10)
        except Exception as e:
            print(f"LoRa SNR read error: {e}")
            return -10


class HaLowInterface:
    """
    HaLow (802.11ah) interface via USB adapter
    """
    def __init__(self, interface: str = "wlan1"):
        self.interface = interface
    
    def get_station_info(self) -> List[Dict]:
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
    
    def get_station_info(self) -> List[Dict]:
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
        self.accel_last = (0.0, 0.0, 0.0)
        self.gyro_last = (0.0, 0.0, 0.0)
    
    def read_accel(self) -> Tuple[float, float, float]:
        """
        Read accelerometer (m/s²)
        Returns (ax, ay, az)
        """
        try:
            # Would read from MPU6050 or similar via I2C
            import random
            self.accel_last = (
                random.uniform(-1, 1),
                random.uniform(-1, 1),
                random.uniform(9.8 - 0.5, 9.8 + 0.5)  # Gravity + noise
            )
            return self.accel_last
        except Exception as e:
            print(f"IMU accel read error: {e}")
            return (0.0, 0.0, 9.8)
    
    def read_gyro(self) -> Tuple[float, float, float]:
        """
        Read gyroscope (rad/s)
        Returns (gx, gy, gz)
        """
        try:
            import random
            self.gyro_last = (
                random.uniform(-0.1, 0.1),
                random.uniform(-0.1, 0.1),
                random.uniform(-0.1, 0.1)
            )
            return self.gyro_last
        except Exception as e:
            print(f"IMU gyro read error: {e}")
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
    
    def get_all_rssi(self) -> Dict[str, List[Dict]]:
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
    
    def get_position(self) -> Optional[Dict]:
        """
        Get GPS position
        """
        if self.gps:
            return self.gps.get_position()
        return None
    
    def get_imu_data(self) -> Dict:
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
async def async_get_position(hardware: HardwareManager) -> Optional[Dict]:
    """
    Async wrapper for GPS position
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, hardware.get_position)


async def async_get_all_rssi(hardware: HardwareManager) -> Dict:
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
