# Telegram Bot Setup Guide

## 🤖 **Step 1: Create the Bot**

1. **Open Telegram** and search for `@BotFather`
2. **Send `/newbot`** command
3. **Follow the instructions:**
   - Choose a name: `FXSentinel Alerts`
   - Choose a username: `FXSentinelAlertsBot` (must end in 'bot')
4. **Copy the bot token** (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

## 🔧 **Step 2: Configure Environment**

Add the bot token to your `.env` file:

```bash
# Add to .env file
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_BOT_USERNAME=@FXSentinelAlertsBot
```

## 🚀 **Step 3: Run the Bot**

### **Option A: Simple Bot (Recommended for testing)**
```bash
cd backend
python3 working_bot.py
```

### **Option B: Webhook Bot (For production)**
```bash
cd backend
python3 bot_webhook.py
```

### **Option C: Integrated with Flask (Current setup)**
The bot endpoints are already integrated into the main Flask app, so when you run:
```bash
cd backend
python3 app.py
```

The bot setup endpoints are available at:
- `POST /api/telegram/setup`
- `POST /api/telegram/verify`

## 🧪 **Step 4: Test the Bot**

1. **Start the backend server:**
   ```bash
   cd backend
   python3 app.py
   ```

2. **Test the bot setup:**
   ```bash
   python3 test_alerts_security.py
   ```

3. **Test manually:**
   - Go to your bot: `https://t.me/FXSentinelAlertsBot`
   - Send `/start`
   - You should get an access denied message (because you're not authenticated)

## 🔒 **Security Features**

The bot now has these security features:

- ✅ **Only authenticated dashboard users** can access the bot
- ✅ **Access verification** via backend API
- ✅ **Unique setup tokens** for each user
- ✅ **Proper error messages** for unauthorized users

## 📱 **User Flow**

1. **User logs into dashboard**
2. **User goes to Alerts tab**
3. **User clicks "Connect Telegram Bot"**
4. **System generates unique bot link**
5. **User clicks link and sends `/start`**
6. **Bot verifies user has dashboard access**
7. **If authorized, bot connects and sends welcome message**
8. **If unauthorized, bot sends access denied message**

## 🐛 **Troubleshooting**

### **Bot not responding:**
- Check if bot token is correct
- Make sure bot is running
- Check server logs for errors

### **Access denied for valid users:**
- Check if backend server is running
- Verify user authentication is working
- Check Firebase configuration

### **Bot setup not working:**
- Verify bot token in `.env`
- Check if bot username matches
- Test API endpoints manually

## 🎯 **Next Steps**

1. **Create the bot** via @BotFather
2. **Add token to `.env`**
3. **Test the security implementation**
4. **Deploy to production**

The bot is ready to run once you have the token from @BotFather!
