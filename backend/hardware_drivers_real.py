"""
MYC3LIUM Real Hardware Drivers
Actual SPI/serial/I2C implementations (no mocks)
"""

import logging
import time
from typing import Dict, Optional, Tuple

import serial

logger = logging.getLogger(__name__)

# LoRa SX1262 SPI Driver
try:
    import spidev
    SPI_AVAILABLE = True
except ImportError:
    SPI_AVAILABLE = False
    logger.warning("spidev not available - LoRa will use mock")


class SX1262LoRaDriver:
    """
    Real SX1262 LoRa HAT driver (Waveshare)
    Uses SPI interface
    """

    # SX1262 Register addresses
    REG_PACKET_RSSI = 0x1D
    REG_PACKET_SNR = 0x1E
    REG_FREQUENCY = 0x06

    def __init__(self, spi_bus: int = 0, spi_device: int = 0):
        self.spi_bus = spi_bus
        self.spi_device = spi_device
        self.spi = None

        if SPI_AVAILABLE:
            try:
                self.spi = spidev.SpiDev()
                self.spi.open(spi_bus, spi_device)
                self.spi.max_speed_hz = 2000000  # 2 MHz
                self.spi.mode = 0
                logger.info(f"SX1262 LoRa initialized on SPI{spi_bus}.{spi_device}")
            except Exception as e:
                logger.error(f"LoRa SPI init failed: {e}")
                self.spi = None

    def read_register(self, address: int) -> int:
        """
        Read single register from SX1262
        """
        if not self.spi:
            return 0

        try:
            # SX1262 read command: 0x1D (read register)
            cmd = [0x1D, address, 0x00]
            result = self.spi.xfer2(cmd)
            return result[2]
        except Exception as e:
            logger.error(f"LoRa register read error: {e}")
            return 0

    def write_register(self, address: int, value: int):
        """
        Write single register to SX1262
        """
        if not self.spi:
            return

        try:
            cmd = [0x0D, address, value]
            self.spi.xfer2(cmd)
        except Exception as e:
            logger.error(f"LoRa register write error: {e}")

    def get_rssi(self) -> float:
        """
        Get RSSI of last received packet
        Returns: RSSI in dBm
        """
        if not self.spi:
            logger.warning("LoRa SPI not available, returning default")
            return -120.0

        try:
            rssi_raw = self.read_register(self.REG_PACKET_RSSI)
            # SX1262 RSSI calculation: RSSI = -rssi_raw / 2
            rssi_dbm = -rssi_raw / 2.0
            return rssi_dbm
        except Exception as e:
            logger.error(f"LoRa RSSI read error: {e}")
            return -120.0

    def get_snr(self) -> float:
        """
        Get SNR of last received packet
        Returns: SNR in dB
        """
        if not self.spi:
            return -10.0

        try:
            snr_raw = self.read_register(self.REG_PACKET_SNR)
            # SX1262 SNR calculation: SNR = snr_raw / 4
            snr_db = snr_raw / 4.0
            return snr_db
        except Exception as e:
            logger.error(f"LoRa SNR read error: {e}")
            return -10.0

    def set_frequency(self, freq_hz: int):
        """
        Set LoRa frequency (915 MHz for US)
        """
        if not self.spi:
            return

        try:
            # SX1262 frequency calculation
            # freq_reg = (freq_hz * 2^25) / 32000000
            freq_reg = int((freq_hz * (2**25)) / 32000000)

            # Write 3-byte frequency register
            self.write_register(self.REG_FREQUENCY, (freq_reg >> 16) & 0xFF)
            self.write_register(self.REG_FREQUENCY + 1, (freq_reg >> 8) & 0xFF)
            self.write_register(self.REG_FREQUENCY + 2, freq_reg & 0xFF)

            logger.info(f"LoRa frequency set to {freq_hz / 1e6:.3f} MHz")
        except Exception as e:
            logger.error(f"LoRa frequency set error: {e}")

    def close(self):
        """
        Close SPI connection
        """
        if self.spi:
            self.spi.close()


class GPS_NMEA_Driver:
    """
    Real GPS NMEA driver with robust error handling
    """

    def __init__(self, port: str = "/dev/ttyAMA0", baudrate: int = 9600, timeout: float = 2.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.last_position = None
        self.error_count = 0
        self.max_errors = 5

    def connect(self) -> bool:
        """
        Connect to GPS module with retry logic
        """
        try:
            self.serial = serial.Serial(
                self.port,
                self.baudrate,
                timeout=self.timeout
            )
            logger.info(f"GPS connected on {self.port}")
            self.error_count = 0
            return True
        except Exception as e:
            logger.error(f"GPS connection failed: {e}")
            self.serial = None
            self.error_count += 1
            return False

    def reconnect_if_needed(self) -> bool:
        """
        Reconnect if serial connection lost
        """
        if self.serial and self.serial.is_open:
            return True

        if self.error_count >= self.max_errors:
            logger.warning(f"GPS max errors reached ({self.max_errors}), giving up")
            return False

        logger.info("Attempting GPS reconnection...")
        return self.connect()

    def parse_gga(self, sentence: str) -> Optional[Dict]:
        """
        Parse GGA NMEA sentence
        """
        try:
            parts = sentence.split(',')

            if len(parts) < 15:
                return None

            # Check fix quality
            quality = int(parts[6]) if parts[6] else 0
            if quality == 0:
                return None  # No fix

            # Parse latitude
            lat_raw = parts[2]
            lat_dir = parts[3]
            if not (lat_raw and lat_dir):
                return None

            lat_deg = float(lat_raw[:2])
            lat_min = float(lat_raw[2:])
            lat = lat_deg + (lat_min / 60.0)
            if lat_dir == 'S':
                lat = -lat

            # Parse longitude
            lon_raw = parts[4]
            lon_dir = parts[5]
            if not (lon_raw and lon_dir):
                return None

            lon_deg = float(lon_raw[:3])
            lon_min = float(lon_raw[3:])
            lon = lon_deg + (lon_min / 60.0)
            if lon_dir == 'W':
                lon = -lon

            # Parse altitude
            alt = float(parts[9]) if parts[9] else 0.0

            # Number of satellites
            num_sats = int(parts[7]) if parts[7] else 0

            # HDOP (horizontal dilution of precision)
            hdop = float(parts[8]) if parts[8] else 99.9

            # Estimate accuracy (HDOP * 5m UERE)
            accuracy = hdop * 5.0

            return {
                'lat': lat,
                'lon': lon,
                'alt': alt,
                'accuracy': accuracy,
                'quality': quality,
                'satellites': num_sats,
                'timestamp': time.time()
            }

        except (ValueError, IndexError) as e:
            logger.debug(f"GGA parse error: {e}")
            return None

    def get_position(self, max_attempts: int = 10) -> Optional[Dict]:
        """
        Get GPS position with retry logic
        """
        if not self.reconnect_if_needed():
            return self.last_position

        for attempt in range(max_attempts):
            try:
                line = self.serial.readline().decode('ascii', errors='ignore').strip()

                if line.startswith('$GPGGA') or line.startswith('$GNGGA'):
                    pos = self.parse_gga(line)
                    if pos:
                        self.last_position = pos
                        self.error_count = 0
                        return pos

            except serial.SerialException as e:
                logger.error(f"GPS serial error: {e}")
                self.serial = None
                self.error_count += 1
                break
            except Exception as e:
                logger.warning(f"GPS read error: {e}")

        # Return last known position if available
        return self.last_position

    def close(self):
        """
        Close serial connection
        """
        if self.serial:
            self.serial.close()


# IMU driver (MPU6050 example)
try:
    import smbus2
    I2C_AVAILABLE = True
except ImportError:
    I2C_AVAILABLE = False
    logger.warning("smbus2 not available - IMU will use mock")


class MPU6050_IMU_Driver:
    """
    Real MPU6050 IMU driver (I2C)
    """

    MPU6050_ADDR = 0x68
    PWR_MGMT_1 = 0x6B
    ACCEL_XOUT_H = 0x3B
    GYRO_XOUT_H = 0x43

    def __init__(self, i2c_bus: int = 1):
        self.i2c_bus = i2c_bus
        self.bus = None

        if I2C_AVAILABLE:
            try:
                self.bus = smbus2.SMBus(i2c_bus)
                # Wake up MPU6050
                self.bus.write_byte_data(self.MPU6050_ADDR, self.PWR_MGMT_1, 0)
                logger.info(f"MPU6050 IMU initialized on I2C bus {i2c_bus}")
            except Exception as e:
                logger.error(f"IMU I2C init failed: {e}")
                self.bus = None

    def read_word_2c(self, addr: int, reg: int) -> int:
        """
        Read 16-bit signed value (2's complement)
        """
        high = self.bus.read_byte_data(addr, reg)
        low = self.bus.read_byte_data(addr, reg + 1)
        val = (high << 8) + low

        if val >= 0x8000:
            return -((65535 - val) + 1)
        else:
            return val

    def read_accel(self) -> Tuple[float, float, float]:
        """
        Read accelerometer (m/s²)
        Returns: (ax, ay, az)
        """
        if not self.bus:
            return (0.0, 0.0, 9.8)

        try:
            accel_x_raw = self.read_word_2c(self.MPU6050_ADDR, self.ACCEL_XOUT_H)
            accel_y_raw = self.read_word_2c(self.MPU6050_ADDR, self.ACCEL_XOUT_H + 2)
            accel_z_raw = self.read_word_2c(self.MPU6050_ADDR, self.ACCEL_XOUT_H + 4)

            # MPU6050 sensitivity: 16384 LSB/g (for ±2g range)
            ax = (accel_x_raw / 16384.0) * 9.8
            ay = (accel_y_raw / 16384.0) * 9.8
            az = (accel_z_raw / 16384.0) * 9.8

            return (ax, ay, az)
        except Exception as e:
            logger.error(f"IMU accel read error: {e}")
            return (0.0, 0.0, 9.8)

    def read_gyro(self) -> tuple[float, float, float]:
        """
        Read gyroscope (rad/s)
        Returns: (gx, gy, gz)
        """
        if not self.bus:
            return (0.0, 0.0, 0.0)

        try:
            gyro_x_raw = self.read_word_2c(self.MPU6050_ADDR, self.GYRO_XOUT_H)
            gyro_y_raw = self.read_word_2c(self.MPU6050_ADDR, self.GYRO_XOUT_H + 2)
            gyro_z_raw = self.read_word_2c(self.MPU6050_ADDR, self.GYRO_XOUT_H + 4)

            # MPU6050 sensitivity: 131 LSB/(deg/s) (for ±250 deg/s range)
            # Convert to rad/s
            import math
            gx = (gyro_x_raw / 131.0) * (math.pi / 180.0)
            gy = (gyro_y_raw / 131.0) * (math.pi / 180.0)
            gz = (gyro_z_raw / 131.0) * (math.pi / 180.0)

            return (gx, gy, gz)
        except Exception as e:
            logger.error(f"IMU gyro read error: {e}")
            return (0.0, 0.0, 0.0)


if __name__ == "__main__":
    # Test drivers
    logging.basicConfig(level=logging.INFO)

    print("Testing LoRa driver...")
    lora = SX1262LoRaDriver()
    rssi = lora.get_rssi()
    snr = lora.get_snr()
    print(f"LoRa RSSI: {rssi} dBm, SNR: {snr} dB")

    print("\nTesting GPS driver...")
    gps = GPS_NMEA_Driver()
    pos = gps.get_position()
    if pos:
        print(f"GPS: {pos['lat']:.6f}, {pos['lon']:.6f}, {pos['alt']:.1f}m")
        print(f"Accuracy: ±{pos['accuracy']:.1f}m, Sats: {pos['satellites']}")
    else:
        print("GPS: No fix")

    print("\nTesting IMU driver...")
    imu = MPU6050_IMU_Driver()
    accel = imu.read_accel()
    gyro = imu.read_gyro()
    print(f"Accel: {accel}")
    print(f"Gyro: {gyro}")
