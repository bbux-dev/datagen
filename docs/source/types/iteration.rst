iteration
---------

An `iteration` or `rownum` spec is used to populate the record number that is being generated. By default the offset
is set to `1`. To get zero based indexes for iteration, set the `offset` config parameter to 0.

Prototype:

.. code-block:: text

    {
      "<field name>": {
        "type": "iteration",
        OR
        "type": "rownum",
        OR
        "type": "rownum",
        "config": {
          "offset": N
        }
    }

Examples:

.. code-block:: json

    {
      "id": {
        "type": "iteration"
      }
    }

.. code-block:: json

    {
      "id": {
        "type": "rownum",
        "config": { "offset": 0 }
      }
    }

.. code-block:: text

    $ datacraft -s iteration.json  -i 3 -t 'ID: {{ id | safe }}' -l off
    ID: 1
    ID: 2
    ID: 3
