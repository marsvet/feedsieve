FROM python:3.10-alpine

WORKDIR /app
EXPOSE 8000

COPY ./pyproject.toml ./poetry.lock ./

RUN set -x; pip install poetry --no-cache-dir && \
    poetry install

COPY . .

CMD ["poetry", "run", "python", "main.py"]
