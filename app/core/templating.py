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


def generate_calendar(task_schedule: dict) -> dict:
    calendar = defaultdict(list)
    for date_str, tasks in task_schedule.items():
        try:
            date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            month_key = date_obj.strftime('%Y-%m')
            calendar[month_key].append({
                "date": date_obj,
                "tasks": tasks
            })
        except ValueError:
            continue
    return dict(calendar)


def parse_date_filter(date_str, fmt="%B %Y"):
    if not date_str:
        return None
    try:
        return datetime.datetime.strptime(date_str, fmt)
    except ValueError:
        return None
def format_datetime_filter(value: Optional[Any]) -> str:
    if isinstance(value, datetime.datetime):
        try:
            return value.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"Error formatting datetime object {value}: {e}", exc_info=True)
            return "Invalid Date"
    elif isinstance(value, str):
        if not value:
            return ""
        try:
            dt = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not parse timestamp string '{value}' as ISO format: {e}")
            return value

    elif value is None:
        return ""

    else:
        logger.warning(f"Received unexpected type for timestamp filter: {type(value)}, value: {value}")
        try:
            return str(value)
        except Exception:
            return "Invalid Input"



def month_year_filter(date_str):
    if not date_str: return ""
    try:
        dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime("%B %Y")
    except ValueError:
        return date_str


def format_date_filter(date_input, fmt="%Y-%m-%d"):
    if date_input is None:
        return ""
    if isinstance(date_input, datetime.datetime):
        return date_input.strftime(fmt)
    if isinstance(date_input, str):
        try:
            dt = datetime.datetime.strptime(date_input, '%Y-%m-%d')
            return dt.strftime(fmt)
        except ValueError:
            return date_input
    return str(date_input)

templates.env.filters['format_datetime'] = format_datetime_filter
templates.env.filters['month_year'] = month_year_filter
templates.env.filters['format_date'] = format_date_filter
templates.env.filters['parse_date'] = parse_date_filter
