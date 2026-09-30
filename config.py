from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://geoagentic:geoagentic@localhost:5432/geoagentic"
    osrm_base_url: str = "https://router.project-osrm.org"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    deviation_buffer_meters: float = 50
    civilian_alert_radius_meters: float = 500
    telemetry_interval_seconds: float = 2
    allowed_origins: str = "http://localhost:5173,http://localhost:5174"

    class Config:
        env_file = ".env"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
