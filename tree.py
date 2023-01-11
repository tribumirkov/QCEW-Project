import numpy as np

from helpers import get_children_codes


class Tree():
    """
    Define tree class
    """
    def __init__(self, ind, estabs, empl, children):
        """
        Initialize class
        """
        self.ind = ind
        self.estabs = estabs
        self.empl = empl
        self.children = children


    def find_object(self, key, value):
        """
        Find key - value pair
        """        
        if getattr(self, key) == value:
            return self
        else:
            for child in self.children:
                match = child.find_object(key, value)
                if match is not None:
                    return match


def build_tree(df, code, aggregation):
    """
    Return the complete tree with nodes and leaves
    """
    if aggregation <= 78:
        if code is None:
            codes = np.unique(sorted(list(df['industry_code'][df['agglvl_code']==aggregation])))
            if codes is not None:
                for code in codes:
                    print(code)
                    build_tree(df, code, aggregation+1)
        else:
            print(code)
            children_codes = get_children_codes(df, code, aggregation)
            for child_code in children_codes:
                build_tree(df, child_code, aggregation+1)
    return None