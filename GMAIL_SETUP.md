# Gmail IMAP Setup Guide

## Step-by-Step Instructions for Gmail

### 1. Enable IMAP in Gmail Settings

1. **Go to Gmail.com** and sign in to your account
2. **Click the Settings gear icon** (⚙️) in the top right
3. **Select "See all settings"**
4. **Go to the "Forwarding and POP/IMAP" tab**
5. **Under "IMAP access":**
   - ✅ **Enable IMAP**
6. **Click "Save Changes"**

### 2. Generate App Password (Required for Gmail)

1. **Go to:** https://myaccount.google.com/security
2. **Sign in** with your Google account
3. **Navigate to:** Security → 2-Step Verification
4. **Make sure 2-Step Verification is ON** (required for app passwords)
5. **Go to:** Security → App passwords
6. **Select app:** "Mail"
7. **Select device:** "Other (custom name)"
8. **Enter name:** "Email Parser App"
9. **Copy the generated 16-character password** (you'll need this!)

### 3. Update Your Application

Use your Gmail address and the app password in the configuration:

- **Email:** your-email@gmail.com
- **Password:** The 16-character app password (not your regular password)

### 4. Test the Connection

1. **Go to:** http://localhost:8000/config
2. **Enter your Gmail credentials**
3. **Test the connection**

## Gmail IMAP Settings

- **Server:** imap.gmail.com
- **Port:** 993
- **Encryption:** SSL/TLS
- **Authentication:** App Password (not regular password)

## Troubleshooting Gmail

### Common Issues:

1. **"Authentication failed"** 
   - ✅ Use app password, not regular password
   - ✅ Make sure 2-Step Verification is enabled

2. **"IMAP not enabled"**
   - ✅ Enable IMAP in Gmail settings

3. **"Less secure app access"**
   - ✅ Gmail no longer supports this - use app passwords instead

### Why App Passwords?

Gmail requires app-specific passwords for security when using IMAP with third-party applications. This is more secure than using your regular password.

## Alternative: Use OAuth2 (Advanced)

For production applications, consider using OAuth2 instead of app passwords for better security and user experience.

## Quick Test

1. **Enable IMAP** in Gmail settings
2. **Enable 2-Step Verification** 
3. **Generate App Password**
4. **Test connection** at http://localhost:8000/config

That's it! Gmail is much simpler than Outlook! 🎉
