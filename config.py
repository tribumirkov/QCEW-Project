from pydantic import BaseSettings


class Settings(BaseSettings):
    qcew_api_url = 'http://data.bls.gov/cew/data/api'

    root_aggregation = 70
    highest_aggregation = 74
    lowest_aggregation = 78

    establishments = 'qtrly_estabs' #'annual_avg_estabs'
    employment = 'month3_emplvl' #'annual_avg_emplvl'


settings = Settings()