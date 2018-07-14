from setuptools import setup, find_packages
from os import path
from io import open
import re

here = path.abspath(path.dirname(__file__))
REQUIREMENTS = open(path.join(here, "requirements.txt")).readlines()
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

compiled = re.compile("([^=><]*).*")


def parse_req(req):
    return compiled.search(req).group(1).strip()


requires = [_f for _f in REQUIREMENTS if _f]

setup(
    name="channelstream",
    version="0.6.1",
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
