# anonxconnect_bot
# Anonymous Chat Bot 🤖

Telegram anonymous chat bot with partner matching system. Chat with strangers worldwide while maintaining your privacy.

## Features
- 🔒 Anonymous random chat
- ⭐ Partner rating system
- 🎁 Daily bonuses
- ⚙️ Profile customization
- 🛡️ Reporting system
- 🌐 Multi-language support

## Deployment Instructions

### 1. Get Your Bot Token
- Create a new bot via [@BotFather](https://t.me/BotFather) on Telegram
- Copy the token you receive (format: `1234567890:ABCDefghIJKlmnoPQRsTUVwxyZ`)

### 2. Prepare for Deployment
1. Fork this repository
2. Create account on [Railway.app](https://railway.app)

### 3. Set Environment Variables
On Railway.app, go to your project → Settings → Variables and add:

| Variable Name      | Value Description                     | Example Value              |
|--------------------|---------------------------------------|----------------------------|
| `TELEGRAM_TOKEN`   | Your bot token from @BotFather        | `8117045817:AAEI...wNUw`   |
| `ADMIN_USERNAME`   | Your Telegram username (with @)       | `@mysteryman02`            |

### 4. Deploy to Railway
1. Click "New Project" on Railway
2. Select "Deploy from GitHub repo"
3. Choose your forked repository
4. Railway will automatically deploy your bot

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

## Bot Commands
- `/start` - Begin chat journey
- `/next` - Find new partner
- `/stop` - End current chat
- `/menu` - Access main menu
- `/bonus` - Get daily reward
- `/profile` - View your profile
- `/premium` - VIP benefits info
- `/rules` - Community guidelines
- `/complaint` - Report behavior
- `/language` - Set language
- `/help` - Usage instructions

## Configuration Notes
- The bot will automatically create a SQLite database
- For production use, consider using PostgreSQL by setting `DATABASE_URL`
- Daily bonus resets every 24 hours

## Support
For assistance, contact the bot developer: [@mysteryman02](https://t.me/mysteryman02)
