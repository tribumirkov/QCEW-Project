"""
Tree methods for state level optimization
"""
from helpers import get_node_variables, county_children_codes, county_aggregation, \
    state_aggregation, state_children_codes

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
    return None


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


def build_county_tree(df, code, aggregation):
    """
    Return the complete tree with nodes and leaves
    """
    if code is not None:
        aggregation = county_aggregation(aggregation)
        est, emp, wages = get_node_variables(df, code, aggregation)
        children_codes = county_children_codes(df, code, aggregation)
        children = []
        if aggregation <= settings.county_lowest_aggregation:
            for child_code in children_codes:
                children.append(build_county_tree(df, child_code, aggregation+1))
        return {'ind': code, 'est': est, 'emp': emp, 'wages': wages,'children':children}
    return None


def build_state_tree(df, code, aggregation):
    """
    Return the complete tree with nodes and leaves
    """
    if code is not None:
        aggregation = state_aggregation(aggregation)
        est, emp, wages = get_node_variables(df, code, aggregation)
        children_codes = state_children_codes(df, code, aggregation)
        children = []
        if aggregation <= settings.state_lowest_aggregation:
            for child_code in children_codes:
                children.append(build_state_tree(df, child_code, aggregation+1))
        return {'ind': code, 'est': est, 'emp': emp, 'wages': wages,'children':children}
    return None


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
