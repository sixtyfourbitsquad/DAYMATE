#!/usr/bin/env python3
"""
DayMate 📅 - Button-only Age / Days / Time Calculator Bot (updated with .env)
Requires: python-telegram-bot >= 21.0
Usage:
  1. Create a .env file containing: TELEGRAM_TOKEN=123456:ABC...
  2. pip install python-telegram-bot python-dotenv
  3. python daymate_bot.py
"""

import logging
import os
from datetime import datetime, date, timedelta, time as dtime

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Load .env
load_dotenv()

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Conversation states (internal) ---
(
    CHOOSING_FEATURE,
    AGE_PICK_DATE,
    DAYS_PICK_START,
    DAYS_PICK_END,
    TIME_PICK_START_DATE,
    TIME_PICK_START_TIME,
    TIME_PICK_END_DATE,
    TIME_PICK_END_TIME,
) = range(8)


# --- Keyboards / UI helpers ---
def main_menu_kb():
    kb = [
        [InlineKeyboardButton("🎂 Age Calculator", callback_data="age")],
        [InlineKeyboardButton("📅 Days Calculator", callback_data="days")],
        [InlineKeyboardButton("🕰 Time Calculator", callback_data="time")],
    ]
    return InlineKeyboardMarkup(kb)


def month_kb(year: int, month: int, prefix: str):
    import calendar

    cal = calendar.Calendar(firstweekday=6)  # Sunday start
    month_days = cal.monthdayscalendar(year, month)

    buttons = []
    # weekday header row
    header = [InlineKeyboardButton(d[:2], callback_data="IGNORE") for d in ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]]
    buttons.append(header)

    # day buttons
    for wk in month_days:
        row = []
        for d in wk:
            if d == 0:
                row.append(InlineKeyboardButton(" ", callback_data="IGNORE"))
            else:
                row.append(InlineKeyboardButton(str(d), callback_data=f"{prefix}|{year}-{month:02d}-{d:02d}"))
        buttons.append(row)

    # navigation row
    prev_month = month - 1
    prev_year = year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1

    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1

    nav = [
        InlineKeyboardButton("◀", callback_data=f"{prefix}|NAV|{prev_year}-{prev_month}"),
        InlineKeyboardButton(f"{year}-{month:02d}", callback_data="IGNORE"),
        InlineKeyboardButton("▶", callback_data=f"{prefix}|NAV|{next_year}-{next_month}"),
    ]
    buttons.append(nav)
    return InlineKeyboardMarkup(buttons)


def hour_kb(prefix: str):
    rows = []
    for h in range(0, 24, 6):
        row = [InlineKeyboardButton(f"{hh:02d}", callback_data=f"{prefix}|H|{hh}") for hh in range(h, min(h + 6, 24))]
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def minute_kb(prefix: str):
    rows = []
    # compact minute choices (step 5 or 15 for fewer buttons)
    for m in range(0, 60, 15):
        row = [InlineKeyboardButton(f"{mm:02d}", callback_data=f"{prefix}|M|{mm}") for mm in range(m, min(m + 15, 60), 5)]
        rows.append(row)
    return InlineKeyboardMarkup(rows)


# --- Parsing & Calculation helpers ---
def parse_ymd(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def calc_age(birth: date, ref: date = None):
    if ref is None:
        ref = date.today()
    if birth > ref:
        return None
    y = ref.year - birth.year
    m = ref.month - birth.month
    d = ref.day - birth.day
    if d < 0:
        prev_month_days = (ref.replace(day=1) - timedelta(days=1)).day
        d += prev_month_days
        m -= 1
    if m < 0:
        m += 12
        y -= 1
    total_days = (ref - birth).days
    weeks = total_days // 7
    return {"years": y, "months": m, "days": d, "total_days": total_days, "weeks": weeks}


def calc_ymd_between(start: date, end: date):
    if start > end:
        start, end = end, start
    y = end.year - start.year
    m = end.month - start.month
    d = end.day - start.day
    if d < 0:
        prev_month_days = (end.replace(day=1) - timedelta(days=1)).day
        d += prev_month_days
        m -= 1
    if m < 0:
        m += 12
        y -= 1
    total_days = (end - start).days
    weeks = total_days // 7
    return {"years": y, "months": m, "days": d, "total_days": total_days, "weeks": weeks}


def calc_time_delta(start_dt: datetime, end_dt: datetime):
    if start_dt > end_dt:
        start_dt, end_dt = end_dt, start_dt
    delta = end_dt - start_dt
    total_seconds = int(delta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return {"hours": hours, "minutes": minutes, "seconds": seconds, "total_seconds": total_seconds}


# --- Handlers ---
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu. This function handles /start and any plain message (button-only thereafter)."""
    if update.message:
        await update.message.reply_text("Welcome to DayMate 📅 — choose a feature:", reply_markup=main_menu_kb())
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Welcome to DayMate 📅 — choose a feature:", reply_markup=main_menu_kb())
    return CHOOSING_FEATURE


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    choice = q.data
    context.user_data.clear()
    today = date.today()
    if choice == "age":
        context.user_data["calendar_prefix"] = "AGEDATE"
        await q.edit_message_text("Select your birth date:", reply_markup=month_kb(today.year, today.month, "AGEDATE"))
        return AGE_PICK_DATE
    if choice == "days":
        context.user_data["calendar_prefix"] = "DAYS_START"
        await q.edit_message_text("Select START date:", reply_markup=month_kb(today.year, today.month, "DAYS_START"))
        return DAYS_PICK_START
    if choice == "time":
        context.user_data["calendar_prefix"] = "TIME_START"
        await q.edit_message_text("Select START date & time:", reply_markup=month_kb(today.year, today.month, "TIME_START"))
        return TIME_PICK_START_DATE
    await q.edit_message_text("Unknown option. Returning to menu.", reply_markup=main_menu_kb())
    return CHOOSING_FEATURE


# AGE flow
async def age_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data.startswith("AGEDATE|NAV|"):
        _, _, ym = data.split("|")
        y, m = map(int, ym.split("-"))
        await q.edit_message_text("Select your birth date:", reply_markup=month_kb(y, m, "AGEDATE"))
        return AGE_PICK_DATE
    if data.startswith("AGEDATE|"):
        _, ymd = data.split("|", 1)
        birth = parse_ymd(ymd)
        res = calc_age(birth, date.today())
        if res is None:
            await q.edit_message_text("That date is in the future. Choose a valid birth date.", reply_markup=month_kb(date.today().year, date.today().month, "AGEDATE"))
            return AGE_PICK_DATE
        text = (
            f"🎂 *Age Result*\n\n"
            f"Born: {birth.isoformat()}\n"
            f"→ {res['years']} years, {res['months']} months, {res['days']} days\n"
            f"({res['weeks']} weeks — {res['total_days']} days total)"
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("↩ Back to menu", callback_data="MENU")]])
        await q.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
        return CHOOSING_FEATURE
    return AGE_PICK_DATE


# DAYS flow
async def days_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data.startswith("DAYS_START|NAV|"):
        _, _, ym = data.split("|")
        y, m = map(int, ym.split("-"))
        await q.edit_message_text("Select START date:", reply_markup=month_kb(y, m, "DAYS_START"))
        return DAYS_PICK_START
    if data.startswith("DAYS_START|"):
        _, ymd = data.split("|", 1)
        start_date = parse_ymd(ymd)
        context.user_data["days_start"] = start_date.isoformat()
        today = date.today()
        await q.edit_message_text(f"Start date set: {start_date.isoformat()}\nNow select END date:", reply_markup=month_kb(today.year, today.month, "DAYS_END"))
        return DAYS_PICK_END
    return DAYS_PICK_START


async def days_end_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data.startswith("DAYS_END|NAV|"):
        _, _, ym = data.split("|")
        y, m = map(int, ym.split("-"))
        await q.edit_message_text("Select END date:", reply_markup=month_kb(y, m, "DAYS_END"))
        return DAYS_PICK_END
    if data.startswith("DAYS_END|"):
        _, ymd = data.split("|", 1)
        end_date = parse_ymd(ymd)
        start = parse_ymd(context.user_data.get("days_start"))
        res = calc_ymd_between(start, end_date)
        text = (
            f"📅 *Days Difference*\n\n"
            f"From: {start.isoformat()}\nTo:   {end_date.isoformat()}\n\n"
            f"→ {res['years']} years, {res['months']} months, {res['days']} days\n"
            f"({res['weeks']} weeks — {res['total_days']} days total)"
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("↩ Back to menu", callback_data="MENU")]])
        await q.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
        return CHOOSING_FEATURE
    return DAYS_PICK_END


# TIME flow
async def time_start_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data.startswith("TIME_START|NAV|"):
        _, _, ym = data.split("|")
        y, m = map(int, ym.split("-"))
        await q.edit_message_text("Select START date:", reply_markup=month_kb(y, m, "TIME_START"))
        return TIME_PICK_START_DATE
    if data.startswith("TIME_START|"):
        _, ymd = data.split("|", 1)
        start_date = parse_ymd(ymd)
        context.user_data["time_start_date"] = start_date.isoformat()
        await q.edit_message_text(f"Start date: {start_date.isoformat()}\nSelect START hour:", reply_markup=hour_kb("TIME_START"))
        return TIME_PICK_START_TIME
    return TIME_PICK_START_DATE


async def time_start_time_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    parts = data.split("|")
    if len(parts) == 3 and parts[1] == "H":
        _, _, hh = parts
        context.user_data["time_start_hour"] = int(hh)
        await q.edit_message_text(f"Start date: {context.user_data['time_start_date']}\nStart hour: {hh}\nNow select START minutes:", reply_markup=minute_kb("TIME_START"))
        return TIME_PICK_START_TIME
    if len(parts) == 3 and parts[1] == "M":
        _, _, mm = parts
        hour = context.user_data.get("time_start_hour", 0)
        minute = int(mm)
        sd = parse_ymd(context.user_data["time_start_date"])
        start_dt = datetime.combine(sd, dtime(hour=hour, minute=minute))
        context.user_data["time_start_dt"] = start_dt.isoformat()
        today = date.today()
        await q.edit_message_text(f"Start datetime set: {start_dt.isoformat()}\n\nSelect END date:", reply_markup=month_kb(today.year, today.month, "TIME_END"))
        return TIME_PICK_END_DATE
    return TIME_PICK_START_TIME


async def time_end_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data.startswith("TIME_END|NAV|"):
        _, _, ym = data.split("|")
        y, m = map(int, ym.split("-"))
        await q.edit_message_text("Select END date:", reply_markup=month_kb(y, m, "TIME_END"))
        return TIME_PICK_END_DATE
    if data.startswith("TIME_END|"):
        _, ymd = data.split("|", 1)
        end_date = parse_ymd(ymd)
        context.user_data["time_end_date"] = end_date.isoformat()
        await q.edit_message_text(f"End date: {end_date.isoformat()}\nSelect END hour:", reply_markup=hour_kb("TIME_END"))
        return TIME_PICK_END_TIME
    return TIME_PICK_END_DATE


async def time_end_time_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    parts = data.split("|")
    if len(parts) == 3 and parts[1] == "H":
        context.user_data["time_end_hour"] = int(parts[2])
        await q.edit_message_text(f"End date: {context.user_data['time_end_date']}\nEnd hour: {parts[2]}\nNow select END minutes:", reply_markup=minute_kb("TIME_END"))
        return TIME_PICK_END_TIME
    if len(parts) == 3 and parts[1] == "M":
        hour = context.user_data.get("time_end_hour", 0)
        minute = int(parts[2])
        ed = parse_ymd(context.user_data["time_end_date"])
        end_dt = datetime.combine(ed, dtime(hour=hour, minute=minute))
        start_dt = datetime.fromisoformat(context.user_data["time_start_dt"])
        res = calc_time_delta(start_dt, end_dt)
        text = (
            f"🕰 *Time Difference*\n\n"
            f"From: {start_dt.isoformat()}\nTo:   {end_dt.isoformat()}\n\n"
            f"→ {res['hours']} hours, {res['minutes']} minutes, {res['seconds']} seconds\n"
            f"({res['total_seconds']} seconds total)"
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("↩ Back to menu", callback_data="MENU")]])
        await q.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
        return CHOOSING_FEATURE
    return TIME_PICK_END_TIME


# Menu back
async def menu_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text("Welcome to DayMate 📅 — choose a feature:", reply_markup=main_menu_kb())
    context.user_data.clear()
    return CHOOSING_FEATURE


# Ignore empty buttons
async def ignore_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()


# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)


# Build app and register handlers
def build_app(token: str):
    app = ApplicationBuilder().token(token).build()

    # Start / message entrypoint (shows menu)
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.ALL, start_handler))

    # Main menu choices
    app.add_handler(CallbackQueryHandler(main_menu_handler, pattern="^(age|days|time)$"))

    # Age
    app.add_handler(CallbackQueryHandler(age_date_callback, pattern="^AGEDATE"))

    # Days
    app.add_handler(CallbackQueryHandler(days_start_callback, pattern="^DAYS_START"))
    app.add_handler(CallbackQueryHandler(days_end_callback, pattern="^DAYS_END"))

    # Time
    app.add_handler(CallbackQueryHandler(time_start_date_callback, pattern="^TIME_START"))
    app.add_handler(CallbackQueryHandler(time_start_time_callback, pattern="^TIME_START\\|"))
    app.add_handler(CallbackQueryHandler(time_end_date_callback, pattern="^TIME_END"))
    app.add_handler(CallbackQueryHandler(time_end_time_callback, pattern="^TIME_END\\|"))

    # Menu navigation and ignore
    app.add_handler(CallbackQueryHandler(menu_back_callback, pattern="^MENU$"))
    app.add_handler(CallbackQueryHandler(ignore_callback, pattern="^IGNORE$"))

    app.add_error_handler(error_handler)
    return app


if __name__ == "__main__":
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.error("No TELEGRAM_TOKEN found. Add TELEGRAM_TOKEN=... to your .env file.")
        raise SystemExit("Missing TELEGRAM_TOKEN")
    app = build_app(token)
    print("DayMate 📅 bot starting (polling)...")
    app.run_polling()
