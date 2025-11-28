"""
OAuth 2.0 Client Credentials Authentication Module for EHR Server
Implements app-to-app authentication using client_id, client_secret, and app_id
"""

import jwt
import hashlib
import secrets
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from database import get_db_session
from models import OAuthClient

# OAuth Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_secret(secret: str) -> str:
    """Hash client secret using SHA-256"""
    return hashlib.sha256(secret.encode()).hexdigest()


def verify_secret(secret: str, secret_hash: str) -> bool:
    """Verify client secret against hash"""
    return hash_secret(secret) == secret_hash


def generate_client_credentials() -> Dict[str, str]:
    """Generate new client_id and client_secret"""
    client_id = f"client_{secrets.token_urlsafe(32)}"
    client_secret = secrets.token_urlsafe(48)
    return {
        "client_id": client_id,
        "client_secret": client_secret
    }


def create_access_token(client_id: str, app_id: str, role: str, scopes: list) -> str:
    """Create OAuth access token"""
    payload = {
        "client_id": client_id,
        "app_id": app_id,
        "role": role,
        "scopes": scopes,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[Dict]:
    """Verify and decode OAuth access token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


def authenticate_client(client_id: str, client_secret: str, app_id: str) -> dict:
    """
    Authenticate OAuth client using Client Credentials flow
    
    Args:
        client_id: Unique client identifier
        client_secret: Client secret key
        app_id: Application identifier
    
    Returns:
        dict with access_token or error
    """
    db = get_db_session()
    try:
        # Find client by client_id and app_id
        client = db.query(OAuthClient).filter(
            OAuthClient.client_id == client_id,
            OAuthClient.app_id == app_id,
            OAuthClient.is_active == True
        ).first()
        
        if not client:
            return {
                "status": "error",
                "message": "Invalid client credentials"
            }
        
        # Verify client secret
        if not verify_secret(client_secret, client.client_secret_hash):
            return {
                "status": "error",
                "message": "Invalid client credentials"
            }
        
        # Parse scopes
        import json
        scopes = json.loads(client.scopes) if client.scopes else []
        
        # Generate access token
        access_token = create_access_token(
            client_id=client.client_id,
            app_id=client.app_id,
            role=client.role,
            scopes=scopes
        )
        
        # Update last used timestamp
        client.last_used = datetime.utcnow()
        db.commit()
        
        return {
            "status": "success",
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "scope": " ".join(scopes),
            "client_info": {
                "client_id": client.client_id,
                "app_id": client.app_id,
                "app_name": client.app_name,
                "role": client.role
            }
        }
    finally:
        db.close()


def validate_token(token: str) -> dict:
    """Validate OAuth token and return client info"""
    try:
        payload = verify_token(token)
        
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")
        
        return {
            "valid": True,
            "client_id": payload["client_id"],
            "app_id": payload["app_id"],
            "role": payload["role"],
            "scopes": payload.get("scopes", [])
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }


def require_role(token: str, required_roles: list) -> bool:
    """Check if token has required role"""
    validation = validate_token(token)
    
    if not validation.get("valid"):
        return False
    
    return validation.get("role") in required_roles


def require_scope(token: str, required_scope: str) -> bool:
    """Check if token has required scope"""
    validation = validate_token(token)
    
    if not validation.get("valid"):
        return False
    
    scopes = validation.get("scopes", [])
    return required_scope in scopes


def register_client(app_id: str, app_name: str, role: str, scopes: list, 
                   description: str = "", contact_email: str = "") -> dict:
    """
    Register a new OAuth client
    
    Args:
        app_id: Application identifier
        app_name: Human-readable application name
        role: Role for the client (doctor, nurse, patient, admin, system)
        scopes: List of allowed scopes
        description: Optional description
        contact_email: Optional contact email
    
    Returns:
        dict with client_id and client_secret
    """
    db = get_db_session()
    try:
        # Generate credentials
        credentials = generate_client_credentials()
        client_id = credentials["client_id"]
        client_secret = credentials["client_secret"]
        
        # Hash the secret
        secret_hash = hash_secret(client_secret)
        
        # Create client record
        import json
        client = OAuthClient(
            client_id=client_id,
            client_secret_hash=secret_hash,
            app_id=app_id,
            app_name=app_name,
            role=role,
            scopes=json.dumps(scopes),
            description=description,
            contact_email=contact_email,
            is_active=True
        )
        
        db.add(client)
        db.commit()
        
        return {
            "status": "success",
            "client_id": client_id,
            "client_secret": client_secret,  # Only returned once!
            "app_id": app_id,
            "app_name": app_name,
            "role": role,
            "scopes": scopes,
            "message": "⚠️  IMPORTANT: Save the client_secret securely. It cannot be retrieved again!"
        }
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        db.close()
