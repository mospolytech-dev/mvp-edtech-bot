# EdTech Bot — MVP: Доска задач

> **Область:** только MVP. Отложенные функции — в разделе [Будущие задачи](#будущие-задачи-не-mvp).
> **Стек:** Python 3.12+ · Aiogram 3 · PostgreSQL · SQLAlchemy Async · Alembic · python-dotenv

---

## Распределение задач по команде

| Направление | Участник |
|---|---|
| Backend / База данных | — |
| Bot Core / Aiogram | — |
| Роли и авторизация | — |
| Модуль расписания | — |
| Модуль посещаемости | — |
| Модуль оценок | — |
| Документация / Тестирование | — |

---

## MVP Фаза 1 — Настройка проекта

- [ + ] Создать структуру директорий проекта:
  ```
  app/
    handlers/
    keyboards/
    states/
    services/
    utils/
    database/
  ```
- [ + ] Создать `bot.py` — точка входа с `asyncio.run(main())`
- [ + ] Реализовать корутину `main()`: инициализация диспетчера, регистрация роутеров, запуск поллинга
- [ + ] Настроить чтение `BOT_TOKEN` из окружения через `python-dotenv`
- [ + ] Создать `.env.example` со всеми необходимыми переменными (`BOT_TOKEN`, `DATABASE_URL`, `LOG_LEVEL`)
- [ + ] Создать локальный `.env` (не коммитить в репозиторий)
- [ + ] Создать `requirements.txt` с зафиксированными версиями:
  - `aiogram==3.x.x`
  - `sqlalchemy[asyncio]`
  - `alembic`
  - `asyncpg`
  - `python-dotenv`
- [ + ] Создать `config.py` — датакласс или Pydantic-модель `Settings`, загружаемая из `.env`
- [ ] Настроить логирование в `utils/logger.py` с уровнем из конфига, форматом с временной меткой
- [ + ] Создать `.gitignore` (Python, `.env`, `__pycache__`, `*.pyc`, `alembic/versions/`)
- [ + ] Создать `README.md` с описанием проекта, инструкцией по установке и запуску
- [ ] Создать пустые `__init__.py` в каждой директории-пакете
- [ ] Создать `handlers/__init__.py` — импортирует и экспортирует все роутеры
- [ ] Создать файлы-заглушки: `keyboards/main.py`, `states/registration.py`, `utils/helpers.py`

---

## MVP Фаза 2 — Настройка базы данных

- [ ] Создать `database/engine.py`:
  - Асинхронный движок через `create_async_engine(DATABASE_URL, echo=False)`
  - `AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)`
- [ ] Создать `database/base.py`:
  - Подкласс `DeclarativeBase` (`class Base(DeclarativeBase): pass`)
- [ ] Создать `database/session.py`:
  - Асинхронный генератор `get_session()` для dependency injection
- [ ] Выполнить `alembic init alembic` в корне проекта
- [ ] Настроить `alembic/env.py`:
  - Импортировать `Base` и все модели для работы автогенерации
  - Установить `target_metadata = Base.metadata`
  - Настроить асинхронное использование движка через `run_async_main`
  - Читать `DATABASE_URL` из конфига
- [ ] Обновить `alembic.ini` — указать `script_location` и заглушку для `sqlalchemy.url`
- [ ] Написать `database/validation.py` — корутина выполняет `SELECT 1` и логирует результат
- [ ] Вызвать валидацию БД в хуке `on_startup` перед стартом поллинга
- [ ] Создать первую пустую миграцию: `alembic revision --autogenerate -m "init"`
- [ ] Применить `alembic upgrade head` и убедиться, что миграция проходит без ошибок

---

## MVP Фаза 3 — Ядро бота

- [ ] Создать `handlers/common.py` — базовый роутер с командами `/start` и `/help`
- [ ] Зарегистрировать все роутеры в `main()` через `dp.include_router(...)`
- [ ] Создать `dispatcher.py` — фабричная функция `build_dispatcher() -> Dispatcher`
- [ ] Настроить хранилище состояний FSM: `MemoryStorage` для MVP
- [ ] Создать `keyboards/main_menu.py`:
  - `InlineKeyboardMarkup` главное меню для роли студента
  - `InlineKeyboardMarkup` главное меню для роли преподавателя
- [ ] Реализовать callback-роутер в `handlers/navigation.py` для кнопок главного меню
- [ ] Добавить хук `on_startup`: логировать имя бота, выполнять валидацию БД
- [ ] Добавить хук `on_shutdown`: логировать завершение, закрывать движок БД
- [ ] Настроить `BotCommand` при старте — зарегистрировать `/start`, `/help`, `/menu` через BotFather
- [ ] Проверить: поллинг запускается без ошибок, `/start` возвращает ответ

---

## MVP Фаза 4 — Пользователи и роли


- [ ] Создать `database/models/user.py`:
  - Модель `User`: `id`, `telegram_id` (уникальный), `username`, `full_name`, `role`, `created_at`
- [ ] Создать `database/models/role.py`:
  - `RoleEnum(str, Enum)` со значениями: `student`, `teacher`, `admin`
  - Добавить колонку `role` в `User` с типом `Enum(RoleEnum)`
- [ ] Создать `services/user_service.py`:
  - `get_or_create_user(telegram_id, username, full_name) -> User`
  - `get_user_by_telegram_id(telegram_id) -> User | None`
  - `set_user_role(telegram_id, role) -> User`
- [ ] Создать `states/registration.py`:
  - `RegistrationStates(StatesGroup)`: `choosing_role`, `entering_full_name`
- [ ] Создать `handlers/registration.py`:
  - `/start` запускает регистрацию, если пользователь не найден в БД
  - Предложить выбор роли через инлайн-клавиатуру
  - Сохранить полное имя через состояние FSM
  - Подтвердить регистрацию и показать меню по роли
- [ ] Создать `middlewares/role.py`:
  - `RoleMiddleware(BaseMiddleware)` — добавляет объект `user` в данные хендлера
  - Вспомогательный декоратор `require_role(*roles)` для контроля доступа на уровне хендлера
- [ ] Зарегистрировать `RoleMiddleware` на message и callback роутерах диспетчера
- [ ] Закрыть хендлеры только для преподавателей декоратором `require_role(RoleEnum.teacher)`
- [ ] Закрыть хендлеры только для администраторов декоратором `require_role(RoleEnum.admin)`
- [ ] Сгенерировать и применить миграцию Alembic для таблицы `users`

---

## MVP Фаза 5 — Модуль расписания

- [ ] Создать `database/models/group.py`:
  - Модель `Group`: `id`, `name`, `year`
- [ ] Создать `database/models/lesson.py`:
  - Модель `Lesson`: `id`, `subject`, `teacher_id` (FK → User), `group_id` (FK → Group), `weekday` (0–6), `start_time`, `end_time`, `room`
- [ ] Создать `services/schedule_service.py`:
  - `get_today_schedule_for_student(group_id) -> list[Lesson]`
  - `get_weekly_schedule_for_student(group_id) -> dict[int, list[Lesson]]`
  - `get_today_schedule_for_teacher(teacher_id) -> list[Lesson]`
  - `get_weekly_schedule_for_teacher(teacher_id) -> dict[int, list[Lesson]]`
- [ ] Создать `handlers/schedule.py`:
  - Callback: показать меню расписания (сегодня / неделя)
  - Callback: вывести расписание на сегодня в виде форматированного сообщения
  - Callback: вывести расписание на неделю, каждый день отдельным блоком
- [ ] Создать `keyboards/schedule.py`:
  - `schedule_menu_keyboard()` — инлайн-кнопки: Сегодня, Неделя, Назад
- [ ] Форматировать вывод расписания: предмет, аудитория, время, имя преподавателя/группы
- [ ] Сгенерировать и применить миграции для таблиц `groups` и `lessons`
- [ ] Добавить 2–3 тестовых занятия через скрипт `scripts/seed.py` для проверки

---

## MVP Фаза 6 — Модуль посещаемости

- [ ] Создать `database/models/attendance.py`:
  - Модель `Attendance`: `id`, `lesson_id` (FK), `student_id` (FK → User), `date`, `status`
  - `AttendanceStatus(str, Enum)`: `present`, `absent`, `late`, `excused`
- [ ] Создать `services/attendance_service.py`:
  - `mark_attendance(lesson_id, student_id, date, status) -> Attendance`
  - `get_attendance_for_lesson(lesson_id, date) -> list[Attendance]`
  - `get_student_attendance(student_id) -> list[Attendance]`
- [ ] Создать `handlers/attendance.py` (сценарий преподавателя):
  - Показать список сегодняшних занятий преподавателя
  - По выбранному занятию: показать список студентов группы
  - Инлайн-кнопки на каждого студента: ✅ Присутствует / ❌ Отсутствует / ⏰ Опоздал
  - Сохранить статус в БД при нажатии callback
- [ ] Создать `handlers/attendance_student.py`:
  - Студент просматривает историю своей посещаемости
  - Вывести итог: всего занятий, присутствовал, отсутствовал, процент посещаемости
- [ ] Создать `keyboards/attendance.py`:
  - Кнопки статуса для каждого студента в виде `InlineKeyboardMarkup`
  - Навигация: возврат к списку занятий
- [ ] Сгенерировать и применить миграцию для таблицы `attendance`

---

## MVP Фаза 7 — Модуль оценок

- [ ] Создать `database/models/mark.py`:
  - Модель `Mark`: `id`, `student_id` (FK → User), `lesson_id` (FK → Lesson), `teacher_id` (FK → User), `value` (1–5), `comment`, `created_at`
- [ ] Создать `services/mark_service.py`:
  - `create_mark(student_id, lesson_id, teacher_id, value, comment) -> Mark`
  - `get_marks_for_student(student_id) -> list[Mark]`
  - `get_marks_for_lesson(lesson_id) -> list[Mark]`
- [ ] Создать `states/marks.py`:
  - `MarkStates(StatesGroup)`: `selecting_student`, `entering_value`, `entering_comment`
- [ ] Создать `handlers/marks_teacher.py`:
  - Преподаватель выбирает занятие → выбирает студента → вводит оценку → комментарий (опционально) → подтверждение
  - Валидировать значение оценки в допустимом диапазоне
- [ ] Создать `handlers/marks_student.py`:
  - Студент просматривает список своих оценок, сгруппированных по предметам
  - Показать среднее значение по каждому предмету
- [ ] Создать `keyboards/marks.py`:
  - Выбор оценки: инлайн-кнопки 1–5
  - Навигация: назад, подтвердить, отмена
- [ ] Сгенерировать и применить миграцию для таблицы `marks`

---

## MVP Фаза 8 — Уведомления

- [ ] Создать `services/notification_service.py`:
  - `send_notification(bot, telegram_id, text)` — обёртка над `bot.send_message`
- [ ] Уведомление о новой оценке: после `create_mark` отправить уведомление студенту
- [ ] Уведомление о посещаемости: после отметки «отсутствует» уведомить студента
- [ ] Создать `utils/scheduler.py`:
  - Ежедневное напоминание о расписании: отправлять студентам занятия на сегодня в заданное время
  - Использовать фоновый `asyncio`-таск или `apscheduler` (добавить в requirements при необходимости)
- [ ] Добавить `REMINDER_TIME` в `.env.example` (например, `08:00`)
- [ ] Корректно обрабатывать `TelegramForbiddenError` если пользователь заблокировал бота

---

## MVP Фаза 9 — Тестирование и финализация

- [ ] Проверить все хендлеры: у каждого должен быть `router = Router()` и регистрация в `main()`
- [ ] Проверить все сервисы: все обращения к БД используют паттерн `async with session`
- [ ] Добавить аннотации типов ко всем функциям сервисов и сигнатурам хендлеров
- [ ] Убедиться, что нет вызовов `print()` — заменить на `logger.*`
- [ ] Удалить хардкодированные ID, токены и учётные данные из исходников
- [ ] Запустить `alembic upgrade head` на чистой БД — убедиться, что все миграции применяются по порядку
- [ ] Выполнить `alembic downgrade base` и снова `alembic upgrade head` — проверить обратимость
- [ ] Smoke-тест: `/start` как новый пользователь → регистрация → выбор роли → главное меню
- [ ] Smoke-тест (студент): просмотр расписания на сегодня → просмотр оценок → просмотр посещаемости
- [ ] Smoke-тест (преподаватель): отметить посещаемость на занятии → выставить оценку → убедиться, что студент получил уведомление
- [ ] Проверить граничные случаи: студент без расписания, пустой список оценок, повторная отметка посещаемости
- [ ] Обновить `README.md`: все переменные окружения, инструкция по установке, шаги миграции, контакты команды
- [ ] Подготовить сценарий демонстрации: пошаговый показ всех функций MVP для презентации

---

## Будущие задачи (НЕ MVP)

> Эти задачи **явно выходят за рамки MVP**. Не реализовывать в фазах 1–9.

- [ ] **FastAPI** — REST API-слой для внешних интеграций
- [ ] **Telegram Mini App** — веб-интерфейс внутри Telegram
- [ ] **Веб-интерфейс** — отдельная административная панель
- [ ] **Аналитическая панель** — графики посещаемости и успеваемости
- [ ] **AI-модуль** — автоматический анализ данных студентов
- [ ] **AI-тьютор** — диалоговый ассистент для обучения
- [ ] **Генерация отчётов** — автоматические сводные отчёты по расписанию
- [ ] **Экспорт в PDF** — скачиваемые отчёты для преподавателей и администраторов
- [ ] **Система рекомендаций** — персональные учебные рекомендации
- [ ] **Расширенная аналитика** — тренды оценок, прогноз отчислений
- [ ] **Docker / Docker Compose** — контейнеризованное развёртывание
- [ ] **CI/CD pipeline** — автоматическое тестирование и деплой

---

## GitHub Workflow

### Стратегия веток

| Ветка | Назначение |
|---|---|
| `main` | Стабильный, готовый к демо код. Слияние только через PR после ревью. |
| `feature/<название>` | Одна задача или функция на ветку, создаётся от `develop`. |

### Примеры названий веток

```
feature/project-setup
feature/database-setup
feature/start-handler
feature/user-registration
feature/role-middleware
feature/schedule-module
feature/attendance-module
feature/marks-module
feature/notifications
feature/testing-cleanup
```

### Правила работы с PR

- PR создаётся из `feature/*` → `main`
- Требуется **минимум 1 апрув** перед слиянием
- Формат названия PR: `[Фаза N] Краткое описание`
- Фичевая ветка удаляется после слияния

### Формат коммитов

```
feat: добавить хендлер отметки посещаемости для преподавателя
fix: исправить область действия асинхронной сессии в mark_service
refactor: вынести форматирование расписания в utils
chore: обновить requirements.txt, добавить apscheduler
```
