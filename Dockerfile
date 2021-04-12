FROM python:3 as base

ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
COPY . /code/

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "./slack_notify.py"]
