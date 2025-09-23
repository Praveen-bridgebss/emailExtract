# Gmail Email Parser

A simple and beautiful FastAPI application to connect to your Gmail account and view all emails in a table format.

## Features

- 📧 **Gmail-only support** - Optimized for Gmail accounts
- 🎨 **Beautiful UI** - Modern, responsive design
- 🔒 **Secure connection** - Supports both regular and app passwords
- 📊 **Email table** - View all emails with subject, sender, date, and preview
- ⚡ **Fast performance** - Quick email retrieval and display
- 🔄 **Auto-refresh** - Automatically refreshes email list

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the application:**
   ```bash
   python main.py
   ```

3. **Open your browser:**
   ```
   http://localhost:8000
   ```

## Gmail Setup

### Option 1: Regular Password (Try this first)
1. **Enable IMAP** in Gmail settings
2. **Use your regular Gmail password**
3. **The app will try both methods automatically**

### Option 2: App Password (If Option 1 fails)
1. **Go to:** https://myaccount.google.com/security
2. **Enable 2-Step Verification** (required)
3. **Generate App Password** for "Mail"
4. **Use the 16-character app password**

## Usage

1. **Configure Gmail:** Go to `/config` and enter your credentials
2. **View Emails:** Go to `/emails` to see all your emails in a table
3. **API Access:** Use `/api/emails` for JSON data

## Project Structure

```
├── main.py              # FastAPI application
├── email_service.py     # Gmail IMAP service
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── GMAIL_SETUP.md      # Detailed Gmail setup guide
└── templates/          # HTML templates
    ├── index.html       # Home page
    ├── config.html      # Gmail configuration
    └── emails.html      # Email table display
```

## API Endpoints

- `GET /` - Home page
- `GET /config` - Gmail configuration page
- `GET /emails` - Email table display
- `GET /api/emails` - JSON API for emails
- `POST /test-connection` - Test Gmail connection

## Security

- Uses secure SSL connections
- Supports Gmail's app password system
- No credentials stored permanently
- Automatic connection cleanup

## Troubleshooting

### Common Issues:
- **"Authentication failed"** → Try app password instead
- **"IMAP not enabled"** → Enable IMAP in Gmail settings
- **"Connection refused"** → Check firewall settings

### Gmail Requirements:
- IMAP must be enabled in Gmail settings
- 2FA required for app passwords
- Regular password works if 2FA is disabled

## License

MIT License - Feel free to use and modify!