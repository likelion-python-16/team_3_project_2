FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /code/

# Set proper permissions for the database file (already copied with .)
RUN chmod 664 /code/db.sqlite3

ENV SECRET_KEY=dummy-key-for-collectstatic
RUN python manage.py collectstatic --noinput
ENV SECRET_KEY=

EXPOSE 8000

CMD ["gunicorn", "team3.wsgi:application", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info"]

