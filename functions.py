import cvxpy as cp
import numpy as np
import re

from helpers import get_undisclosed_data
from tree import write_into, get_constraints, fetch_branch
from config import settings


def run_proportional_scaling(county, industry, data):
    """
    Return the given tree with proportional scaling (ps) results in it
    """
    if len(industry['ind']) < settings.max_digits_of_naics:
        undisclosed = get_undisclosed_data(industry, data)
        if np.sum(undisclosed['est']) > 0:
            for i,subind in enumerate(undisclosed['ind']):
                data = {
                    'emp_ps': undisclosed['emp'] * undisclosed['est'][i]/np.sum(undisclosed['est']),
                    'wages_ps': undisclosed['wages'] * undisclosed['est'][i]/np.sum(undisclosed['est']),
                }              
                county = write_into(county, 'ind', subind, data)
    return county


def run_linear_programming(county, key):
    """
    Return the given tree with linear programming results in it
    """
    constraints = get_constraints(county, key, [])
    variables = []
    for constraint in constraints:
        variables+=re.findall(r"epe_[^ ]* ", constraint)
    for variable in variables:
        exec(f"{variable} = cp.Variable()")
    objective = None
    exec(f"objective = cp.Minimize(cp.abs({constraints[0].replace('=', '-').replace('+', '-')}))")
    numerical_constraints = []
    for i,constraint in enumerate(constraints):
        if i > 0:
            numerical_constraints.append(eval(f"{constraint.replace('=','==')}"))
    for variable in variables:
        numerical_constraints.append(eval(f"{variable}>= 0"))
    problem = cp.Problem(objective, numerical_constraints)
    problem.solve()
    for variable in variables:
        ind = variable[variable.find('_')+1:-1]
        branch = fetch_branch(county, 'ind', ind)
        if branch[key] == 0:
            write_into(
                county, 'ind', branch['ind'],
                {'emp_lp': branch['est'] * eval(f"float({variable}.value)")}
            )
    return county

