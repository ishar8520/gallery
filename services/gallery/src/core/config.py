from pydantic_settings import BaseSettings, SettingsConfigDict

class ProjectConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='project_')
    
    title: str

class MinioConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='minio_')
    
    host: str
    port: int    
    user: str
    password: str

class AuthConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='auth_service_')

    host: str
    port: int
    
class Settings(BaseSettings):
    project: ProjectConfig = ProjectConfig()
    minio: MinioConfig = MinioConfig()
    auth: AuthConfig = AuthConfig()

settings = Settings()