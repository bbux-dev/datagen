from collections import Counter
from typing import Any, Dict, List, Callable
from typing import Generator, Union

from datacraft.suppliers import REPLACEMENTS

_LOOKUP = {
    "True": "_TRUE_",
    "False": "_FALSE_",
    "None": "_NONE_"
}


def _simple_type_compatibility_check(values: Generator[Any, None, None],
                                     type_check: type,
                                     list_check_func: Callable):
    """Checks to see if the values are of uniform type. This includes lists of lists of the values.

    Args:
        values: generator for values to check
        type_check: type of values to expect
        list_check_func: function for testing lists of this type

    Returns:
        (bool): if the values are compatible with this type

    Examples
        >>> _simple_type_compatibility_check((v for v in [1, 2, 3]), int, _is_all_int)
        True
        >>> _simple_type_compatibility_check((v for v in [1, 'a', 3]), int, _is_all_int)
        False
        >>> _simple_type_compatibility_check((v for v in [[1], [2], [-3]), int, _is_all_int)
        True
        >>> _simple_type_compatibility_check((v for v in [[1, 2], 2, 3]), int, _is_all_int)
        False
    """
    value_type = None
    result = True
    # since generator check one value at a time until condition invalidated
    for value in values:
        if isinstance(value, list):
            if value_type is None:
                value_type = 'lists'
            elif value_type == str(type_check):
                result = False
                break
            if not list_check_func(value):
                result = False
                break
        elif not isinstance(value, type_check) or isinstance(value, bool):
            result = False
        else:
            if value_type is None:
                value_type = str(type_check)
            elif value_type == 'lists':
                result = False
                break
    return result


def _is_replacement(sublist):
    return any(v in REPLACEMENTS for v in sublist)


def _is_nested_lists(values: Generator[Any, None, None]):
    for item in values:
        if not isinstance(item, list):
            return False
    return True


def _requires_substitution(values: List[Any]):
    return _any_is_boolean(values) or _any_is_none(values)


def _substitute(values):
    return [_LOOKUP.get(str(v), v) for v in values]


def _all_is_numeric(values):
    return all((isinstance(value, (int, float)) and not isinstance(value, bool)) for value in values)


def _all_is_int(values):
    return all((isinstance(value, int) and not isinstance(value, bool)) for value in values)


def _all_is_float(values):
    return all((isinstance(value, float) and not isinstance(value, bool)) for value in values)


def _all_is_str(values):
    return all(isinstance(value, str) for value in values)


def _all_lists_numeric(values):
    return all(_all_is_numeric(sublist) for sublist in values)


def _all_is_of_type(values, type_check):
    return all(isinstance(val, type_check) for val in values)


def _all_lists_of_type(lists, type_check):
    return all(isinstance(val, type_check) for sublist in lists for val in sublist)


def _any_is_boolean(values):
    return any(isinstance(value, bool) for value in values)


def _any_is_none(values):
    return any(v is None for v in values)


def _calculate_list_size_weights(values):
    # Calculate the frequency of each sublist length
    length_freq = Counter(len(sublist) for sublist in values)
    # Calculate the total number of lists
    total_lists = len(values)
    # Calculate the weights for each sublist length
    weights = {str(length): freq / total_lists for length, freq in length_freq.items()}
    return weights


def _calculate_weights(values: List[str]) -> Dict[str, float]:
    """
    Calculate the weights of occurrences of values from a list.

    Args:
        values (List[str]): A list of string values.

    Returns:
        Dict[str, float]: A dictionary containing each unique value from the list as the key
                          and its corresponding weight (or relative frequency) as the value.
    """
    total_count = len(values)
    counts = Counter(values)

    return {key: count / total_count for key, count in counts.items()}


def _are_values_unique(values: List) -> bool:
    """
    Check if all values in the list are unique.

    Args:
        values (List): A list of values.

    Returns:
        bool: True if all values are unique, otherwise False.
    """
    return len(values) == len(set(values))


def _all_list_is_str(lists):
    return all(isinstance(val, str) for sublist in lists for val in sublist)
