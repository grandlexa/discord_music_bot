# Требования и окружение ✅

## Системные требования
- Операционная система: Linux (для контейнера) / Windows / macOS (локальная разработка)
- Python 3.12
- FFmpeg (системный пакет) — нужен для `discord.FFmpegPCMAudio` (устанавливается в Dockerfile)

## Переменные окружения
- `DISCORD_BOT_TOKEN` — токен Discord-бота (обязательная переменная)

## Python зависимости (из `app/requirements.txt`)
- `discord.py==2.5.2` — библиотека Discord API
- `yt-dlp==2025.7.21` — загрузка/разбор YouTube
- `PyNaCl==1.5.0` — библиотека для голосового функционала (нативные зависимости)
- `asyncio==3.4.3` — тут указана, но это стандартная библиотека Python (необязательно в requirements)

Рекомендации:
- В `requirements.txt` не указывать `asyncio` (он встроен); добавить `pytest`, `pytest-asyncio`, `mypy`, `black` для разработки и тестирования.

## Docker
- Базовый образ: `python:3.12-slim`.
- Системные пакеты: `ffmpeg`.
- CMD в Dockerfile: `python main.py` (поэтому контейнер запускает `app/main.py`, а не `python -m app`).

## Дополнительные инструменты для разработки
- `pytest` + `pytest-asyncio` — тестирование async функций
- Flake8 / MyPy — статический анализ
- `pre-commit` — автоматические хуки

## Замечания по безопасности
- Никогда не храните `DISCORD_BOT_TOKEN` в репозитории.
- Рекомендую добавить проверку/логирование неудачных попыток подключения в Docker/CI.

---

Готов предоставить пример `docker-compose.override.yml` и CI pipeline для GitHub Actions (с шагами: check, lint, test, build Docker image, push) по запросу.