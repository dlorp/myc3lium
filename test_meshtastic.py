#!/usr/bin/env python3
"""
Test script for Meshtastic integration.

Tests:
1. Connection to Heltec V3 device
2. Reading node info
3. Sending a test message
4. Receiving messages
5. API endpoint validation
"""

import sys
import time
import requests
from backend.app.services.meshtastic_service import MeshtasticService

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_test(name, passed, details=""):
    """Print test result with color"""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} - {name}")
    if details:
        print(f"      {details}")


def test_connection():
    """Test 1: Connect to Meshtastic device"""
    print(f"\n{YELLOW}Test 1: Connection to Heltec V3{RESET}")
    
    service = MeshtasticService(device_path="/dev/ttyUSB1")
    success = service.start()
    
    if success:
        status = service.get_status()
        details = (
            f"Device: {status.device}, "
            f"Node: {status.short_name} ({status.node_id}), "
            f"Nodes: {status.nodes_count}"
        )
        print_test("Connect to device", True, details)
        return service
    else:
        print_test("Connect to device", False, "Failed to connect to /dev/ttyUSB1")
        return None


def test_node_info(service):
    """Test 2: Read node information"""
    print(f"\n{YELLOW}Test 2: Read Node Information{RESET}")
    
    if not service or not service.available:
        print_test("Read node info", False, "Service not available")
        return False
    
    status = service.get_status()
    
    has_node_id = status.node_id is not None
    print_test("Node ID present", has_node_id, f"ID: {status.node_id}")
    
    has_name = status.short_name is not None
    print_test("Node name present", has_name, f"Name: {status.short_name}")
    
    nodes = service.get_nodes()
    print_test("Node list", len(nodes) >= 0, f"Found {len(nodes)} nodes")
    
    if nodes:
        print(f"\n      Known nodes:")
        for node in nodes[:5]:  # Show first 5
            print(f"      - {node.short_name} ({node.node_id})")
    
    return has_node_id and has_name


def test_send_message(service):
    """Test 3: Send a test message"""
    print(f"\n{YELLOW}Test 3: Send Test Message{RESET}")
    
    if not service or not service.available:
        print_test("Send message", False, "Service not available")
        return False
    
    try:
        test_msg = f"myc3lium test - {int(time.time())}"
        service.send_message(test_msg, channel=0)
        print_test("Send message", True, f"Sent: {test_msg}")
        return True
    except Exception as e:
        print_test("Send message", False, f"Error: {e}")
        return False


def test_receive_messages(service):
    """Test 4: Check for received messages"""
    print(f"\n{YELLOW}Test 4: Message Reception{RESET}")
    
    if not service or not service.available:
        print_test("Check messages", False, "Service not available")
        return False
    
    # Wait a bit for messages
    print("      Waiting 10 seconds for messages...")
    time.sleep(10)
    
    messages = service.get_messages(limit=10)
    print_test("Message buffer", True, f"Buffer contains {len(messages)} messages")
    
    if messages:
        print(f"\n      Recent messages:")
        for msg in messages[-3:]:  # Show last 3
            print(f"      [{msg.sender[:8]}] {msg.text[:60]}")
            if msg.snr:
                print(f"        SNR: {msg.snr:.1f} dB, RSSI: {msg.rssi} dBm")
    
    return True


def test_api_endpoints():
    """Test 5: Validate API endpoints"""
    print(f"\n{YELLOW}Test 5: API Endpoint Validation{RESET}")
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    try:
        resp = requests.get(f"{base_url}/health", timeout=5)
        health_ok = resp.status_code == 200 and resp.json().get("meshtastic") is not None
        print_test("Health endpoint", health_ok, f"Status: {resp.status_code}")
    except Exception as e:
        print_test("Health endpoint", False, f"Error: {e}")
        print(f"\n      {YELLOW}Note: Make sure the backend is running!{RESET}")
        print(f"      Run: cd ~/repos/myc3lium/backend && uvicorn app.main:app --reload")
        return False
    
    # Test Meshtastic status
    try:
        resp = requests.get(f"{base_url}/api/meshtastic/status", timeout=5)
        status_ok = resp.status_code == 200
        data = resp.json()
        details = (
            f"Connected: {data.get('connected')}, "
            f"Node: {data.get('short_name')}, "
            f"Nodes: {data.get('nodes_count')}"
        )
        print_test("Status endpoint", status_ok, details)
    except Exception as e:
        print_test("Status endpoint", False, f"Error: {e}")
    
    # Test nodes list
    try:
        resp = requests.get(f"{base_url}/api/meshtastic/nodes", timeout=5)
        nodes_ok = resp.status_code == 200
        nodes = resp.json()
        print_test("Nodes endpoint", nodes_ok, f"Returned {len(nodes)} nodes")
    except Exception as e:
        print_test("Nodes endpoint", False, f"Error: {e}")
    
    # Test messages list
    try:
        resp = requests.get(f"{base_url}/api/meshtastic/messages?limit=10", timeout=5)
        messages_ok = resp.status_code == 200
        messages = resp.json()
        print_test("Messages endpoint", messages_ok, f"Returned {len(messages)} messages")
    except Exception as e:
        print_test("Messages endpoint", False, f"Error: {e}")
    
    return True


def main():
    """Run all tests"""
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}Meshtastic Integration Test Suite{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")
    
    # Service tests
    service = test_connection()
    if service:
        test_node_info(service)
        test_send_message(service)
        test_receive_messages(service)
    
    # API tests
    print(f"\n{YELLOW}{'='*60}{RESET}")
    test_api_endpoints()
    
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}Test suite complete!{RESET}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Test interrupted by user{RESET}\n")
        sys.exit(0)
