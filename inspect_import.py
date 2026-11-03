import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "apps", "api"))
from app.main import app  # noqa: E402, F401

print("App imported OK")
