# syntax=docker/dockerfile:1

FROM python:3.10.5-buster

WORKDIR /arxiv

RUN /usr/local/bin/python -m pip install --upgrade pip

RUN pip install flask
RUN pip install PyPDF2
RUN pip install gunicorn

COPY entry_point.py .
COPY main.py .
COPY checks.py .

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "entry_point:app"]