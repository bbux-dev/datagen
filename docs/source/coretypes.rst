***************
 Core Types
***************

These are the built-in field spec types. Organized by the type of Data they generate or by
their function or utility.

Strings
=======

For generating strings in various formats

.. include:: types/char_class.rst

.. include:: types/unicode.rst

.. include:: types/uuid.rst

Numeric
=======

For generating numeric values in different ways.

.. include:: types/ranges.rst

.. include:: types/distribution.rst

.. include:: types/iteration.rst

Date & Time
===========

For generating dates and timestamp in a variety of formats

.. include:: types/date.rst

Geographic
==========

For generating basic decimal degrees of latitude and longitude

.. include:: types/geo.rst

Network
=======

Network related types

.. include:: types/network.rst

Utility/Common
==============

Common types or types that are used in a utility capacity.

.. include:: types/values.rst

.. include:: types/refs.rst

.. include:: types/ref_list.rst

.. include:: types/weighted_refs.rst

.. _config_ref_core_types:

.. include:: types/config_ref.rst

.. include:: types/nested.rst

External Data
=============

The csv types are used to input large numbers of values into a spec.

.. _csv_core_types:

.. include:: types/csv.rst

Operator Types
==============

These make use of one or more other fields or references to compute their values.

.. include:: types/sample.rst

.. include:: types/combine.rst

.. include:: types/calculate.rst

.. include:: types/templated.rst

.. include:: types/replace.rst
