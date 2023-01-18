import numpy as np
import pandas as pd

from config import settings


def fetch_area_data(year, quarter, area):
    """
    Return a pandas table from BLS given year, quarter (a for year), and area code
    """
    urlPath = f'{settings.qcew_api_url}/{year}/{quarter}/area/{area}.csv'
    return pd.read_csv(urlPath), urlPath


def fetch_industry_data(year, quarter, industry):
    """
    Return a pandas table from BLS given year, quarter (a for year), and NAICS code
    """
    urlPath = f'{settings.qcew_api_url}/{year}/{quarter}/industry/{industry}.csv'
    return pd.read_csv(urlPath)


def adjust_aggregation_code(aggregation):
    """
    Return aggregation code that skips 72, and 73
    """
    aggregation_levels = list(
        range(
            settings.highest_aggregation, settings.lowest_aggregation + 1
        )
    )
    aggregation_levels.append(settings.root_aggregation)
    if aggregation in aggregation_levels:
        return aggregation
    if settings.root_aggregation < aggregation < settings.highest_aggregation:
        return settings.highest_aggregation
    raise Exception('Aggregation level code unknown.')
    

def get_variables(df, code, aggregation):
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


def get_children_codes(df, code, aggregation):
    """
    Return a list of children codes
    """
    if '-' in code:
        search_it = tuple([str(number) for number in range(int(code[0:2]), int(code[-2:]) + 1)])
    else:
        search_it = code
    if search_it == '10':
        where = (df['agglvl_code']==settings.highest_aggregation) & \
                (df['own_code']==settings.ownership_code)
    else:
        where = (df['industry_code'].str.startswith(search_it)) & \
                (df['own_code']==settings.ownership_code) & \
                (df['agglvl_code']==aggregation+1)
    return sorted(np.unique(df['industry_code'][where].values))


def get_undisclosed_data(industry, data):
    """
    Return the sum of undisclosed variables depending on whether parent variable is disclosed
    """
    undisclosed_est = data['est'][np.where(data['emp']==0)]
    undisclosed_ind = data['subind'][np.where(data['emp']==0)].tolist()
    if industry['est'] > 0 and industry['emp'] == 0:
        undisclosed_emp = industry['emp_ps'] - np.sum(data['emp'])
        undisclosed_wages = industry['wages_ps'] - np.sum(data['wages'])
    else:
        undisclosed_emp = industry['emp'] - np.sum(data['emp'])
        undisclosed_wages = industry['wages'] - np.sum(data['wages'])
    return {
        'est': undisclosed_est,
        'ind': undisclosed_ind,
        'emp': undisclosed_emp,
        'wages': undisclosed_wages
    }

        

