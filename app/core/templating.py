import datetime
import logging
from collections import defaultdict
from typing import Optional, Any

from fastapi.templating import Jinja2Templates
from pathlib import Path

APP_ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = APP_ROOT_DIR / "view" / "templates"

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
logger = logging.getLogger(__name__)

