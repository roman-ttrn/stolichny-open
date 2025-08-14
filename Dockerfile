#############################
# ЭТАП 1: Сборка проекта
#############################

FROM python:3.11.8-slim AS builder

# Обновляем и устанавливаем dev-зависимости для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаём непривилегированного пользователя (UID фиксируем)
RUN adduser --disabled-password --gecos "" --uid 1001 appuser

# Рабочая директория
WORKDIR /app

# Создаём виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем только зависимости для кэширования слоёв
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Делаем скрипт запуска исполняемым
RUN chmod +x entrypoint.sh

#############################
# ЭТАП 2: Финальный контейнер
#############################

FROM python:3.11.8-slim

# Обновляем и устанавливаем только runtime-зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    zlib1g \
    libwebp7 \
    && rm -rf /var/lib/apt/lists/*

# Создаём непривилегированного пользователя
RUN adduser --disabled-password --gecos "" --uid 1001 appuser

# Устанавливаем переменные окружения
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONHASHSEED=random

# Копируем окружение и проект из builder
COPY --from=builder /opt/venv /opt/venv

# Назначаем рабочую директорию
WORKDIR /app

# Меняем владельца файлов на непривилегированного пользователя
RUN chown -R appuser:appuser /app

# Переключаемся на непривилегированного пользователя
USER appuser

# Запрет на интерактивный режим
STOPSIGNAL SIGTERM

# Объявляем точку входа
ENTRYPOINT ["sh", "entrypoint.sh"]
