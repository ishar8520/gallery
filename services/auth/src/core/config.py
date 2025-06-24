from pydantic_settings import BaseSettings, SettingsConfigDict
from hashlib import sha256

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
    
    secret: str
    authjwt_token_location: set = {"headers"} 
    # authjwt_cookie_csrf_protect: bool = True
    # authjwt_cookie_secure: bool = True
    
    @property
    def authjwt_secret_key(self):
        return sha256(self.secret)
    
class Settings(BaseSettings):
    postgres: PostgresConfig = PostgresConfig()
    redis: RedisConfig = RedisConfig()
    jwt_config: JWTConfig = JWTConfig()
    authjwt_secret_key: str = jwt_config.secret
    authjwt_token_location: set = jwt_config.authjwt_token_location
    # authjwt_cookie_csrf_protect: bool = jwt_config.authjwt_cookie_csrf_protect
    # authjwt_cookie_secure: bool = jwt_config.authjwt_cookie_secure

settings = Settings()