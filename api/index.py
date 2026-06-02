import sys
import os

# Ensure the root directory is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app
# This makes 'app' accessible as a serverless handler for Vercel
