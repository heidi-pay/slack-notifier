FROM python:3 as base

ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
COPY slack_notify.py /code/
COPY templates /code/

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "/code/slack_notify.py"]
