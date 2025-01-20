import datacraft

from . import builder


def test_iteration_spec():
    spec = builder.single_field("foo:iteration", {}).build()
    loader = datacraft.loader.field_loader(spec)
    supplier = loader.get('foo')

    value1 = supplier.next(0)
    assert value1 == 1
    value2 = supplier.next(1)
    assert value2 == 2


def test_iteration_spec_with_offset():
    spec = builder.single_field("foo:iteration", {"config": {"offset": 0}}).build()
    loader = datacraft.loader.field_loader(spec)
    supplier = loader.get('foo')

    value1 = supplier.next(0)
    assert value1 == 0
    value2 = supplier.next(1)
    assert value2 == 1
