import random
from datetime import date, time, timedelta

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import IsAdmin
from bot.keyboards.admin import admin_menu_keyboard
from bot.keyboards.inline import teacher_menu_keyboard, student_menu_keyboard
from database.crud.users import get_user_by_telegram_id
from database.models.attendance import Attendance, AttendanceStatus
from database.models.group import Group
from database.models.lesson import Lesson
from database.models.mark import Mark
from database.models.subject import Subject
from database.models.user import User, UserRole, UserStatus

admin_router = Router(name=__name__)
admin_router.callback_query.filter(IsAdmin())

_SEED_GROUPS = [
    ("253-324", 2025),
    ("253-325", 2025),
    ("253-326", 2024),
]

_SEED_SUBJECTS = [
    "Проектная деятельность",
    "Элементы математического анализа",
    "Дискретная математика",
    "История России",
    "Иностранный язык",
    "Философия",
    "Линейная алгебра",
]

_SEED_STUDENTS = [
    "Иванов Алексей Сергеевич",
    "Петров Дмитрий Олегович",
    "Смирнова Анна Павловна",
    "Козлов Михаил Андреевич",
    "Новикова Екатерина Ивановна",
    "Морозов Артём Владимирович",
]

# (weekday, subject_index, start, end, room)
_TEST_LESSONS = [
    (1, 0, time(9, 0),   time(10, 30), "101"),
    (3, 2, time(12, 40), time(14, 10), "205"),
    (5, 6, time(14, 20), time(15, 50), "310"),
]


def _test_mode_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🌱 Заполнить тестовые данные", callback_data="adm:test:seed"))
    builder.row(
        InlineKeyboardButton(text="👨‍🎓 Войти как студент", callback_data="adm:test:student"),
        InlineKeyboardButton(text="👨‍🏫 Войти как преподаватель", callback_data="adm:test:teacher"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:menu"))
    return builder.as_markup()


async def _upsert_user(
    session: AsyncSession,
    tg_id: int,
    role: UserRole,
    full_name: str,
    group_id: int | None = None,
) -> User:
    user = await get_user_by_telegram_id(session, tg_id)
    if user is None:
        user = User(
            telegram_id=tg_id,
            username=None,
            full_name=full_name,
            role=role,
            status=UserStatus.active,
            group_id=group_id,
        )
        session.add(user)
        await session.flush()
    else:
        user.role = role
        user.status = UserStatus.active
        user.full_name = full_name
        user.group_id = group_id
        await session.flush()
    return user


async def _seed_test_data(session: AsyncSession) -> str:
    lines: list[str] = []

    # Groups
    existing_names = {
        g.name for g in (await session.execute(select(Group))).scalars()
    }
    new_groups: list[Group] = []
    for name, year in _SEED_GROUPS:
        if name not in existing_names:
            g = Group(name=name, year=year)
            session.add(g)
            new_groups.append(g)
    await session.flush()
    lines.append(
        f"🏫 Группы: +{len(new_groups)} новых, {len(existing_names)} уже было"
    )

    # Subjects
    existing_subj = {
        s.name for s in (await session.execute(select(Subject))).scalars()
    }
    new_subj = 0
    subject_objects: list[Subject] = []
    for name in _SEED_SUBJECTS:
        if name not in existing_subj:
            s = Subject(name=name)
            session.add(s)
            new_subj += 1
        else:
            res = await session.execute(select(Subject).where(Subject.name == name))
            subject_objects.append(res.scalar_one())
    await session.flush()
    # fetch all subjects for lesson creation
    all_subjects = list((await session.execute(select(Subject))).scalars())
    lines.append(f"📚 Дисциплины: +{new_subj} новых, {len(existing_subj)} уже было")

    # Students — добавляем в каждую группу
    all_groups = list((await session.execute(select(Group))).scalars())
    new_students = 0
    fake_tg_id = 10000
    for group in all_groups:
        count = (await session.execute(
            select(func.count()).select_from(User)
            .where(User.group_id == group.id, User.role == UserRole.student)
        )).scalar()
        if count == 0:
            for name in _SEED_STUDENTS:
                while (await session.execute(
                    select(func.count()).select_from(User).where(User.telegram_id == fake_tg_id)
                )).scalar() > 0:
                    fake_tg_id += 1
                session.add(User(
                    telegram_id=fake_tg_id,
                    username=None,
                    full_name=name,
                    role=UserRole.student,
                    status=UserStatus.active,
                    group_id=group.id,
                ))
                fake_tg_id += 1
                new_students += 1
    await session.flush()
    lines.append(f"👨‍🎓 Студенты: +{new_students} новых")

    return "\n".join(lines)


async def _ensure_test_lessons(session: AsyncSession, teacher_id: int) -> None:
    if (await session.execute(
        select(func.count()).select_from(Lesson).where(Lesson.teacher_id == teacher_id)
    )).scalar() > 0:
        return

    group = (await session.execute(select(Group).limit(1))).scalar_one_or_none()
    subjects = list((await session.execute(select(Subject))).scalars())
    if not group or not subjects:
        return

    for weekday, subj_idx, start, end, room in _TEST_LESSONS:
        subject = subjects[subj_idx % len(subjects)]
        session.add(Lesson(
            subject_id=subject.id,
            teacher_id=teacher_id,
            group_id=group.id,
            weekday=weekday,
            start_time=start,
            end_time=end,
            room=room,
        ))
    await session.flush()


async def _seed_attendance_and_marks(session: AsyncSession, student_id: int, group_id: int) -> tuple[int, int]:
    lessons = list((await session.execute(
        select(Lesson).where(Lesson.group_id == group_id)
    )).scalars())
    if not lessons:
        return 0, 0

    today = date.today()
    att_statuses = [
        AttendanceStatus.present, AttendanceStatus.present, AttendanceStatus.present,
        AttendanceStatus.absent, AttendanceStatus.late,
    ]

    att_count = 0
    mark_count = 0

    for lesson in lessons:
        # последние 4 занятия по дню недели (назад по неделям)
        days_back = (today.isoweekday() - lesson.weekday) % 7
        lesson_date = today - timedelta(days=days_back if days_back else 7)

        for week in range(4):
            d = lesson_date - timedelta(weeks=week)
            exists = (await session.execute(
                select(func.count()).select_from(Attendance).where(
                    Attendance.lesson_id == lesson.id,
                    Attendance.student_id == student_id,
                    Attendance.date == d,
                )
            )).scalar()
            if exists == 0:
                session.add(Attendance(
                    lesson_id=lesson.id,
                    student_id=student_id,
                    date=d,
                    status=random.choice(att_statuses),
                ))
                att_count += 1

        # 2 оценки на дисциплину
        existing_marks = (await session.execute(
            select(func.count()).select_from(Mark).where(
                Mark.lesson_id == lesson.id,
                Mark.student_id == student_id,
            )
        )).scalar()
        if existing_marks == 0:
            for _ in range(2):
                session.add(Mark(
                    student_id=student_id,
                    lesson_id=lesson.id,
                    teacher_id=lesson.teacher_id,
                    value=random.randint(3, 5),
                ))
                mark_count += 1

    await session.flush()
    return att_count, mark_count


@admin_router.callback_query(F.data == "adm:menu")
async def back_to_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text("<b>Панель администратора</b>", reply_markup=admin_menu_keyboard())
    await callback.answer()


@admin_router.callback_query(F.data == "adm:noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()


@admin_router.callback_query(F.data == "adm:test")
async def test_mode(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🧪 <b>Тест-режим</b>\n\nВыберите роль — бот настроит всё автоматически.\n"
        "Вернуться в панель администратора: /start",
        reply_markup=_test_mode_keyboard(),
    )
    await callback.answer()


@admin_router.callback_query(F.data == "adm:test:seed")
async def seed_test_data(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer("Заполняю базу...")
    report = await _seed_test_data(session)
    await callback.message.edit_text(
        f"✅ <b>Готово!</b>\n\n{report}\n\nТеперь выберите роль для тестирования:",
        reply_markup=_test_mode_keyboard(),
    )


@admin_router.callback_query(F.data == "adm:test:student")
async def test_as_student(callback: CallbackQuery, session: AsyncSession) -> None:
    group = (await session.execute(select(Group).limit(1))).scalar_one_or_none()
    group_id = group.id if group else None
    group_name = group.name if group else "—"

    user = await _upsert_user(
        session,
        tg_id=callback.from_user.id,
        role=UserRole.student,
        full_name=callback.from_user.full_name or "Тест Студент",
        group_id=group_id,
    )

    att, marks = (0, 0)
    if group_id:
        att, marks = await _seed_attendance_and_marks(session, user.id, group_id)

    note = f"\n+{att} отметок посещаемости, +{marks} оценок" if att or marks else ""
    await callback.message.edit_text(
        f"👨‍🎓 <b>Режим студента</b>\nГруппа: {group_name}{note}\n\nДля возврата в админку — /start",
        reply_markup=student_menu_keyboard(),
    )
    await callback.answer()


@admin_router.callback_query(F.data == "adm:test:teacher")
async def test_as_teacher(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _upsert_user(
        session,
        tg_id=callback.from_user.id,
        role=UserRole.teacher,
        full_name=callback.from_user.full_name or "Тест Преподаватель",
        group_id=None,
    )
    await _ensure_test_lessons(session, user.id)
    await callback.message.edit_text(
        "👨‍🏫 <b>Режим преподавателя</b>\n3 тестовых занятия добавлены (Пн/Ср/Пт)\n\nДля возврата в админку — /start",
        reply_markup=teacher_menu_keyboard(),
    )
    await callback.answer()
