from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    qdrant_host: str = Field(
        default="localhost",
        validation_alias=AliasChoices("QDRANT_HOST"),
    )
    collection_name: str = Field(
        default="my_collection",
        validation_alias=AliasChoices("COLLECTION_NAME"),
    )
    port: int = 8010


settings = Settings()  # type: ignore[call-arg]  # injected from env, not args (pydantic-settings)
