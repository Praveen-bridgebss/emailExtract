from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from email_service import EmailService
from pydantic import BaseModel
import uvicorn
import base64
import io

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
    """Display all emails categorized by job titles"""
    try:
        # Get credentials from query parameters or use defaults
        email = request.query_params.get("email", EMAIL_ADDRESS)
        password = request.query_params.get("password", EMAIL_PASSWORD)
        
        print(f"Attempting to connect to email: {email}")
        email_service = EmailService(email, password)
        emails = email_service.get_all_emails(limit=100)
        print(f"Retrieved {len(emails)} emails")
        
        # Categorize emails by job titles
        categorized_emails = email_service.categorize_emails(emails)
        
        return templates.TemplateResponse("emails.html", {
            "request": request, 
            "categorized_emails": categorized_emails,
            "total_emails": len(emails),
            "error": None
        })
    except Exception as e:
        print(f"Error retrieving emails: {e}")
        return templates.TemplateResponse("emails.html", {
            "request": request, 
            "categorized_emails": {},
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

@app.get("/download-attachment")
async def download_attachment(
    email_address: str = Query(...),
    password: str = Query(...),
    message_id: str = Query(...),
    filename: str = Query(...)
):
    """Download a specific attachment from an email"""
    try:
        # Create email service and connect
        email_service = EmailService(email_address, password)
        
        if not email_service.connect():
            raise HTTPException(status_code=400, detail="Failed to connect to email account")
        
        try:
            # Search for the specific email by Message-ID
            status, messages = email_service.mail.search(None, f'HEADER Message-ID "{message_id}"')
            
            if status != "OK" or not messages[0]:
                raise HTTPException(status_code=404, detail="Email not found")
            
            email_ids = messages[0].split()
            if not email_ids:
                raise HTTPException(status_code=404, detail="Email not found")
            
            # Fetch the email
            status, msg_data = email_service.mail.fetch(email_ids[0], "(RFC822)")
            
            if status != "OK":
                raise HTTPException(status_code=500, detail="Failed to fetch email")
            
            # Parse the email
            import email as email_lib
            email_message = email_lib.message_from_bytes(msg_data[0][1])
            
            # Get attachments
            attachments = email_service.get_attachments(email_message)
            
            # Find the requested attachment
            target_attachment = None
            for attachment in attachments:
                if attachment["filename"] == filename:
                    target_attachment = attachment
                    break
            
            if not target_attachment:
                raise HTTPException(status_code=404, detail="Attachment not found")
            
            # Return the attachment as a download
            headers = {
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": target_attachment["content_type"]
            }
            
            return Response(
                content=target_attachment["data"],
                headers=headers,
                media_type=target_attachment["content_type"]
            )
            
        finally:
            email_service.disconnect()
            
    except Exception as e:
        print(f"Error downloading attachment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download attachment: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
