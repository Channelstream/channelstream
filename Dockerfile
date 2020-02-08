# Use an official Python runtime as a parent image
FROM python:3.7.6-slim-stretch

# Set the working directory to /channelstream
WORKDIR /channelstream

# create channelstream user
RUN useradd --create-home channelstream

RUN chown channelstream /channelstream

# Copy the current directory contents into the container at /channelstream
COPY requirements.txt /tmp/requirements.txt

# change to non-root user
USER channelstream

RUN python -m venv env
# Install any needed packages specified in requirements.txt
RUN env/bin/pip install  --disable-pip-version-check --trusted-host pypi.python.org -r /tmp/requirements.txt --no-cache-dir
# make channelstream scripts visible
ENV PATH $PATH:env/bin
# Copy the current directory contents into the container at /channelstream
COPY . /channelstream
RUN mkdir /channelstream/config
# install the app
RUN env/bin/pip install  --disable-pip-version-check --trusted-host pypi.python.org -e .

# Make port 8000 available to the world outside this container
EXPOSE 8000
VOLUME /channelstream/config
ENTRYPOINT ["/channelstream/docker-entrypoint.sh"]
# Run channelstream when the container launches
CMD ["channelstream", "-i", "/channelstream/config/channelstream_config.ini"]
