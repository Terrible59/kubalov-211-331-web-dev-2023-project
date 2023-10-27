FROM python:3.9

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

WORKDIR /code/app

CMD ["flask", "--app", "main", "run", "--debug", "-p", "8006", "-h", "0.0.0.0"]