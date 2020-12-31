import typing as t
import textwrap
import dataclasses
from .generic_wrapper import *


def StructField(
    subcon: Construct[ParsedType, BuildTypes],
    doc: t.Optional[str] = None,
    parsed: t.Optional[t.Callable[[t.Any, "cs.Context"], None]] = None,
) -> ParsedType:
    """
    Create a dataclass field for a "TStruct" and "TBitStruct" from a subcon.
    """
    # Rename subcon, if doc or parsed are available
    if (doc is not None) or (parsed is not None):
        if doc is not None:
            doc = textwrap.dedent(doc)
        subcon = cs.Renamed(subcon, newdocs=doc, newparsed=parsed)

    if subcon.flagbuildnone is True:
        # some subcons have a predefined default value. all other have "None"
        default: t.Any = None
        if isinstance(subcon, (cs.Const, cs.Default)):
            if callable(subcon.value):  # type: ignore
                raise ValueError("lamda as default is not supported")
            default = subcon.value  # type: ignore

        # if subcon builds from "None", set default to "None"
        field = dataclasses.field(
            default=default,
            init=False,
            metadata={"subcon": cs.Renamed(subcon, newdocs=doc)},
        )
    else:
        field = dataclasses.field(metadata={"subcon": subcon})

    return field  # type: ignore


class _TStruct(Adapter[t.Any, t.Any, ParsedType, BuildTypes]):
    """
    Base class for a typed struct, based on standard dataclasses.
    """

    def __init__(
        self, dataclass_type: t.Type[DataclassType], swapped: bool = False
    ) -> None:
        if not dataclasses.is_dataclass(dataclass_type):
            raise TypeError(
                'The class "{}" is not a "dataclasses.dataclass"'.format(
                    dataclass_type.__name__
                )
            )
        self.dataclass_type = dataclass_type
        self.swapped = swapped

        # get all fields from the dataclass
        fields = dataclasses.fields(self.dataclass_type)
        if self.swapped:
            fields = tuple(reversed(fields))

        # extract the construct formats from the struct_type
        subcon_fields = {}
        for field in fields:
            subcon_fields[field.name] = field.metadata["subcon"]

        # init adatper
        super(_TStruct, self).__init__(self._create_subcon(subcon_fields))  # type: ignore

    def _create_subcon(
        self, subcon_fields: t.Dict[str, t.Any]
    ) -> Construct[t.Any, t.Any]:
        raise NotImplementedError

    def _decode(
        self, obj: "cs.Container[t.Any]", context: "cs.Context", path: "cs.PathType"
    ) -> DataclassType:
        # get all fields from the dataclass
        fields = dataclasses.fields(self.dataclass_type)

        # extract all fields from the container, that are used for create the dataclass object
        dc_init = {}
        for field in fields:
            if field.init:
                value = getattr(obj, field.name)
                dc_init[field.name] = value

        # create object of dataclass
        dc = self.dataclass_type(**dc_init)  # type: ignore

        # extract all other values from the container, an pass it to the dataclass
        for field in fields:
            if not field.init:
                value = getattr(obj, field.name)
                setattr(dc, field.name, value)

        return dc

    def _encode(
        self, obj: DataclassType, context: "cs.Context", path: "cs.PathType"
    ) -> t.Dict[str, t.Any]:
        # get all fields from the dataclass
        fields = dataclasses.fields(self.dataclass_type)

        # extract all fields from the container, that are used for create the dataclass object
        ret_dict = {}
        for field in fields:
            value = getattr(obj, field.name)
            ret_dict[field.name] = value

        return ret_dict


class TStruct(_TStruct[ParsedType, BuildTypes]):
    """
    Typed struct, based on standard dataclasses.
    """

    # this is unfortunately needed because the stubs are using __new__ instead of __init__
    if t.TYPE_CHECKING:

        def __new__(
            cls, dataclass_type: t.Type[DataclassType], swapped: bool = False
        ) -> "TStruct[DataclassType, DataclassType]":
            ...

    def _create_subcon(
        self, subcon_fields: t.Dict[str, t.Any]
    ) -> Construct[t.Any, t.Any]:
        return cs.Struct(**subcon_fields)


class TBitStruct(_TStruct[ParsedType, BuildTypes]):
    """
    Typed bit struct, based on standard dataclasses.
    """

    # this is unfortunately needed because the stubs are using __new__ instead of __init__
    if t.TYPE_CHECKING:

        def __new__(
            cls, dataclass_type: t.Type[DataclassType], swapped: bool = False
        ) -> "TBitStruct[DataclassType, DataclassType]":
            ...

    def _create_subcon(
        self, subcon_fields: t.Dict[str, t.Any]
    ) -> Construct[t.Any, t.Any]:
        return cs.BitStruct(**subcon_fields)
