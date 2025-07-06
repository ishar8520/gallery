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
    authjwt_token_location: set = {"cookies"}
    authjwt_cookie_csrf_protect: bool = False
    access_expires_seconds: int
    refresh_expires_seconds: int


class Settings(BaseSettings):
    postgres: PostgresConfig = PostgresConfig()
    redis: RedisConfig = RedisConfig()
    jwt: JWTConfig = JWTConfig()


settings = Settings()