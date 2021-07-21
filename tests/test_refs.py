import pytest
import dataspec


def test_ref_with_ref_name():
    spec_builder = dataspec.spec_builder()
    spec_builder.add_ref('values', dataspec.builder.values([1, 2, 3]))
    spec_builder.ref('points_at_values', ref_name='values')
    generator = spec_builder.build().generator(1)
    assert next(generator) == {'points_at_values': 1}


def test_ref_with_data_as_name():
    spec_builder = dataspec.spec_builder()
    spec_builder.add_ref('values', dataspec.builder.values([1, 2, 3]))
    spec_builder.ref('points_at_values_with_prefix', data='values', prefix='@')
    generator = spec_builder.build().generator(1)
    assert next(generator) == {'points_at_values_with_prefix': '@1'}


def test_ref_missing_required():
    spec_builder = dataspec.spec_builder()
    spec_builder.add_ref('values', dataspec.builder.values([1, 2, 3]))
    spec_builder.ref('points_at_nothing')
    generator = spec_builder.build().generator(1)
    with pytest.raises(dataspec.SpecException):
        next(generator)