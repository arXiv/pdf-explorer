# syntax=docker/dockerfile:1

FROM python:3.10.5-buster

WORKDIR /arxiv

COPY requirements.txt requirements.txt
RUN /usr/local/bin/python -m pip install --upgrade pip

RUN apt-get update && apt-get -y install cmake libpoppler-cpp-dev poppler-utils
# RUN python3 -m pip install --pre --upgrade apturl==0.5.2
# RUN python -m pip install --upgrade pip
# RUN cat requirements.txt | xargs -n 1 pip install
RUN pip install flask
RUN pip install PyPDF2
RUN pip install numpy
RUN pip install pillow
RUN pip install pdf2image
RUN pip install python-poppler
RUN pip install gunicorn
RUN mkdir static

COPY ./templates ./templates
COPY ImageParser.py .
COPY main.py .
COPY pdf_gui.py .
COPY treeview.py .
COPY entry_point.py .

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "entry_point:app"]