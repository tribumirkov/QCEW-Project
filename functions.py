import numpy as np

from helpers import get_undisclosed_data
from tree import write_into
from config import settings


def run_proportional_scaling(county, industry, data):
    """
    Return the given tree with results written in appropriate dictionaries
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
