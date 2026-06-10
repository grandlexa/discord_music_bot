# Детализированные задачи для ИИ-агента (коммиты и проверки) 🤖

Формат: для каждого шага указано имя ветки (пример), файлы которые будут изменены/созданы и критерии приёмки + минимальные тесты.

---

## 0. Стартовая ветка
- Ветка: `init/project-structure`
- Изменения: создать структуру `app/`, `tests/`, `spec/`, `pyproject.toml` или `requirements.txt`, `.gitignore`, `README.md`.
- Тесты: `pytest` запускается без тестов.
- PR title: "Project skeleton and basic configuration"

---

## 1. Конфигурация
- Ветка: `feature/config`
- Файлы: `app/core/config.py`, `.env.example`.
- Содержимое: конфиги логирования, `BOT_TOKEN` (env), `YDL_OPTIONS`, `FFMPEG_OPTIONS`, `BOT_PREFIX`.
- Тесты: unit test проверяющий чтение env-переменной и default values.
- PR title: "Add configuration module and env example"

---

## 2. Сервисы YouTube и Media
- Ветка: `feature/services-youtube-media`
- Файлы:
  - `app/services/youtube_service.py` (search_and_extract_tracks, resolve_track_stream_url, create_track_info)
  - `app/services/media_service.py` (parse_time, volume_fade, fade_out_task_func, get_current_volume)
- Тесты:
  - `tests/test_youtube_service.py` — mock `yt_dlp.YoutubeDL.extract_info`, проверить результаты для ссылок/поиска/плейлистов.
  - `tests/test_media_service.py` — mock `voice_client` и проверить `volume_fade` и `fade_out_task_func` поведение.
- PR title: "Implement youtube & media services with tests"

---

## 3. Очередь (queue_service)
- Ветка: `feature/queue`
- Файл: `app/services/queue_service.py`
- Содержимое: интерфейсы для get_queue, add_track, clear_queue, set_current_index, set_fade_tasks, cancel_fade_tasks, set_disconnect_timer, cancel_disconnect_timer
- Тесты: `tests/test_queue_service.py` — проверка состояния очереди и отмены задач.
- PR title: "Implement queue service and tests"

---

## 4. UI и embed
- Ветка: `feature/ui`
- Файл: `app/ui/player_ui.py`
- Содержимое: `MusicPlayerView`, `SeekModal`, `send_player_message`, `create_now_playing_embed`, `create_queue_embed`.
- Тесты: `tests/test_ui.py` — проверка embed-полей и содержимого.
- PR title: "Add player UI and embed builders"

---

## 5. Команды и логика воспроизведения
- Ветка: `feature/commands`
- Файлы:
  - `app/commands/music_commands.py` — команды и `play_next` интегрированно использующий сервисы
  - (если нужно) `app/main.py` — точка запуска для локальной разработки
- Тесты:
  - `tests/test_commands.py` — mock `ctx`, mock `voice_client`, тест на `!play` flow (search -> add -> play_next` вызывает voice_client.play)
- PR title: "Implement music commands and playback flow"

---

## 6. Core bot runner и регистрация команд
- Ветка: `feature/core-bot`
- Файлы: `app/core/bot.py`, `app/__main__.py`
- Содержимое: регистрация команд, обработчики ошибок, `run_bot()` и `setup_commands()`.
- Тесты: `tests/test_core.py` — проверка регистрации команд (mock bot.add_command calls) и обработчика ошибок.
- PR title: "Add core bot runner and error handling"

---

## 7. Docker & CI
- Ветка: `feature/infra-ci`
- Файлы:
  - `Dockerfile` (системный ffmpeg, copy requirements and app)
  - `docker-compose.yml` (env variables, restart)
  - `.github/workflows/ci.yml` (lint, tests, build)
- Тесты: CI должен запускать тесты и собирать образ без ошибок.
- PR title: "Add Dockerfile and CI pipeline"

---

## 8. Quality & polish
- Ветка: `chore/quality`
- Шаги:
  - добавление `black`, `mypy`, `flake8` конфигураций и pre-commit
  - добавить документацию и README usage
- Тесты: `pytest` green, linter green
- PR title: "Add linting, formatting and docs"

---

## Проверки и acceptance criteria (общие)
- Все измененные файлы покрыты unit тестами минимум на happy path.
- Для сетевых вызовов используются моки.
- Локальная сборка и `docker compose up --build` запускается и бот логт "бот запущен" (при наличии валидного токена).

---

Если нужно, могу сгенерировать конкретные шаблоны PR описаний, тестовые фикстуры и примеры моков для `yt_dlp` и `voice_client`.