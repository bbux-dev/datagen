Data Maker Repository
========================

## Overview

This is a tool for making data according to specifications. The goal is to separate the structure of the data from the
values that populate it. A single Data Spec could be used to generate JSON, XML, or a csv file. Each field has its own
Field Spec that defines how the values for it should be created.

## Build

To build a command line version of the tool:

```shell script
pyinstaller cli.py --name datamaker --onefile
```

The executable will be located in `dist/datamaker`


## Examples
See [examples](docs/EXAMPLES.md)

## Templating
To populate a template file with the generated values for each iteration, pass the -t /path/to/template arg to the datamaker
command.  We use the [Jinja2](https://pypi.org/project/Jinja2/) templating engine under the hood.  The basic format is to put
the field names in {{ field name }} notation wherever they should be substituted.  For example the following is a template
for bulk indexing data into Elasticsearch.

```json
{ "index" : { "_index" : "test", "_id" : "{{ id }}" } }
{ "doc" : {"name" : "{{ name }}", "age": "{{ age }}", "gender": "{{ gender }}" } }
```

We could then create a spec to populate the id, name, age, and gender fields. Such as:
```json
{
  "id": {"type": "range", "data": [1, 10]},
  "gender": { "M":  0.48, "F":  0.52 },
  "name": [ "bob", "rob", "bobby", "bobo", "robert", "roberto", "bobby joe", "roby", "robi", "steve"]
}
```

When we run the tool we get the data populated for the template:
```shell script
./cli.py -s ~/scratch/es-spec.json -t ~/scratch/template.json -i 10
{ "index" : { "_index" : "test", "_id" : "1" } }
{ "doc" : {"name" : "bob", "age": "", "gender": "M" } }
{ "index" : { "_index" : "test", "_id" : "2" } }
{ "doc" : {"name" : "rob", "age": "", "gender": "M" } }
...
```

## Custom Code Loading
There are a lot of types of data that are not generated with this tool. Instead of adding them all, there is a mechanism
to bring your own data suppliers. We make use of the awesome [catalogue](https://pypi.org/project/catalogue/) library to
allow auto discovery of custom functions using decorators.  Below is an example of a custom class which reverses the output
of another supplier. Types that are amazing and useful should be nominated for core inclusion, please put up a PR if you
create or use one that solves many of your data generation issues.

```python
import datamaker
from datamaker import suppliers

class ReverseStringSupplier:
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def next(self, iteration):
        # value from the wrapped supplier
        value = str(self.wrapped.next(iteration))
        # python way to reverse a string, hehe
        return value[::-1]


@datamaker.registry.types('reverse_string')
def configure_supplier(field_spec, loader):
    # load the supplier for the given ref
    key = field_spec.get('ref')
    spec = loader.refs.get(key)
    wrapped = suppliers.values(spec)
    # wrap this with our custom reverse string supplier
    return ReverseStringSupplier(wrapped)
```

Now when we see a type of "reverse_string" like in the example below, we will use the given function to configure the
supplier for it. The function name is arbitrary, but the signature must match.
```
{
  "backwards": {
    "type": "reverse_string",
    "ref": "ANIMALS"
  },
  "refs": { 
    "ANIMALS": {
      "type": "values",
      "data": ["zebra", "hedgehog", "llama", "flamingo"]
    }
  }
}
```

To supply custom code to the tool use the -c or --code arguments.
```shell script
.dist/datamaker -s reverse-spec.json -i 4 -c custom.py another.py
arbez
gohegdeh
amall
ognimalf
```

## Data Spec

A Data Spec is a Dictionary where the keys are the names of the fields to generate and each value is a Field Spec that
describes how the values for that field are to be generated. There is one reserved key in the root of the Data Spec: refs.
The refs is a special section of the Data Spec where Field Specs are defined but not tied to any specific field.  These
refs can then be used or referenced by other Specs. An example would be a combine Spec which points to two references that
should be joined. Below is an example Data Spec for creating email addresses.

```json
{
  "email": {
    "type": "combine",
    "refs": ["HANDLE", "DOMAINS"],
    "config": { "join_with": "@"}
  },
  "refs": { 
    "HANDLE": {
      "type": "combine",
      "refs": ["ANIMALS", "ACTIONS"],
      "config": { "join_with": "_"}
    },
    "ANIMALS": {
      "type": "values",
      "data": ["zebra", "hedgehog", "llama", "flamingo"]
    },
    "ACTIONS": {
      "type": "values",
      "data": ["fling", "jump", "launch", "dispatch"]
    },
    "DOMAINS": {
      "type": "values",
      "data": ["gmail.com", "yahoo.com", "hotmail.com"]
    } 
  }
}
```

This Data Spec uses two Combine Specs to build up the pieces for the email address.  The first Combine Spec lives in the
Refs section. This one creates the user name or handle by combining the values generated by the ANIMALS Ref with the ACTIONS one.
The email field then combines the HANDLE Ref with the DOMAINS one.

Running datamaker from the command line against this spec:

```shell script
dist/datamaker -s ~/example.json -i 12
zebra_fling@gmail.com
hedgehog_jump@yahoo.com
llama_launch@hotmail.com
flamingo_dispatch@gmail.com
zebra_fling@yahoo.com
hedgehog_jump@hotmail.com
llama_launch@gmail.com
flamingo_dispatch@yahoo.com
zebra_fling@hotmail.com
hedgehog_jump@gmail.com
llama_launch@yahoo.com
flamingo_dispatch@hotmail.com
```

## Field Specs
See [field specs](docs/FIELDSPECS.md)