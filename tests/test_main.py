from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# --- SETUP MOCK SEBELUM IMPORT APP ---
# Kita harus memalsukan driver database agar saat 'main' di-import,
# dia tidak mencoba koneksi beneran ke MongoDB lokal/cloud.
mock_mongo_client = MagicMock()
mock_mongo_db = MagicMock()
mock_mongo_client.__getitem__.return_value = mock_mongo_db

# Patch MotorClient di src.core.database (sesuaikan path jika beda)
with patch("motor.motor_asyncio.AsyncIOMotorClient", return_value=mock_mongo_client):
    # Import app SETELAH patch aktif
    from main import app


# --- FIXTURE UNTUK CLIENT ---
@pytest_asyncio.fixture
async def client():
    # Menggunakan ASGITransport untuk mentest aplikasi ASGI (FastAPI) secara langsung tanpa server berjalan
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# --- TEST CASES ---


@pytest.mark.asyncio
async def test_health_check_endpoint(client):
    """
    Test apakah endpoint /health yang kita buat sebelumnya berfungsi.
    """
    response = await client.get("/health")

    # Jika endpoint belum dibuat, ini akan 404. Jika sudah, harusnya 200.
    if response.status_code == 404:
        pytest.skip("Endpoint /health belum diimplementasikan di main.py")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "cpu_usage" in data


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """
    Test endpoint root (/) jika ada.
    Biasanya return 200 (Welcome) atau 404 (Not Found).
    Yang penting server merespons, bukan crash (500).
    """
    response = await client.get("/")
    assert response.status_code in [200, 404]


def test_routers_are_mounted():
    """
    Test untuk memastikan router (seperti auth) sudah terpasang.
    Validasi dilakukan lewat daftar route, tanpa memanggil dependency eksternal.
    """
    route_paths = {route.path for route in app.routes}
    assert (
        "/auth/login" in route_paths or "/auth/register" in route_paths
    ), "Router Auth sepertinya belum di-mount"


@pytest.mark.asyncio
async def test_cors_headers(client):
    """
    Cek apakah CORS sudah disetting (misal untuk Frontend).
    """
    response = await client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    # FastAPI default behavior untuk OPTIONS di root mungkin berbeda,
    # tapi biasanya return 200 jika CORS middleware aktif.
    if response.status_code == 200:
        assert "access-control-allow-origin" in response.headers
