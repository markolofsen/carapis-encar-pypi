# Configuration for the encar client package

import os
from pathlib import Path
import dotenv

# Determine project root and .env path
# Assumes config.py is in src/encar/, so three parents up is the root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
env_path = PROJECT_ROOT / '.env'

# Attempt to load .env file from project root, overriding system variables
# dotenv.load_dotenv() returns True if loaded, False otherwise, but doesn't error if not found
dotenv.load_dotenv(dotenv_path=env_path, override=True)

# Get API URL, using default if ENCAR_API_URL is not set (either in system or .env)
DEFAULT_BASE_URL = "https://api.carapis.com"
BASE_URL = os.getenv('ENCAR_API_URL', DEFAULT_BASE_URL)
