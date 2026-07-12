from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False, extra="ignore")

    data_project_id: str = ""
    clan_tag: str = ""
    coc_apikey: str = ""
    dataset_id: str = "coc_bronze"

settings = Settings()
