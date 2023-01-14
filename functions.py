import numpy as np

from tree import write_into


def run_proportional_scaling(county, industry, data):
    """
    Return the given tree with results written in appropriate dictionaries
    """
    undisclosed_ind = data['subind'][np.where(data['emp']==0)].tolist()
    undisclosed_est = data['est'][np.where(data['emp']==0)]
    undisclosed_emp = industry['emp'] - np.sum(data['emp'])
    undisclosed_wages = industry['wages'] - np.sum(data['wages'])
    for i,ind in enumerate(undisclosed_ind):
        data = {
            'emp_ps': undisclosed_emp * undisclosed_est[i]/np.sum(undisclosed_est),
            'wages_ps': undisclosed_wages * undisclosed_est[i]/np.sum(undisclosed_est),
        }
        county = write_into(county, 'ind', ind, data)
    return county
