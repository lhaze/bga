#!/usr/bin/env python3
from os import path
from setuptools import (
    setup,
    find_packages,
)

PROJECT_NAME = "bga"
VERSION = "0.1.0"
PROJECT_DIR = path.dirname(__file__)


if __name__ == "__main__":
    setup(
        name=PROJECT_NAME,
        version=VERSION,
        url=f"https://github.com/lhaze/{PROJECT_NAME}",
        author="lhaze",
        author_email="lhaze@lhaze.name",
        platforms="any",
        install_requires=[
            "dataclasses; python_version < '3.7'",
        ],
        tests_require=["pytest"],
        packages=find_packages(),
    )
