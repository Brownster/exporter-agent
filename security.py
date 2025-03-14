"""Security utilities for the exporter-agent."""
import os
from pathlib import Path
import base64
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from exceptions import APIKeyError
from logging_utils import get_logger

logger = get_logger()

# Default location for storing encrypted API keys
DEFAULT_KEY_PATH = Path.home() / ".exporter_agent" / "keys"


def derive_key(password: str, salt: Optional[bytes] = None) -> tuple:
    """
    Derive a key from a password using PBKDF2.
    
    Args:
        password: Password to derive key from
        salt: Optional salt (generated if not provided)
        
    Returns:
        Tuple of (key, salt)
    """
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt


def encrypt_api_key(api_key: str, password: str) -> tuple:
    """
    Encrypt an API key using a password.
    
    Args:
        api_key: API key to encrypt
        password: Password to encrypt with
        
    Returns:
        Tuple of (encrypted_key, salt)
    """
    key, salt = derive_key(password)
    f = Fernet(key)
    encrypted_key = f.encrypt(api_key.encode())
    return encrypted_key, salt


def decrypt_api_key(encrypted_key: bytes, salt: bytes, password: str) -> str:
    """
    Decrypt an API key using a password and salt.
    
    Args:
        encrypted_key: Encrypted API key
        salt: Salt used for encryption
        password: Password used for encryption
        
    Returns:
        Decrypted API key
        
    Raises:
        APIKeyError: If decryption fails
    """
    try:
        key, _ = derive_key(password, salt)
        f = Fernet(key)
        decrypted_key = f.decrypt(encrypted_key)
        return decrypted_key.decode()
    except Exception as e:
        raise APIKeyError(f"Failed to decrypt API key: {str(e)}")


def save_api_key(
    api_key: str, 
    provider: str, 
    password: str, 
    key_path: Optional[Path] = None
) -> None:
    """
    Encrypt and save an API key to a file.
    
    Args:
        api_key: API key to save
        provider: Provider name (e.g., 'openai', 'anthropic')
        password: Password to encrypt with
        key_path: Path to save key to (default: ~/.exporter_agent/keys)
        
    Raises:
        APIKeyError: If saving fails
    """
    if key_path is None:
        key_path = DEFAULT_KEY_PATH
    
    # Create directory if it doesn't exist
    key_path.mkdir(parents=True, exist_ok=True)
    
    try:
        encrypted_key, salt = encrypt_api_key(api_key, password)
        
        # Save encrypted key and salt
        with open(key_path / f"{provider}.key", "wb") as f:
            f.write(encrypted_key)
        
        with open(key_path / f"{provider}.salt", "wb") as f:
            f.write(salt)
            
        logger.info(f"Saved encrypted API key for {provider}")
    except Exception as e:
        raise APIKeyError(f"Failed to save API key: {str(e)}")


def load_api_key(
    provider: str, 
    password: str, 
    key_path: Optional[Path] = None
) -> str:
    """
    Load and decrypt an API key from a file.
    
    Args:
        provider: Provider name (e.g., 'openai', 'anthropic')
        password: Password to decrypt with
        key_path: Path to load key from (default: ~/.exporter_agent/keys)
        
    Returns:
        Decrypted API key
        
    Raises:
        APIKeyError: If loading or decryption fails
    """
    if key_path is None:
        key_path = DEFAULT_KEY_PATH
    
    try:
        # Load encrypted key and salt
        with open(key_path / f"{provider}.key", "rb") as f:
            encrypted_key = f.read()
        
        with open(key_path / f"{provider}.salt", "rb") as f:
            salt = f.read()
        
        # Decrypt and return
        return decrypt_api_key(encrypted_key, salt, password)
    except FileNotFoundError:
        raise APIKeyError(f"No API key found for {provider}")
    except Exception as e:
        raise APIKeyError(f"Failed to load API key: {str(e)}")


def set_api_key_env(
    provider: str, 
    password: str, 
    key_path: Optional[Path] = None
) -> None:
    """
    Load an API key and set it as an environment variable.
    
    Args:
        provider: Provider name (e.g., 'openai', 'anthropic')
        password: Password to decrypt with
        key_path: Path to load key from (default: ~/.exporter_agent/keys)
        
    Raises:
        APIKeyError: If loading or decryption fails
    """
    try:
        api_key = load_api_key(provider, password, key_path)
        
        # Set environment variable based on provider
        if provider.lower() in ["openai", "gpt"]:
            os.environ["OPENAI_API_KEY"] = api_key
            logger.info("Set OPENAI_API_KEY environment variable")
        elif provider.lower() == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = api_key
            logger.info("Set ANTHROPIC_API_KEY environment variable")
        else:
            os.environ[f"{provider.upper()}_API_KEY"] = api_key
            logger.info(f"Set {provider.upper()}_API_KEY environment variable")
    except Exception as e:
        raise APIKeyError(f"Failed to set API key environment variable: {str(e)}")