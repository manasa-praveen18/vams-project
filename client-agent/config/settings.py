import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Monitoring settings
POLL_INTERVAL = 1  # seconds between window checks
IDLE_THRESHOLD = 300  # seconds before user is marked idle

# Sync settings
SYNC_INTERVAL = 60  # seconds between sync attempts
BATCH_SIZE = 50  # number of logs to upload at once

# Server settings
SERVER_URL = "https://viswaendpoints.theviswagroup.com"  # change to real server URL later
API_ENDPOINT_REGISTER = "/api/client/register"
API_ENDPOINT_UPLOAD = "/api/logs/upload"
API_ENDPOINT_HEALTH = "/api/health"

# Database settings
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'vams.db')

# Device settings
DEVICE_NAME = os.environ.get('COMPUTERNAME', 'UNKNOWN_DEVICE')
DEVICE_ID = os.getenv("DEVICE_ID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")