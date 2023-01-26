"""
Functions for state level optimization
"""
import cvxpy as cp

from helpers import get_optimization_variables
from tree import write_into, get_objective, get_constraints, fetch_branch


def set_optimization_problem(county, key):
    """
    Return the optimization problem
    """
    objective_function = get_objective(county, key, str(county[key]))
    constraints = get_constraints(county, key, [])
    variables = get_optimization_variables(constraints, key)
    return objective_function, variables, constraints


def run_linear_programming(county, key):
    """
    Return the given tree with linear programming results in it
    """
    objective_function, variables, constraints = set_optimization_problem(county, key)
    for variable in variables:
        exec(f"{variable} = cp.Variable()", globals())
    numerical_constraints = []
    for i,constraint in enumerate(constraints):
        if i > 0:
            numerical_constraints.append(eval(f"{constraint.replace('=','==')}"))
    for variable in variables:
        numerical_constraints.append(eval(f"{variable}>= 0"))
    exec(f"objective = cp.Minimize(cp.abs({objective_function}))")
    problem = cp.Problem(locals()['objective'], numerical_constraints)
    problem.solve(solver=cp.ECOS)
    for variable in variables:
        ind = variable[variable.find('_')+1:-1]
        branch = fetch_branch(county, 'ind', ind)
        if branch[key] == 0:
            write_into(
                county, 'ind', branch['ind'],
                {f'{key}_lp': branch['est'] * eval(f"float({variable}.value)")}
            )
    return county


def save_data_to_time_series(time_series, county, industry_codes, key, year):
    """
    Returns time series that contains all the industries across time
    """
    for ind in industry_codes:
        industry = fetch_branch(county, 'ind', ind)
        if industry is not None:
            if industry.get(f'{key}_lp') is not None:
                time_series.at[year, ind] = industry[f'{key}_lp']
            else:
                time_series.at[year, ind] = industry[f'{key}']
    return time_series
