"""
Helpers for state level optimization
"""
import re

import numpy as np
import pandas as pd

from config import settings


def fetch_area_data(year, quarter, area):
    """
    Return a pandas table from BLS given year, quarter (a for year), and area code
    """
    url_path = f'{settings.qcew_api_url}/{year}/{quarter}/area/{area}.csv'
    df = pd.read_csv(url_path)
    df['industry_code'] = df['industry_code'].str.replace(
        '-',
        settings.string_connecting_codes
    )
    return df, url_path


def fetch_industry_data(year, quarter, industry):
    """
    Return a pandas table from BLS given year, quarter (a for year), and NAICS code
    """
    url_path = f'{settings.qcew_api_url}/{year}/{quarter}/industry/{industry}.csv'
    return pd.read_csv(url_path), url_path


def county_aggregation(aggregation):
    """
    Return aggregation code that skips 72, and 73
    """
    aggregation_levels = list(
        range(
            settings.county_highest_aggregation, settings.county_lowest_aggregation + 1
        )
    )
    aggregation_levels.append(settings.county_root_aggregation)
    if aggregation in aggregation_levels:
        return aggregation
    if settings.county_root_aggregation < aggregation < settings.county_highest_aggregation:
        return settings.county_highest_aggregation
    raise Exception('Aggregation level code unknown.')


def state_aggregation(aggregation):
    """
    Return aggregation code that skips 52, and 53
    """
    aggregation_levels = list(
        range(
            settings.state_highest_aggregation, settings.state_lowest_aggregation + 1
        )
    )
    aggregation_levels.append(settings.state_root_aggregation)
    if aggregation in aggregation_levels:
        return aggregation
    if settings.state_root_aggregation < aggregation < settings.state_highest_aggregation:
        return settings.state_highest_aggregation
    raise Exception('Aggregation level code unknown.')


def get_node_variables(df, code, aggregation):
    """
    Return variables of interest given industry code
    """
    ownership_code = settings.ownership_code
    where = (df['industry_code']==code) & \
            (df['agglvl_code']==aggregation) & \
            (df['own_code']==ownership_code)
    est = df[where][f'{settings.establishments}'].values[0]
    emp = df[where][f'{settings.employment}'].values[0]
    wages = df[where][f'{settings.wages}'].values[0]
    return est, emp, wages


def county_children_codes(df, code, aggregation):
    """
    Return a list of children codes
    """
    if settings.string_connecting_codes in code:
        search_it = tuple([str(number) for number in range(int(code[0:2]), int(code[-2:]) + 1)])
    else:
        search_it = code
    if search_it == '10':
        where = (df['agglvl_code']==settings.county_highest_aggregation) & \
                (df['own_code']==settings.ownership_code)
    else:
        where = (df['industry_code'].str.startswith(search_it)) & \
                (df['own_code']==settings.ownership_code) & \
                (df['agglvl_code']==aggregation+1)
    return sorted(np.unique(df['industry_code'][where].values))


def state_children_codes(df, code, aggregation):
    """
    Return a list of children codes
    """
    if settings.string_connecting_codes in code:
        search_it = tuple(str(number) for number in range(int(code[0:2]), int(code[-2:]) + 1))
    else:
        search_it = code
    if search_it == '10':
        where = (df['agglvl_code']==settings.state_highest_aggregation) & \
                (df['own_code']==settings.ownership_code)
    else:
        where = (df['industry_code'].str.startswith(search_it)) & \
                (df['own_code']==settings.ownership_code) & \
                (df['agglvl_code']==aggregation+1)
    return sorted(np.unique(df['industry_code'][where].values))


def get_optimization_variables(constraints, key):
    """
    Return a list of variables from constraints
    """
    variables = []
    if key == settings.employment_abbreviation:
        regex = r"epe_[^ ]* "
    elif key == settings.wages_abbreviation:
        regex = r"wpe_[^ ]* "
    else:
        raise Exception(
            f'''
            Unknown variable abbreviation:
            it can be either {settings.employment_abbreviation} or {settings.wages_abbreviation}
            '''
        )
    for constraint in constraints:
        variables+=re.findall(regex, constraint)
    return list(np.unique(variables))
