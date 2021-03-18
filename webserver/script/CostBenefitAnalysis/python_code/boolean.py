from __future__ import unicode_literals
__author__ = 'ryan'

from datetime import datetime as _datetime


def is_strint(s):
    """
    Checks to see if a string is an integer.

    Args:
        s (string)

    Returns:
        Boolean
    """
    try:
        int(s)
        return True
    except ValueError:
        return False


def is_strnumeric(s):
    """
    Checks to see if a string is numeric.

    Args:
        s (string)

    Returns:
        Boolean
    """
    try:
        float(s)
        return True
    except ValueError:
        return False


def is_strtrue(s):
    """
    Checks to see if a string is true or t.

    Args:
        s (string)

    Returns:
        Boolean
    """
    if s.lower() == 'true' or s.lower() == 't':
        return True
    else:
        return False


def is_strfalse(s):
    """
    Checks to see if a string is false or f.

    Args:
        s (string)

    Returns:
        Boolean
    """
    if s.lower() == 'false' or s.lower() == 'f':
        return True
    else:
        return False


def is_strbool(s):
    """
    Checks to see if a string is true, t, false, or f.

    Args:
        s (string)

    Returns:
        Boolean
    """
    if is_strtrue(s) or is_strfalse(s):
        return True
    else:
        return False


def is_iterable(some_object):
    """
    Checks to see if an object is iterable.

    Args:
        s (string)

    Returns:
        Boolean
    """
    try:
        iter(some_object)
        return True
    except:
        return False


def is_strdate(s, dateformat):
    """
    Checks to see if a string matches a datetime format.

    Args:
        s (string)
        dateformat (string): format as used by python Datetime in strptime

    Returns:
        Boolean

    Example:

    """
    try:
        _datetime.strptime(s, dateformat)
        return True
    except:
        return False


def is_electworkday(date):
    """Function would check to see if a date is a workday, including pseudo holidays"""
    pass
