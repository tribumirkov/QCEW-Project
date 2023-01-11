import numpy as np
import pandas as pd

from config import settings


def fetch_area_data(year, quarter, area):
    """
    Return a pandas table from BLS given year, quarter (a for year), and area code
    """
    urlPath = f'{settings.qcew_api_url}/{year}/{quarter}/area/{area}.csv'
    return pd.read_csv(urlPath)


def fetch_industry_data(year, quarter, industry):
    """
    Return a pandas table from BLS given year, quarter (a for year), and NAICS code
    """
    urlPath = f'{settings.qcew_api_url}/{year}/{quarter}/industry/{industry}.csv'
    return pd.read_csv(urlPath)


