# construct-typing
This project is an extension of the python package [*construct*](https://pypi.org/project/construct/). This Repository consists of two packages:

- **construct-stubs**: Adding .pyi for the whole *construct 2.10* package (according to  [PEP 561 stub-only packages](https://www.python.org/dev/peps/pep-0561/#stub-only-packages))
- **construct_typed**: Adding the additional classes that help with autocompletion and additional type hints.

## Installation
This package comply to [PEP 561](https://www.python.org/dev/peps/pep-0561/). So most of the static code analysers will recognise the stubs automatically.

You just have to type:
```
pip install construct-typing
```

## Usage
I'm mostly working with VSCode and Pylance (which works really great) ??? But i have also tested the stubs with mypy. ????

## Tests
The stubs are tested against the pytests of the *construct* package in a slightly modified form. Since the tests are relatively detailed I think most cases are covered.
The new typed constructs have new written tests.

The tests do not generate errors with:
- mypy (Version TODO)
- pyright (Version TODO)

## Explanation
### Stubs
The **construct-stubs** package is used for creating type hints for the orignial *construct* package. In particular the `build` and `parse` methods get type hints. So the core of the stubs  are the `TypeVar`'s `ParsedType` and `BuildTypes`:
- The `build` method of a `Construct` converts an object of one of the types defined by `BuildTypes` to a `bytes` object.
- The `parse` method of a `Construct` converts a `bytes` object to an object of type `ParsedType`.

For each of the `Construct`s it is defined which type it is parsed to and from which it can be build. 
For example:
 - an `Int16ub` construct parses to an `int` and can be build from an `int`.
 - an `Bytes` construct parsed to a `bytes` and can be build from an `bytes`, `bytearray` or `memoryview`.
 - an `Array(5, Int16ub)` construct parses to a `ListContainer[int]` and can be build from an `List[int]`. 

The problem is to describe the more complex constructs like:
 - `Sequence`, `FocusedSeq` which has heterogenous subcons in comparison to an `Array` with only homogenous subcons. 
 - `Struct`, `BitStruct`, `LazyStruct`, `Union` which has heterogenous and named subcons.

Currently only the very unspecific type `typing.Any` can be used as type hint (maybe in the future it can be optimised a little, when [variadic generics](https://mail.python.org/archives/list/typing-sig@python.org/thread/SQVTQYWIOI4TIO7NNBTFFWFMSMS2TA4J/) become available). But the biggest disadvantage is that autocompletion for the named subcons is not available.

Note: The stubs are based on *construct* in Version 2.10.


### Typed
TODO:
Es werden die Standard Python Klassen benutzt:
- "dataclasses.dataclass" für Struct, Union, ... (anstatt construct.Container)
- "list" für Array, ... (anstatt construct.ListContainer)
- "enum.Enum" für Enums
- "enum.EnumFlag" für EnumFlags

TODO:
Es handelt sich in der aktuellen Version noch um einen experimentelle Version!

TODO:
Es handelt sich um "strongly typed". D.h. es gibt keine Unterscheidung zwischen ParsedType und BuildTypes... Die korrenten Typen werden beim
"build" erzwungen (enforced). Bei einem falschen typen, wird eine exception (TypeError) erzeugt.
Nachteil: dass man manchmal mehr code schreiben muss um den korrekten klassennamen zu deklarieren, anstatt einfach nur "dict" zu schreiben
Vorteil: während der statischen Codeanalyse können schon mehr fehler entdeckt werden.


To include autocompletion and further enhance the type hints for these complex constructs the **construct_typed** package is used as an extension to the original *construct* package. It is mainly a bunch of Adapters for the original constructs with the focus on type hints.

It implements the following new types:
- `TStruct`: similar to `construct.Struct` but with `dataclasses.dataclass`
- `TBitStruct`: similar to `construct.BitStruct` but with `dataclasses.dataclass`
- `TEnum`: similar to `construct.Enum` but with `construct_typed.EnumBase`
- `TArray`: similar to `construct.Array` but with `list` insted of `construct.ListContainer`
- TODO: `TUnion`


A short example:

```python
import dataclasses
import typing as t
import construct as cs
import construct_typed as cst


class Orientation(cst.EnumBase):
    HORIZONTAL = 0
    VERTICAL = 1

@dataclasses.dataclass
class Image:
    signature: t.Optional[bytes] = cst.TStructField(cs.Const(b"BMP"))
    orientation: Orientation = cst.TStructField(cst.TEnum(cs.Int8ub, Orientation))
    width: int = cst.TStructField(cs.Int8ub)
    height: int = cst.TStructField(cs.Int8ub)
    pixels: t.List[int] = cst.TStructField(cst.TArray(cs.this.width * cs.this.height, cs.Byte))

format = cst.TStruct(Image)
obj = Image(orientation=Orientation.VERTICAL, width=3, height=2, pixels=[7, 8, 9, 11, 12, 13])
print(format.build(obj))
print(format.parse(b"BMP\x01\x03\x02\x07\x08\t\x0b\x0c\r"))
```
Output:
```
b'BMP\x01\x03\x02\x07\x08\t\x0b\x0c\r'
Image(signature=b'BMP', orientation=<Orientation.VERTICAL: 1>, width=3, height=2, pixels=[7, 8, 9, 11, 12, 13])
```


