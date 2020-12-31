#!/usr/bin/env python
from setuptools import setup

setup(
    name="construct-typing",
    version="0.0.1",
    packages=["construct-stubs", "construct_typed"],
    package_data={
        "construct-stubs": ["*.pyi", "lib/*.pyi"],
        "construct_typed": ["py.typed"],
    },
    include_package_data=True,
    license="MIT",
    description="Extension for the python package 'construct' that adds typing features",
    long_description=open("README.md").read(),
    platforms=["Windows"],
    url="http://construct.readthedocs.org",
    author="Tim Riddermann",
    python_requires=">=3.6",
    install_requires=["construct==2.10.56"],
    keywords=[
        "construct",
        "kaitai",
        "declarative",
        "data structure",
        "struct",
        "binary",
        "symmetric",
        "parser",
        "builder",
        "parsing",
        "building",
        "pack",
        "unpack",
        "packer",
        "unpacker",
        "bitstring",
        "bytestring",
        "annotation",
        "type hint",
        "typing",
        "typed",
        "bitstruct",
        "PEP 561"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Code Generators",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Typing :: Typed"
    ],
)
