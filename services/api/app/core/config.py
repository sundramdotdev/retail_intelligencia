from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_prefix: str = "/api/v1"
    project_name: str = "Retail Intelligencia Device Gateway"
    version: str = "1.0.0"

    # Data Service connection
    data_service_url: str = "http://localhost:5000"
    internal_service_secret: str = "internal_data_secret_2026"

    # MQTT Broker
    mqtt_enabled: bool = True
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None
    mqtt_tls: bool = False
    mqtt_client_id: str = "fastapi-gateway-01"
    environment: str = "dev"

    # Security & Tokens
    device_tokens: List[str] = ["devkey_edge_001_secret", "devkey_demo_secret"]
    human_jwt_secret: str = "super_secret_jwt_key_for_human_auth_2026"

    cors_origins: List[str] = ["*"]


settings = Settings()
