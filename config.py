#!/usr/bin/env python3
"""
Configuration file for DayMate Telegram Bot
"""

import os
from zoneinfo import ZoneInfo

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
DEFAULT_TIMEZONE = os.getenv('DEFAULT_TIMEZONE', 'Asia/Kolkata')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Bot Settings
MAX_SESSION_SIZE = 1000  # Maximum number of sessions to keep in memory
SESSION_TIMEOUT = 3600   # Session timeout in seconds (1 hour)

# Supported Timezones
SUPPORTED_TIMEZONES = [
    'Asia/Kolkata',
    'UTC',
    'America/New_York',
    'Asia/Tokyo',
    'Europe/London',
    'America/Los_Angeles',
    'Europe/Paris',
    'Asia/Shanghai',
    'Australia/Sydney',
    'America/Chicago'
]

# Quick Time Presets (in seconds)
TIME_PRESETS = {
    '1 min': 60,
    '5 min': 300,
    '15 min': 900,
    '30 min': 1800,
    '1 hour': 3600,
    '2 hours': 7200,
    '6 hours': 21600,
    '12 hours': 43200,
    '1 day': 86400,
    '1 week': 604800
}

# Calendar Settings
CALENDAR_MONTHS_AHEAD = 12  # How many months ahead to show in calendar
CALENDAR_MONTHS_BEHIND = 12  # How many months behind to show in calendar

# Validation Settings
MAX_AGE_YEARS = 150  # Maximum age to allow
MIN_BIRTH_YEAR = 1900  # Minimum birth year to allow
MAX_FUTURE_DAYS = 365  # Maximum days in future for date calculations

def get_timezone():
    """Get the configured timezone"""
    try:
        return ZoneInfo(DEFAULT_TIMEZONE)
    except Exception:
        # Fallback to UTC if timezone is invalid
        return ZoneInfo('UTC')

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    if not BOT_TOKEN or BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        errors.append("BOT_TOKEN is not set or is using default value")
    
    try:
        get_timezone()
    except Exception as e:
        errors.append(f"Invalid timezone: {DEFAULT_TIMEZONE} - {e}")
    
    if MAX_SESSION_SIZE <= 0:
        errors.append("MAX_SESSION_SIZE must be positive")
    
    if SESSION_TIMEOUT <= 0:
        errors.append("SESSION_TIMEOUT must be positive")
    
    return errors

if __name__ == '__main__':
    # Validate configuration when run directly
    errors = validate_config()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid!")
