from setuptools import setup, find_packages
from os import path
from io import open
import re

from channelstream import __version__


here = path.abspath(path.dirname(__file__))
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

compiled = re.compile("([^=><]*).*")

requires = [
    "gevent>=1.1",
    "ws4py>=0.3.5",
    "marshmallow==2.15.0",
    "dateutils",
    "pyramid>=1.8",
    "pyramid_jinja2",
    "pyramid_apispec>=0.2",
    "itsdangerous",
    "requests",
    "six",
]

version = "{}.{}.{}".format(
    __version__["major"], __version__["minor"], __version__["patch"]
)

setup(
    name="channelstream",
    version=version,
    description="Websocket server supporting channels/users communication",
    classifiers=["Intended Audience :: Developers"],
    author="Marcin Lulek",
    author_email="info@webreactor.eu",
    long_description=long_description,
    license="BSD",
    long_description_content_type="text/markdown",
    zip_safe=True,
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires,
    setup_requires=["pytest-runner"],
    extras_require={
        "dev": ["coverage", "pytest", "pyramid", "tox", "mock"],
        "lint": ["black"],
    },
    entry_points={"console_scripts": ["channelstream = channelstream.cli:cli_start"]},
)
