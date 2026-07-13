from pydantic_settings import BaseSettings, SettingsConfigDict


class ClickHouseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='clickhouse_')

    host: str = 'clickhouse'
    port: int = 8123
    database: str = 'ugc'
    user: str = 'default'
    password: str = ''


class KafkaConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='kafka_')

    bootstrap_servers: str = 'kafka:9092'
    group_id: str = 'ugc-service'


class AuthConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='auth_service_')

    host: str = 'auth-service'
    port: int = 8000


class Settings(BaseSettings):
    clickhouse: ClickHouseConfig = ClickHouseConfig()
    kafka: KafkaConfig = KafkaConfig()
    auth: AuthConfig = AuthConfig()


settings = Settings()
