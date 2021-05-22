# -*- coding: utf-8 -*-

import dataclasses
import enum

import construct as cs
import construct_typed as cst
import pytest
import typing as t

from .declarativeunittest import common, raises, setattrs


def test_tcontainer_const_default() -> None:
    @dataclasses.dataclass
    class ConstDefaultTest(cst.TContainerMixin):
        const_bytes: bytes = cst.sfield(cs.Const(b"BMP"))
        const_int: int = cst.sfield(cs.Const(5, cs.Int8ub))
        default_int: int = cst.sfield(cs.Default(cs.Int8ub, 28))
        default_lambda: bytes = cst.sfield(
            cs.Default(cs.Bytes(cs.this.const_int), lambda ctx: bytes(ctx.const_int))
        )

    a = ConstDefaultTest()
    assert a.const_bytes == b"BMP"
    assert a.const_int == 5
    assert a.default_int == 28
    assert a.default_lambda == None


def test_tcontainer_access() -> None:
    @dataclasses.dataclass
    class TestTContainer(cst.TContainerMixin):
        a: t.Optional[int] = cst.sfield(cs.Const(1, cs.Byte))
        b: int = cst.sfield(cs.Int8ub)

    tcontainer = TestTContainer(b=2)

    # tcontainer
    assert tcontainer.a == 1
    assert tcontainer["a"] == 1
    assert tcontainer.b == 2
    assert tcontainer["b"] == 2

    tcontainer.a = 5
    assert tcontainer.a == 5
    assert tcontainer["a"] == 5
    tcontainer["a"] = 6
    assert tcontainer.a == 6
    assert tcontainer["a"] == 6

    # wrong creation
    assert raises(lambda: TestTContainer(a=0, b=1)) == TypeError


def test_tcontainer_str_repr() -> None:
    @dataclasses.dataclass
    class Image(cst.TContainerMixin):
        signature: t.Optional[bytes] = cst.sfield(cs.Const(b"BMP"))
        width: int = cst.sfield(cs.Int8ub)
        height: int = cst.sfield(cs.Int8ub)

    format = cst.TStruct(Image)
    obj = Image(width=3, height=2)
    assert (
        str(obj)
        == "Image: \n    signature = b'BMP' (total 3)\n    width = 3\n    height = 2"
    )
    obj = format.parse(format.build(obj))
    assert (
        str(obj)
        == "Image: \n    signature = b'BMP' (total 3)\n    width = 3\n    height = 2"
    )


def test_tstruct() -> None:
    @dataclasses.dataclass
    class TestContainer(cst.TContainerMixin):
        a: int = cst.sfield(cs.Int16ub)
        b: int = cst.sfield(cs.Int8ub)

    common(cst.TStruct(TestContainer), b"\x00\x01\x02", TestContainer(a=1, b=2), 3)

    # check __getattr__
    c = cst.TStruct(TestContainer)
    assert c.a.name == "a"
    assert c.b.name == "b"
    assert c.a.subcon is cs.Int16ub
    assert c.b.subcon is cs.Int8ub


def test_tstruct_reverse() -> None:
    @dataclasses.dataclass
    class TestContainer(cst.TContainerMixin):
        a: int = cst.sfield(cs.Int16ub)
        b: int = cst.sfield(cs.Int8ub)

    common(
        cst.TStruct(TestContainer, reverse=True),
        b"\x02\x00\x01",
        TestContainer(a=1, b=2),
        3,
    )
    normal = cst.TStruct(TestContainer)
    reverse = cst.TStruct(TestContainer, reverse=True)
    assert str(normal.parse(b"\x00\x01\x02")) == str(reverse.parse(b"\x02\x00\x01"))


def test_tstruct_nested() -> None:
    @dataclasses.dataclass
    class TestContainer(cst.TContainerMixin):
        @dataclasses.dataclass
        class InnerDataclass(cst.TContainerMixin):
            b: int = cst.sfield(cs.Byte)
            c: bytes = cst.sfield(cs.Bytes(cs.this._.length))

        length: int = cst.sfield(cs.Byte)
        a: InnerDataclass = cst.sfield(cst.TStruct(InnerDataclass))

    common(
        cst.TStruct(TestContainer),
        b"\x02\x01\xF1\xF2",
        TestContainer(length=2, a=TestContainer.InnerDataclass(b=1, c=b"\xF1\xF2")),
    )


def test_tstruct_default_field() -> None:
    @dataclasses.dataclass
    class Image(cst.TContainerMixin):
        width: int = cst.sfield(cs.Int8ub)
        height: int = cst.sfield(cs.Int8ub)
        pixels: t.Optional[bytes] = cst.sfield(
            cs.Default(
                cs.Bytes(cs.this.width * cs.this.height),
                lambda ctx: bytes(ctx.width * ctx.height),
            )
        )

    common(
        cst.TStruct(Image),
        b"\x02\x03\x00\x00\x00\x00\x00\x00",
        setattrs(Image(2, 3), pixels=bytes(6)),
        sample_building=Image(2, 3),
    )


def test_tstruct_const_field() -> None:
    @dataclasses.dataclass
    class TestContainer(cst.TContainerMixin):
        const_field: t.Optional[bytes] = cst.sfield(cs.Const(b"\x00"))

    common(
        cst.TStruct(TestContainer),
        bytes(1),
        setattrs(TestContainer(), const_field=b"\x00"),
        1,
    )

    assert (
        raises(
            cst.TStruct(TestContainer).build,
            setattrs(TestContainer(), const_field=b"\x01"),
        )
        == cs.ConstError
    )


def test_tstruct_array_field() -> None:
    @dataclasses.dataclass
    class TestContainer(cst.TContainerMixin):
        array_field: t.List[int] = cst.sfield(cs.Array(5, cs.Int8ub))

    common(
        cst.TStruct(TestContainer),
        bytes(5),
        TestContainer(array_field=[0, 0, 0, 0, 0]),
        5,
    )


def test_tstruct_anonymus_fields_1() -> None:
    @dataclasses.dataclass
    class TestContainer(cst.TContainerMixin):
        _1: t.Optional[bytes] = cst.sfield(cs.Const(b"\x00"))
        _2: None = cst.sfield(cs.Padding(1))
        _3: None = cst.sfield(cs.Pass)
        _4: None = cst.sfield(cs.Terminated)

    common(
        cst.TStruct(TestContainer),
        bytes(2),
        setattrs(TestContainer(), _1=b"\x00"),
        cs.SizeofError,
    )


def test_tstruct_anonymus_fields_2() -> None:
    @dataclasses.dataclass
    class TestContainer(cst.TContainerMixin):
        _1: int = cst.sfield(cs.Computed(7))
        _2: t.Optional[bytes] = cst.sfield(cs.Const(b"JPEG"))
        _3: None = cst.sfield(cs.Pass)
        _4: None = cst.sfield(cs.Terminated)

    d = cst.TStruct(TestContainer)
    assert d.build(TestContainer()) == d.build(TestContainer())


def test_tstruct_overloaded_method() -> None:
    # Test dot access to some names that are not accessable via dot
    # in the original 'cs.Container'.
    @dataclasses.dataclass
    class TestContainer(cst.TContainerMixin):
        clear: int = cst.sfield(cs.Int8ul)
        copy: int = cst.sfield(cs.Int8ul)
        fromkeys: int = cst.sfield(cs.Int8ul)
        get: int = cst.sfield(cs.Int8ul)
        items: int = cst.sfield(cs.Int8ul)
        keys: int = cst.sfield(cs.Int8ul)
        move_to_end: int = cst.sfield(cs.Int8ul)
        pop: int = cst.sfield(cs.Int8ul)
        popitem: int = cst.sfield(cs.Int8ul)
        search: int = cst.sfield(cs.Int8ul)
        search_all: int = cst.sfield(cs.Int8ul)
        setdefault: int = cst.sfield(cs.Int8ul)
        update: int = cst.sfield(cs.Int8ul)
        values: int = cst.sfield(cs.Int8ul)

    d = cst.TStruct(TestContainer)
    obj = d.parse(
        d.build(
            TestContainer(
                clear=1,
                copy=2,
                fromkeys=3,
                get=4,
                items=5,
                keys=6,
                move_to_end=7,
                pop=8,
                popitem=9,
                search=10,
                search_all=11,
                setdefault=12,
                update=13,
                values=14,
            )
        )
    )
    assert obj.clear == 1
    assert obj.copy == 2
    assert obj.fromkeys == 3
    assert obj.get == 4
    assert obj.items == 5
    assert obj.keys == 6
    assert obj.move_to_end == 7
    assert obj.pop == 8
    assert obj.popitem == 9
    assert obj.search == 10
    assert obj.search_all == 11
    assert obj.setdefault == 12
    assert obj.update == 13
    assert obj.values == 14


def test_tstruct_no_dataclass() -> None:
    class TestContainer(cst.TContainerMixin):
        a: int = cst.sfield(cs.Int16ub)
        b: int = cst.sfield(cs.Int8ub)

    assert raises(lambda: cst.TStruct(TestContainer)) == TypeError


def test_tstruct_no_TContainerMixin() -> None:
    @dataclasses.dataclass
    class TestContainer:
        a: int = cst.sfield(cs.Int16ub)
        b: int = cst.sfield(cs.Int8ub)

    assert raises(lambda: cst.TStruct(TestContainer)) == TypeError


def test_tstruct_wrong_container() -> None:
    @dataclasses.dataclass
    class TestContainer1(cst.TContainerMixin):
        a: int = cst.sfield(cs.Int16ub)
        b: int = cst.sfield(cs.Int8ub)

    @dataclasses.dataclass
    class TestContainer2(cst.TContainerMixin):
        a: int = cst.sfield(cs.Int16ub)
        b: int = cst.sfield(cs.Int8ub)

    assert (
        raises(cst.TStruct(TestContainer1).build, TestContainer2(a=1, b=2)) == TypeError
    )


def test_tstruct_doc() -> None:
    @dataclasses.dataclass
    class TestContainer(cst.TContainerMixin):
        a: int = cst.sfield(cs.Int16ub, "This is the documentation of a")
        b: int = cst.sfield(
            cs.Int8ub, doc="This is the documentation of b\nwhich is multiline"
        )
        c: int = cst.sfield(
            cs.Int8ub,
            """
            This is the documentation of c
            which is also multiline
            """,
        )

    format = cst.TStruct(TestContainer)
    common(format, b"\x00\x01\x02\x03", TestContainer(a=1, b=2, c=3), 4)

    assert format.subcon.a.docs == "This is the documentation of a"
    assert format.subcon.b.docs == "This is the documentation of b\nwhich is multiline"
    assert (
        format.subcon.c.docs
        == "This is the documentation of c\nwhich is also multiline"
    )


# @pytest.mark.xfail(reason="not implemented yet")
def test_tbitstruct() -> None:
    @dataclasses.dataclass
    class TestContainer(cst.TContainerMixin):
        a: int = cst.sfield(cs.BitsInteger(7))
        b: int = cst.sfield(cs.Bit)
        c: int = cst.sfield(cs.BitsInteger(8))

    common(
        cst.TBitStruct(TestContainer),
        b"\xFD\x12",
        TestContainer(a=0x7E, b=1, c=0x12),
        2,
    )

    # check __getattr__
    c = cst.TStruct(TestContainer)
    assert c.a.name == "a"
    assert c.b.name == "b"
    assert c.c.name == "c"
    assert isinstance(c.a.subcon, cs.BitsInteger)
    assert c.b.subcon is cs.Bit
    assert isinstance(c.c.subcon, cs.BitsInteger)


def test_tenum() -> None:
    class TestEnum(cst.EnumBase):
        one = 1
        two = 2
        four = 4
        eight = 8

    d = cst.TEnum(cs.Byte, TestEnum)

    common(d, b"\x01", TestEnum.one, 1)
    common(d, b"\xff", TestEnum(255), 1)
    assert d.parse(b"\x01") == TestEnum.one
    assert d.parse(b"\x01") == 1
    assert int(d.parse(b"\x01")) == 1
    assert d.parse(b"\xff") == TestEnum(255)
    assert d.parse(b"\xff") == 255
    assert int(d.parse(b"\xff")) == 255
    assert raises(d.build, 8) == TypeError


def test_tenum_no_enumbase() -> None:
    class E(enum.Enum):
        a = 1
        b = 2

    assert raises(lambda: cst.TEnum(cs.Byte, E)) == TypeError


def test_tstruct_wrong_enumbase() -> None:
    class E1(cst.EnumBase):
        a = 1
        b = 2

    class E2(cst.EnumBase):
        a = 1
        b = 2

    assert raises(cst.TEnum(cs.Byte, E1).build, E2.a) == TypeError


def test_tenum_in_tstruct() -> None:
    class TestEnum(cst.EnumBase):
        a = 1
        b = 2

    @dataclasses.dataclass
    class TestContainer(cst.TContainerMixin):
        a: TestEnum = cst.sfield(cst.TEnum(cs.Int8ub, TestEnum))
        b: int = cst.sfield(cs.Int8ub)

    common(
        cst.TStruct(TestContainer),
        b"\x01\x02",
        TestContainer(a=TestEnum.a, b=2),
        2,
    )

    assert (
        raises(cst.TEnum(cs.Byte, TestEnum).build, TestContainer(a=1, b=2)) == TypeError  # type: ignore
    )


def test_tenum_flags() -> None:
    class TestEnum(cst.FlagsEnumBase):
        one = 1
        two = 2
        four = 4
        eight = 8

    d = cst.TFlagsEnum(cs.Byte, TestEnum)
    common(d, b"\x03", TestEnum.one | TestEnum.two, 1)
    assert d.build(TestEnum(0)) == b"\x00"
    assert d.build(TestEnum.one | TestEnum.two) == b"\x03"
    assert d.build(TestEnum(8)) == b"\x08"
    assert d.build(TestEnum(1 | 2)) == b"\x03"
    assert d.build(TestEnum(255)) == b"\xff"
    assert d.build(TestEnum.eight) == b"\x08"
    assert raises(d.build, 2) == TypeError
