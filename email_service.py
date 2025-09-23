import imaplib
import email
from email.header import decode_header
from datetime import datetime
from typing import List, Dict
import ssl

class EmailService:
    def __init__(self, email_address: str, password: str):
        self.email_address = email_address
        self.password = password
        
        # Gmail-only configuration
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993
        self.provider = "Gmail"
        
    def connect(self):
        """Connect to Gmail IMAP server"""
        print(f"Connecting to Gmail account: {self.email_address}")
        
        try:
            print(f"Connecting to {self.imap_server}:{self.imap_port}")
            
            # Create SSL context with more permissive settings
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect to Gmail IMAP server
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, ssl_context=context)
            
            # Login with credentials - this will raise an exception if authentication fails
            print(f"Attempting login for: {self.email_address}")
            try:
                self.mail.login(self.email_address, self.password)
                print("Login successful!")
            except imaplib.IMAP4.error as auth_error:
                error_msg = str(auth_error)
                print(f"Authentication failed: {error_msg}")
                if "Authentication failed" in error_msg or "Invalid credentials" in error_msg or "LOGIN failed" in error_msg:
                    raise Exception("Invalid Gmail credentials. Please check your email and password.")
                else:
                    raise Exception(f"Gmail authentication failed: {error_msg}")
            
            # Select INBOX
            self.mail.select("INBOX")
            print("INBOX selected successfully")
            
            # Test the connection by trying to get mailbox status
            status, messages = self.mail.status("INBOX", "(MESSAGES)")
            if status != "OK":
                raise Exception("Failed to access mailbox")
            
            print("Mailbox access confirmed")
            return True
                    
        except imaplib.IMAP4.error as e:
            error_msg = str(e)
            print(f"IMAP error: {error_msg}")
            
            if "Authentication failed" in error_msg or "Invalid credentials" in error_msg or "LOGIN failed" in error_msg:
                raise Exception("Invalid Gmail credentials. Please check your email and password.")
            elif "IMAP access disabled" in error_msg:
                raise Exception("IMAP access is disabled. Please enable IMAP in your Gmail settings.")
            elif "App password required" in error_msg or "2-step verification" in error_msg:
                raise Exception("App password required. Please generate an app password from Google Security settings.")
            else:
                raise Exception(f"Gmail connection failed: {error_msg}")
                
        except Exception as e:
            error_msg = str(e)
            print(f"Connection failed: {error_msg}")
            
            if "Authentication failed" in error_msg or "Invalid credentials" in error_msg or "LOGIN failed" in error_msg:
                raise Exception("Invalid Gmail credentials. Please check your email and password.")
            elif "IMAP access disabled" in error_msg:
                raise Exception("IMAP access is disabled. Please enable IMAP in your Gmail settings.")
            elif "App password required" in error_msg or "2-step verification" in error_msg:
                raise Exception("App password required. Please generate an app password from Google Security settings.")
            else:
                raise Exception(f"Gmail connection failed: {error_msg}")
    
    def disconnect(self):
        """Disconnect from the IMAP server"""
        try:
            self.mail.close()
            self.mail.logout()
        except:
            pass
    
    def decode_mime_words(self, s):
        """Decode MIME encoded words"""
        if s is None:
            return ""
        decoded_parts = decode_header(s)
        decoded_string = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_string += part.decode(encoding)
                else:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += part
        return decoded_string
    
    def get_all_emails(self, limit: int = 50) -> List[Dict]:
        """Get all emails from the inbox"""
        if not self.connect():
            raise Exception("Failed to connect to Gmail. Please check your credentials.")
        
        try:
            # Search for all emails
            status, messages = self.mail.search(None, "ALL")
            
            if status != "OK":
                raise Exception("Failed to search emails. Please check your Gmail settings.")
            
            email_ids = messages[0].split()
            
            # If no emails found, still return success but with empty list
            if not email_ids:
                print("No emails found in inbox")
                return []
            
            email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
            emails = []
            
            for email_id in reversed(email_ids):
                try:
                    # Fetch the email
                    status, msg_data = self.mail.fetch(email_id, "(RFC822)")
                    
                    if status != "OK":
                        continue
                    
                    # Parse the email
                    email_message = email.message_from_bytes(msg_data[0][1])
                    
                    # Extract email details
                    email_data = self.parse_email(email_message)
                    emails.append(email_data)
                    
                except Exception as e:
                    print(f"Error processing email {email_id}: {e}")
                    continue
            
            # Verify we actually got some emails
            if not emails:
                print("No emails could be retrieved")
                return []
            
            print(f"Successfully retrieved {len(emails)} emails")
            return emails
            
        except Exception as e:
            print(f"Error fetching emails: {e}")
            raise e
        finally:
            self.disconnect()
    
    def test_connection(self) -> bool:
        """Test if we can actually connect and access emails"""
        try:
            if not self.connect():
                return False
            
            # Try to get mailbox status
            status, messages = self.mail.status("INBOX", "(MESSAGES)")
            if status != "OK":
                return False
            
            # Try to search for emails
            status, messages = self.mail.search(None, "ALL")
            if status != "OK":
                return False
            
            return True
            
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
        finally:
            self.disconnect()
    
    def parse_email(self, email_message) -> Dict:
        """Parse email message and extract relevant information"""
        # Get subject
        subject = self.decode_mime_words(email_message.get("Subject", ""))
        
        # Get sender
        sender = self.decode_mime_words(email_message.get("From", ""))
        
        # Get recipient
        recipient = self.decode_mime_words(email_message.get("To", ""))
        
        # Get date
        date_str = email_message.get("Date", "")
        try:
            date_obj = email.utils.parsedate_to_datetime(date_str)
            formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_date = date_str
        
        # Get email body
        body = self.get_email_body(email_message)
        
        # Get email ID
        message_id = email_message.get("Message-ID", "")
        
        return {
            "subject": subject,
            "sender": sender,
            "recipient": recipient,
            "date": formatted_date,
            "body": body[:200] + "..." if len(body) > 200 else body,
            "message_id": message_id,
            "has_attachments": self.has_attachments(email_message)
        }
    
    def get_email_body(self, email_message) -> str:
        """Extract email body text"""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        pass
                elif content_type == "text/html" and "attachment" not in content_disposition and not body:
                    try:
                        body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        pass
        else:
            try:
                body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                pass
        
        return body.strip()
    
    def has_attachments(self, email_message) -> bool:
        """Check if email has attachments"""
        if email_message.is_multipart():
            for part in email_message.walk():
                content_disposition = str(part.get("Content-Disposition"))
                if "attachment" in content_disposition:
                    return True
        return False
