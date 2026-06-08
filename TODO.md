# EdTech Bot — MVP: Доска задач

> **Область:** только MVP. Отложенные функции — в разделе [Будущие задачи](#будущие-задачи-не-mvp).
> **Стек:** Python 3.12+ · Aiogram 3 · PostgreSQL · SQLAlchemy Async · Alembic · python-dotenv

---

## Распределение задач по команде

| Направление | Участник |
|---|---|
| Локальный деплой (бд, гит и т.д.) | Все |
| Авторизация | Сима |
| Роль админа | Сима |
| Роль студента | Егор |
| Роль препода | - |
| Модуль расписания | Егор |
| Модуль посещаемости | — |
| Модуль оценок | — |
| Модуль уведомлений | — |
| Тестирование | Все |
| Документация | — |

---

## Фаза 1 — Настройка проекта ✅

- [x] Структура: `bot/`, `database/`, `alembic/`, `scripts/`
- [x] `bot/main.py` — точка входа, регистрация роутеров, запуск поллинга
- [x] `bot/config.py` — загрузка `BOT_TOKEN`, `DATABASE_URL`, `ADMIN_IDS` из `.env`
- [x] `.env.example`, `.gitignore`, `requirements.txt`, `README.md`
- [ ] Логирование — настроить формат с временной меткой, убрать все `print()`

---

## Фаза 2 — База данных ✅

- [x] `database/base.py` — `DeclarativeBase` с общим полем `id`
- [x] `database/session.py` — async engine + sessionmaker
- [x] `bot/middlewares/db.py` — `DbSessionMiddleware` (инжектит `session` в каждый хендлер)
- [x] `alembic/env.py` — async-конфигурация
- [x] Миграция `alembic/versions/90b2c9904cd5_init.py` — создаёт все таблицы
- [x] Модели: `database/models/user.py`, `group.py`, `subject.py`, `lesson.py`, `attendance.py`, `mark.py`

---

## Фаза 3 — Регистрация и роли ✅

- [x] `bot/states/user.py` — `RegistrationStates`: `waiting_role`, `waiting_full_name`, `waiting_group`, `waiting_subjects`
- [x] `bot/handlers/registration.py` — FSM флоу регистрации:
  - Выбор роли → ввод ФИО (валидация: кириллица, 2–3 слова) → группа (студент) / дисциплины (преподаватель)
  - Заявка уходит администратору, повторная подача после отклонения
- [x] `bot/handlers/start.py` — `/start`: новый пользователь, pending, rejected, active (студент/преподаватель/админ)
- [x] `bot/keyboards/inline.py` — клавиатуры регистрации с пагинацией и 2 колонками
- [x] `bot/filters/admin.py` — `IsAdmin()` по `ADMIN_IDS` из `.env`
- [x] `database/crud/users.py` — `create_user`, `get_user_by_telegram_id`, `update_user_status`, `delete_user_by_telegram_id`

---

## Фаза 4 — Админ-панель ✅

- [x] `bot/keyboards/admin.py` — все клавиатуры панели (пагинация `PER_PAGE=8`, 2 колонки)
- [x] `bot/handlers/admin/panel.py` — навигация по меню (`adm:menu`)
- [x] `bot/handlers/admin/applications.py` — просмотр заявок, одобрение / отклонение
- [x] `bot/handlers/admin/groups.py` — CRUD групп
- [x] `bot/handlers/admin/subjects.py` — CRUD дисциплин
- [x] `bot/handlers/admin/users.py` — список преподавателей и студентов
- [x] `bot/handlers/admin/schedule.py` — просмотр и добавление занятий
- [x] `database/crud/groups.py`, `subjects.py`, `lessons.py`

---

## Фаза 5 — Модуль расписания

- [ ] `database/crud/lessons.py` — добавить:
  - `get_lessons_for_group(session, group_id) -> list[Lesson]`
  - `get_lessons_for_teacher(session, teacher_id) -> list[Lesson]`
- [ ] `bot/states/user.py` — добавить `ScheduleStates` если нужен FSM
- [ ] `bot/handlers/schedule.py` — хендлеры для `menu:schedule`:
  - Показать меню (Сегодня / Вся неделя / Назад)
  - Вывести расписание на сегодня: предмет, аудитория, время
  - Вывести расписание на неделю: каждый день отдельным блоком
- [ ] `bot/keyboards/schedule.py` — `schedule_menu_keyboard()`, `back_to_menu_keyboard()`
- [ ] Зарегистрировать `schedule_router` в `bot/main.py`
- [ ] Добавить тестовые занятия через `scripts/seed.py` для проверки

---

## Фаза 6 — Модуль посещаемости

- [ ] `database/crud/attendance.py` — добавить:
  - `mark_attendance(session, lesson_id, student_id, date, status) -> Attendance`
  - `get_attendance_for_lesson(session, lesson_id, date) -> list[Attendance]`
  - `get_student_attendance(session, student_id) -> list[Attendance]`
- [ ] `bot/states/user.py` — добавить `AttendanceStates`
- [ ] `bot/handlers/attendance.py` — хендлеры для `menu:attendance` (преподаватель):
  - Список сегодняшних занятий преподавателя
  - По занятию: список студентов группы с кнопками ✅ Присутствует / ❌ Отсутствует / ⏰ Опоздал
  - Сохранить статус в БД при нажатии
- [ ] `bot/handlers/attendance_student.py` — хендлеры для `menu:attendance` (студент):
  - История посещаемости: всего занятий, был, отсутствовал, % посещаемости
- [ ] `bot/keyboards/attendance.py` — кнопки статуса, навигация назад
- [ ] Зарегистрировать роутеры в `bot/main.py`

---

## Фаза 7 — Модуль оценок

- [ ] `database/crud/marks.py` — добавить:
  - `create_mark(session, student_id, lesson_id, teacher_id, value, comment) -> Mark`
  - `get_marks_for_student(session, student_id) -> list[Mark]`
  - `get_marks_for_lesson(session, lesson_id) -> list[Mark]`
- [ ] `bot/states/user.py` — добавить `MarkStates`: `selecting_student`, `entering_value`, `entering_comment`
- [ ] `bot/handlers/marks_teacher.py` — хендлеры для `menu:grades` (преподаватель):
  - Занятие → студент → оценка (1–5) → комментарий (опционально) → подтверждение
- [ ] `bot/handlers/marks_student.py` — хендлеры для `menu:grades` (студент):
  - Оценки сгруппированы по предметам, среднее по каждому
- [ ] `bot/keyboards/marks.py` — кнопки 1–5, назад, подтвердить, отмена
- [ ] Зарегистрировать роутеры в `bot/main.py`

---

## Фаза 8 — Уведомления(вынесено из MVP на другую стадию)

- [ ] `bot/handlers/attendance.py` — после отметки «отсутствует» отправить `bot.send_message` студенту
- [ ] `bot/handlers/marks_teacher.py` — после `create_mark` отправить уведомление студенту
- [ ] `bot/utils/scheduler.py` — ежедневное напоминание о расписании (asyncio-таск или apscheduler)
- [ ] Добавить `REMINDER_TIME` в `.env.example`
- [ ] Обрабатывать `TelegramForbiddenError` если пользователь заблокировал бота

---

## Фаза 9 — Финализация

- [ ] Smoke-тест: `/start` → регистрация → выбор роли → главное меню
- [ ] Smoke-тест студент: расписание → посещаемость → оценки
- [ ] Smoke-тест преподаватель: отметить посещаемость → выставить оценку → студент получил уведомление
- [ ] Проверить граничные случаи: нет расписания, пустой список оценок, повторная отметка посещаемости
- [ ] `alembic downgrade base` → `alembic upgrade head` — убедиться что миграции обратимы
- [ ] Убрать все `print()`, заменить на логирование
- [ ] Подготовить сценарий демо для презентации

---

## Будущие задачи (НЕ MVP)

> Эти задачи **явно выходят за рамки MVP**.

- [ ] **Просмотр расписания преподавателя на неделю** — выбрать преподавателя (инлайн-кнопки), затем показать его расписание, сгруппированное по дням недели (Пн–Вс); альтернатива — красивая веб-страница через Telegram Mini App
- [ ] **Переработка создания расписания** — текущий флоу создаёт по одному занятию за раз; необходимо:
  - Заменить `aiogram_calendar` на собственный компактный виджет выбора дня недели (Пн–Вс кнопками) вместо полного календаря — расписание повторяется еженедельно, конкретная дата не нужна
  - Поддержка добавления нескольких слотов за один сеанс: после сохранения занятия предлагать «Добавить ещё один день/час для этого же предмета/преподавателя/группы» или «Готово»
  - Валидация конфликтов: запрет добавления двух занятий у одного преподавателя или для одной группы в один день на пересекающееся время
- [ ] **teacher_subjects** — таблица many-to-many `users ↔ subjects`; сейчас дисциплины преподавателя уходят только в уведомление администратору и не хранятся в БД
- [ ] **Управление администраторами через БД** — сейчас `ADMIN_IDS` только в `.env`, требует перезапуска бота
- [ ] **Экспорт списка пользователей** — выгрузка преподавателей и студентов в Excel / CSV / PDF
- [ ] **FastAPI** — REST API-слой для внешних интеграций
- [ ] **Telegram Mini App** — веб-интерфейс внутри Telegram
- [ ] **Аналитическая панель** — графики посещаемости и успеваемости
- [ ] **AI-модуль** — автоматический анализ данных студентов
- [ ] **Docker / Docker Compose** — контейнеризованное развёртывание
- [ ] **CI/CD pipeline** — автоматическое тестирование и деплой

---

## GitHub Workflow

| Ветка | Назначение |
|---|---|
| `main` | Стабильный, готовый к демо код. Слияние только через PR после ревью. |
| `feature/<название>` | Одна задача или функция на ветку. |

**Формат коммитов:**
```
feat: добавить хендлер отметки посещаемости
fix: исправить пагинацию групп при регистрации
refactor: вынести форматирование расписания в отдельную функцию
chore: обновить requirements.txt
docs: обновить README
```
