import os
from pathlib import Path
from pydantic_settings import BaseSettings


class ETLSettings(BaseSettings):
    database_url: str = "postgresql://seace_user:changeme@localhost:5432/seace_db"
    seace_base_url: str = "https://prodapp2.seace.gob.pe"
    etl_raw_dir: str = "data/raw"
    etl_processed_dir: str = "data/processed"
    etl_log_dir: str = "logs"
    etl_batch_size: int = 100

    class Config:
        env_file = "../.env"
        extra = "ignore"

    def ensure_dirs(self):
        for d in [self.etl_raw_dir, self.etl_processed_dir, self.etl_log_dir]:
            Path(d).mkdir(parents=True, exist_ok=True)


settings = ETLSettings()
