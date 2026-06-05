# CLAUDE.md — Контекст для Claude Code

> Этот файл помогает Claude Code ориентироваться в проекте. Добавлен в `.gitignore`.

## Стек

Python 3.12 · Aiogram 3 · PostgreSQL · SQLAlchemy 2.0 Async · Alembic · python-dotenv  
Запуск: `python -m bot.main`

---

## Структура проекта

```
bot/
  main.py                  # точка входа, регистрирует все роутеры
  config.py                # Settings из .env: BOT_TOKEN, DATABASE_URL, ADMIN_IDS
  handlers/
    start.py               # /start — показывает меню по роли или запускает регистрацию
    registration.py        # FSM регистрации (см. ниже)
    admin/
      panel.py             # adm:menu, adm:noop
      groups.py            # CRUD групп
      subjects.py          # CRUD дисциплин
      schedule.py          # CRUD расписания
      users.py             # список пользователей
      applications.py      # одобрение / отклонение заявок
  keyboards/
    inline.py              # клавиатуры для обычных пользователей (регистрация)
    admin.py               # клавиатуры админ-панели
  states/
    user.py                # RegistrationStates
    admin.py               # AdminGroupStates, AdminSubjectStates, AdminLessonStates
  middlewares/
    db.py                  # DbSessionMiddleware
  filters/
    admin.py               # IsAdmin()

database/
  base.py                  # DeclarativeBase — все модели наследуют отсюда, поле id BigInteger PK
  session.py               # async_engine + async_sessionmaker
  models/
    user.py                # User
    group.py               # Group
    subject.py             # Subject
    lesson.py              # Lesson
    attendance.py          # Attendance
    mark.py                # Mark
  crud/
    users.py
    groups.py
    subjects.py
    lessons.py

alembic/
  versions/90b2c9904cd5_init.py   # единственная миграция, создаёт все таблицы
```

---

## Ключевые паттерны

### Session injection
`session: AsyncSession` попадает в хендлеры через `DbSessionMiddleware` как обычный аргумент. Никакого `Depends()` нет — это aiogram, не FastAPI.

### Роли и доступ
- `UserRole` (enum): `student / teacher / admin` — хранится в БД
- **Admin** определяется по `ADMIN_IDS` в `.env` через `IsAdmin()` фильтр, а НЕ по полю `role` в БД
- Обычные пользователи проходят регистрацию и ждут одобрения (`status=pending`)

### Пагинация (admin.py)
- `PER_PAGE = 8`, 2 кнопки в строке
- `PageCallback(section: str, page: int)` — section = `"groups"` / `"subjects"`
- `_pagination_row(builder, section, page, total)` добавляет строку ◀️ / `N / M` / ▶️
- Кнопка-счётчик (`adm:noop`) ничего не делает — просто показывает текущую страницу

### Пагинация регистрации (inline.py)
- Те же принципы, но отдельные callback-классы: `RegGroupPageCallback(page)`, `RegSubjectPageCallback(page)`
- `_pagination_row(builder, page_callback_cls, page, total)` — аналог, без section
- Счётчик идёт с `callback_data="reg:noop"`, обрабатывается хендлером `reg_noop` в `registration.py`

---

## FSM регистрации

```
waiting_role
    │  RegRoleCallback(role)
waiting_full_name
    │  text message
    ├─ student → waiting_group      (если есть группы в БД)
    ├─ teacher → waiting_subjects   (если есть дисциплины в БД)
    └─ иначе  → _finish_registration()

waiting_group
    │  RegGroupCallback(group_id)   — один клик = одна группа, регистрация завершается
    │  RegGroupPageCallback(page)   — навигация по страницам (edit_reply_markup)
    └─ group_id=0 = "Пропустить"

waiting_subjects
    │  RegSubjectCallback(subject_id, page)  — toggle ✅/снять, обновляет клавиатуру
    │  RegSubjectPageCallback(page)          — навигация
    └─ F.data == "reg:subjects_done"         — завершить выбор
```

**Важно про дисциплины преподавателя:**  
Выбранные дисциплины **не сохраняются в БД** — они уходят только в текст уведомления администратору (`📚 Дисциплины: Математика, Физика`). Это MVP-решение. Постоянная связь teacher↔subject появится позже через таблицу `teacher_subjects` (many-to-many), отмечено в TODO.md.

**Важно про группу студента:**  
Студент может принадлежать только одной группе (`User.group_id` — одно поле). Один клик = выбор = конец регистрации.

### После завершения FSM
`_finish_registration()` в `registration.py`:
1. `create_user(session, ...)` → `User` со статусом `pending`
2. Отправляет сообщение пользователю: "Заявка отправлена"
3. Рассылает уведомление всем `ADMIN_IDS` с кнопками "Одобрить / Отклонить" (`ApplicationCallback`)

---

## Модели БД (User подробнее)

```python
User:
  telegram_id: BigInteger UNIQUE
  username:    String(255) nullable
  full_name:   String(255)
  role:        Enum(UserRole)   — student / teacher / admin
  status:      Enum(UserStatus) — pending / active / rejected  (default: pending)
  group_id:    FK → groups.id   nullable  (только для student)
  created_at:  DateTime server_default=now()
```

Связь teacher↔subject через `User.taught_lessons` → `Lesson.subject_id` (не прямая).

---

## Что реализовано

- [x] Регистрация (роль, имя, группа для студента, дисциплины для преподавателя)
- [x] Заявки: admin одобряет / отклоняет
- [x] Админ-панель: группы, дисциплины, расписание, пользователи
- [x] Пагинация везде (8 элементов, 2 колонки)
- [x] DB middleware

## Что ещё нужно (MVP)

- [ ] Просмотр расписания (студент / преподаватель)
- [ ] Отметка посещаемости (преподаватель)
- [ ] Просмотр посещаемости (студент)
- [ ] Оценки: выставление (преподаватель), просмотр (студент)
- [ ] Push-уведомления

---

## Миграции

Одна миграция: `alembic/versions/90b2c9904cd5_init.py` — создаёт все таблицы разом.

```bash
alembic upgrade head      # применить
alembic downgrade base    # откатить всё
```
