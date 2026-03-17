FROM python:3.14-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock README.md ./

RUN poetry config virtualenvs.create false && poetry install --no-root --no-interaction

COPY . .

EXPOSE 8000

CMD [ "poetry", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]