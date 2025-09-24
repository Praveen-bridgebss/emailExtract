#!/usr/bin/env python3
"""
Production S3 CV Checker
Simple script to check uploaded CVs in S3 bucket
"""

import boto3
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    print("📋 Checking S3 bucket for uploaded CVs...")
    
    try:
        # Get credentials from environment variables
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_region = os.getenv("AWS_REGION", "us-east-2")
        bucket_name = os.getenv("S3_BUCKET_NAME")
        folder_name = os.getenv("S3_CV_FOLDER", "emailCvs")
        
        if not all([aws_access_key, aws_secret_key, bucket_name]):
            print("❌ Missing required environment variables!")
            print("Please check your .env file for:")
            print("- AWS_ACCESS_KEY_ID")
            print("- AWS_SECRET_ACCESS_KEY") 
            print("- S3_BUCKET_NAME")
            sys.exit(1)
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        # List files in CV folder
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=f"{folder_name}/"
        )
        
        if 'Contents' in response:
            files = response['Contents']
            print(f"\n✅ Found {len(files)} CV files in S3:")
            print("-" * 50)
            
            for i, file_obj in enumerate(files, 1):
                key = file_obj['Key']
                size = file_obj['Size']
                last_modified = file_obj['LastModified']
                
                # Extract original filename (skip timestamp and UUID)
                filename = key.split('/')[-1]
                if '_' in filename:
                    parts = filename.split('_')
                    if len(parts) >= 4:
                        original_name = '_'.join(parts[3:])  # Skip timestamp and UUID
                    else:
                        original_name = filename
                else:
                    original_name = filename
                
                # Format size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                
                print(f"{i:2d}. {original_name}")
                print(f"    📏 {size_str} | 📅 {last_modified.strftime('%Y-%m-%d %H:%M')}")
            
            print("-" * 50)
            print(f"📊 Total: {len(files)} CV files uploaded")
        else:
            print("❌ No CV files found in S3 bucket")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
