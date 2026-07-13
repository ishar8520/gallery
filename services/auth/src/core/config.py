from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='postgresql_')

    username: str
    password: str
    database: str
    host: str
    port: int

    @property
    def url(self):
        return f'postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}'


class RedisConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='redis_')

    host: str
    port: int

    @property
    def url(self):
        return f'redis://{self.host}:{self.port}/0'


class JWTConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='jwt_')

    authjwt_secret_key: str
    authjwt_token_location: set = {"cookies", "headers"}
    authjwt_cookie_csrf_protect: bool = False
    access_expires_seconds: int
    refresh_expires_seconds: int


class KafkaConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='kafka_')

    bootstrap_servers: str = 'kafka:9092'


class RegistrationConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='confirmation_token_')

    ttl_seconds: int = 86400


class GoogleOAuthConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='google_')

    client_id: str = ''
    client_secret: str = ''
    redirect_uri: str = 'http://localhost:8000/auth/api/v1/oauth/google/callback'


class GitHubOAuthConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='github_')

    client_id: str = ''
    client_secret: str = ''
    redirect_uri: str = 'http://localhost:8000/auth/api/v1/oauth/github/callback'


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='app_')

    frontend_url: str = 'http://localhost:8000'


class Settings(BaseSettings):
    postgres: PostgresConfig = PostgresConfig()
    redis: RedisConfig = RedisConfig()
    jwt: JWTConfig = JWTConfig()
    kafka: KafkaConfig = KafkaConfig()
    registration: RegistrationConfig = RegistrationConfig()
    google: GoogleOAuthConfig = GoogleOAuthConfig()
    github: GitHubOAuthConfig = GitHubOAuthConfig()
    app: AppConfig = AppConfig()


settings = Settings()
