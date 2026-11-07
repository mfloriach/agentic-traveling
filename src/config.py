from pydantic import AliasChoices, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Valkey(BaseModel):
    host: str
    password: str
    port: int
    database: int

    model_config = SettingsConfigDict(env_prefix="VALKEY_")


class Qdrant(BaseModel):
    host: str
    collection: str

    model_config = SettingsConfigDict(env_prefix="QDRANT_")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    otlp_endpoint: str = Field(
        default="http://localhost:4318/v1/traces",
        validation_alias=AliasChoices("OTLP_ENDPOINT", "OTEL_EXPORTER_OTLP_ENDPOINT"),
    )
    tika_server_endpoint: str = Field(
        default="http://localhost:9998",
        validation_alias=AliasChoices("TIKA_SERVER_ENDPOINT"),
    )
    temporal_host: str = Field(
        default="localhost:7233",  # temporal service in docker-compose.yml
        validation_alias=AliasChoices("TEMPORAL_HOST", "TEMPORAL_ADDRESS"),
    )
    qdrant: Qdrant
    valkey: Valkey

    port: int = 8010


settings = Settings()  # type: ignore[call-arg]  # injected from env, not args (pydantic-settings)
