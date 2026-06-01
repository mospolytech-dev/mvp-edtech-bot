# MVP EdTech Bot

> **Telegram-бот для управления учебным процессом: расписание, посещаемость, оценки**

---

## Стек

| Компонент     | Технология              |
|--------------|-------------------------|
| Язык          | Python 3.12+            |
| Telegram Bot  | Aiogram 3.28            |
| База данных   | PostgreSQL 14+          |
| ORM           | SQLAlchemy 2.0 Async    |
| Миграции      | Alembic                 |
| Конфигурация  | python-dotenv           |

---

## Структура проекта

```
mvp-edtech-bot/
├── bot/
│   ├── main.py                   # точка входа
│   ├── config.py                 # загрузка .env
│   ├── filters/
│   │   └── admin.py              # фильтр IsAdmin
│   ├── middlewares/
│   │   └── db.py                 # DbSessionMiddleware (инжектит session в хендлеры)
│   ├── handlers/
│   │   ├── start.py              # /start — показывает меню по роли
│   │   └── admin/
│   │       ├── panel.py          # навигация по админ-меню
│   │       ├── groups.py         # CRUD групп
│   │       ├── subjects.py       # CRUD дисциплин
│   │       ├── schedule.py       # CRUD расписания
│   │       └── users.py          # список пользователей
│   ├── keyboards/
│   │   ├── inline.py             # клавиатура обычного пользователя
│   │   └── admin.py              # клавиатуры админ-панели
│   └── states/
│       └── admin.py              # FSM-состояния для создания групп / дисциплин / занятий
├── database/
│   ├── base.py                   # DeclarativeBase
│   ├── session.py                # async engine + sessionmaker
│   ├── models/
│   │   ├── user.py               # User (roles: student / teacher / admin)
│   │   ├── group.py              # Group
│   │   ├── subject.py            # Subject
│   │   ├── lesson.py             # Lesson (шаблон расписания)
│   │   ├── attendance.py         # Attendance
│   │   └── mark.py               # Mark
│   └── crud/
│       ├── users.py
│       ├── groups.py
│       ├── subjects.py
│       └── lessons.py
├── scripts/
│   └── setup_db.py               # создаёт БД и применяет миграции
├── alembic/
│   ├── versions/                 # файлы миграций
│   └── env.py                    # async-конфигурация Alembic
├── alembic.ini
├── requirements.txt
└── .env.example
```

---

## Быстрый старт

### 1. Клонировать и перейти в папку

```bash
git clone https://github.com/mospolytech-dev/mvp-edtech-bot.git
cd mvp-edtech-bot
```

### 2. Создать виртуальное окружение и установить зависимости

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 3. Настроить переменные окружения

```bash
cp .env.example .env
```

Открыть `.env` и заполнить:

```env
# Токен бота — получить у @BotFather
BOT_TOKEN=your_telegram_bot_token_here

# Строка подключения к PostgreSQL
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/edtech_db

# Telegram ID администраторов через запятую (узнать через @userinfobot)
ADMIN_IDS=123456789,987654321
```

### 4. Сгенерировать миграцию

```bash
alembic revision --autogenerate -m "init"
```

### 5. Создать базу данных и применить миграции

Скрипт сам создаст БД `edtech_db` (если не существует) и применит все миграции:

```bash
python -m scripts.setup_db
```

> PostgreSQL должен быть запущен. Пользователь из `DATABASE_URL` должен иметь право создавать базы данных (обычно это `postgres`).

### 6. Запустить бота

```bash
python -m bot.main
```

---

## Как работает /start

| Кто открывает | Что видит |
|--------------|-----------|
| Telegram ID из `ADMIN_IDS` | Панель администратора |
| Обычный пользователь | Главное меню (расписание, посещаемость, оценки) |

---

## Админ-панель

Доступна автоматически при `/start` для пользователей из `ADMIN_IDS`.

| Раздел | Функционал |
|--------|-----------|
| 👥 Пользователи | Список активных пользователей |
| 🏫 Группы | Просмотр и создание групп |
| 📚 Дисциплины | Просмотр и создание дисциплин |
| 📅 Расписание | Просмотр и добавление занятий |

---

## Roadmap

```
[x] Инициализация проекта
[x] PostgreSQL + SQLAlchemy Async + Alembic
[x] Схема БД: users, groups, subjects, lessons, attendance, marks
[x] Админ-панель: группы, дисциплины, расписание, пользователи
[x] DB middleware (автоматический inject сессии в хендлеры)
[x] Разграничение доступа по ADMIN_IDS

[ ] Регистрация пользователей (FSM + одобрение администратором)
[ ] Просмотр расписания для студента / преподавателя
[ ] Отметка посещаемости
[ ] Выставление и просмотр оценок
[ ] Push-уведомления
```

---

## Лицензия

MIT
