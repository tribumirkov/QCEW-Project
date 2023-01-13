from helpers import get_variables, get_children_codes, adjust_aggregation_code

from config import settings


def fetch(tree, key, value):
    """
    Find key - value pair in the tree
    """        
    if tree.get(key) == value:
        return tree
    else:
        for child in tree['children']:
            match = fetch(child, key, value)
            if match is not None:
                return match


def build_tree(df, code, aggregation):
    """
    Return the complete tree with nodes and leaves
    """
    if code is not None:
        aggregation = adjust_aggregation_code(aggregation)
        est, emp = get_variables(df, code, aggregation)
        children_codes = get_children_codes(df, code, aggregation)
        children = []
        if aggregation <= settings.lowest_aggregation:
            for child_code in children_codes:
                children.append(build_tree(df, child_code, aggregation+1))
        return {'ind': code, 'est': est, 'emp': emp, 'children':children}
