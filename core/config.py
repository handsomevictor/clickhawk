from pydantic_settings import BaseSettings


class ClickHouseConfig(BaseSettings):
    host: str = "localhost"
    port: int = 8123
    user: str = "default"
    password: str = ""
    database: str = "default"
    secure: bool = False

    model_config = {"env_prefix": "CH_", "env_file": ".env"}
