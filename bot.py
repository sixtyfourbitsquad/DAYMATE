#!/usr/bin/env python3
"""
DayMate Telegram Bot - Age, Days, and Time Calculator
A button-only interface for date and time calculations
"""

import logging
import json
import re
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, Tuple
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import configuration
from config import BOT_TOKEN, DEFAULT_TIMEZONE, get_timezone, validate_config

# In-memory session storage (ephemeral)
sessions: Dict[str, Dict[str, Any]] = {}

class DayMateBot:
    def __init__(self):
        self.timezone = get_timezone()
        
    def get_session(self, chat_id: int, message_id: int) -> Dict[str, Any]:
        """Get or create session for user"""
        key = f"{chat_id}_{message_id}"
        if key not in sessions:
            sessions[key] = {
                'timezone': self.timezone,
                'current_flow': None,
                'data': {}
            }
        return sessions[key]
    
    def update_session(self, chat_id: int, message_id: int, updates: Dict[str, Any]):
        """Update session data"""
        session = self.get_session(chat_id, message_id)
        session.update(updates)
    
    def clear_session(self, chat_id: int, message_id: int):
        """Clear session data"""
        key = f"{chat_id}_{message_id}"
        if key in sessions:
            del sessions[key]

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await self.show_main_menu(update, context)
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main menu with all calculator options"""
        keyboard = [
            [
                InlineKeyboardButton("🎂 Age Calculator", callback_data="age_calc"),
                InlineKeyboardButton("📅 Days Calculator", callback_data="days_calc")
            ],
            [
                InlineKeyboardButton("🕰 Time Calculator", callback_data="time_calc"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings")
            ],
            [
                InlineKeyboardButton("❓ Help", callback_data="help")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = (
            "🎉 Welcome to DayMate! 📅\n\n"
            "I'm your personal date and time calculator. Choose what you'd like to calculate:\n\n"
            "• 🎂 Calculate your exact age\n"
            "• 📅 Find days between two dates\n"
            "• 🕰 Convert time durations\n"
            "• ⚙️ Change timezone settings\n"
            "• ❓ Get help and examples\n\n"
            "Everything is button-based - no typing required! 🎯"
        )
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=welcome_text,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text=welcome_text,
                reply_markup=reply_markup
            )

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        chat_id = query.message.chat_id
        message_id = query.message.message_id
        
        # Update session
        self.update_session(chat_id, message_id, {'current_flow': data})
        
        if data == "age_calc":
            await self.show_age_calculator(query, context)
        elif data == "days_calc":
            await self.show_days_calculator(query, context)
        elif data == "time_calc":
            await self.show_time_calculator(query, context)
        elif data == "settings":
            await self.show_settings(query, context)
        elif data == "help":
            await self.show_help(query, context)
        elif data == "back_to_menu":
            await self.show_main_menu(update, context)
        elif data.startswith("age_"):
            await self.handle_age_callback(query, context)
        elif data.startswith("days_"):
            await self.handle_days_callback(query, context)
        elif data.startswith("time_"):
            await self.handle_time_callback(query, context)
        elif data.startswith("settings_"):
            await self.handle_settings_callback(query, context)

    async def show_age_calculator(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Show age calculator interface"""
        keyboard = [
            [
                InlineKeyboardButton("📅 Pick Date of Birth", callback_data="age_calendar"),
                InlineKeyboardButton("🔢 Enter Year/Month/Day", callback_data="age_numeric")
            ],
            [
                InlineKeyboardButton("📅 Today", callback_data="age_today"),
                InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "🎂 Age Calculator\n\n"
            "Choose how you'd like to enter your date of birth:\n\n"
            "• 📅 Use calendar picker\n"
            "• 🔢 Enter year, month, day manually\n"
            "• 📅 Use today's date"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )

    async def show_days_calculator(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Show days calculator interface"""
        keyboard = [
            [
                InlineKeyboardButton("📅 Pick Start Date", callback_data="days_start"),
                InlineKeyboardButton("📅 Pick End Date", callback_data="days_end")
            ],
            [
                InlineKeyboardButton("📅 Today", callback_data="days_today"),
                InlineKeyboardButton("📅 +7 Days", callback_data="days_plus7")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "📅 Days Calculator\n\n"
            "Calculate the difference between two dates:\n\n"
            "• 📅 Pick start and end dates\n"
            "• 📅 Use today as reference\n"
            "• 📅 Quick presets available"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )

    async def show_time_calculator(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Show time calculator interface"""
        keyboard = [
            [
                InlineKeyboardButton("⏱️ Duration to H/M/S", callback_data="time_duration"),
                InlineKeyboardButton("🔢 H/M/S to Seconds", callback_data="time_convert")
            ],
            [
                InlineKeyboardButton("⚡ Quick Presets", callback_data="time_presets"),
                InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "🕰 Time Calculator\n\n"
            "Convert time durations and formats:\n\n"
            "• ⏱️ Convert duration to hours/minutes/seconds\n"
            "• 🔢 Convert H/M/S to total seconds\n"
            "• ⚡ Use quick presets for common durations"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )

    async def show_settings(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Show settings interface"""
        keyboard = [
            [
                InlineKeyboardButton("🌏 Asia/Kolkata", callback_data="settings_tz_Asia/Kolkata"),
                InlineKeyboardButton("🌍 UTC", callback_data="settings_tz_UTC")
            ],
            [
                InlineKeyboardButton("🌎 America/New_York", callback_data="settings_tz_America/New_York"),
                InlineKeyboardButton("🌏 Asia/Tokyo", callback_data="settings_tz_Asia/Tokyo")
            ],
            [
                InlineKeyboardButton("🌍 Europe/London", callback_data="settings_tz_Europe/London"),
                InlineKeyboardButton("🌎 America/Los_Angeles", callback_data="settings_tz_America/Los_Angeles")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "⚙️ Settings\n\n"
            "Choose your timezone:\n\n"
            "Current timezone: Asia/Kolkata\n"
            "Note: Settings are temporary and reset when bot restarts."
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )

    async def show_help(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Show help information"""
        keyboard = [
            [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "❓ Help & Examples\n\n"
            "🎂 Age Calculator:\n"
            "• Select your date of birth using calendar or numeric input\n"
            "• Get exact age in years, months, weeks, and days\n"
            "• See total days and hours lived\n\n"
            "📅 Days Calculator:\n"
            "• Pick start and end dates\n"
            "• Calculate precise difference between dates\n"
            "• Get breakdown in years, months, weeks, days\n\n"
            "🕰 Time Calculator:\n"
            "• Convert durations to hours/minutes/seconds\n"
            "• Convert H/M/S to total seconds\n"
            "• Use quick presets for common durations\n\n"
            "⚙️ Settings:\n"
            "• Change timezone for calculations\n"
            "• Settings are temporary (reset on restart)\n\n"
            "All interactions are button-based - no typing required! 🎯"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )

    async def handle_age_callback(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Handle age calculator callbacks"""
        data = query.data
        chat_id = query.message.chat_id
        message_id = query.message.message_id
        session = self.get_session(chat_id, message_id)
        
        if data == "age_calendar":
            await self.show_calendar(query, context, "age")
        elif data == "age_numeric":
            session['data']['numeric_input'] = ""
            await self.show_numeric_input(query, context, "age")
        elif data == "age_today":
            await self.calculate_age(query, context, date.today())
        elif data.startswith("age_date_"):
            # Extract date from callback data
            date_str = data.replace("age_date_", "")
            try:
                dob = datetime.strptime(date_str, "%Y%m%d").date()
                await self.calculate_age(query, context, dob)
            except ValueError:
                await query.answer("Invalid date format", show_alert=True)
        elif data.startswith("age_prev_") or data.startswith("age_next_"):
            # Handle calendar navigation
            parts = data.split("_")
            year = int(parts[2])
            month = int(parts[3])
            
            if "prev" in data:
                month -= 1
                if month < 1:
                    month = 12
                    year -= 1
            else:
                month += 1
                if month > 12:
                    month = 1
                    year += 1
            
            keyboard = self.build_calendar_keyboard(year, month, "age")
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            import calendar
            month_name = calendar.month_name[month]
            text = f"📅 Select Date of Birth\n\n{month_name} {year}"
            
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup
            )
        elif data.startswith("age_num_"):
            # Handle numeric input
            digit = data.split("_")[2]
            current_input = session['data'].get('numeric_input', "")
            
            if digit == "backspace":
                current_input = current_input[:-1]
            else:
                current_input += digit
            
            session['data']['numeric_input'] = current_input
            await self.update_numeric_display(query, context, "age", current_input)
        elif data == "age_confirm":
            # Confirm numeric input
            current_input = session['data'].get('numeric_input', "")
            if len(current_input) == 8:  # YYYYMMDD format
                try:
                    dob = datetime.strptime(current_input, "%Y%m%d").date()
                    await self.calculate_age(query, context, dob)
                except ValueError:
                    await query.answer("Invalid date format", show_alert=True)
            else:
                await query.answer("Please enter date in YYYYMMDD format", show_alert=True)
        elif data == "age_back":
            await self.show_age_calculator(query, context)

    async def handle_days_callback(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Handle days calculator callbacks"""
        data = query.data
        chat_id = query.message.chat_id
        message_id = query.message.message_id
        session = self.get_session(chat_id, message_id)
        
        if data == "days_start":
            session['data']['selecting'] = 'start'
            await self.show_calendar(query, context, "days")
        elif data == "days_end":
            session['data']['selecting'] = 'end'
            await self.show_calendar(query, context, "days")
        elif data == "days_today":
            if session['data'].get('selecting') == 'start':
                session['data']['start_date'] = date.today()
                session['data']['selecting'] = 'end'
                await self.show_calendar(query, context, "days")
            else:
                session['data']['end_date'] = date.today()
                await self.calculate_days_difference(query, context)
        elif data == "days_plus7":
            if session['data'].get('selecting') == 'start':
                session['data']['start_date'] = date.today()
                session['data']['selecting'] = 'end'
                await self.show_calendar(query, context, "days")
            else:
                session['data']['end_date'] = date.today() + timedelta(days=7)
                await self.calculate_days_difference(query, context)
        elif data.startswith("days_date_"):
            date_str = data.replace("days_date_", "")
            try:
                selected_date = datetime.strptime(date_str, "%Y%m%d").date()
                if session['data'].get('selecting') == 'start':
                    session['data']['start_date'] = selected_date
                    session['data']['selecting'] = 'end'
                    await self.show_calendar(query, context, "days")
                else:
                    session['data']['end_date'] = selected_date
                    await self.calculate_days_difference(query, context)
            except ValueError:
                await query.answer("Invalid date format", show_alert=True)
        elif data.startswith("days_prev_") or data.startswith("days_next_"):
            # Handle calendar navigation
            parts = data.split("_")
            year = int(parts[2])
            month = int(parts[3])
            
            if "prev" in data:
                month -= 1
                if month < 1:
                    month = 12
                    year -= 1
            else:
                month += 1
                if month > 12:
                    month = 1
                    year += 1
            
            keyboard = self.build_calendar_keyboard(year, month, "days")
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            import calendar
            month_name = calendar.month_name[month]
            selecting = session['data'].get('selecting', 'start')
            text = f"📅 Select {'Start' if selecting == 'start' else 'End'} Date\n\n{month_name} {year}"
            
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup
            )
        elif data == "days_swap":
            # Swap start and end dates
            start = session['data'].get('start_date')
            end = session['data'].get('end_date')
            if start and end:
                session['data']['start_date'] = end
                session['data']['end_date'] = start
                await self.calculate_days_difference(query, context)

    async def handle_time_callback(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Handle time calculator callbacks"""
        data = query.data
        
        if data == "time_duration":
            await self.show_duration_input(query, context)
        elif data == "time_convert":
            await self.show_time_convert_input(query, context)
        elif data == "time_presets":
            await self.show_time_presets(query, context)
        elif data.startswith("time_dur_"):
            # Handle duration calculations
            if data == "time_dur_custom":
                await self.show_custom_duration_input(query, context)
            else:
                seconds = int(data.split("_")[2])
                await self.handle_time_duration_callback(query, context, seconds)
        elif data.startswith("time_preset_"):
            # Handle time presets
            seconds = int(data.split("_")[2])
            await self.handle_time_duration_callback(query, context, seconds)
        elif data.startswith("time_custom_"):
            # Handle custom time input
            if data == "time_custom_hours":
                await self.show_custom_time_input(query, context, "hours")
            elif data == "time_custom_minutes":
                await self.show_custom_time_input(query, context, "minutes")
            elif data == "time_custom_seconds":
                await self.show_custom_time_input(query, context, "seconds")
            elif data.startswith("time_custom_num_"):
                # Handle numeric input for custom time
                chat_id = query.message.chat_id
                message_id = query.message.message_id
                session = self.get_session(chat_id, message_id)
                
                digit = data.split("_")[3]
                current_input = session['data'].get('custom_time_input', "")
                
                if digit == "backspace":
                    current_input = current_input[:-1]
                else:
                    current_input += digit
                
                session['data']['custom_time_input'] = current_input
                await self.update_custom_time_display(query, context, current_input)
            elif data == "time_custom_confirm":
                # Confirm custom time input
                chat_id = query.message.chat_id
                message_id = query.message.message_id
                session = self.get_session(chat_id, message_id)
                
                current_input = session['data'].get('custom_time_input', "")
                time_type = session['data'].get('custom_time_type', 'seconds')
                
                try:
                    value = int(current_input)
                    if time_type == "hours":
                        total_seconds = value * 3600
                    elif time_type == "minutes":
                        total_seconds = value * 60
                    else:
                        total_seconds = value
                    
                    await self.handle_time_duration_callback(query, context, total_seconds)
                except ValueError:
                    await query.answer("Please enter a valid number", show_alert=True)

    async def handle_settings_callback(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Handle settings callbacks"""
        data = query.data
        
        if data.startswith("settings_tz_"):
            timezone_str = data.replace("settings_tz_", "")
            try:
                self.timezone = ZoneInfo(timezone_str)
                await query.answer(f"Timezone changed to {timezone_str}")
                await self.show_settings(query, context)
            except Exception as e:
                await query.answer(f"Invalid timezone: {timezone_str}", show_alert=True)

    async def show_calendar(self, query, context: ContextTypes.DEFAULT_TYPE, flow_type: str):
        """Show calendar widget"""
        now = datetime.now(self.timezone)
        year = now.year
        month = now.month
        
        keyboard = self.build_calendar_keyboard(year, month, flow_type)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        month_name = now.strftime("%B %Y")
        text = f"📅 Select Date\n\n{month_name}"
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )

    def build_calendar_keyboard(self, year: int, month: int, flow_type: str) -> list:
        """Build calendar keyboard"""
        import calendar
        
        # Header with month navigation
        keyboard = [
            [
                InlineKeyboardButton("<<", callback_data=f"{flow_type}_prev_{year}_{month}"),
                InlineKeyboardButton(f"{calendar.month_name[month]} {year}", callback_data="noop"),
                InlineKeyboardButton(">>", callback_data=f"{flow_type}_next_{year}_{month}")
            ]
        ]
        
        # Weekday headers
        keyboard.append([
            InlineKeyboardButton("Mo", callback_data="noop"),
            InlineKeyboardButton("Tu", callback_data="noop"),
            InlineKeyboardButton("We", callback_data="noop"),
            InlineKeyboardButton("Th", callback_data="noop"),
            InlineKeyboardButton("Fr", callback_data="noop"),
            InlineKeyboardButton("Sa", callback_data="noop"),
            InlineKeyboardButton("Su", callback_data="noop")
        ])
        
        # Days
        cal = calendar.monthcalendar(year, month)
        for week in cal:
            row = []
            for day in week:
                if day == 0:
                    row.append(InlineKeyboardButton(" ", callback_data="noop"))
                else:
                    row.append(InlineKeyboardButton(
                        str(day), 
                        callback_data=f"{flow_type}_date_{year:04d}{month:02d}{day:02d}"
                    ))
            keyboard.append(row)
        
        # Footer
        keyboard.append([
            InlineKeyboardButton("Today", callback_data=f"{flow_type}_today"),
            InlineKeyboardButton("Back", callback_data="back_to_menu")
        ])
        
        return keyboard

    async def show_numeric_input(self, query, context: ContextTypes.DEFAULT_TYPE, flow_type: str):
        """Show numeric input interface"""
        keyboard = [
            [
                InlineKeyboardButton("1", callback_data=f"{flow_type}_num_1"),
                InlineKeyboardButton("2", callback_data=f"{flow_type}_num_2"),
                InlineKeyboardButton("3", callback_data=f"{flow_type}_num_3")
            ],
            [
                InlineKeyboardButton("4", callback_data=f"{flow_type}_num_4"),
                InlineKeyboardButton("5", callback_data=f"{flow_type}_num_5"),
                InlineKeyboardButton("6", callback_data=f"{flow_type}_num_6")
            ],
            [
                InlineKeyboardButton("7", callback_data=f"{flow_type}_num_7"),
                InlineKeyboardButton("8", callback_data=f"{flow_type}_num_8"),
                InlineKeyboardButton("9", callback_data=f"{flow_type}_num_9")
            ],
            [
                InlineKeyboardButton("0", callback_data=f"{flow_type}_num_0"),
                InlineKeyboardButton("⌫", callback_data=f"{flow_type}_backspace"),
                InlineKeyboardButton("OK", callback_data=f"{flow_type}_confirm")
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data=f"{flow_type}_back")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            f"🔢 Enter Date\n\n"
            f"Format: YYYY-MM-DD\n"
            f"Current input: \n\n"
            f"Example: 1992-07-15"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )

    async def calculate_age(self, query, context: ContextTypes.DEFAULT_TYPE, dob: date):
        """Calculate and display age"""
        now = datetime.now(self.timezone).date()
        
        if dob > now:
            await query.answer("Date of birth cannot be in the future!", show_alert=True)
            return
        
        # Calculate age using relativedelta for accuracy
        age = relativedelta(now, dob)
        
        # Calculate total days
        total_days = (now - dob).days
        total_weeks = total_days / 7
        total_hours = total_days * 24
        
        # Format result
        result_text = (
            f"🎂 Age Result for {dob.strftime('%Y-%m-%d')}\n"
            f"(Reference: {now.strftime('%Y-%m-%d')}, {self.timezone})\n\n"
            f"• {age.years} years, {age.months} months, {age.days} days\n"
            f"• Weeks lived: {total_weeks:.0f} weeks (approx)\n"
            f"• Total days: {total_days:,} days\n"
            f"• Total hours: {total_hours:,} hours"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🔁 New Age Calculation", callback_data="age_calc"),
                InlineKeyboardButton("⬅️ Main Menu", callback_data="back_to_menu")
            ],
            [
                InlineKeyboardButton("📌 Share", callback_data=f"share_age_{dob}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=result_text,
            reply_markup=reply_markup
        )

    async def calculate_days_difference(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Calculate days difference between two dates"""
        chat_id = query.message.chat_id
        message_id = query.message.message_id
        session = self.get_session(chat_id, message_id)
        
        start_date = session['data'].get('start_date')
        end_date = session['data'].get('end_date')
        
        if not start_date or not end_date:
            await query.answer("Please select both start and end dates", show_alert=True)
            return
        
        # Calculate difference
        if end_date < start_date:
            # Swap dates for negative difference
            start_date, end_date = end_date, start_date
            swapped = True
        else:
            swapped = False
        
        diff = relativedelta(end_date, start_date)
        total_days = (end_date - start_date).days
        total_weeks = total_days / 7
        
        # Format result
        if swapped:
            result_text = (
                f"📅 From {end_date.strftime('%Y-%m-%d')} to {start_date.strftime('%Y-%m-%d')}\n\n"
                f"• {diff.years} years, {diff.months} months, {diff.days} days\n"
                f"• Total days: {total_days:,}\n"
                f"• Total weeks: {total_weeks:.1f}\n\n"
                f"Note: Dates were swapped (end < start)"
            )
        else:
            result_text = (
                f"📅 From {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n\n"
                f"• {diff.years} years, {diff.months} months, {diff.days} days\n"
                f"• Total days: {total_days:,}\n"
                f"• Total weeks: {total_weeks:.1f}"
            )
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Swap Dates", callback_data="days_swap"),
                InlineKeyboardButton("🔁 New Calculation", callback_data="days_calc")
            ],
            [
                InlineKeyboardButton("⬅️ Main Menu", callback_data="back_to_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=result_text,
            reply_markup=reply_markup
        )

    async def show_duration_input(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Show duration input interface"""
        keyboard = [
            [
                InlineKeyboardButton("1 hr", callback_data="time_dur_3600"),
                InlineKeyboardButton("30 min", callback_data="time_dur_1800"),
                InlineKeyboardButton("90 min", callback_data="time_dur_5400")
            ],
            [
                InlineKeyboardButton("1 day", callback_data="time_dur_86400"),
                InlineKeyboardButton("Custom", callback_data="time_dur_custom"),
                InlineKeyboardButton("⬅️ Back", callback_data="time_calc")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "⏱️ Duration to Hours/Minutes/Seconds\n\n"
            "Select a duration or choose custom input:"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )

    async def show_time_presets(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Show time presets"""
        keyboard = [
            [
                InlineKeyboardButton("1 min", callback_data="time_preset_60"),
                InlineKeyboardButton("5 min", callback_data="time_preset_300"),
                InlineKeyboardButton("15 min", callback_data="time_preset_900")
            ],
            [
                InlineKeyboardButton("1 hour", callback_data="time_preset_3600"),
                InlineKeyboardButton("2 hours", callback_data="time_preset_7200"),
                InlineKeyboardButton("1 day", callback_data="time_preset_86400")
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="time_calc")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "⚡ Quick Time Presets\n\n"
            "Select a common duration:"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )

    def format_duration(self, total_seconds: int) -> str:
        """Format duration in seconds to H/M/S"""
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"{hours} hours, {minutes} minutes, {seconds} seconds"

    async def handle_time_duration_callback(self, query, context: ContextTypes.DEFAULT_TYPE, seconds: int):
        """Handle time duration calculation"""
        formatted = self.format_duration(seconds)
        
        result_text = (
            f"🕰 Convert {seconds} seconds:\n\n"
            f"• {formatted}\n"
            f"• Total seconds: {seconds:,}"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🔁 New Time Calculation", callback_data="time_calc"),
                InlineKeyboardButton("⬅️ Main Menu", callback_data="back_to_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=result_text,
            reply_markup=reply_markup
        )

    async def update_numeric_display(self, query, context: ContextTypes.DEFAULT_TYPE, flow_type: str, current_input: str):
        """Update numeric input display"""
        keyboard = [
            [
                InlineKeyboardButton("1", callback_data=f"{flow_type}_num_1"),
                InlineKeyboardButton("2", callback_data=f"{flow_type}_num_2"),
                InlineKeyboardButton("3", callback_data=f"{flow_type}_num_3")
            ],
            [
                InlineKeyboardButton("4", callback_data=f"{flow_type}_num_4"),
                InlineKeyboardButton("5", callback_data=f"{flow_type}_num_5"),
                InlineKeyboardButton("6", callback_data=f"{flow_type}_num_6")
            ],
            [
                InlineKeyboardButton("7", callback_data=f"{flow_type}_num_7"),
                InlineKeyboardButton("8", callback_data=f"{flow_type}_num_8"),
                InlineKeyboardButton("9", callback_data=f"{flow_type}_num_9")
            ],
            [
                InlineKeyboardButton("0", callback_data=f"{flow_type}_num_0"),
                InlineKeyboardButton("⌫", callback_data=f"{flow_type}_backspace"),
                InlineKeyboardButton("OK", callback_data=f"{flow_type}_confirm")
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data=f"{flow_type}_back")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Format input display
        display_input = current_input
        if len(current_input) > 8:
            display_input = current_input[-8:]
        
        # Add separators for date format
        if len(display_input) >= 4:
            formatted = f"{display_input[:4]}-{display_input[4:6]}-{display_input[6:8]}" if len(display_input) >= 6 else f"{display_input[:4]}-{display_input[4:]}"
        else:
            formatted = display_input
        
        text = (
            f"🔢 Enter Date of Birth\n\n"
            f"Format: YYYY-MM-DD\n"
            f"Current input: {formatted}\n\n"
            f"Example: 1992-07-15"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )

    async def show_custom_duration_input(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Show custom duration input options"""
        keyboard = [
            [
                InlineKeyboardButton("Hours", callback_data="time_custom_hours"),
                InlineKeyboardButton("Minutes", callback_data="time_custom_minutes")
            ],
            [
                InlineKeyboardButton("Seconds", callback_data="time_custom_seconds"),
                InlineKeyboardButton("⬅️ Back", callback_data="time_duration")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "⏱️ Custom Duration Input\n\n"
            "Choose the unit for your custom duration:"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )

    async def show_custom_time_input(self, query, context: ContextTypes.DEFAULT_TYPE, time_type: str):
        """Show custom time input interface"""
        chat_id = query.message.chat_id
        message_id = query.message.message_id
        session = self.get_session(chat_id, message_id)
        
        session['data']['custom_time_type'] = time_type
        session['data']['custom_time_input'] = ""
        
        keyboard = [
            [
                InlineKeyboardButton("1", callback_data="time_custom_num_1"),
                InlineKeyboardButton("2", callback_data="time_custom_num_2"),
                InlineKeyboardButton("3", callback_data="time_custom_num_3")
            ],
            [
                InlineKeyboardButton("4", callback_data="time_custom_num_4"),
                InlineKeyboardButton("5", callback_data="time_custom_num_5"),
                InlineKeyboardButton("6", callback_data="time_custom_num_6")
            ],
            [
                InlineKeyboardButton("7", callback_data="time_custom_num_7"),
                InlineKeyboardButton("8", callback_data="time_custom_num_8"),
                InlineKeyboardButton("9", callback_data="time_custom_num_9")
            ],
            [
                InlineKeyboardButton("0", callback_data="time_custom_num_0"),
                InlineKeyboardButton("⌫", callback_data="time_custom_num_backspace"),
                InlineKeyboardButton("OK", callback_data="time_custom_confirm")
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="time_dur_custom")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            f"🔢 Enter {time_type.title()}\n\n"
            f"Current input: \n\n"
            f"Enter the number of {time_type}:"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )

    async def update_custom_time_display(self, query, context: ContextTypes.DEFAULT_TYPE, current_input: str):
        """Update custom time input display"""
        chat_id = query.message.chat_id
        message_id = query.message.message_id
        session = self.get_session(chat_id, message_id)
        
        time_type = session['data'].get('custom_time_type', 'seconds')
        
        keyboard = [
            [
                InlineKeyboardButton("1", callback_data="time_custom_num_1"),
                InlineKeyboardButton("2", callback_data="time_custom_num_2"),
                InlineKeyboardButton("3", callback_data="time_custom_num_3")
            ],
            [
                InlineKeyboardButton("4", callback_data="time_custom_num_4"),
                InlineKeyboardButton("5", callback_data="time_custom_num_5"),
                InlineKeyboardButton("6", callback_data="time_custom_num_6")
            ],
            [
                InlineKeyboardButton("7", callback_data="time_custom_num_7"),
                InlineKeyboardButton("8", callback_data="time_custom_num_8"),
                InlineKeyboardButton("9", callback_data="time_custom_num_9")
            ],
            [
                InlineKeyboardButton("0", callback_data="time_custom_num_0"),
                InlineKeyboardButton("⌫", callback_data="time_custom_num_backspace"),
                InlineKeyboardButton("OK", callback_data="time_custom_confirm")
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data="time_dur_custom")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            f"🔢 Enter {time_type.title()}\n\n"
            f"Current input: {current_input}\n\n"
            f"Enter the number of {time_type}:"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )

    async def show_time_convert_input(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Show time convert input interface"""
        keyboard = [
            [
                InlineKeyboardButton("Hours", callback_data="time_convert_hours"),
                InlineKeyboardButton("Minutes", callback_data="time_convert_minutes")
            ],
            [
                InlineKeyboardButton("Seconds", callback_data="time_convert_seconds"),
                InlineKeyboardButton("⬅️ Back", callback_data="time_calc")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "🔢 H/M/S to Total Seconds\n\n"
            "Choose what you want to convert to total seconds:"
        )
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )

    async def handle_noop_callback(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Handle no-op callbacks (like weekday headers)"""
        await query.answer()

def main():
    """Main function to run the bot"""
    # Validate configuration
    config_errors = validate_config()
    if config_errors:
        print("Configuration errors found:")
        for error in config_errors:
            print(f"  - {error}")
        print("\nPlease fix the configuration before running the bot.")
        return
    
    # Create bot instance
    bot = DayMateBot()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CallbackQueryHandler(bot.handle_callback_query))
    
    # Add no-op handler for non-functional buttons
    application.add_handler(CallbackQueryHandler(bot.handle_noop_callback, pattern="^noop$"))
    
    # Start the bot
    print("Starting DayMate bot...")
    print(f"Default timezone: {DEFAULT_TIMEZONE}")
    print("Press Ctrl+C to stop")
    application.run_polling()

if __name__ == '__main__':
    main()
