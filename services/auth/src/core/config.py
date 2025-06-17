from pydantic_settings import BaseSettings, SettingsConfigDict

class PostgresConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='auth_postgresql_')

    username: str
    password: str
    database: str
    host: str
    port: int

    @property
    def url(self):
        return f'postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}'
    

class Settings(BaseSettings):
    postgres: PostgresConfig = PostgresConfig()


settings = Settings()
