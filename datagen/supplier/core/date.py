"""
A Date Field Spec is used to generate date strings. The default format is
day-month-year i.e. Christmas 2050 would be: 25-12-2050. There is also
a `date.iso` type that generates ISO8601 formatted date strings without
microseconds and a `date.iso.us` for one that generates them with microseconds.
We use the `format specification <https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format
-codes>`_ from the datetime module.

Uniformly Sampled Dates
-----------------------

The default strategy is to create random dates within a 30 day range, where the
start date is today. You can use the `start` parameter to set a specific start
date for the dates. You can also explicitly specify an `end` date. The `start`
and `end` parameters should conform to the specified date format, or the default
if none is provided. The `offset` parameter can be used to shift the dates by a
specified number of days. A positive `offset` will shift the start date back. A
negative `offset` will shift the date forward. The `duration_days` parameter can
be used to specify the number of days that should be covered in the date range,
instead of the default 30 days. This parameter is usually specified as an
integer constant.

.. code-block::

       start                              end (default start + 30 days)
          |--------------------------------|
  |+offset|                           start+duration_days
  |--------------------------------|
          |-offset|
                  |--------------------------------|


Dates Distributed around a Center Point
---------------------------------------

An alternative strategy is to specify a `center_date` parameter with an
optional `stddev_days`. This will create a normal or gaussian distribution of
dates around the center point.

.. code-block::

                       |
                       |
                    |  |  |
                 |  |  |  |  |
              |  |  |  |  |  |  |
     |  |  |  |  |  |  |  |  |  |  |  |  |
    |-------------------------------------|
    |         | stddev | stddev |         |
                    center

Prototype:

.. code-block:: python

    {
      "<field name>": {
        "type": "date",
        OR,
        "type": "date.iso",
        OR,
        "type": "date.iso.us",
        "config": {
          "format": "Valid datetime format string",
          "duration_days": "The number of days from the start date to create date strings for",
          "start": "date string matching format or default format to use for start date",
          "end": "date string matching format or default  format to use for end date",
          "offset": "number of days to shift base date by, positive means shift backwards, negative means forward",
          "center_date": "date string matching format or default format to use for center date",
          "stddev_days": "The standard deviation in days from the center date that dates should be distributed"
        }
      }
    }

Examples:

.. code-block:: json

    {
      "dates": {
        "type": "date",
        "config": {
          "duration_days": "90",
          "start": "15-Dec-2050 12:00",
          "format": "%d-%b-%Y %H:%M"
        }
      }
    }

.. code-block:: json

    {
      "dates": {
        "type": "date",
        "config": {
          "center_date": "20500601 12:00",
          "format": "%Y%m%d %H:%M",
          "stddev_days": "2"
        }
      }
    }

"""
from typing import Union
import datetime
import json
import logging

import datagen
import datagen.model

DATE_KEY = 'date'
DATE_ISO_KEY = 'date.iso'
DATE_ISO_US_KEY = 'date.iso.us'

ISO_FORMAT_NO_MICRO = '%Y-%m-%dT%H:%M:%S'
ISO_FORMAT_WITH_MICRO = '%Y-%m-%dT%H:%M:%S.%f'

SECONDS_IN_DAY = 24.0 * 60.0 * 60.0

log = logging.getLogger(__name__)


@datagen.registry.schemas(DATE_KEY)
def _get_date_schema():
    """ returns the schema for date types """
    return datagen.schemas.load(DATE_KEY)


@datagen.registry.schemas(DATE_ISO_KEY)
def _get_date_iso_schema():
    """ returns the schema for date.iso types """
    # NOTE: These all share a schema
    return datagen.schemas.load(DATE_KEY)


@datagen.registry.schemas(DATE_ISO_US_KEY)
def _get_date_iso_us_schema():
    """ returns the schema for date.iso.us types """
    # NOTE: These all share a schema
    return datagen.schemas.load(DATE_KEY)


class DateSupplier(datagen.ValueSupplierInterface):
    """
    Value Supplier implementation for dates
    """

    def __init__(self,
                 timestamp_distribution: datagen.model.Distribution,
                 date_format_string: str):
        """
        Args:
            timestamp_distribution: distribution for timestamps
            date_format_string: format string for timestamps
        """

        self.date_format = date_format_string
        self.timestamp_distribution = timestamp_distribution

    def next(self, iteration):
        random_seconds = self.timestamp_distribution.next_value()
        next_date = datetime.datetime.fromtimestamp(random_seconds)
        if self.date_format:
            return next_date.strftime(self.date_format)
        return next_date.replace(microsecond=0).isoformat()


def uniform_date_timestamp(
        start: str,
        end: str,
        offset: int,
        duration: int,
        date_format_string: str) -> Union[None, datagen.Distribution]:
    """
    Creates a uniform distribution for the start and end dates shifted by the offset

    Args:
        start: start date string
        end: end date string
        offset: number of days to shift the duration, positive is back negative is forward
        duration: number of days after start
        date_format_string: format for parsing dates

    Returns:
        Distribution that gives uniform seconds since epoch for the given params
    """
    offset_date = datetime.timedelta(days=offset)
    if start:
        try:
            start_date = datetime.datetime.strptime(start, date_format_string) - offset_date
        except TypeError as err:
            raise datagen.SpecException(f"TypeError. Format: {date_format_string}, may not match param: {start}") from err
    else:
        start_date = datetime.datetime.now() - offset_date
    if end:
        # buffer end date by one to keep inclusive
        try:
            end_date = datetime.datetime.strptime(end, date_format_string) \
                + datetime.timedelta(days=1) - offset_date
        except TypeError as err:
            raise datagen.SpecException(f"TypeError. Format: {date_format_string}, may not match param: {end}") from err
    else:
        # start date already include offset, don't include it here
        end_date = start_date + datetime.timedelta(days=abs(int(duration)), seconds=1)

    start_ts = int(start_date.timestamp())
    end_ts = int(end_date.timestamp())
    if end_ts < start_ts:
        log.warning("End date (%s) is before start date (%s)", start_date, end_date)
        return None
    return datagen.distributions.uniform(start=start_ts, end=end_ts)


def gauss_date_timestamp(
        center_date_str: Union[str, None],
        stddev_days: float,
        date_format_string: str):
    """
    Creates a normally distributed date distribution around the center date

    Args:
        center_date_str: center date for distribution
        stddev_days: standard deviation from center date in days
        date_format_string: format for returned dates

    Returns:
        Distribution that gives normally distributed seconds since epoch for the given params
    """
    if center_date_str:
        center_date = datetime.datetime.strptime(center_date_str, date_format_string)
    else:
        center_date = datetime.datetime.now()
    mean = center_date.timestamp()
    stddev = stddev_days * SECONDS_IN_DAY
    return datagen.distributions.normal(mean=mean, stddev=stddev)


@datagen.registry.types(DATE_KEY)
def _configure_supplier(field_spec: dict, loader: datagen.Loader):
    """ configures the date value supplier """
    config = datagen.utils.load_config(field_spec, loader)
    if 'center_date' in config or 'stddev_days' in config:
        return _create_stats_based_date_supplier(config)
    return _create_uniform_date_supplier(config)


def _create_stats_based_date_supplier(config: dict):
    """ creates stats based date supplier from config """
    center_date = config.get('center_date')
    stddev_days = config.get('stddev_days', datagen.types.get_default('date_stddev_days'))
    date_format = config.get('format', datagen.types.get_default('date_format'))
    timestamp_distribution = gauss_date_timestamp(center_date, float(stddev_days), date_format)
    return DateSupplier(timestamp_distribution, date_format)


def _create_uniform_date_supplier(config):
    """ creates uniform based date supplier from config """
    duration_days = config.get('duration_days', 30)
    offset = int(config.get('offset', 0))
    start = config.get('start')
    end = config.get('end')
    date_format = config.get('format', datagen.types.get_default('date_format'))
    timestamp_distribution = uniform_date_timestamp(start, end, offset, duration_days, date_format)
    if timestamp_distribution is None:
        raise datagen.SpecException(f'Unable to generate timestamp supplier from config: {json.dumps(config)}')
    return DateSupplier(timestamp_distribution, date_format)


@datagen.registry.types(DATE_ISO_KEY)
def _configure_supplier_iso(field_spec: dict, loader: datagen.Loader):
    """ configures the date.iso value supplier """
    return _configure_supplier_iso_date(field_spec, loader, ISO_FORMAT_NO_MICRO)


@datagen.registry.types(DATE_ISO_US_KEY)
def _configure_supplier_iso_microseconds(field_spec: dict, loader: datagen.Loader):
    """ configures the date.iso.us value supplier """
    return _configure_supplier_iso_date(field_spec, loader, ISO_FORMAT_WITH_MICRO)


def _configure_supplier_iso_date(field_spec, loader, iso_date_format):
    """ configures an iso based date supplier using the provided date format """
    config = datagen.utils.load_config(field_spec, loader)

    # make sure the start and end dates match the ISO format we are using
    start = config.get('start')
    end = config.get('end')
    date_format = config.get('format', )
    if start:
        start_date = datetime.datetime.strptime(start, date_format)
        config['start'] = start_date.strftime(iso_date_format)
    if end:
        end_date = datetime.datetime.strptime(end, date_format)
        config['end'] = end_date.strftime(iso_date_format)
    config['format'] = iso_date_format
    # End fixes to support iso

    if 'center_date' in config or 'stddev_days' in config:
        return _create_stats_based_date_supplier(config)
    return _create_uniform_date_supplier(config)
