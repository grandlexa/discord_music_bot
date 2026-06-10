# Design Document

## Overview
Технический дизайн музыкального бота для Discord, построенного на асинхронной архитектуре с использованием `discord.py` и `yt-dlp`. Бот спроектирован для потоковой передачи аудио без предварительной загрузки файлов на диск, что минимизирует использование дискового пространства.

## Architecture

### System Architecture
Бот состоит из нескольких функциональных слоев:
1. **Core Layer**: Инициализация бота, конфигурация и обработка событий Discord.
2. **Service Layer**: Логика взаимодействия с внешними API (YouTube) и управление очередями.
3. **UI Layer**: Определение интерактивных компонентов (кнопок, модальных окон).
4. **Media Layer**: Обработка аудиопотока через FFmpeg.

### Component Design
1. **YoutubeService** (`app/services/youtube_service.py`)
   - Цель: Поиск и извлечение метаданных видео.
   - Ответственность: Работа с `yt-dlp`, fuzzy matching заголовков, извлечение прямых ссылок на потоки.
   
2. **QueueService** (`app/services/queue_service.py`)
   - Цель: Управление состоянием воспроизведения для каждого сервера.
   - Ответственность: Хранение списков треков, индексов, задач таймеров и эффектов затухания.

3. **MusicPlayerView** (`app/ui/player_ui.py`)
   - Цель: Интерактивный интерфейс.
   - Ответственность: Обработка нажатий кнопок и обновление сообщений плеера.

## Data Design

### Data Models
```
TrackInfo (dict)
- url: str (ссылка на YouTube)
- title: str (название трека)
- duration: int (длительность в секундах)
- requester: str (упоминание пользователя)
- thumbnail: str (ссылка на обложку)
- stream_url: str (прямая ссылка на аудиопоток)

QueueState (dict)
- queue: list[TrackInfo]
- current_index: int
- is_seeking: bool
- seek_time: int
- current_message: discord.Message
- fade_in_task: asyncio.Task
- fade_out_task: asyncio.Task
```

### Data Flow
1. Пользователь вводит команду `!play`.
2. `YoutubeService` извлекает метаданные (без `stream_url` для плейлистов для скорости).
3. Треки добавляются в `QueueService`.
4. `play_next` запрашивает `stream_url` только перед началом проигрывания.
5. FFmpeg подключается к `stream_url` и передает данные в `discord.VoiceClient`.

## User Interface Design

### Views/Pages
1. **MusicPlayerView**
   - Компоненты: Кнопки ⏮️, ⏯️, ⏹️, ⏭️, ⏩ (Seek), ℹ️, 📜, 🔀.
   - Действия: Управление воспроизведением и просмотр информации.

2. **SeekModal**
   - Компоненты: Текстовое поле ввода времени.
   - Действия: Принимает формат `мм:сс` или секунды.

## Technical Decisions

### Technology Stack
- **discord.py**: Основной фреймворк для взаимодействия с Discord API.
- **yt-dlp**: Самый актуальный форк youtube-dl для обхода блокировок.
- **FFmpeg**: Обработка и декодирование аудио на лету.
- **Docker**: Изоляция зависимостей (особенно FFmpeg).

### Design Patterns
- **Singleton-like Queues**: Глобальный словарь `queues` для хранения состояния по `guild_id`.
- **Observer (Events)**: Использование событий `on_ready`, `on_command_error`.
- **Command Pattern**: Разделение команд на отдельные модули.

## Performance Considerations
- **Non-blocking I/O**: Использование `run_in_executor` для вызовов `yt-dlp.extract_info`, которые блокируют событийный цикл.
- **Flat Extraction**: При добавлении плейлистов используется `extract_flat`, чтобы не ждать обработки всех видео сразу.

## Testing Strategy
- **Unit Testing**: Тестирование парсера времени и логики очереди.
- **Integration Testing**: Проверка взаимодействия с Discord API (требует тестового токена).
