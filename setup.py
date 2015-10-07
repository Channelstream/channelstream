from setuptools import setup, find_packages


setup(name='channelstream',
      version='0.3',
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
      install_requires=[
          'gevent>=1.0',
          'gevent-websocket>=0.9.3',
          'pyramid',
          'pyramid_jinja2',
          'itsdangerous'
      ],
    entry_points = {
        'console_scripts': [
            'channelstream = channelstream.cli:cli_start',
        ],
        })
