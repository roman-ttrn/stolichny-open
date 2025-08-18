#!/bin/sh
set -e

echo "⏳ Ожидание запуска Postgres..."
while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  sleep 1
done
echo "✅ Postgres доступен!"

echo "Применяем миграции..."
python manage.py migrate --noinput

echo "Собираем статические файлы..."
python manage.py collectstatic --noinput

echo "Запускаем WSGI сервер..."
gunicorn stolichny.wsgi:application --bind 0.0.0.0:8000 --workers 3

