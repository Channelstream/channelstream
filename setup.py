from setuptools import setup, find_packages
from os import path
from io import open

here = path.abspath(path.dirname(__file__))
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

requires = [
    "gevent>=1.3.7",
    "ws4py>=0.5.1",
    "marshmallow==2.18.0,<3.0.0",
    "python-dateutil>=2.7.5",
    "pyramid>=1.9.2",
    "pyramid_jinja2>=2.7",
    "pyramid_apispec==0.3.3",
    "itsdangerous==1.1.0",
    "requests>=2.20.0",
]

setup(
    name="channelstream",
    version="0.7.0rc1",
    description="Websocket server supporting channels/users communication",
    keywords="websockets async communication chat notification django flask pyramid",
    url="https://github.com/Channelstream/channelstream",
    classifiers=[
        "Framework :: Django",
        "Framework :: Flask",
        "Framework :: Pyramid",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Communications :: Chat",
        "Topic :: Communications :: Conferencing",
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
    python_requires=">=3.6",
    setup_requires=["pytest-runner"],
    extras_require={
        "dev": ["coverage", "pytest", "pyramid", "tox", "mock", "webtest"],
        "lint": ["black"],
    },
    entry_points={
        "console_scripts": [
            "channelstream = channelstream.cli.start:main",
            "channelstream_utils = channelstream.cli.utils:main",
        ]
    },
)
