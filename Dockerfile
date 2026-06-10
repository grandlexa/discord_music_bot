# Используем Python 3.14.2-slim, как указано в требованиях
FROM python:3.14.2-slim

# Установка системных зависимостей (FFmpeg необходим для аудио)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование файла зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода приложения
COPY app ./app
COPY .env .
COPY cookies.txt .

# Команда запуска
CMD ["python", "app/main.py"]
