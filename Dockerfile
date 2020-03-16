# Use an official Python runtime as a parent image
FROM python:3.7.6-slim-stretch
RUN apt-get update && apt-get install -y \
    gosu curl \
 && rm -rf /var/lib/apt/lists/*

# Set the working directory to /opt/application
WORKDIR /opt/application

# create application user
RUN useradd --create-home application

RUN chown application /opt/application

# Copy the current directory contents into the container at /opt/application
COPY requirements.txt /tmp/requirements.txt

# change to non-root user
USER application

RUN python -m venv /home/application/env
# make channelstream scripts visible
ENV PATH /home/application/env/bin:$PATH
# Install any needed packages specified in requirements.txt
RUN pip install --disable-pip-version-check --trusted-host pypi.python.org -r /tmp/requirements.txt --no-cache-dir
# Copy the current directory contents into the container at /application
COPY --chown=application:application . /opt/application/src
RUN mkdir /opt/application/rundir
# install the app
RUN pip install --disable-pip-version-check --trusted-host pypi.python.org -e /opt/application/src

# Make port 8000 available to the world outside this container
EXPOSE 8000
VOLUME /application/rundir
ENV CHANNELSTREAM_HOST 0.0.0.0
ENV CHANNELSTREAM_PORT 8000
HEALTHCHECK --interval=1m --timeout=3s \
  CMD curl -s -o /dev/null -w "%{http_code}" http://$CHANNELSTREAM_HOST:$CHANNELSTREAM_PORT/admin/sign_in || exit 1

# change back to root user so we can later manipulate UID/GID
USER root

ENTRYPOINT ["/opt/application/src/docker-entrypoint.sh"]
# Run channelstream when the container launches
CMD ["channelstream", "-i", "/opt/application/rundir/config.ini"]
