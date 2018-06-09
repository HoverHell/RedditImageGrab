FROM python:2.7.15-alpine3.7
COPY . /app
RUN pip install /app[redditdl.py] && redditdl.py -h
WORKDIR /data
ENTRYPOINT [ "redditdl.py" ]
