FROM python:3 as base

ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
COPY slack_notify.py /code/
COPY slack_release_template.json /code/

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "slack_notify.py"]
