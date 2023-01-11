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


def get_variables(df, code):
    """
    Return variables of interest given industry code
    """
    where = (df['industry_code']==code)
    estabs = np.sum(df[where]['annual_avg_estabs'])
    empl = np.sum(df[where]['annual_avg_emplvl'].values)
    return estabs, empl


def get_children_codes(df, code, aggregation):
    """
    Return a list of children codes
    """
    if '-' in code:
        search_it = tuple([str(number) for number in range(int(code[0:2]), int(code[-2:]) + 1)])
    else:
        search_it = code
    where = (df['industry_code'].str.startswith(search_it)) & (df['agglvl_code']==aggregation+1)
    return df['industry_code'][where].values


