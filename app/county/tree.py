"""
Tree methods for county level optimization
"""
import numpy as np
import numexpr as ne

from helpers import get_variables, get_children_codes, adjust_aggregation_code
from config import settings


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


def get_subindustries_data(industry):
    """
    Return data for subindustries of a given industry
    """
    subind = np.array([subindustry['ind'] for subindustry in industry['children']])
    est = np.array([subindustry['est'] for subindustry in industry['children']], dtype = object)
    emp = np.array([subindustry['emp'] for subindustry in industry['children']], dtype = object)
    wages = np.array([subindustry['wages'] for subindustry in industry['children']], dtype = object)
    return {
        'subind': subind,
        'est': est,
        'emp': emp,
        'wages': wages,
    }


def get_objective(tree, key, objective):
    """
    Return the objective function as key_10 - sum (key_6digits)
    """
    if len(tree['children'])==0:
        if tree[key] == 0:
            objective += f" - {tree['est']}*{key[0]}pe_{tree['ind']}"
        else:
            objective += f" - {tree[key]}"
    for child in tree['children']:
        objective = get_objective(child, key, objective)
    return objective


def get_constraints(tree, key, constraints):
    """
    Return all the constraints in a tree
    """
    if len(tree['children'])>0:
        if tree[key] == 0:
            constraint = f"{tree['est']}*{key[0]}pe_{tree['ind']} = "
        else:
            constraint = f"{tree[key]} = "
        for i,child in enumerate(tree['children']):
            if i > 0:
                constraint += ' + '
            if child[key] == 0:
                constraint+= f"{child['est']}*{key[0]}pe_{child['ind']} "
            else:
                constraint+= f"{child[key]}"
        check = constraint.split(' = ')
        if check[0] != check[1]:
            constraints.append(constraint)
        if 'epe' not in constraint:
            if not bool(ne.evaluate(constraint.replace(' = ', ' == '))):
                constraints.append(constraint)
    for child in tree['children']:
        constraints = get_constraints(child, key, constraints)
    return constraints


def get_constraints_free(tree, key, constraints):
    """
    Return all the constraints in a tree allowing free parameters
    """
    if len(tree['children'])>0:
        if tree[key] == 0:
            constraint = f"{key}_{tree['ind']} = "
        else:
            constraint = f"{tree[key]} = "
        for i,child in enumerate(tree['children']):
            if i > 0:
                constraint += ' + '
            if child[key] == 0:
                constraint+= f"{key}_{child['ind']} "
            else:
                constraint+= f"{child[key]}"
        check = constraint.split(' = ')
        if check[0] != check[1]:
            constraints.append(constraint)
    for child in tree['children']:
        constraints = get_constraints_free(child, key, constraints)
    return constraints
