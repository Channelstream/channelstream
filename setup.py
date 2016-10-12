import os
import re
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
REQUIREMENTS = open(os.path.join(here, 'requirements.txt')).readlines()

compiled = re.compile('([^=><]*).*')


def parse_req(req):
    return compiled.search(req).group(1).strip()


requires = [_f for _f in map(parse_req, REQUIREMENTS) if _f]

setup(name='channelstream',
      version='0.6.0',
      description='Websocket server supporting channels/users communication',
      classifiers=[
          'Intended Audience :: Developers'
      ],
      author='Marcin Lulek',
      author_email='info@webreactor.eu',
      license='BSD',
      zip_safe=True,
      packages=find_packages(),
      include_package_data=True,
      install_requires=requires,
      entry_points={
          'console_scripts': [
              'channelstream = channelstream.cli:cli_start',
          ],
      })
