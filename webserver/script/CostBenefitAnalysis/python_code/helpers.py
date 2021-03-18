from __future__ import division
from __future__ import unicode_literals

from past.utils import old_div
import numpy as np
import operator
import pickle
import csv as _csv
import os
import boolean as _boolean
from collections import defaultdict

def npv(values, discount_rate):

        # npv assumes the first year is not discounted
        # excel_npv discounts the first year

        npv = np.npv(discount_rate, values)
        excel_npv = old_div(npv, (1 + discount_rate))

        return npv, excel_npv


def percent_error(value_a, value_b):
    return old_div(abs(value_a - value_b),value_a)


def get_max_index(dictionary):

    sorted_items = sorted(list(dictionary.items()), key=operator.itemgetter(1), reverse=True)
    max_key = sorted_items[0][0]
    return max_key


def format_as_dollars(flt):

    return '${:,.2f}'.format(flt)


def csvwrite(path, data, writetype='w'):
    '''Writes a CSV from a series of data
    '''
    with open(path, writetype, newline ='') as outfile:
        csv_writer = _csv.writer(outfile, delimiter=',')

        for row in data:
            if _boolean.is_iterable(row):
                csv_writer.writerow(row)
            else:
                csv_writer.writerow([row])

def make_dir_if_not_exist(directory):
    if not os.path.exists(directory):
        # if the directory is not already exist, make a directory
        os.mkdir(directory)

def comma_format(flt):

    return '{:,.2f}'.format(flt)


def save_pyobject(pyobject, path):
    """
    Simple function to save Python pyobject to a pickle file located at path
    """

    # Save data as pickle file
    with open(path, 'w') as handle:
        pickle.dump(pyobject, handle, protocol=pickle.HIGHEST_PROTOCOL)


def load_pyobject(path):
    """
    Simple function to load Python object from file located at path
    """
    import pickle

    with open(path, 'rb') as handle:
        pyobject = pickle.load(handle)
        return pyobject


def FloatOrZero(value):
    """
    Convert non-floats to floats with value 0
    """
    try:
        return float(value)
    except:
        return 0.0



def dsum(*dicts):
    """ Sums keys of two dictionaries together"""
    ret = defaultdict(int)
    for d in dicts:
        for k, v in d.items():
            ret[k] += v
    return dict(ret)