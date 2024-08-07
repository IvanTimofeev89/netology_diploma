###########
# BUILDER #
###########

# pull official base image
FROM python:3.12-slim as builder

# set work directory
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc

# install python dependencies
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

#########
# FINAL #
#########

# pull official base image
FROM python:3.12-slim

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN addgroup --system app && adduser --system --group app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
WORKDIR $APP_HOME

# install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends netcat-openbsd wait-for-it
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*

# copy project
COPY . $APP_HOME

# copy .sh files
COPY ./run.sh .
RUN sed -i 's/\r$//g'  $APP_HOME/run.sh
RUN chmod +x  $APP_HOME/run.sh

COPY ./run_celery.sh .
RUN sed -i 's/\r$//g'  $APP_HOME/run_celery.sh
RUN chmod +x  $APP_HOME/run_celery.sh

# chown all the files to the app user
RUN chown -R app:app $APP_HOME

# change to the app user
USER app

# run run.sh
ENTRYPOINT ["bash", "run.sh"]
