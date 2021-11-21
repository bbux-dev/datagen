import os

import pytest

import catalogue
import datagen
from datagen import __main__ as dgmain

test_dir = f'{os.path.dirname(os.path.realpath(__file__))}/data'


def test_parse_empty_args():
    with pytest.raises(datagen.SpecException):
        dgmain.main([])


def test_parse_custom_code():
    dgmain.main(['-c', os.path.join(test_dir, 'custom.py'), '--inline', '{}'])

    # verify string_reverser is now in registry
    handler = datagen.types.lookup_type('string_reverser')
    assert handler is not None


def test_parse_defaults_file():
    args = ['--defaults', os.path.join(test_dir, 'new_defaults.json'), '--inline', '{}']
    _test_default_is_changed('date_format', args, "%Y-%m-%d")


def test_parse_set_defaults():
    args = ['--set-defaults', 'date_format=%Y-%m-%d', '--inline', '{}']
    _test_default_is_changed('date_format', args, "%Y-%m-%d")


def test_parse_set_default_invalid_ignored():
    args = ['--set-defaults', 'incorrect_format', 'is_valid=should_exist', '--inline', '{}']
    dgmain.main(args)
    with pytest.raises(catalogue.RegistryError):
        datagen.types.get_default('incorrect_format')


def test_parse_sample_mode():
    args = ['--sample-lists', '--inline', '{}']
    _test_default_is_changed('sample_mode', args, True)


def _test_default_is_changed(key, args, expected):
    orig_value = datagen.types.get_default(key)
    dgmain.main(args)
    new_value = datagen.types.get_default(key)
    # reset default in registry
    datagen.types.set_default(key, orig_value)
    assert orig_value != new_value
    assert new_value == expected, f'{key} changed with args {args}, expected {expected}, but got {new_value}'


def test_parse_debug_spec(tmpdir):
    args = ['--debug-spec', '-o', str(tmpdir), '--inline', '{foo: [1,2,3]}']
    dgmain.main(args)
    assert os.path.exists(os.path.join(tmpdir, 'generated-0'))


def test_parse_debug_spec_yaml(tmpdir):
    args = ['--debug-spec-yaml', '-o', str(tmpdir), '--inline', '{foo: [1,2,3]}']
    dgmain.main(args)
    assert os.path.exists(os.path.join(tmpdir, 'generated-0'))


def test_parse_debug_defaults(tmpdir):
    args = ['--debug-defaults', '-o', str(tmpdir)]
    dgmain.main(args)
    assert os.path.exists(os.path.join(tmpdir, 'dataspec_defaults.json'))


def test_parse_apply_raw(tmpdir):
    args = ['-o', str(tmpdir),
            '--apply-raw',
            '-t', os.path.join(test_dir, 'template.jinja'),
            '--inline', '{"A": 1, "B":2, "C": 3}']
    dgmain.main(args)
    assert os.path.exists(os.path.join(tmpdir, 'generated-0'))


def test_parse_template_output(tmpdir):
    args = ['-o', str(tmpdir),
            '-t', os.path.join(test_dir, 'template.jinja'),
            '--inline', '{"A": 1, "B":2, "C": 3}']
    dgmain.main(args)
    assert os.path.exists(os.path.join(tmpdir, 'generated-0'))


def test_parse_template_output_inline(tmpdir):
    args = ['-o', str(tmpdir),
            '-t', 'A:{{ A }}, B:{{ B }}, C:{{ C }}',
            '--inline', '{"A": 1, "B":2, "C": 3}']
    dgmain.main(args)
    assert os.path.exists(os.path.join(tmpdir, 'generated-0'))


def test_parse_format_output(tmpdir):
    args = ['-o', str(tmpdir),
            '--format', 'json',
            '--inline', '{"A": 1, "B":2, "C": 3}']
    dgmain.main(args)
    assert os.path.exists(os.path.join(tmpdir, 'generated-0'))


def test_parse_spec_and_inline_invalid():
    args = ['--spec', os.path.join(test_dir, 'spec.json'),
            '--inline', '{"A": 1, "B":2, "C": 3}']
    with pytest.raises(datagen.SpecException):
        dgmain.main(args)


def test_parse_spec_invalid_path():
    args = ['--spec', os.path.join(test_dir, 'spec_not_there.json')]
    # just for test coverage
    dgmain.main(args)


def test_parse_spec_not_json_or_yaml():
    args = ['--spec', os.path.join(test_dir, 'blank_file')]
    with pytest.raises(datagen.SpecException):
        dgmain.main(args)


def test_parse_spec_yaml_format(tmpdir):
    args = ['--spec', os.path.join(test_dir, 'spec.yaml'),
            '-o', str(tmpdir),
            '-i', '5']
    dgmain.main(args)
    assert os.path.exists(os.path.join(tmpdir, 'generated-0'))


def test_parse_inline_yaml(tmpdir):
    args = ['-o', str(tmpdir),
            '--format', 'json',
            '--inline', '{A: 1, B: [2, 4, 6], C: 3}',
            '-i', '5']
    dgmain.main(args)
    assert os.path.exists(os.path.join(tmpdir, 'generated-0'))


def test_parse_inline_yaml_blank_string():
    args = ['--format', 'json',
            '--inline', ' ']
    with pytest.raises(datagen.SpecException):
        dgmain.main(args)


def test_wrap_main(tmpdir):
    args = ['test_main.py',
            '-o', str(tmpdir),
            '--format', 'json',
            '--inline', ' ']
    import sys
    sys.argv = args
    # for coverage
    dgmain.wrap_main()
