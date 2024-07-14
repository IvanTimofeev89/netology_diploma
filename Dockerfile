
FROM python:3.12-slim

ENV \
	PIP_NO_CACHE_DIR=off \
	PIP_DISABLE_PIP_VERSION_CHECK=on \
	PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	VIRTUAL_ENV=/pybay-venv

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*


WORKDIR /app
COPY . .

COPY ./run.sh /
COPY ./requirements.txt /
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

RUN chmod +x /run.sh

ENTRYPOINT ["bash", "run.sh"]
