"""Tests for MeshtasticService PyPubSub callback integration."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.meshtastic_service import MeshtasticService


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset MeshtasticService singleton between tests."""
    MeshtasticService._instance = None
    yield
    MeshtasticService._instance = None


@pytest.fixture
def mock_pub():
    """Mock the pub module for PyPubSub testing."""
    mock = MagicMock()
    with patch("app.services.meshtastic_service.pub", mock):
        yield mock


@pytest.fixture
def mock_serial():
    """Mock the serial interface and meshtastic modules."""
    mock_interface = MagicMock()
    # myInfo is a protobuf in Meshtastic 2.x, not a dict
    mock_my_info = MagicMock()
    mock_my_info.my_node_num = 123456
    mock_interface.myInfo = mock_my_info
    mock_interface.nodes = {
        "!abc123": {
            "num": 123456,
            "user": {"id": "!abc123", "shortName": "TST", "longName": "Test Node"},
        },
    }

    mock_serial_mod = MagicMock()
    mock_serial_mod.SerialInterface.return_value = mock_interface

    with (
        patch("app.services.meshtastic_service._serial", mock_serial_mod),
        patch("app.services.meshtastic_service._meshtastic", MagicMock()),
        patch("app.services.meshtastic_service._IMPORT_ATTEMPTED", True),
        patch("app.services.meshtastic_service.time"),
    ):
        yield mock_serial_mod, mock_interface


def test_start_subscribes_to_pypubsub_topics(mock_pub, mock_serial):
    """start() registers 3 PyPubSub subscriptions with correct topics."""
    service = MeshtasticService()
    result = service.start()

    assert result is True
    assert service._subscribed is True
    assert mock_pub.subscribe.call_count == 3

    topic_names = [c.args[1] for c in mock_pub.subscribe.call_args_list]
    assert "meshtastic.receive" in topic_names
    assert "meshtastic.connection.established" in topic_names
    assert "meshtastic.node.updated" in topic_names


def test_start_without_pypubsub_logs_warning(mock_serial):
    """start() succeeds but warns when PyPubSub is not available."""
    with patch("app.services.meshtastic_service.pub", None):
        service = MeshtasticService()
        result = service.start()

    assert result is True
    assert service._subscribed is False


def test_on_receive_keyword_args(mock_pub, mock_serial):
    """_on_receive accepts keyword args and stores message + fires ws_callback."""
    service = MeshtasticService()
    service.start()

    ws_callback = MagicMock()
    service.set_ws_callback(ws_callback)

    test_packet = {
        "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello mesh"},
        "fromId": "!node001",
        "rxTime": 1234567890.0,
        "rxSnr": 5.5,
        "rxRssi": -80,
        "hopLimit": 3,
        "channel": 0,
    }

    # PyPubSub calls with keyword args
    service._on_receive(packet=test_packet, interface=None)

    assert len(service._messages) == 1
    assert service._messages[0].text == "Hello mesh"
    assert service._messages[0].sender == "!node001"

    ws_callback.assert_called_once()
    event_type, data = ws_callback.call_args.args
    assert event_type == "meshtastic_message"
    assert data["text"] == "Hello mesh"


def test_on_connection_with_none_interface(mock_pub, mock_serial):
    """_on_connection does not raise when interface is None."""
    service = MeshtasticService()
    service.start()

    # Should not raise AttributeError
    service._on_connection(interface=None)


def test_on_node_info_updated_calls_ws_callback(mock_pub, mock_serial):
    """_on_node_info_updated fires ws_callback with correct data."""
    service = MeshtasticService()
    service.start()

    ws_callback = MagicMock()
    service.set_ws_callback(ws_callback)

    test_node = {
        "user": {"id": "!node002", "shortName": "N02", "longName": "Node Two"},
        "lastHeard": 1234567890.0,
        "snr": 8.0,
        "position": {"latitude": 40.0, "longitude": -74.0, "altitude": 100},
    }

    service._on_node_info_updated(node=test_node)

    assert "!node002" in service._nodes
    ws_callback.assert_called_once()
    event_type, data = ws_callback.call_args.args
    assert event_type == "meshtastic_node_updated"
    assert data["node_id"] == "!node002"
    assert data["short_name"] == "N02"
    assert data["position"]["lat"] == 40.0


def test_stop_unsubscribes_from_pypubsub(mock_pub, mock_serial):
    """stop() calls pub.unsubscribe for all 3 topics."""
    service = MeshtasticService()
    service.start()
    service.stop()

    assert mock_pub.unsubscribe.call_count == 3
    assert service._subscribed is False
    assert service._available is False

    topic_names = [c.args[1] for c in mock_pub.unsubscribe.call_args_list]
    assert "meshtastic.receive" in topic_names
    assert "meshtastic.connection.established" in topic_names
    assert "meshtastic.node.updated" in topic_names


def test_stop_without_prior_subscribe(mock_pub, mock_serial):
    """stop() skips unsubscribe when _subscribed is False but still closes interface."""
    service = MeshtasticService()
    service.start()

    # Simulate: pub was available but subscriptions somehow not registered
    service._subscribed = False
    mock_interface = mock_serial[1]

    service.stop()

    mock_pub.unsubscribe.assert_not_called()
    mock_interface.close.assert_called_once()
    assert service._available is False


def test_stop_unsubscribe_failure_does_not_block_close(mock_pub, mock_serial):
    """interface.close() still runs even if pub.unsubscribe raises."""
    service = MeshtasticService()
    service.start()

    mock_pub.unsubscribe.side_effect = Exception("Topic not found")
    mock_interface = mock_serial[1]

    service.stop()

    mock_interface.close.assert_called_once()
    assert service._available is False
    assert service._interface is None


def test_stop_nulls_interface(mock_pub, mock_serial):
    """stop() sets _interface to None to prevent use-after-close."""
    service = MeshtasticService()
    service.start()
    assert service._interface is not None

    service.stop()

    assert service._interface is None


def test_on_receive_sanitizes_input(mock_pub, mock_serial):
    """_on_receive caps text length and strips control characters."""
    service = MeshtasticService()
    service.start()

    test_packet = {
        "decoded": {
            "portnum": "TEXT_MESSAGE_APP",
            "text": "Hello\x00\x07World" + "A" * 500,
        },
        "fromId": "!node\x00bad",
        "rxTime": -999,
        "channel": 99,
    }

    service._on_receive(packet=test_packet, interface=None)

    assert len(service._messages) == 1
    msg = service._messages[0]
    # Control chars stripped
    assert "\x00" not in msg.text
    assert "\x07" not in msg.text
    assert "\x00" not in msg.sender
    # Text capped at 237 chars
    assert len(msg.text) <= 237
    # Invalid channel clamped to 0
    assert msg.channel == 0
    # Invalid timestamp replaced (not the original -999)
    assert msg.timestamp != -999


def test_on_receive_drops_non_text_packets(mock_pub, mock_serial):
    """_on_receive silently drops non-TEXT_MESSAGE_APP packets."""
    service = MeshtasticService()
    service.start()

    service._on_receive(packet={"decoded": {"portnum": "POSITION_APP"}}, interface=None)

    assert len(service._messages) == 0


def test_on_node_info_updated_with_none_node(mock_pub, mock_serial):
    """_on_node_info_updated returns early when node is None."""
    service = MeshtasticService()
    service.start()

    ws_callback = MagicMock()
    service.set_ws_callback(ws_callback)

    service._on_node_info_updated(node=None)

    assert len(service._nodes) == 0
    ws_callback.assert_not_called()
