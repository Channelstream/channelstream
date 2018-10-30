from setuptools import setup, find_packages
from os import path
from io import open


here = path.abspath(path.dirname(__file__))
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


requires = [
    "gevent==1.3.7",
    "ws4py==0.5.1",
    "marshmallow==2.16.0",
    "python-dateutil",
    "pyramid==1.9.2",
    "pyramid_jinja2",
    "pyramid_apispec==0.2.1",
    "itsdangerous==0.24",
    "requests==2.20.0",
    "six",
]


setup(
    name="channelstream",
    version="0.6.9",
    description="Websocket server supporting channels/users communication",
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    author="Marcin Lulek",
    author_email="info@webreactor.eu",
    long_description=long_description,
    license="BSD",
    long_description_content_type="text/markdown",
    zip_safe=True,
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires,
    python_requires=">=2.7",
    setup_requires=["pytest-runner"],
    extras_require={
        "dev": ["coverage", "pytest", "pyramid", "tox", "mock"],
        "lint": ["black"],
    },
    entry_points={"console_scripts": ["channelstream = channelstream.cli:cli_start"]},
)
