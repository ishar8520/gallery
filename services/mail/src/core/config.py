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


class Settings(BaseSettings):
    kafka: KafkaConfig = KafkaConfig()
    smtp: SmtpConfig = SmtpConfig()


settings = Settings()
