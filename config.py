import os
import sys
import logging

# Configure logging first to capture errors
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_env_variable(name, default=None, required=True):
    """Safely get environment variable with validation"""
    value = os.getenv(name, default)
    
    if required and value is None:
        logger.critical(f"❌ Environment variable {name} is required but not set!")
        sys.exit(1)
    
    return value

def get_int_env(name, default=None, required=True):
    """Get integer environment variable safely"""
    value = get_env_variable(name, default, required)
    
    if value is None:
        return None
        
    try:
        return int(value)
    except (TypeError, ValueError):
        logger.critical(f"❌ Environment variable {name} must be an integer!")
        sys.exit(1)

# Get required configuration values
try:
    BOT_TOKEN = get_env_variable("BOT_TOKEN", required=True)
    ADMIN_ID = get_int_env("ADMIN_ID", required=True)
    
    # VIP pricing configuration
    VIP_PRICES = {1: 500, 2: 1000, 3: 1500, 5: 2000}
    
    # Inactivity timeout in seconds (default: 5 minutes)
    INACTIVITY_TIMEOUT = 300
    
    # Log successful configuration
    logger.info("✅ Configuration loaded successfully")
    logger.info(f"🤖 Bot Token: {'*' * 20}{BOT_TOKEN[-5:]}")
    logger.info(f"👑 Admin ID: {ADMIN_ID}")
    logger.info(f"⏱️ Inactivity Timeout: {INACTIVITY_TIMEOUT}s")
    
except Exception as e:
    logger.critical(f"❌ Critical configuration error: {str(e)}")
    sys.exit(1)
