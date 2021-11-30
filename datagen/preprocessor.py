"""
Module for preprocessing spec before generating values. Exists to handle shorthand notation and
pushing params from URL form of field?param=value in to config object.
"""
import re
import json
import logging
from urllib.parse import parse_qs
from .exceptions import SpecException
from . import registries

_log = logging.getLogger(__name__)


@registries.registry.preprocessors('default')
def _preprocess_spec(raw_spec):
    """
    Preprocesses the spec into a format that is easier to use.
    Pushes all url params in keys into config object. Converts shorthand specs into full specs

    Args:
        raw_spec: to preprocess

    Returns:
        the reformatted spec
    """
    updated_specs = {}
    for key, spec in raw_spec.items():
        if key == 'refs':
            updated_specs[key] = _preprocess_spec(raw_spec[key])
            continue
        if key == 'field_groups':
            updated_specs[key] = spec
            continue
        if '?' not in key:
            _update_no_params(key, spec, updated_specs)
        else:
            _update_with_params(key, spec, updated_specs)

    return updated_specs


@registries.registry.preprocessors('csv-select')
def _preprocess_csv_select(raw_spec):
    """
    Converts and csv-select elements into standard csv ones

    Args:
        raw_spec: to process

    Returns:
        converted spec
    """
    updated_specs = {}
    for key, spec in raw_spec.items():
        if 'type' in spec and spec['type'] == 'csv_select':
            config_ref_name = f'{key}_config_ref'
            config_ref = {
                'type': 'config_ref',
                'config': spec.get('config', {})
            }
            if 'refs' not in raw_spec:
                updated_specs['refs'] = {config_ref_name: config_ref}
            else:
                updated_specs['refs'][config_ref_name] = config_ref
            for name, column in spec.get('data', {}).items():
                spec_for_column = {
                    'type': 'csv',
                    'config': {
                        'column': column,
                        'config_ref': config_ref_name
                    }
                }
                if name not in raw_spec:
                    updated_specs[name] = spec_for_column
                else:
                    alt_name = f'{name}-{column}'
                    updated_specs[alt_name] = spec_for_column
        else:
            updated_specs[key] = spec
    return updated_specs


@registries.registry.preprocessors('nested')
def _preprocess_nested(raw_spec):
    """
    Converts all nested elements

    Args:
        raw_spec: to process

    Returns:
        converted spec
    """
    updated_specs = {}
    if 'refs' in raw_spec:
        if 'refs' in updated_specs:
            updated_specs['refs'].update(_preprocess_spec(raw_spec['refs']))
        else:
            updated_specs['refs'] = _preprocess_spec(raw_spec['refs'])
    for key, spec in raw_spec.items():
        if key == 'refs':
            # run preprocessors on refs too
            updated_refs = _preprocess_spec(spec)
            updated_refs = _preprocess_csv_select(updated_refs)
            # in case we have nested nested elements
            updated_refs = _preprocess_nested(updated_refs)
            updated_specs['refs'] = updated_refs
            continue

        if 'type' in spec and spec['type'] == 'nested':
            if 'fields' not in spec:
                raise SpecException('Missing fields key for nested spec: ' + json.dumps(spec))
            fields = spec['fields']
            updated = _preprocess_spec(fields)
            updated = _preprocess_csv_select(updated)
            # in case we have nested nested elements
            updated = _preprocess_nested(updated)
            # this may have created a refs element, need to move this to the root
            _update_root_refs(updated_specs, updated)
            spec['fields'] = updated
            updated_specs[key] = spec
        else:
            updated_specs[key] = spec
    return updated_specs


@registries.registry.preprocessors('type_check')
def _preprocess_verify_types(raw_spec):
    """ log only checks """
    for key, field_spec in raw_spec.items():
        if key == 'refs':
            _preprocess_verify_types(field_spec)
            continue
        type_name = field_spec.get('type')
        if registries.lookup_type(type_name) is None:
            _log.warning('Unknown type key: %s for spec %s, known types are %s',
                         type_name, field_spec, registries.registered_types())
    return raw_spec


def _update_root_refs(updated_specs, updated):
    """
    Updates to root refs if needed by popping the refs from the updated and merging with existing refs or creating
    a new refs element

    Args:
        updated_specs: specs being updated
        updated: current updated spec that may have refs injected into it
    """
    if 'refs' in updated:
        refs = updated.pop('refs')
        if 'refs' in updated_specs:
            updated_specs.get('refs').update(refs)
        else:
            updated_specs['refs'] = refs


def _update_with_params(key, spec, updated_specs):
    """
    handles the case that there are ?param=value portions in the key
    These get stripped out and pushed into the config object
    """
    newkey, spectype, params = _parse_key(key)

    if newkey in updated_specs:
        raise SpecException(f'Field {key} defined multiple times: ' + json.dumps(spec))
    # the updated spec to populate
    updated = _convert_to_values_if_needed(spec, spectype)

    config = updated.get('config', {})
    config.update(params)
    updated['config'] = config
    if spectype:
        updated['type'] = spectype

    updated_specs[newkey] = updated


def _update_no_params(key, spec, updated_specs):
    """
    handles the case when there are no ?param=value portions in the key
    key may have name:type notation that still needs to be handled
    """
    if ':' in key:
        newkey, spectype = key.split(':', 2)
        if not _is_spec_data(spec, spectype):
            spec['type'] = spectype
        else:
            spec = {
                'type': spectype,
                'data': spec
            }
    else:
        newkey = key
    # check for conflicts
    if key in updated_specs:
        raise SpecException(f'Field {key} defined multiple times: ' + json.dumps(spec))

    spectype = spec.get('type') if isinstance(spec, dict) else None
    updated = _convert_to_values_if_needed(spec, spectype)

    updated_specs[newkey] = updated


def _convert_to_values_if_needed(spec, spectype):
    """converts to a values spec if this is data only"""
    if _is_spec_data(spec, spectype):
        return {
            'type': 'values',
            'data': spec
        }
    else:
        return spec


def _parse_key(field_name):
    """
    Expected key to have URL format. Two main forms:

    1. field:field_type?param1=val&param2=val...

    2. field?param1=val...
    """
    parts = re.split(r'\?', field_name)
    key_type = parts[0].split(':')
    parsed_query = parse_qs(parts[1])

    if len(key_type) > 1:
        newkey = key_type[0]
        spectype = key_type[1]
    else:
        newkey = parts[0]
        spectype = None
    config = {}
    for key, value in parsed_query.items():
        if len(value) == 1:
            config[key.strip()] = value[0]
        else:
            config[key.strip()] = value

    return newkey, spectype, config


def _is_spec_data(spec, spectype):
    """
    Checks to see if the spec is data only

    Args:
        spec: to check
        spectype: if any available

    Returns:
        true if only data, false if it is a spec
    """
    if spec == 'nested' or spectype == 'nested':
        return False
    # if it is not a dictionary, then it is definitely not a spec
    if not isinstance(spec, dict):
        return True
    for core_field in ['type', 'data', 'config', 'ref', 'refs', 'fields']:
        if core_field in spec:
            return False
    # if empty, then may be using abbreviated notation i.e. field:type?param=value...
    if len(spec) == 0:
        return False
    # didn't find any core fields, and spec is not empty, so this must be data
    return True
