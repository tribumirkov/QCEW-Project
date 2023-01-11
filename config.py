from pydantic import BaseSettings


class Settings(BaseSettings):
    qcew_api_url = 'http://data.bls.gov/cew/data/api'


settings = Settings()