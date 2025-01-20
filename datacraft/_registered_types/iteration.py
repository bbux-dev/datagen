"""module for iteration type datacraft registry functions"""
import logging

import datacraft
from . import common
from . import schemas

_log = logging.getLogger(__name__)
_ITERATION_KEY = 'iteration'
_ITERATION_ALIAS_ROW = 'rownum'


class _IterationSupplier(datacraft.ValueSupplierInterface):
    def __init__(self, offset: int):
        self.offset = offset

    def next(self, iteration):
        return iteration + self.offset


@datacraft.registry.schemas(_ITERATION_ALIAS_ROW)
@datacraft.registry.schemas(_ITERATION_KEY)
def _get_iteration_schema():
    """ get the schema for iteration type """
    return schemas.load(_ITERATION_KEY)


@datacraft.registry.types(_ITERATION_ALIAS_ROW)
@datacraft.registry.types(_ITERATION_KEY)
def _configure_iteration_supplier(field_spec, loader):
    """ configure the supplier for iteration types """
    config = datacraft.utils.load_config(field_spec, loader)

    offset = int(config.get('offset', 1))

    return _IterationSupplier(offset)


@datacraft.registry.usage(_ITERATION_ALIAS_ROW)
@datacraft.registry.usage(_ITERATION_KEY)
def _example_iteration_usage():
    example_one = {
        "id": {
            "type": _ITERATION_KEY
        }
    }
    example_two = {
        "row": {
            "type": _ITERATION_ALIAS_ROW,
            "config": {"offset": 0}
        }
    }
    examples = [example_one, example_two]
    clis = [common.standard_cli_example_usage(example, 3, pretty=True) for example in examples]
    apis = [common.standard_api_example_usage(example, 3) for example in examples]

    return {
        'cli': '\n'.join(clis),
        'api': '\n'.join(apis)
    }
