"""Edge device enrollment and registration client."""
import logging
import uuid
from typing import Any, Dict, Optional, Tuple

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger("communication.registration")


def get_mac_address() -> str:
    """Retrieve device hardware MAC address or deterministic fallback."""
    mac_num = uuid.getnode()
    mac_hex = ":".join(f"{(mac_num >> elements) & 0xff:02x}" for elements in range(40, -1, -8))
    return mac_hex


class DeviceRegistrationClient:
    """Handles device enrollment handshake with FastAPI Device Gateway."""

    def __init__(
        self,
        backend_url: str = "http://localhost:8000",
        device_id: str = "edge-dev-001",
        store_id: str = "store_001",
        provisioning_token: Optional[str] = None,
        timeout_seconds: float = 5.0,
    ):
        self.backend_url = backend_url.rstrip("/")
        self.device_id = device_id
        self.store_id = store_id
        self.provisioning_token = provisioning_token
        self.timeout_seconds = timeout_seconds

    def check_reachability(self) -> Tuple[bool, str]:
        """Check if backend gateway is reachable."""
        if not httpx:
            return False, "httpx not installed"
        endpoint = f"{self.backend_url}/health"
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                res = client.get(endpoint)
                if res.status_code == 200:
                    return True, "Backend reachable and healthy"
                return False, f"Backend returned status {res.status_code}"
        except Exception as e:
            return False, f"Connection failed: {e}"

    def register(self) -> Dict[str, Any]:
        """Enroll or verify device registration against backend."""
        if not httpx:
            return {"status": "ERROR", "message": "httpx library not available"}

        endpoint = f"{self.backend_url}/api/v1/devices/register"
        headers = {"Content-Type": "application/json"}
        if self.provisioning_token:
            headers["Authorization"] = f"Bearer {self.provisioning_token}"

        payload = {
            "deviceId": self.device_id,
            "storeId": self.store_id,
            "hardwareModel": "Retail-Edge-AI-Node",
            "macAddress": get_mac_address(),
            "firmwareVersion": "1.0.0",
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                res = client.post(endpoint, json=payload, headers=headers)
                if res.status_code in (200, 201):
                    data = res.json()
                    logger.info(f"Device {self.device_id} successfully enrolled / validated with store {self.store_id}")
                    return {
                        "status": "AUTHORIZED",
                        "deviceId": self.device_id,
                        "storeId": self.store_id,
                        "data": data,
                    }
                else:
                    logger.warning(f"Registration rejected with status {res.status_code}: {res.text}")
                    return {
                        "status": "UNAUTHORIZED",
                        "statusCode": res.status_code,
                        "message": res.text,
                    }
        except Exception as e:
            logger.error(f"Device registration error: {e}")
            return {"status": "ERROR", "message": str(e)}
