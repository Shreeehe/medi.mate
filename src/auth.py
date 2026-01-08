import bcrypt
from pymongo import MongoClient
from datetime import datetime
from src.config import Config
from src.utils import setup_logger

logger = setup_logger(__name__)

class AuthManager:
    """
    Manages User Authentication (Login/Register).
    """
    def __init__(self):
        self.client = MongoClient(Config.MONGO_URI)
        self.db = self.client.get_database("prescription_db")
        self.users = self.db.users

    def register_user(self, username, password):
        """Registers a new user."""
        if self.users.find_one({"username": username}):
            return False, "Username already exists."
        
        # Hash password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        self.users.insert_one({
            "username": username,
            "password_hash": hashed,
            "created_at": datetime.utcnow()
        })
        logger.info(f"Registered user: {username}")
        return True, "User registered successfully."

    def login_user(self, username, password):
        """Authenticates a user."""
        user = self.users.find_one({"username": username})
        if not user:
            return False, "Invalid username or password."
        
        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
            logger.info(f"User logged in: {username}")
            return True, "Login successful."
        else:
            return False, "Invalid username or password."
