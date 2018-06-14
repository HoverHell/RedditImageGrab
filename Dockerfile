FROM python:2.7.15-alpine3.7
RUN pip install bs4
COPY . /app
RUN pip install /app
RUN redditdl.py -h
WORKDIR /data
ENTRYPOINT [ "redditdl.py" ]
