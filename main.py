from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.templating import Jinja2Templates
from services.email_service import EmailService
from services.s3_service import S3Service
from services.mongodb_service import MongoDBService
from pydantic import BaseModel
import uvicorn
import base64
import io
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Gmail Email Parser")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Gmail credentials (will be overridden by user input)
EMAIL_ADDRESS = "your-email@gmail.com"
EMAIL_PASSWORD = "your-password"

# AWS S3 credentials from environment variables
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_CV_FOLDER = os.getenv("S3_CV_FOLDER", "emailCvs")

# MongoDB connection - Load from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

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
    """Display unread emails categorized by job titles"""
    try:
        # Get credentials from query parameters or use defaults
        email = request.query_params.get("email", EMAIL_ADDRESS)
        password = request.query_params.get("password", EMAIL_PASSWORD)
        
        print(f"Attempting to connect to email: {email}")
        email_service = EmailService(email, password)
        
        # Fetch only unread emails
        emails = email_service.get_unread_emails(limit=100)
        print(f"Retrieved {len(emails)} unread emails")
        
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
        print(f"Download request for: {filename} from {email_address}")
        
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
            
            print(f"Found {len(attachments)} attachments in email")
            
            # Find the requested attachment
            target_attachment = None
            print(f"Looking for attachment: '{filename}'")
            print(f"Total attachments found: {len(attachments)}")
            
            for i, attachment in enumerate(attachments):
                print(f"Attachment {i+1}: '{attachment['filename']}'")
                print(f"  Size: {attachment.get('size', 'Unknown')} bytes")
                print(f"  Content Type: {attachment.get('content_type', 'Unknown')}")
                
                # Try exact match first
                if attachment["filename"] == filename:
                    target_attachment = attachment
                    print(f"✅ Exact match found!")
                    break
                # Try URL decoded match
                elif attachment["filename"] == filename.replace('%20', ' '):
                    target_attachment = attachment
                    print(f"✅ URL decoded match found!")
                    break
                # Try case insensitive match
                elif attachment["filename"].lower() == filename.lower():
                    target_attachment = attachment
                    print(f"✅ Case insensitive match found!")
                    break
            
            if not target_attachment:
                print(f"❌ Attachment not found: '{filename}'")
                available_filenames = [att["filename"] for att in attachments]
                print(f"Available attachments:")
                for i, name in enumerate(available_filenames):
                    print(f"  {i+1}. '{name}'")
                
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "error": "Attachment not found",
                        "message": f"Attachment '{filename}' not found in email",
                        "debug_info": {
                            "requested_filename": filename,
                            "available_attachments": available_filenames,
                            "total_attachments": len(attachments)
                        }
                    }
                )
            
            print(f"Found target attachment: {target_attachment['filename']}, size: {target_attachment['size']} bytes")
            
            # Return the attachment as a download
            headers = {
                "Content-Disposition": f"attachment; filename=\"{filename}\"",
                "Content-Type": target_attachment["content_type"],
                "Content-Length": str(target_attachment["size"])
            }
            
            return Response(
                content=target_attachment["data"],
                headers=headers,
                media_type=target_attachment["content_type"]
            )
            
        finally:
            email_service.disconnect()
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"Error downloading attachment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download attachment: {str(e)}")

@app.post("/upload-to-s3")
async def upload_to_s3(
    request: Request,
    email_address: str = Query(...),
    password: str = Query(...),
    message_id: str = Query(...),
    filename: str = Query(...),
    job_category: str = Query("Unknown", description="Job category for the candidate")
):
    """Upload attachment to S3 bucket"""
    try:
        print(f"S3 upload request for: {filename} from {email_address}")
        
        # Initialize S3 service
        s3_service = S3Service(AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION)
        
        # Test S3 connection first
        if not s3_service.test_connection(S3_BUCKET_NAME):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "S3 connection failed",
                    "message": "Cannot connect to S3 bucket. Please check your AWS credentials and bucket name."
                }
            )
        
        # Create email service and connect to get attachment
        email_service = EmailService(email_address, password)
        
        if not email_service.connect():
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Email connection failed",
                    "message": "Failed to connect to email account"
                }
            )
        
        try:
            # Search for the specific email by Message-ID
            status, messages = email_service.mail.search(None, f'HEADER Message-ID "{message_id}"')
            
            if status != "OK" or not messages[0]:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "error": "Email not found",
                        "message": "The email containing this attachment was not found"
                    }
                )
            
            email_ids = messages[0].split()
            if not email_ids:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "error": "Email not found",
                        "message": "The email containing this attachment was not found"
                    }
                )
            
            # Fetch the email
            status, msg_data = email_service.mail.fetch(email_ids[0], "(RFC822)")
            
            if status != "OK":
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "error": "Failed to fetch email",
                        "message": "Could not retrieve the email content"
                    }
                )
            
            # Parse the email
            import email as email_lib
            email_message = email_lib.message_from_bytes(msg_data[0][1])
            
            # Get attachments
            attachments = email_service.get_attachments(email_message)
            
            print(f"Found {len(attachments)} attachments in email")
            
            # Find the requested attachment
            target_attachment = None
            for attachment in attachments:
                if attachment["filename"] == filename:
                    target_attachment = attachment
                    break
            
            if not target_attachment:
                print(f"Attachment not found: {filename}")
                available_filenames = [att["filename"] for att in attachments]
                print(f"Available attachments: {available_filenames}")
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "error": "Attachment not found",
                        "message": f"Attachment '{filename}' not found in the email"
                    }
                )
            
            print(f"Found target attachment: {target_attachment['filename']}, size: {target_attachment['size']} bytes")
            
            # Upload to S3
            upload_result = s3_service.upload_attachment(
                bucket_name=S3_BUCKET_NAME,
                attachment_data=target_attachment["data"],
                filename=target_attachment["filename"],
                folder=S3_CV_FOLDER
            )
            
            if upload_result["success"]:
                # Initialize MongoDB service
                try:
                    mongodb_service = MongoDBService()
                except Exception as e:
                    return JSONResponse(
                        status_code=500,
                        content={
                            "success": False,
                            "error": "MongoDB configuration error",
                            "message": f"S3 upload successful but database configuration failed: {str(e)}"
                        }
                    )
                
                # Test MongoDB connection
                if not await mongodb_service.test_connection():
                    return JSONResponse(
                        status_code=500,
                        content={
                            "success": False,
                            "error": "MongoDB connection failed",
                            "message": "S3 upload successful but failed to connect to database"
                        }
                    )
                
                # Use the job category from the request parameter
                job_posting = job_category
                
                # Extract relative path from S3 URL (remove base URL)
                s3_url = upload_result["s3_url"]
                # Remove the base URL part: https://bridge-cv-dev.s3.us-east-2.amazonaws.com
                base_url = "https://bridge-cv-dev.s3.us-east-2.amazonaws.com"
                if s3_url.startswith(base_url):
                    relative_path = s3_url.replace(base_url, "")
                else:
                    # Fallback: try to extract path from any S3 URL format
                    relative_path = "/" + upload_result["key"]
                
                # Save to MongoDB
                db_result = await mongodb_service.create_expected_candidate(
                    name=target_attachment["filename"],
                    job_posting=job_posting,
                    cv_file_path=relative_path
                )
                
                # Close MongoDB connection
                await mongodb_service.close_connection()
                
                if db_result["success"]:
                    # Combine S3 and database results
                    combined_result = {
                        "success": True,
                        "message": f"Successfully uploaded {target_attachment['filename']} to S3 and saved to database",
                        "s3_url": upload_result["s3_url"],
                        "bucket": upload_result["bucket"],
                        "key": upload_result["key"],
                        "filename": upload_result["filename"],
                        "original_filename": upload_result["original_filename"],
                        "size": upload_result["size"],
                        "database": {
                            "candidate_id": db_result["candidate_id"],
                            "job_posting": job_posting,
                            "cv_file_path": relative_path
                        }
                    }
                    return JSONResponse(
                        status_code=200,
                        content=combined_result
                    )
                else:
                    # S3 upload successful but database failed
                    return JSONResponse(
                        status_code=207,  # Multi-status
                        content={
                            "success": True,
                            "message": f"S3 upload successful but database save failed: {db_result['message']}",
                            "s3_url": upload_result["s3_url"],
                            "bucket": upload_result["bucket"],
                            "key": upload_result["key"],
                            "filename": upload_result["filename"],
                            "original_filename": upload_result["original_filename"],
                            "size": upload_result["size"],
                            "database_error": db_result["error"],
                            "cv_file_path": relative_path
                        }
                    )
            else:
                return JSONResponse(
                    status_code=500,
                    content=upload_result
                )
            
        finally:
            email_service.disconnect()
            
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "message": "An unexpected error occurred during S3 upload"
            }
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
