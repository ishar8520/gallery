from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='kafka_')

    bootstrap_servers: str = 'kafka:9092'
    group_id: str = 'mail-service'


class SmtpConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='smtp_')

    host: str = 'mailhog'
    port: int = 1025
    from_email: str = 'noreply@gallery.local'


class LinkServiceConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='link_service_')

    url: str = 'http://link-service:8000'


class AuthConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='auth_')

    public_url: str = 'http://localhost:8000'


class Settings(BaseSettings):
    kafka: KafkaConfig = KafkaConfig()
    smtp: SmtpConfig = SmtpConfig()
    link_service: LinkServiceConfig = LinkServiceConfig()
    auth: AuthConfig = AuthConfig()


settings = Settings()
