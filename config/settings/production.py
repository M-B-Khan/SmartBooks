from .base import *

DEBUG = False

CORS_ALLOWED_ORIGINS = [
    # Add your frontend domain here later
]

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'