FROM python:3.10.5

RUN mkdir usr/app
WORKDIR usr/app

COPY . .

RUN pip3 install -r requirements.txt
RUN pip3 install bcrypt

CMD python3 app.py