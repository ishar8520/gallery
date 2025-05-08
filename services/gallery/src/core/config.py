from pydantic_settings import BaseSettings, SettingsConfigDict

class Project(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='project_')
    
class Settings(BaseSettings):
    pass

settings = Settings()