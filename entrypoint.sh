#!/bin/sh

set -e  # Прекращаем выполнение при ошибках

echo "Применяем миграции..."
python manage.py migrate --noinput

echo "Собираем статические файлы..."
python manage.py collectstatic --noinput

echo "Запускаем WSGI сервер..."
# Запуск gunicorn (замени на нужный тебе командный запуск)
gunicorn stolichny.wsgi:application --bind 0.0.0.0:8000 --workers 3

