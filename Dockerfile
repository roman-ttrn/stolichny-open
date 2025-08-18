#############################
# ЭТАП 1: Сборка проекта
#############################
FROM python:3.11.8-slim AS builder

RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Dev-зависимости для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

# Непривилегированный пользователь
RUN adduser --disabled-password --gecos "" --uid 1000 appuser

# Рабочая директория
WORKDIR /app

# Виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Зависимости
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем entrypoint.sh
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

#############################
# ЭТАП 2: Финальный контейнер
#############################
FROM python:3.11.8-slim

# Runtime-зависимости + netcat
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    zlib1g \
    libwebp7 \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Пользователь
RUN adduser --disabled-password --gecos "" --uid 1000 appuser

# Переменные окружения
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONHASHSEED=random

# Копируем окружение и entrypoint
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /usr/local/bin/entrypoint.sh /usr/local/bin/entrypoint.sh

# Рабочая директория
WORKDIR /app
RUN chown -R appuser:appuser /app

# создаём каталоги и даём права
RUN mkdir -p /vol/web/static /vol/web/media \
    && chown -R appuser:appuser /app /vol

# Запуск от непривилегированного пользователя
USER appuser

STOPSIGNAL SIGTERM
ENTRYPOINT ["sh", "/usr/local/bin/entrypoint.sh"]