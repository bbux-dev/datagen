""" Module for ListCountSamplerSupplier """
from typing import Union
import random

import datagen


class ListCountSamplerSupplier(datagen.ValueSupplierInterface):
    """
    Supplies values by sampling from a list with hard min max and count
    """

    def __init__(self, data: Union[str, list],
                 count_supplier: datagen.ValueSupplierInterface,
                 join_with: Union[str, None] = ''):
        """
        Args:
            data: string or list to sample from
            count_supplier: to supply number of values to return
            join_with: how to join the values into a string, None means return as list
        """
        self.values = data
        self.count_supplier = count_supplier
        self.join_with = join_with

    def next(self, iteration):
        count = self.count_supplier.next(iteration)
        data = random.sample(self.values, count)
        if self.join_with is not None:
            return self.join_with.join([str(elem) for elem in data])
        return data
