FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

COPY pyproject.toml README.md /app/
COPY src/ /app/src/

RUN pip install --no-cache-dir .

CMD ["python", "-m", "coc_elt.main"]
