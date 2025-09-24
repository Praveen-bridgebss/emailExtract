import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import os
from typing import Dict, Any
import uuid
from datetime import datetime

class S3Service:
    def __init__(self, access_key: str, secret_key: str, region: str = 'us-east-1'):
        """
        Initialize S3 service with AWS credentials
        
        Args:
            access_key: AWS Access Key ID
            secret_key: AWS Secret Access Key
            region: AWS region (default: us-east-1)
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        
        try:
            # Initialize S3 client
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            print(f"S3 client initialized successfully for region: {region}")
        except Exception as e:
            print(f"Failed to initialize S3 client: {e}")
            raise e
    
    def upload_attachment(self, bucket_name: str, attachment_data: bytes, filename: str, 
                         folder: str = "emailCV") -> Dict[str, Any]:
        """
        Upload attachment to S3 bucket
        
        Args:
            bucket_name: Name of the S3 bucket
            attachment_data: Binary data of the attachment
            filename: Original filename
            folder: Folder name in bucket (default: emailCV)
            
        Returns:
            Dict with upload result information
        """
        try:
            # Generate unique filename to avoid conflicts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = os.path.splitext(filename)[1] if '.' in filename else ''
            unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}_{filename}"
            
            # Create S3 key (path) for the file
            s3_key = f"{folder}/{unique_filename}"
            
            print(f"Uploading {filename} to S3 bucket: {bucket_name}, key: {s3_key}")
            
            # Upload file to S3
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=attachment_data,
                ContentType=self._get_content_type(filename),
                Metadata={
                    'original-filename': filename,
                    'upload-timestamp': timestamp,
                    'uploaded-by': 'email-parser-app'
                }
            )
            
            # Generate S3 URL
            s3_url = f"https://{bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            result = {
                "success": True,
                "message": f"Successfully uploaded {filename} to S3",
                "s3_url": s3_url,
                "bucket": bucket_name,
                "key": s3_key,
                "filename": unique_filename,
                "original_filename": filename,
                "size": len(attachment_data)
            }
            
            print(f"Upload successful: {result}")
            return result
            
        except NoCredentialsError:
            error_msg = "AWS credentials not found or invalid"
            print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "message": "Please check your AWS credentials"
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = f"AWS S3 error: {error_code} - {e.response['Error']['Message']}"
            print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "message": f"Failed to upload to S3: {error_code}"
            }
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "message": "An unexpected error occurred during upload"
            }
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension"""
        extension = os.path.splitext(filename)[1].lower()
        
        content_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.txt': 'text/plain',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.zip': 'application/zip',
            '.rar': 'application/x-rar-compressed',
            '.7z': 'application/x-7z-compressed',
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav'
        }
        
        return content_types.get(extension, 'application/octet-stream')
    
    def test_connection(self, bucket_name: str) -> bool:
        """Test S3 connection and bucket access"""
        try:
            # Try to list objects in bucket (limited to 1 item)
            response = self.s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
            print(f"S3 connection test successful for bucket: {bucket_name}")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                print(f"Bucket '{bucket_name}' does not exist")
            elif error_code == 'AccessDenied':
                print(f"Access denied to bucket '{bucket_name}'")
            else:
                print(f"S3 connection test failed: {error_code}")
            return False
        except Exception as e:
            print(f"S3 connection test failed: {e}")
            return False
