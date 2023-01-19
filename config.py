from pydantic import BaseSettings


class Settings(BaseSettings):
    qcew_api_url = 'http://data.bls.gov/cew/data/api'

    ownership_code = 5

    root_aggregation = 71
    highest_aggregation = 74
    lowest_aggregation = 78
    max_digits_of_naics = 6

    establishments = 'qtrly_estabs'
    employment = 'month3_emplvl'
    wages = 'total_qtrly_wages'

    employment_abbreviation = 'emp'
    wages_abbreviation = 'wages'

settings = Settings()