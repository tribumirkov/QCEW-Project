"""
Set configuration
"""
from pydantic import BaseSettings


class Settings(BaseSettings):
    qcew_api_url = 'http://data.bls.gov/cew/data/api'

    ownership_code = 5

    county_root_aggregation = 71
    county_highest_aggregation = 74
    county_lowest_aggregation = 78
    max_digits_of_naics = 6

    state_root_aggregation = 51
    state_highest_aggregation = 54
    state_lowest_aggregation = 58

    string_connecting_codes = '_'

    establishments = 'annual_avg_estabs' #'qtrly_estabs'
    employment = 'annual_avg_emplvl' #'month3_emplvl'
    wages = 'total_annual_wages' #'total_qtrly_wages'

    employment_abbreviation = 'emp'
    wages_abbreviation = 'wages'

settings = Settings()
