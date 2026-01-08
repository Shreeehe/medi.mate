from pymongo import MongoClient
from datetime import datetime
import uuid
from src.config import Config
from src.utils import setup_logger

logger = setup_logger(__name__)

class MemoryManager:
    """
    Manages chat history and sessions - MongoDB.
    """
    def __init__(self):
        self.client = MongoClient(Config.MONGO_URI)
        self.db = self.client.get_database("prescription_db")
        self.sessions = self.db.sessions
        self.messages = self.db.messages
        logger.info("Connected to MongoDB")

    def get_or_create_session(self, user_id, prescription_id, title=None, filename=None, details=None):
        """
        Retrieves an existing session for the (user, prescription) pair, 
        or creates a new one if it doesn't exist.
        """
        # Check if session exists
        existing_session = self.sessions.find_one({
            "user_id": user_id,
            "prescription_id": prescription_id
        })
        
        if existing_session:
            # Update fields if provided and missing
            updates = {}
            if title and not existing_session.get("title"):
                updates["title"] = title
            if filename and not existing_session.get("filename"):
                updates["filename"] = filename
            if details and not existing_session.get("details"):
                updates["details"] = details
            
            if updates:
                self.sessions.update_one(
                    {"_id": existing_session["_id"]},
                    {"$set": updates}
                )
            return existing_session["session_id"]
            
        # Create new session
        session_id = str(uuid.uuid4())
        doc = {
            "session_id": session_id,
            "user_id": user_id,
            "prescription_id": prescription_id,
            "summary": "",
            "created_at": datetime.utcnow(),
            "last_active": datetime.utcnow()
        }
        if title:
            doc["title"] = title
        if filename:
            doc["filename"] = filename
        if details:
            doc["details"] = details
            
        self.sessions.insert_one(doc)
        logger.info(f"Created new session {session_id} for user {user_id} on prescription {prescription_id}")
        return session_id

    def get_session_details(self, session_id):
        """Retrieves details (medicine summary) for a session."""
        session = self.sessions.find_one({"session_id": session_id})
        return session.get("details", "") if session else ""

    def get_prescription_by_filename(self, user_id, filename):
        """Checks if a user has already uploaded a file with this name."""
        # Find session with this filename for this user
        session = self.sessions.find_one({
            "user_id": user_id,
            "filename": filename
        })
        if session:
            return session["prescription_id"]
        return None

    def add_message(self, session_id, role, content):
        """Adds a message to the session history."""
        self.messages.insert_one({
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow()
        })
        self.update_last_active(session_id)

    def get_history(self, session_id, limit=10):
        """Retrieves recent messages for a session."""
        cursor = self.messages.find({"session_id": session_id}).sort("timestamp", 1).limit(limit)
        return list(cursor)

    def get_summary(self, session_id):
        """Retrieves the summary for a session."""
        session = self.sessions.find_one({"session_id": session_id})
        return session.get("summary", "") if session else ""

    def update_summary(self, session_id, new_summary):
        """Updates the session summary."""
        self.sessions.update_one(
            {"session_id": session_id},
            {"$set": {"summary": new_summary, "last_active": datetime.utcnow()}}
        )

    def update_last_active(self, session_id):
        """Updates the last active timestamp."""
        self.sessions.update_one(
            {"session_id": session_id},
            {"$set": {"last_active": datetime.utcnow()}}
        )
    
    def get_user_prescriptions(self, user_id):
        """Returns list of dicts {id, title} that the user has interacted with."""
        # Find sessions for this user, excluding GLOBAL
        # We want the prescription_id and the title
        cursor = self.sessions.find(
            {"user_id": user_id, "prescription_id": {"$ne": "GLOBAL"}},
            {"prescription_id": 1, "title": 1, "last_active": 1}
        ).sort("last_active", -1)
        
        results = []
        seen_ids = set()
        for doc in cursor:
            p_id = doc["prescription_id"]
            if p_id not in seen_ids:
                results.append({
                    "id": p_id,
                    "title": doc.get("title", f"Prescription {p_id[:8]}...")
                })
                seen_ids.add(p_id)
        return results

    def get_all_sessions(self):
        """Returns all sessions sorted by last active."""
        return list(self.sessions.find().sort("last_active", -1))

    def save_otc_result(self, session_id, otc_result):
        """Saves the OTC analysis result to the session."""
        self.sessions.update_one(
            {"session_id": session_id},
            {"$set": {"otc_result": otc_result}}
        )

    def get_otc_result(self, session_id):
        """Retrieves the OTC analysis result for a session."""
        session = self.sessions.find_one({"session_id": session_id})
        return session.get("otc_result") if session else None

