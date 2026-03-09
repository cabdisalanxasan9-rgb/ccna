import os
import sys
from pathlib import Path

# Ensure project root (contains manage.py and mysite/) is importable.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

from mysite.wsgi import application

app = application
