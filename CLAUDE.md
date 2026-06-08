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
  filters/
    admin.py               # IsAdmin() — проверка по ADMIN_IDS из .env
    teacher.py             # IsTeacher() — роль из БД, инжектит teacher: User в хендлер
    student.py             # IsStudent() — роль из БД, инжектит student: User в хендлер
  middlewares/
    db.py                  # DbSessionMiddleware — инжектит session: AsyncSession
  handlers/
    start.py               # /start — маршрутизация по роли
    registration.py        # FSM регистрации
    admin/
      panel.py             # adm:menu, adm:noop, тест-режим (seed + переключение ролей)
      groups.py            # CRUD групп
      subjects.py          # CRUD дисциплин
      schedule.py          # CRUD расписания (календарь + выбор времени кнопками)
      users.py             # список пользователей
      applications.py      # одобрение / отклонение заявок
    teacher/
      menu.py              # teacher:menu, teacher:noop
      schedule.py          # список занятий (пагинация) + карточка занятия
      attendance.py        # отметка посещаемости (тогл на лету)
      marks.py             # выставление оценок (занятие → студент → 1–5)
    student/
      menu.py              # student:menu, student:noop
      schedule.py          # расписание группы по дням недели
      attendance.py        # своя посещаемость + статистика
      grades.py            # свои оценки сгруппированы по дисциплинам
  keyboards/
    inline.py              # меню студента/преподавателя, клавиатуры регистрации
    admin.py               # клавиатуры админ-панели
    teacher.py             # клавиатуры панели преподавателя + CallbackData классы
    student.py             # клавиатуры панели студента
  states/
    user.py                # RegistrationStates
    admin.py               # AdminGroupStates, AdminSubjectStates, AdminLessonStates

database/
  base.py                  # DeclarativeBase, поле id BigInteger PK
  session.py               # async_engine + async_sessionmaker_factory
  models/
    user.py                # User
    group.py               # Group
    subject.py             # Subject
    lesson.py              # Lesson
    attendance.py          # Attendance + AttendanceStatus enum
    mark.py                # Mark
  crud/
    users.py               # get_user_by_telegram_id, create_user, update_user_status, get_students_by_group, ...
    groups.py
    subjects.py
    lessons.py             # get_all_lessons, get_lessons_for_teacher, get_lessons_for_group, get_lesson_by_id, create_lesson
    attendance.py          # get_attendance_for_lesson, upsert_attendance, get_attendance_for_student
    marks.py               # create_mark, get_marks_for_student

alembic/
  versions/90b2c9904cd5_init.py   # единственная миграция, создаёт все таблицы
```

---

## Ключевые паттерны

### Session injection
`session: AsyncSession` попадает в хендлеры через `DbSessionMiddleware` как обычный аргумент. Никакого `Depends()` нет — это aiogram, не FastAPI. Commit делает middleware автоматически после хендлера.

### Роли и доступ
- `UserRole` (enum): `student / teacher / admin` — хранится в БД
- **Admin** определяется по `ADMIN_IDS` в `.env` через `IsAdmin()` — без обращения к БД. `/start` проверяет ADMIN_IDS первым, поэтому `/start` всегда открывает админку даже если у пользователя другая роль в БД.
- `IsTeacher()` и `IsStudent()` — смотрят в БД, возвращают `{"teacher": user}` / `{"student": user}`, что инжектится в kwargs хендлера.
- Обычные пользователи проходят регистрацию и ждут одобрения (`status=pending`).

### Тест-режим (admin/panel.py)
Позволяет администратору переключать свою роль в БД для тестирования интерфейсов:
- `adm:test:seed` — создаёт группы, дисциплины, студентов если не существуют
- `adm:test:teacher` — меняет роль на teacher, создаёт 3 тестовых занятия если нет
- `adm:test:student` — меняет роль на student, привязывает к группе, сидирует посещаемость и оценки
- `/start` всегда возвращает в админку (ADMIN_IDS проверяется раньше БД)

### Callback-классы (teacher.py)
```
TeacherLessonCallback(lesson_id)          # выбор занятия из списка
TeacherLessonPageCallback(page)           # пагинация списка занятий
TeacherActionCallback(lesson_id, action)  # action = "att" | "marks"
TeacherAttCallback(lesson_id, student_id, next_status, date_iso)  # тогл посещаемости
TeacherStudentCallback(lesson_id, student_id)  # выбор студента для оценки
TeacherMarkCallback(lesson_id, student_id, value)  # сохранить оценку
```

### Пагинация (admin.py)
- `PER_PAGE = 8`, 2 кнопки в строке
- `PageCallback(section, page)` — section = `"groups"` / `"subjects"`
- `adm:noop` — кнопка-счётчик, ничего не делает

### Пагинация регистрации (inline.py)
- `RegGroupPageCallback(page)`, `RegSubjectPageCallback(page)`
- Счётчик: `callback_data="reg:noop"`

### Выбор времени занятия (admin/schedule.py)
Вместо текстового ввода — кнопки с готовыми парами (`TIME_SLOTS` в `admin.py`).  
`TimeSlotCallback(slot: int)` — индекс в `TIME_SLOTS`.

### Ограничение дат в календаре (admin/schedule.py)
`SimpleCalendar(show_alerts=True)` + `set_dates_range(today, today+2years)` — запрет прошедших дат. Устанавливается на оба экземпляра: при открытии и при `process_selection`.

---

## FSM регистрации

```
waiting_role
    │  RegRoleCallback(role)
waiting_full_name
    │  text message (валидация: 2–3 слова кириллицей)
    ├─ student → waiting_group      (если есть группы в БД)
    ├─ teacher → waiting_subjects   (если есть дисциплины в БД)
    └─ иначе  → _finish_registration()

waiting_group
    │  RegGroupCallback(group_id)   — один клик = выбор = конец
    │  RegGroupPageCallback(page)   — навигация
    └─ group_id=0 = "Пропустить"

waiting_subjects
    │  RegSubjectCallback(subject_id, page)  — toggle ✅/снять
    │  RegSubjectPageCallback(page)          — навигация
    └─ F.data == "reg:subjects_done"         — завершить выбор
```

Дисциплины преподавателя **не сохраняются в БД** — только в текст уведомления администратору. MVP-ограничение, отмечено в TODO.md.

### После завершения FSM
`_finish_registration()`:
1. `create_user(session, ...)` → `User(status=pending)`
2. Сообщение пользователю: "Заявка отправлена"
3. Рассылка всем `ADMIN_IDS` с кнопками "Одобрить / Отклонить" (`ApplicationCallback`)

---

## Модели БД

```python
User:
  telegram_id: BigInteger UNIQUE
  username:    String(255) nullable
  full_name:   String(255)
  role:        Enum(UserRole)   — student / teacher / admin
  status:      Enum(UserStatus) — pending / active / rejected  (default: pending)
  group_id:    FK → groups.id   nullable

Group:    name, year
Subject:  name
Lesson:   subject_id, teacher_id, group_id, weekday (1=Пн…7=Вс), start_time, end_time, room
Attendance: lesson_id, student_id, date, status (present/absent/late/excused)
            UNIQUE(lesson_id, student_id, date)
Mark:     student_id, lesson_id, teacher_id, value (1–5), comment, created_at
```

---

## Миграции

```bash
alembic upgrade head      # применить
alembic downgrade base    # откатить всё
```
