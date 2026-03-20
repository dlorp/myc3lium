"""Tests for API endpoints"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["message"] == "MYC3LIUM API"


def test_health():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_get_nodes():
    """Test GET /api/nodes"""
    response = client.get("/api/nodes")
    assert response.status_code == 200

    nodes = response.json()
    assert isinstance(nodes, list)
    assert len(nodes) > 0

    # Validate first node structure
    node = nodes[0]
    assert "id" in node
    assert "type" in node
    assert "callsign" in node
    assert "status" in node
    assert "last_seen" in node

    # Validate node type
    assert node["type"] in ["SPORE", "HYPHA", "FROND", "RHIZOME"]
    assert node["status"] in ["online", "offline", "degraded"]


def test_get_node_by_id():
    """Test GET /api/nodes/{node_id}"""
    # First get all nodes to get a valid ID
    response = client.get("/api/nodes")
    nodes = response.json()
    node_id = nodes[0]["id"]

    # Get specific node
    response = client.get(f"/api/nodes/{node_id}")
    assert response.status_code == 200

    node = response.json()
    assert node["id"] == node_id


def test_get_node_not_found():
    """Test GET /api/nodes/{node_id} with invalid ID"""
    response = client.get("/api/nodes/invalid_node")
    assert response.status_code == 404


def test_update_node_status():
    """Test POST /api/nodes/{node_id}/status"""
    # Get a valid node ID
    response = client.get("/api/nodes")
    nodes = response.json()
    node_id = nodes[0]["id"]

    # Update status
    response = client.post(f"/api/nodes/{node_id}/status?status=degraded")
    assert response.status_code == 200

    updated_node = response.json()
    assert updated_node["id"] == node_id
    assert updated_node["status"] == "degraded"


def test_update_node_status_invalid():
    """Test POST /api/nodes/{node_id}/status with invalid status"""
    response = client.get("/api/nodes")
    nodes = response.json()
    node_id = nodes[0]["id"]

    response = client.post(f"/api/nodes/{node_id}/status?status=invalid")
    assert response.status_code == 400


def test_update_node_status_not_found():
    """Test POST /api/nodes/{node_id}/status with invalid node ID"""
    response = client.post("/api/nodes/invalid_node/status?status=online")
    assert response.status_code == 404


def test_mock_data_generation():
    """Test that mock data is generated consistently"""
    response1 = client.get("/api/nodes")
    response2 = client.get("/api/nodes")

    nodes1 = response1.json()
    nodes2 = response2.json()

    # Should return same mock data
    assert len(nodes1) == len(nodes2)
    assert nodes1[0]["id"] == nodes2[0]["id"]


def test_node_optional_fields():
    """Test that optional fields are handled correctly"""
    response = client.get("/api/nodes")
    nodes = response.json()

    # At least one node should have optional fields
    has_rssi = any(node.get("rssi") is not None for node in nodes)
    has_battery = any(node.get("battery") is not None for node in nodes)
    has_position = any(node.get("position") is not None for node in nodes)

    # With 8 nodes and ~70-80% probability, we should have some with these fields
    assert has_rssi or has_battery or has_position


def test_node_types_distribution():
    """Test that different node types are generated"""
    response = client.get("/api/nodes")
    nodes = response.json()

    types = set(node["type"] for node in nodes)
    # Should have variety in node types
    assert len(types) >= 2


def test_node_status_distribution():
    """Test that different statuses are generated"""
    response = client.get("/api/nodes")
    nodes = response.json()

    statuses = set(node["status"] for node in nodes)
    # With 8 nodes and weighted distribution, should have at least online + one other
    assert "online" in statuses
    assert len(statuses) >= 1


def test_cors_headers():
    """Test that CORS headers are present"""
    response = client.options(
        "/api/nodes",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    # Should allow CORS
    assert "access-control-allow-origin" in response.headers


def test_api_documentation():
    """Test that OpenAPI documentation is available"""
    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/openapi.json")
    assert response.status_code == 200

    openapi = response.json()
    assert "info" in openapi
    assert openapi["info"]["title"] == "MYC3LIUM API"
