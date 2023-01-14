from pydantic import BaseSettings


class Settings(BaseSettings):
    qcew_api_url = 'http://data.bls.gov/cew/data/api'

    ownership_code = 5

    root_aggregation = 71
    highest_aggregation = 74
    lowest_aggregation = 78

    establishments = 'qtrly_estabs'
    employment = 'month3_emplvl'
    wages = 'total_qtrly_wages'


settings = Settings()