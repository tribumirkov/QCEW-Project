import numpy as np

from tree import write_into
from config import settings


def run_proportional_scaling(county, industry, data):
    """
    Return the given tree with results written in appropriate dictionaries
    """
    if len(industry['ind']) < settings.max_digits_of_naics:
        undisclosed_est = data['est'][np.where(data['emp']==0)]
        if np.sum(undisclosed_est) > 0:
            if industry['emp'] == 0:
                undisclosed_emp = industry['emp_ps'] - np.sum(data['emp'])
                undisclosed_wages = industry['wages_ps'] - np.sum(data['wages'])
            else:
                undisclosed_emp = industry['emp'] - np.sum(data['emp'])
                undisclosed_wages = industry['wages'] - np.sum(data['wages'])
            undisclosed_ind = data['subind'][np.where(data['emp']==0)].tolist()
            for i,subind in enumerate(undisclosed_ind):
                data = {
                    'emp_ps': undisclosed_emp * undisclosed_est[i]/np.sum(undisclosed_est),
                    'wages_ps': undisclosed_wages * undisclosed_est[i]/np.sum(undisclosed_est),
                }              
                county = write_into(county, 'ind', subind, data)
    return county
