from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='link_redis_')

    host: str = 'link-redis'
    port: int = 6379

    @property
    def url(self) -> str:
        return f'redis://{self.host}:{self.port}/0'


class ProjectConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='project_')

    public_url: str = 'http://localhost:8000'


class Settings(BaseSettings):
    redis: RedisConfig = RedisConfig()
    project: ProjectConfig = ProjectConfig()


settings = Settings()
