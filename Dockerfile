FROM python:3.9-slim-buster
RUN mkdir /code
WORKDIR /code
RUN pip install pipenv
COPY . /code/
RUN pipenv install --system
ENV ENV_PATH=env.test
RUN python manage.py collectstatic --no-input
EXPOSE 8080
#ENTRYPOINT ["gunicorn", "sklandymas.wsgi", "--bind", "0.0.0.0:8080", "--log-file", "-"]
