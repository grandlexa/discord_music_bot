# План тестирования и тест-кейсы 🧪

## Уровни тестирования
1. Unit tests — изолированное тестирование функций и небольших модулей
2. Integration tests — тестирование взаимодействия между сервисами
3. End-to-end / Manual — ручное тестирование на тестовом сервере Discord

## Инструменты
- pytest
- pytest-asyncio
- unittest.mock / respx / aioresponses (для подмены сетевых вызовов)

## Unit тесты (предложения)

1) `youtube_service.search_and_extract_tracks`
- Цель: убедиться, что при различных типах запросов (ссылка, плейлист, поиск) возвращается корректный список треков.
- Моки: подменить `yt_dlp.YoutubeDL.extract_info` и вернуть заранее подготовленные структуры.
- Проверки: правильное формирование `url`, `title`, `duration`, `requester`.

2) `youtube_service.resolve_track_stream_url`
- Цель: убедиться, что `stream_url` корректно извлекается и сохраняется.
- Моки: `yt_dlp` возвращает объект с `url`, `title`, `duration`, `thumbnail`.
- Проверки: возвращаемая структура не `None` и содержит `stream_url`.

3) `queue_service` (get_queue, add_track, clear_queue, set_current_index, fade task cancel)
- Цель: управление состоянием очереди и отмена задач.
- Проверки: после `add_track` размер очереди увеличился; `clear_queue` сбрасывает индекс; `cancel_fade_tasks` отменяет таски (mock task с флагом cancelled).

4) `media_service.volume_fade`
- Цель: проверка корректной работы логики изменения громкости и поведения на недоступном `voice_client`.
- Моки: объект `voice_client` с `source` и набором полей `volume`, проверяем, что итоговое значение равно целевому.

5) `ui create_embed functions` (create_now_playing_embed, create_queue_embed)
- Цель: проверить структуру `Embed` и корректность полей.
- Проверки: наличие полей, корректный формат времени и прогресс бара.

## Integration тесты (предложения)

- Сценарий: `play` -> `search_and_extract_tracks` (mock) -> `add_track` -> `play_next` (mock voice client) -> проверка что `voice_client.play` вызван с `PCMVolumeTransformer` и начальная громкость задана 0.0.
- Проверки на обработку ошибок: если `resolve_track_stream_url` возвращает `None`, индекс увеличивается и play_next продолжает цикл.

## End-to-end (manual)
- Развернуть контейнер с тестовым токеном в тестовом сервере Discord.
- Проверки:
  - `!play <запрос>` — добавление и начало воспроизведения
  - UI-кнопки: pause/resume/next/prev/seek
  - Проверить авто-отключение при бездействии
  - Проверить поведение на плейлистах и при отсутствии доступа к видео

## Тестовые данные и сценарии
- Простая ссылка на короткое видео
- Плейлист из нескольких видео
- Искусственный ввод тайм-кода для перемотки (например 1:30)
- Сценарий, когда yt-dlp возвращает ошибку (симуляция network error)

## CI
- Workflow: `lint` → `pytest` (unit + integration) → `build docker image` → (опционально) `push to registry`.

---

Если нужно, могу сгенерировать skeleton тестов (`tests/test_youtube_service.py`, `tests/test_queue.py`, etc.) с мокаем `yt_dlp` и `voice_client`.