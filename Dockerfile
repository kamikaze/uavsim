
FROM python:3.6-slim-stretch

# The price/volume feed is the default one
ENV PYTHONPATH=/usr/local/bin/uavsim

WORKDIR /usr/local/bin/uavsim

COPY requirements.txt /tmp/

COPY ./ /usr/local/bin/uavsim

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install gcc glib2.0 libgl1-mesa-glx -y \
    && apt-get autoremove \
    && apt-get clean

RUN export APP_HOME=/usr/local/bin/uavsim && \
    mkdir -p $APP_HOME && \
    python3 -m venv $APP_HOME/py3env && \
    . $APP_HOME/py3env/bin/activate && \
    /usr/local/bin/uavsim/py3env/bin/python3 -m pip install --upgrade -r /tmp/requirements.txt


EXPOSE 8091

# The approach is that the entrypoint wrapper handless all docker related stuff
# and setups the runtime env for what ever is the CMD
#ENTRYPOINT ["bash", "/tmp/docker_wrapper.sh"]
CMD ["/usr/local/bin/uavsim/py3env/bin/python3", "map.py"]
