# admin_account/templatetags/custom_filters.py
from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def add_days(value, days):
    """Add days to a date."""
    return value + timedelta(days=days)

@register.filter
def dict_get(d, key):
    """Get a dictionary value safely in templates."""
    if isinstance(d, dict):
        return d.get(key, None)
    return None
