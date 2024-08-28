FROM python:3-alpine

RUN pip install --no-cache-dir requests

ADD  alert-awx-integration.py /

CMD [ "python", "./alert-awx-integration.py" ]

