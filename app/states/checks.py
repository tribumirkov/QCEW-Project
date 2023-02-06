"""
Checking state JSONs
"""

import json
import os
import re

import cvxpy as cp
import numpy as np
import pandas as pd
from pydantic import BaseSettings

json_path = os.getcwd()

class Settings(BaseSettings):
    qcew_api_url = 'http://data.bls.gov/cew/data/api'

    ownership_code = 5

    root_aggregation = 71
    highest_aggregation = 74
    lowest_aggregation = 78
    max_digits_of_naics = 6

    state_root_aggregation = 51
    state_highest_aggregation = 54
    state_lowest_aggregation = 58

    max_batch_constraints = 10

    string_connecting_codes = '_'

    establishments = 'annual_avg_estabs'
    employment = 'annual_avg_emplvl'
    wages = 'total_annual_wages'

    employment_abbreviation = 'emp'
    wages_abbreviation = 'wages'

settings = Settings()


class NpEncoder(json.JSONEncoder):
    """
    Return a pandas table from BLS given year, quarter (a for year), and area code
    """
    def default(self, o):
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return super().default(o)


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


def fetch_branch(tree, key, value):
    """
    Find key - value pair in the tree
    """
    if tree.get(key) == value:
        return tree
    for child in tree['children']:
        match = fetch_branch(child, key, value)
        if match is not None:
            return match


def write_into(tree, key, value, data):
    """
    Return the tree with data written in the given node
    """
    if tree.get(key) == value:
        for data_key in data.keys():
            tree[data_key] = data[data_key]
    else:
        for child in tree['children']:
            write_into(child, key, value, data)
    return tree


def fetch_values_given_key(tree, key, values):
    """
    Return all the values in the tree given a key e.g. 'ind'
    """
    if tree.get(key) is not None:
        values.append(tree[key])
    if len(tree['children']) > 0:
        for child in tree['children']:
            values = fetch_values_given_key(child, key, values)
    return values


def save_data_to_time_series(time_series, county, key, year):
    """
    Returns time series that contains all the industries across time
    """
    for ind in fetch_values_given_key(county, 'ind', []):
        industry = fetch_branch(county, 'ind', ind)
        if industry.get(f'{key}_lp') is not None:
            time_series.at[year, ind] = industry[f'{key}_lp']
        else:
            time_series.at[year, ind] = industry[f'{key}']
    return time_series


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


def get_children_codes(df, code, aggregation):
    """
    Return a list of children codes
    """
    if settings.string_connecting_codes in code:
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


def build_tree(df, code, aggregation):
    """
    Return the complete tree with nodes and leaves
    """
    if code is not None:
        aggregation = adjust_aggregation_code(aggregation)
        est, emp, wages = get_variables(df, code, aggregation)
        children_codes = get_children_codes(df, code, aggregation)
        children = []
        if aggregation <= settings.lowest_aggregation:
            for child_code in children_codes:
                children.append(build_tree(df, child_code, aggregation+1))
        return {'ind': code, 'est': est, 'emp': emp, 'wages': wages,'children':children}


def get_constraints(tree_code, tree, key, constraints):
    """
    Return all the constraints in a tree
    """
    if len(tree['children'])>0:
        if tree[key] == 0:
            constraint = f"{key}_{tree_code}_{tree['ind']} = "
        else:
            constraint = f"{tree[key]} = "
        for i,child in enumerate(tree['children']):
            if i > 0:
                constraint += ' + '
            if child[key] == 0:
                constraint+= f"{key}_{tree_code}_{child['ind']} "
            else:
                constraint+= f"{child[key]}"
        if key in constraint:
            check = constraint.split(' = ')
            if check[0] != check[1]:
                if '+' not in constraint:
                    constraint = '0 = ' + constraint.replace('=', '-')
                constraints.append(re.sub(r'\s+', ' ', constraint))
    for child in tree['children']:
        constraints = get_constraints(tree_code, child, key, constraints)
    return constraints


def get_state_county_constraints(state, year, key):
    """
    Return all the constraints in a tree
    """
    state_county_constraints = []
    state_code = list(state[year].keys())[0]
    county_codes = list(state[year].keys())[1:]
    state_inds = fetch_values_given_key(state[year][state_code], 'ind', [])
    for state_ind in state_inds:
        state_node = fetch_branch(state[year][state_code], 'ind', state_ind)
        if state_node[key] == 0:
            state_county_constraint = f"{key}_{state_code}_{state_ind} = "
        else:
            state_county_constraint = f"{state_node[key]} = "
        for county_code in county_codes:
            county_node = fetch_branch(state[year][county_code], 'ind', state_ind)
            if county_node is not None:
                if county_node[key] == 0:
                    state_county_constraint += f" + {key}_{county_code}_{state_ind}"
                else:
                    state_county_constraint += f" + {county_node[key]}"
        if f'{key}_' in state_county_constraint:
            state_county_constraints.append(
                re.sub(r'\s+', ' ', state_county_constraint.replace('=  + ','= '))
            )
    return state_county_constraints


def get_optimization_variables(constraints, key):
    """
    Return a list of variables from constraints
    """
    variables = []
    if key == settings.employment_abbreviation:
        regex = r"emp_[^ ]*"
    elif key == settings.wages_abbreviation:
        regex = r"wages_[^ ]*"
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


def build_state_tree(df, code, aggregation):
    """
    Return the complete tree with nodes and leaves
    """
    if code is not None:
        aggregation = state_aggregation(aggregation)
        est, emp, wages = get_variables(df, code, aggregation)
        children_codes = state_children_codes(df, code, aggregation)
        children = []
        if aggregation <= settings.state_lowest_aggregation:
            for child_code in children_codes:
                children.append(build_state_tree(df, child_code, aggregation+1))
        return {'ind': code, 'est': est, 'emp': emp, 'wages': wages,'children':children}
    return None


def sum_county_employment(state, year, ind):
    """
    Return the total number of employment accross counties
    """
    counties_emp = []
    for code in list(state[year].keys())[1:]:
        node = fetch_branch(state[year][code], 'ind', ind)
        if node is not None:
            if node['emp'] == 0:
                counties_emp.append(node['emp_lp'])
            else:
                counties_emp.append(node['emp'])
    return np.sum(counties_emp)


def extract_codes(variable_name):
    """
    Return county code and industry code from a variable's name
    """
    positions = [i for i, letter in enumerate(variable_name) if letter == '_']
    return variable_name[positions[0]+1:positions[1]], variable_name[positions[1]+1:].strip()


def get_array_elements(variables, equation, key, row, constant):
    """
    Return the total number of employment accross counties
    """
    terms = re.findall(fr'({key}_[^ ]*|[+-]?\d+)', equation)
    for term in terms:
        if f'{key}_' in term:
            sign = equation[equation.find(term)-2]
            if sign == '-':
                row[variables.index(term)] = -1
            else:
                row[variables.index(term)] = 1
        else:
            if equation.find(term) < equation.find('='):
                constant += int(term)
            else:
                constant -= int(term)
    return row, constant

def vectorize_equations(equations, key):
    """
    Vectorize a list of string equations and return the matrix A and the constant vector b.
    """
    variables = set()
    for equation in equations:
        for var in re.findall(fr"{key}_[^ ]*", equation):
            variables.add(var)
    variables = sorted(list(variables))
    N = len(variables)
    M = len(equations)
    A = np.empty((M, N))
    b = np.empty(M)
    if len(equations) > settings.max_batch_constraints:
        indices = list(range(0, len(equations), settings.max_batch_constraints))
        for i, index in enumerate(indices):
            if i == len(indices)-1:
                equation_list = equations[index:M]
            else:
                equation_list = equations[index:indices[i+1]]
            for equation in equation_list:
                which_equation = equations.index(equation)
                row = [0] * N
                constant = 0
                row, constant = get_array_elements(variables, equation, key, row, constant)
                A[which_equation,] = row
                b[which_equation] = constant
    return A, b, variables


with open('state_north_carolina.json', 'r') as fp:
    state = json.load(fp)


print('Milestone a)')
years = list(range(2014,2021+1))
for year in years:
    print(f'year {year}')
    differences = []
    for code in list(state[str(year)].keys()):
        county = state[str(year)][code]
        inds = fetch_values_given_key(county, 'ind', [])
        for ind in inds:
            node = fetch_branch(county, 'ind', ind)
            if len(node['children']) > 0:
                the_sum = []
                for child in node['children']:
                    if child['emp'] == 0:
                        the_sum.append(child['emp_lp'])
                    else:
                        the_sum.append(child['emp'])
                if node['emp'] == 0:
                    differences.append(np.abs(node['emp_lp'] - np.sum(the_sum)))
                else:
                    differences.append(np.abs(node['emp'] - np.sum(the_sum)))
    print('*** discrepancies area totals minus children totals ***')
    print(f'mean {np.mean(differences)}')
    print(f'median {np.median(differences)}')
    print(f'min {np.min(differences)}')
    print(f'max {np.max(differences)}')


print('Milestones b) and c)')
state_code = list(state[str(year)].keys())[0]
industry_codes = []
for year in years:
    industry_codes += fetch_values_given_key(state[str(year)][state_code], 'ind', [])
differences = pd.DataFrame(
    np.empty((len(np.unique(sorted(industry_codes))),len(years))),
    columns=years
)
differences.index = list(np.unique(sorted(industry_codes)))
for ind in differences.index.values.tolist():
    for year in years:
        counties_sum = float(sum_county_employment(state, str(year), ind))
        node = fetch_branch(state[str(year)][state_code], 'ind', ind)
        if node is not None:
            if node['emp'] > 0:
                state_level_employment = float(node['emp'])
            else:
                state_level_employment = float(node['emp_lp'])
            if state_level_employment == 0:
                differences.at[ind, year] = 0
            else:
                differences.at[ind, year] = \
                    np.abs((state_level_employment - counties_sum))
differences.to_csv(f'differences_North_Carolina.csv')

print('*** discrepancies area totals minus children totals ***')
print(f'mean {differences.mean()}')
print(f'median {differences.median()}')
print(f'min {differences.min()}')
print(f'max {differences.max()}')


for county_code in list(state['2014'].keys()):
    industry_codes = []
    for year in years:
        industry_codes += fetch_values_given_key(state[str(year)][county_code], 'ind', [])
    employment = pd.DataFrame([], columns=np.unique(sorted(industry_codes)))
    for year in years:
        employment = save_data_to_time_series(
            employment, state[str(year)][county_code], 'emp', year
        )
        employment[employment<1e-1] = 0
    (employment.transpose()).to_csv(f'North_Carolina_{county_code}_employment.csv')