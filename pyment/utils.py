# -*- coding: utf-8 -*-

import re

__author__ = "A. Daouzli"
__copyright__ = "Copyright 2012-2018, A. Daouzli; Copyright 2026, V. Schekochihin"
__licence__ = "GPL3"
__version__ = "0.5.0"
__maintainer__ = "V. Schekochihin"

from dataclasses import fields

RAISES_NAME_REGEX = r'^([\w.]+)'


def isin_alone(elems, line):
    """Check if an element from a list is the only element of a string.

    :type elems: list
    :type line: str

    """
    found = False
    for e in elems:
        if line.strip().lower() == e.lower():
            found = True
            break
    return found


def isin_start(elems, line):
    """Check if an element from a list starts a string.

    :type elems: list
    :type line: str

    """
    found = False
    elems = [elems] if type(elems) is not list else elems
    for e in elems:
        if line.lstrip().lower().startswith(e):
            found = True
            break
    return found


def isin(elems, line):
    """Check if an element from a list is in a string.

    :type elems: list
    :type line: str

    """
    found = False
    for e in elems:
        if e in line.lower():
            found = True
            break
    return found


def get_leading_spaces(data):
    """Get the leading space of a string if it is not empty

    :type data: str

    """
    spaces = ''
    m = re.match(r'^(\s*)', data)
    if m:
        spaces = m.group(1)
    return spaces


def normalize_default_value(default_value):
    """Normalize default value by converting triple quotes to single quotes.

    If the default value contains triple quotes (triple-double-quotes or
    triple-single-quotes), they are converted to single quotes (').
    This handles cases where triple quotes appear at the start/end of
    the string value.

    :param default_value: the default value string to normalize
    :type default_value: str
    :return: normalized default value with single quotes instead of triple quotes
    :rtype: str

    """
    if not default_value or not isinstance(default_value, str):
        return default_value

    # Check if the value starts and ends with triple double quotes
    if default_value.startswith('"""') and default_value.endswith('"""'):
        # Extract the content between triple quotes
        content = default_value[3:-3]
        # Wrap with single quotes
        return "'" + content + "'"

    # Check if the value starts and ends with triple single quotes
    if default_value.startswith("'''") and default_value.endswith("'''"):
        # Extract the content between triple quotes
        content = default_value[3:-3]
        # Wrap with single quotes
        return "'" + content + "'"

    # If triple quotes appear anywhere else in the string, replace them
    normalized = default_value.replace('"""', "'")
    normalized = normalized.replace("'''", "'")

    return normalized


def from_dict(dc_type: type, data: dict):
    class_fields = {f.name for f in fields(dc_type)}
    filtered_data = {k: v for k, v in data.items() if k in class_fields}

    return dc_type(**filtered_data)