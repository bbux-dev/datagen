v0.11.1
-------
* Added `iteration` and alias type `rownum`. This is used to indicate the number of the record that is being generated.

v0.11.0
-------
* Addition of <date.type>.now e.g.
```
date.now
date.epoch.now
date.epoch.millis.now
date.epoch.ms.now
date.iso.now
date.iso.micros.now
date.iso.us.now
date.iso.millis.now
date.iso.ms.now
```
These give the date in the specified format for the current time on the local system.

v0.10.2
-------
* Fix for `infer-spec` when data lists are empty

v0.10.1
-------
* Added `--type-schema <type>` cli arg to print out the JSON schema for a specific type if defined
* Added `--server-host <HOST>` cli arg for specifying the Flask server host parameter
* Added abbreviations `--format j` for json and `--format jp` for json-pretty

v0.10.0
-------
* Added `record_entries` and `record_generator` methods. These are used with to generate Data Classes instead of raw
dictionaries.
```python
import datacraft

@dataclass
class Entry:
    id: str
    timestamp: str
    handle: str
    
raw_spec = {
    "id": {"type": "uuid"},
    "timestamp": {"type": "date.iso.millis"},
    "handle": {"type": "cc-word", "config": { "min": 4, "max": 8, "prefix": "@" } }
}
print(*datacraft.record_entries(Entry, raw_spec, 3), sep='\\n')
#Entry(id='d5aeb7fa-374c-4228-8645-e8953165f163', timestamp='2024-07-03T04:10:10.016', handle='@DAHQDSsF')
#Entry(id='acde6f46-4692-45a7-8f0c-d0a8736c4386', timestamp='2024-07-06T17:43:36.653', handle='@vBTf71sP')
#Entry(id='4bb5542f-bf7d-4237-a972-257e24a659dd', timestamp='2024-08-01T03:06:49.724', handle='@gzfY_akS')
```
* Fix for infer spec when nested objects are in a list

v0.9.0
------

* Added `masked` type as alias for `regex_replace`. Added feature where single
  value for data element is treated as replace all values with this e.g.

```json
{
  "ssn": {
    "type": "masked",
    "ref": "raw_ssn",
    "data": "NNN-NN-NNNN"
  },
  "refs": {
    "raw_ssn": ["123-45-6789", "555-55-5555"]
  }
}
```
* Added `--endpoint-spec` argument. This specifies the path to a spec like file where each key
is an endpoint and each value is the spec to generate data for that endpoint e.g:

```json
{
  "/products/list": {
    "product_id": { "type": "uuid" }
  },
  "/orders/recent": {
    "order_id": { "type": "uuid" },
    "customer_id": { "type": "uuid" }
  }
}
```

Here when you run data craft with the arg `--endpoint-spec /path/to/epspec.json` the tool will spin up a flask server
with two endpoints one for `/products/list` and one for `/orders/recent`

* Added `--csv-select` option to infer-spec cli. This allows a csv file to be turned into a csv_select spec.
* Fixed broken `caclulate` type

v0.8.1
------
* Fix for infer on multiple JSON files to combine them before inference
* Fix to handle nested Objects in inference

v0.8.0
------
* added New `ref_list` type. For inject field values into positions in list/array objects.
* added `escape` and `escape_str` params for `char_class` types.
* Added new command line utility `infer-spec`. This will take example CSV or JSON data and will attempt to infer a
Data Spec from the examples. This can be used to bootstrap Data Spec generation.

```shell
$ head -5 test.csv
ip,lat,long,city,date
192.168.1.1,34.0522,-118.2437,Los Angeles,2023-10-08T08:45:00
192.168.1.2,40.7306,-73.9352,New York,2023-10-08T09:15:23
192.168.1.3,51.5074,-0.1278,London,2023-10-08T10:32:50
192.168.1.4,48.8566,2.3522,Paris,2023-10-08T11:05:31
```
```shell
$ infer-spec --csv examples.csv
INFO [09-Oct-2023 09:20:37 AM] Processing examples.csv...
{
    "ip": {
        "type": "ip",
        "config": {
            "base": "192.168.1"
        }
    },
    "lat": {
        "type": "geo.lat"
    },
    "long": {
        "type": "geo.long"
    },
    "city": {
        "type": "values",
        "data": [
            "London",
            "Los Angeles",
            "Vancouver",
            "New Delhi",
            "Paris",
            "New York",
            "Tokyo",
            "San Francisco",
            "Berlin",
            "Chicago"
        ]
    },
    "date": {
        "type": "date.iso"
    }
}
```

v0.7.3
------
* added --server-port option

v0.7.2
------
* Fix to allow POST and GET for server end points
* Fix for count as list for values objects
* Added --server-delay arg to add option delay between requests and response in seconds

v0.7.1
------
* Added py.typed to get type hint support to dependent projects

v0.7.0
------
* Added `replace` and `regex_replace` types
* Added `data.iso.ms` and `date.iso.millis` for iso dates that include milliseconds
* Added `date.epoch` and `date.epoch.ms` to create dates that are seconds or milliseconds since epoch (Jan 1 1970)
* Added `datacraft.registered_types()`, `datacraft.registered_formats()`, and `datacraft.registered_casters()` to root.
* Added `datacraft.type_usage('type-name')` for getting API examples for a given registered type, if that type has API
usage information provided
* Added `_TRUE_` and `_FALSE_` special tokens for values specs to produce JSON `true` and `false` values

v0.6.0
------

* Addition of zfillN casters
* Added --cast-list and --format-list command line args to dump registered casters and formatters
* Added `csv-with-header` (`csvh` for short) formatters, i.e. `--format csvh`
* Various bug fixes

v0.5.0
------
* Bug fixes and removal of `datacraft.spec_builder` function and tooling from API.

v0.4.0
------
* Added initial built in type help system with command line --type-list and --type-help command line arguments

v0.3.2
--------
* Switched to lru_cache for pre python 3.9 compatibility

v0.3.1
------

* Fix for custom types not loading when datacraft used programmatically.
* Addition of `datacraft.entries` function for quickly generating records from a given spec

```python
import datacraft

spec = {
   "super_power": {
      "type": "values",
      "config": { "sample": True },
      "data": {
         "fast reader": 0.5,
         "wordle expert": 0.4,
         "super strength": 0.05,
         "super speed": 0.01,
         "invisibility": 0.01,
         "indestructible": 0.01,
         "laser eyes": 0.01,
         "teleportation": 0.00000000001
      }
   }
}
records = datacraft.entries(spec, 5)
```

v0.3.0
------
* Introduced `datacraft.custom_type_loader` entrypoint for discovering and loading `@datacraft.registry.*` functions.

Add to setup.cfg:

```yaml
[options.entry_points]
datacraft.custom_type_loader =
    mycustomstuff = mypackage:load_custom
```

See [custom-types-entry-point](https://datacraft.readthedocs.io/en/latest/usage.html#custom-types-entry-point) for
details

v0.2.1
------
* Added typing support to ``csv_select`` field definitions: i.e.
```json
{
   "multiple_csv_fields": {
      "type": "csv_select",
      "data": {
         "one:float": 1,
         "tre": 3,
         "svn": {"col": 7, "cast": "int"}
      },
      "config": {"datafile": "{{ input_csv }}"}
   }
}
```
* Fixes for GeoJSON example documentation

v0.2.0
------

 * Added new `templated` type 
(see [templated type](https://datacraft.readthedocs.io/en/latest/coretypes.html#templated)) e.g:
```json
{"filled_in": {"type":  "templated", "data": "{{one}} and {{two}} and a ...", "refs": ["one", "two"]}}
```
 * Expanded API for suppliers module. Most core types have an analog function in the suppliers module to create a value 
   supplier. e.g:
```python
from datacraft import suppliers
supplier_map = { 'char': suppliers.values(['a', 'b', 'c']), 'num': suppliers.values([1, 2, 3]) }
template_str = 'letter {{ char }}, number {{ num }}'
supplier = suppliers.templated(supplier_map, template_str)
supplier.next(0)  # -> letter a, number 1
```
 * Records now returned as list by default, so `--records-per-file` or `-r` dictates the size of this list e.g:
```shell
# outputs 10 total records with two per file as a list
datacraft --inline '{foo:date.iso: {}}' --format json-pretty -x --log-level off -i 10 -r 2 -o . -p demo -e .json
ls
demo-0.json  demo-1.json  demo-2.json  demo-3.json  demo-4.json
cat demo-0.json
[
    {
        "foo": "2022-02-01T17:17:58"
    },
    {
        "foo": "2022-02-14T19:56:45"
    }
]
```
 * Migrated from travis-ci to circle-ci for builds
 * Lots of bug fixes and code cleanup

v0.1.0
------

 * Initial Release
