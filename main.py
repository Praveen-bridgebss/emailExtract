from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from email_service import EmailService
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Gmail Email Parser")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Gmail credentials (will be overridden by user input)
EMAIL_ADDRESS = "your-email@gmail.com"
EMAIL_PASSWORD = "your-password"

# Pydantic model for request body
class EmailCredentials(BaseModel):
    email: str
    password: str

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """Configuration page for email settings"""
    return templates.TemplateResponse("config.html", {"request": request})

@app.post("/test-connection")
async def test_connection(credentials: EmailCredentials):
    """Test email connection with provided credentials"""
    try:
        print(f"Testing connection with: {credentials.email}")
        email_service = EmailService(credentials.email, credentials.password)
        
        # Test connection with improved validation
        if not email_service.test_connection():
            return {
                "success": False,
                "error": "Failed to connect to Gmail",
                "message": "Please check your Gmail credentials and IMAP settings."
            }
        
        # Test email retrieval
        emails = email_service.get_all_emails(limit=5)  # Test with just 5 emails
        
        return {
            "success": True,
            "email_count": len(emails),
            "message": f"Successfully connected! Found {len(emails)} emails."
        }
    except Exception as e:
        print(f"Connection test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Connection failed. Please check your credentials and try again."
        }

@app.get("/emails", response_class=HTMLResponse)
async def get_emails(request: Request):
    """Display all emails in a table"""
    try:
        # Get credentials from query parameters or use defaults
        email = request.query_params.get("email", EMAIL_ADDRESS)
        password = request.query_params.get("password", EMAIL_PASSWORD)
        
        print(f"Attempting to connect to email: {email}")
        email_service = EmailService(email, password)
        emails = email_service.get_all_emails(limit=100)
        print(f"Retrieved {len(emails)} emails")
        return templates.TemplateResponse("emails.html", {
            "request": request, 
            "emails": emails,
            "total_emails": len(emails),
            "error": None
        })
    except Exception as e:
        print(f"Error retrieving emails: {e}")
        return templates.TemplateResponse("emails.html", {
            "request": request, 
            "emails": [],
            "total_emails": 0,
            "error": str(e)
        })

@app.get("/api/emails")
async def get_emails_api():
    """API endpoint to get emails as JSON"""
    email_service = EmailService(EMAIL_ADDRESS, EMAIL_PASSWORD)
    emails = email_service.get_all_emails(limit=100)
    return {"emails": emails, "total": len(emails)}

@app.post("/button-click")
async def button_click():
    return {"message": "Button was clicked!", "status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
