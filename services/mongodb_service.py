import motor.motor_asyncio
from pymongo import MongoClient
from typing import Dict, Any, Optional
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class MongoDBService:
    def __init__(self):
        """Initialize MongoDB connection"""
        self.database_url = os.getenv("DATABASE_URL")
        
        if not self.database_url:
            raise Exception("DATABASE_URL environment variable is not set. Please configure it in your .env file.")
        
        try:
            # Create async client
            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.database_url)
            self.db = self.client.recruitment
            self.expected_candidates = self.db.expected_candidate
            print("MongoDB connection initialized successfully")
        except Exception as e:
            print(f"Failed to initialize MongoDB connection: {e}")
            raise e
    
    async def test_connection(self) -> bool:
        """Test MongoDB connection"""
        try:
            # Test the connection
            await self.client.admin.command('ping')
            print("MongoDB connection test successful")
            return True
        except Exception as e:
            print(f"MongoDB connection test failed: {e}")
            return False
    
    async def create_expected_candidate(self, name: str, job_posting: str, cv_file_path: str) -> Dict[str, Any]:
        """
        Create a new expected candidate record
        
        Args:
            name: Name of the candidate (PDF filename)
            job_posting: Job category from email
            cv_file_path: S3 file path
            
        Returns:
            Dict with creation result
        """
        try:
            candidate_data = {
                "name": name,
                "jobPosting": job_posting,
                "cvFilePath": cv_file_path,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
            
            result = await self.expected_candidates.insert_one(candidate_data)
            
            if result.inserted_id:
                print(f"Successfully created expected candidate: {name}")
                return {
                    "success": True,
                    "message": f"Successfully saved candidate {name} to database",
                    "candidate_id": str(result.inserted_id),
                    "data": candidate_data
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to insert candidate record",
                    "message": "Database insertion failed"
                }
                
        except Exception as e:
            error_msg = f"Database error: {str(e)}"
            print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "message": "Failed to save candidate to database"
            }
    
    async def get_expected_candidates(self, limit: int = 50) -> Dict[str, Any]:
        """
        Get all expected candidates
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            Dict with candidates data
        """
        try:
            cursor = self.expected_candidates.find().sort("createdAt", -1).limit(limit)
            candidates = []
            
            async for candidate in cursor:
                candidate["_id"] = str(candidate["_id"])
                candidates.append(candidate)
            
            return {
                "success": True,
                "candidates": candidates,
                "total": len(candidates)
            }
            
        except Exception as e:
            error_msg = f"Database error: {str(e)}"
            print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "candidates": [],
                "total": 0
            }
    
    async def close_connection(self):
        """Close MongoDB connection"""
        try:
            self.client.close()
            print("MongoDB connection closed")
        except Exception as e:
            print(f"Error closing MongoDB connection: {e}")
