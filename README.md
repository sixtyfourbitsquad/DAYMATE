# DayMate 📅 - Telegram Bot

A comprehensive Telegram bot for date and time calculations with a button-only interface. Calculate ages, date differences, and time conversions without typing a single character!

## Features

### 🎂 Age Calculator
- Calculate exact age in years, months, weeks, and days
- Interactive calendar picker for date of birth
- Numeric keypad for manual date entry
- Quick "Today" option
- Detailed breakdown including total days and hours lived

### 📅 Days Calculator
- Calculate difference between any two dates
- Interactive calendar for both start and end dates
- Quick presets (Today, +7 days, etc.)
- Swap dates functionality
- Precise breakdown in years, months, weeks, and days

### 🕰 Time Calculator
- Convert durations to hours/minutes/seconds
- Convert H/M/S to total seconds
- Quick presets for common durations
- Custom numeric input for any duration
- Support for hours, minutes, and seconds

### ⚙️ Settings
- Change timezone (default: Asia/Kolkata)
- Multiple timezone options available
- Settings are session-based (reset on restart)

### ❓ Help
- Comprehensive help and examples
- Button-only interaction guide
- Feature explanations

## Key Features

- **100% Button-Based Interface**: No typing required
- **Stateless Operation**: No persistent data storage
- **Timezone Support**: Configurable timezone (default: Asia/Kolkata)
- **Mobile-Friendly**: Optimized for mobile Telegram clients
- **Accurate Calculations**: Uses `relativedelta` for precise date calculations
- **Session Management**: Ephemeral in-memory sessions

## Installation

### Prerequisites
- Python 3.11 or higher
- Telegram Bot Token (get from [@BotFather](https://t.me/botfather))

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/sixtyfourbitsquad/DAYMATE.git
   cd DAYMATE
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the bot**
   - Open `bot.py`
   - Replace `YOUR_BOT_TOKEN_HERE` with your actual bot token
   - Optionally modify the default timezone in the `DEFAULT_TIMEZONE` variable

4. **Run the bot**
   ```bash
   python bot.py
   ```

## Configuration

### Bot Token
Get your bot token from [@BotFather](https://t.me/botfather) and replace it in `bot.py`:

```python
BOT_TOKEN = "YOUR_ACTUAL_BOT_TOKEN_HERE"
```

### Default Timezone
Change the default timezone by modifying:

```python
DEFAULT_TIMEZONE = "Asia/Kolkata"  # Change to your preferred timezone
```

## Usage

1. Start a conversation with your bot
2. Use `/start` command or send any message
3. Navigate using the button interface:
   - 🎂 **Age Calculator**: Calculate your exact age
   - 📅 **Days Calculator**: Find days between two dates
   - 🕰 **Time Calculator**: Convert time durations
   - ⚙️ **Settings**: Change timezone
   - ❓ **Help**: Get help and examples

## Deployment

### Heroku
1. Create a `Procfile`:
   ```
   worker: python bot.py
   ```

2. Deploy to Heroku:
   ```bash
   git add .
   git commit -m "Initial commit"
   git push heroku main
   ```

3. Set environment variables in Heroku dashboard:
   - `BOT_TOKEN`: Your Telegram bot token

### Railway
1. Connect your GitHub repository to Railway
2. Set environment variables:
   - `BOT_TOKEN`: Your Telegram bot token
3. Deploy automatically

### Google Cloud Run
1. Create a `Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["python", "bot.py"]
   ```

2. Deploy to Cloud Run with environment variables

### VPS Deployment
1. Install Python 3.11+ and pip
2. Clone the repository
3. Install dependencies: `pip install -r requirements.txt`
4. Run with process manager (PM2, systemd, etc.):
   ```bash
   python bot.py
   ```

## Architecture

### Session Management
- Uses ephemeral in-memory sessions keyed by `(chat_id, message_id)`
- Sessions are automatically cleaned up
- No persistent data storage (stateless design)

### Callback Data Schema
- Compact callback data to respect Telegram's 64-byte limit
- Examples:
  - `age_date_20250908`: Age calculation with date
  - `days_start`: Days calculator start date selection
  - `time_dur_3600`: Time duration preset (1 hour)

### Date Handling
- Uses `zoneinfo` for timezone handling (Python 3.9+)
- `relativedelta` for accurate age calculations
- Proper leap year and month boundary handling

## Testing

### Manual Testing Checklist
- [ ] All buttons reachable by keyboard-only navigation
- [ ] Calendar navigation works across year boundaries
- [ ] Numeric keypad entries validate correctly
- [ ] Timezone changes work properly
- [ ] No data persists across bot restarts
- [ ] UI includes Back/Cancel/Main Menu at every step
- [ ] Test on mobile and desktop Telegram clients

### Unit Tests
Run the included unit tests:
```bash
python test_bot.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

For issues and questions:
- Create an issue on GitHub
- Contact the development team

## Changelog

### v1.0.0
- Initial release
- Age calculator with calendar and numeric input
- Days calculator with date difference
- Time calculator with duration conversions
- Timezone settings
- Button-only interface
- Stateless operation

---

**Note**: This bot is designed to be stateless and does not store any persistent data. All sessions are temporary and will be lost when the bot restarts.
