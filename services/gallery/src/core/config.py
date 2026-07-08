from pydantic_settings import BaseSettings, SettingsConfigDict


class ProjectConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='project_')

    title: str = 'Gallery Service'


class PostgresqlConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='gallery_postgresql_')

    username: str
    password: str
    database: str
    host: str
    port: int = 5432

    @property
    def dsn(self) -> str:
        return (
            f'postgresql+asyncpg://{self.username}:{self.password}'
            f'@{self.host}:{self.port}/{self.database}'
        )


class MinioConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='minio_')

    host: str
    port: int
    user: str
    password: str
    bucket: str = 'gallery'
    public_host: str = ''  # MINIO_PUBLIC_HOST — browser-accessible host:port for presigned URLs


class AuthConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='auth_service_')

    host: str
    port: int


class KafkaConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='kafka_')

    bootstrap_servers: str = 'kafka:9092'


class Settings(BaseSettings):
    project: ProjectConfig = ProjectConfig()
    postgresql: PostgresqlConfig = PostgresqlConfig()
    minio: MinioConfig = MinioConfig()
    auth: AuthConfig = AuthConfig()
    kafka: KafkaConfig = KafkaConfig()


settings = Settings()
