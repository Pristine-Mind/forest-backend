FROM python:3.12-slim-bookworm as base
LABEL maintainer="Pristine Dev"
ENV PYTHONUNBUFFERED 1
WORKDIR /code
COPY pyproject.toml poetry.lock /code/
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        gdal-bin \
        libproj-dev \
        libgomp1 \
        wait-for-it \
        wkhtmltopdf \
        libcairo2-dev \
        libpango-1.0-0 \
        libpango1.0-dev \
        libpangoft2-1.0-0 \
        libgdk-pixbuf-2.0-0 \
        libffi-dev \
    && pip install --upgrade --no-cache-dir pip poetry --root-user-action=ignore \
    && poetry --version \
    && poetry config virtualenvs.create false \
    && poetry install --no-root \
    && pip uninstall -y poetry virtualenv-clone virtualenv \
    && apt-get remove -y build-essential cmake libproj-dev libpango1.0-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*
COPY . /code/
