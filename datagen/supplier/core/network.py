"""
Network related types

ip/ipv4
-------

Ip addresses can be generated
using `CIDR notation <https://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing>`_
or by specifying a base. For example, if you wanted to generate ips in the
10.0.0.0 to 10.0.0.255 range, you could either specify a ``cidr`` param of
10.0.0.0/24 or a ``base`` param of 10.0.0.

Prototype:

.. code-block:: python

    {
      "<field name>": {
        "type": "ipv4",
        "config": {
          "cidr": "<cidr value /8 /16 /24 only>",
          OR
          "base": "<beginning of ip i.e. 10.0>"
        }
      }
    }

Examples:

.. code-block:: json

    {
      "network": {
        "type": "ipv4",
        "config": {
          "cidr": "2.22.222.0/16"
        }
      },
      "network_shorthand:ip?cidr=2.22.222.0/16": {},
      "network_with_base:ip?base=192.168.0": {}
    }

ip.precise
----------

The default ip type only supports cidr masks of /8 /16 and /24. If you want more precise ip ranges you need to use the
``ip.precise`` type. This type requires a cidr as the single config param. The default mode for ``ip.precise`` is to
increment the ip addresses. Set config param sample to one of true, on, or yes to enable random ip addresses selected
from the generated ranges.

Prototype:

.. code-block:: python

    {
      "<field name>": {
        "type": "ipv4",
        "config": {
          "cidr": "<valid cidr value>",
        }
      }
    }

Examples:

.. code-block:: json

    {
      "network": {
        "type": "ip.precise",
        "config": {
          "cidr": "192.168.0.0/14",
          "sample": "true"
        }
      }
    }

net.mac
-------

For creating MAC addresses

Prototype:

.. code-block:: python

    {
      "<field name>": {
        "type": "net.mac",
        "config": {
          "dashes": "If dashes should be used as the separator one of on, yes, 'true', or True"
        }
      }
    }

Examples:

.. code-block:: json

    {
      "network": {
        "type": "net.mac"
      }
    }

.. code-block:: json

    {
      "network": {
        "type": "net.mac",
        "config": {
          "dashes": "true"
        }
      }
    }
"""
from typing import Dict
import ipaddress
import json
import string
import random

import datagen

IP_KEY = 'ip'
IPV4_KEY = 'ipv4'
IP_PRECISE_KEY = 'ip.precise'
NET_MAC_KEY = 'net.mac'


class IpV4Supplier(datagen.ValueSupplierInterface):
    """
    Default implementation for generating ip values, uses separate suppliers for each octet of the ip
    """

    def __init__(self, octet_supplier_map: Dict[str, datagen.ValueSupplierInterface]):
        """
        Args:
            octet_supplier_map: dictionary mapping each octet to a ValueSupplier
        """
        self.first = octet_supplier_map['first']
        self.second = octet_supplier_map['second']
        self.third = octet_supplier_map['third']
        self.fourth = octet_supplier_map['fourth']

    def next(self, iteration):
        first = self.first.next(iteration)
        second = self.second.next(iteration)
        third = self.third.next(iteration)
        fourth = self.fourth.next(iteration)
        return f'{first}.{second}.{third}.{fourth}'


@datagen.registry.schemas(IP_KEY)
def _get_ip_schema():
    """ returns the schema for the ip types """
    return datagen.schemas.load(IP_KEY)


@datagen.registry.schemas(IPV4_KEY)
def _get_ipv4_schema():
    """ returns the schema for the ipv4 types """
    # shares schema with ip
    return datagen.schemas.load(IP_KEY)


@datagen.registry.schemas(IP_PRECISE_KEY)
def _get_ip_precise_schema():
    """ returns the schema for the ip.precise types """
    return datagen.schemas.load(IP_PRECISE_KEY)


@datagen.registry.schemas(NET_MAC_KEY)
def _get_mac_addr_schema():
    """ returns the schema for the net.mac types """
    return datagen.schemas.load(NET_MAC_KEY)


@datagen.registry.types(IPV4_KEY)
def _configure_ipv4(field_spec, _):
    """ configures value supplier for ipv4 type """
    return _configure_ip(field_spec, _)


@datagen.registry.types(IP_KEY)
def _configure_ip(field_spec, loader):
    """ configures value supplier for ip type """
    config = datagen.utils.load_config(field_spec, loader)
    if 'base' in config and 'cidr' in config:
        raise datagen.SpecException('Must supply only one of base or cidr param: ' + json.dumps(field_spec))

    parts = _get_base_parts(config)
    # this is the same thing as a constant
    if len(parts) == 4:
        return datagen.suppliers.values('.'.join(parts))
    sample = config.get('sample', 'yes')
    octet_supplier_map = {
        'first': _create_octet_supplier(parts, 0, sample),
        'second': _create_octet_supplier(parts, 1, sample),
        'third': _create_octet_supplier(parts, 2, sample),
        'fourth': _create_octet_supplier(parts, 3, sample),
    }
    return IpV4Supplier(octet_supplier_map)


def _get_base_parts(config):
    """
    Builds the base ip array for the first N octets based on
    supplied base or on the /N subnet mask in the cidr
    """
    if 'base' in config:
        parts = config.get('base').split('.')
    else:
        parts = []

    if 'cidr' in config:
        cidr = config['cidr']
        if '/' in cidr:
            mask = cidr[cidr.index('/') + 1:]
            if not mask.isdigit():
                raise datagen.SpecException('Invalid Mask in cidr for config: ' + json.dumps(config))
            if int(mask) not in [8, 16, 24]:
                raise datagen.SpecException('Invalid Subnet Mask in cidr for config: ' + json.dumps(config)
                                            + ' only one of /8 /16 or /24 supported')
            ip_parts = cidr[0:cidr.index('/')].split('.')
            if len(ip_parts) < 4 or not all(part.isdigit() for part in ip_parts):
                raise datagen.SpecException('Invalid IP in cidr for config: ' + json.dumps(config))
            if mask == '8':
                parts = ip_parts[0:1]
            if mask == '16':
                parts = ip_parts[0:2]
            if mask == '24':
                parts = ip_parts[0:3]
        else:
            raise datagen.SpecException('Invalid Subnet Mask in cidr for config: ' + json.dumps(config)
                                        + ' only one of /8 /16 or /24 supported')
    return parts


def _create_octet_supplier(parts, index, sample):
    """ creates a value supplier for the index'th octet """
    # this index is for a part that is static, create a single value supplier for that part
    if len(parts) >= index + 1 and parts[index].strip() != '':
        octet = parts[index].strip()
        if not octet.isdigit():
            raise datagen.SpecException(f'Octet: {octet} invalid for base, Invalid Input: ' + '.'.join(parts))
        if not 0 <= int(octet) <= 255:
            raise datagen.SpecException(
                f'Each octet: {octet} must be in range of 0 to 255, Invalid Input: ' + '.'.join(parts))
        return datagen.suppliers.values(octet)
    # need octet range at this point
    octet_range = list(range(0, 255))
    spec = {'config': {'sample': sample}, 'data': octet_range}
    return datagen.suppliers.values(spec)


class IpV4PreciseSupplier(datagen.ValueSupplierInterface):
    """
    Class that supports precise ip address generation by specifying cidr values, much slower for large ip ranges
    """

    def __init__(self, cidr: str, sample: bool):
        """
        Args:
            cidr: notation specifying ip range
            sample: if the ip addresses should be sampled from the available set
        """
        self.net = ipaddress.ip_network(cidr)
        self.sample = sample
        cnt = 0
        for _ in self.net:
            cnt += 1
        self.size = cnt

    def next(self, iteration):
        if self.sample:
            idx = random.randint(0, self.size - 1)
        else:
            idx = iteration % self.size
        return str(self.net[idx])


@datagen.registry.types(IP_PRECISE_KEY)
def _configure_precise_ip(field_spec, _):
    """ configures value supplier for ip.precise type """
    config = field_spec.get('config')
    if config is None:
        raise datagen.SpecException('No config for: ' + json.dumps(field_spec) + ', param cidr required')
    cidr = config.get('cidr')
    sample = config.get('sample', 'no').lower() in ['yes', 'true', 'on']
    if cidr is None:
        raise datagen.SpecException('Invalid config for: ' + json.dumps(field_spec) + ', param cidr required')
    return IpV4PreciseSupplier(cidr, sample)


class MacAddressSupplier(datagen.ValueSupplierInterface):
    """ Class for supplying random mac addresses """
    def __init__(self, delim: str):
        """
        Args:
            delim: how mac address pieces are separated
        """
        self.delim = delim
        self.tokens = string.digits + 'ABCDEF'

    def next(self, iteration):
        parts = [''.join(random.sample(self.tokens, 2)) for _ in range(6)]
        return self.delim.join(parts)


@datagen.registry.types(NET_MAC_KEY)
def _configure_mac_address_supplier(field_spec, loader):
    """ configures value supplier for net.mac type """
    config = datagen.utils.load_config(field_spec, loader)
    if datagen.utils.is_affirmative('dashes', config):
        delim = '-'
    else:
        delim = datagen.types.get_default('mac_addr_separator')

    return MacAddressSupplier(delim)