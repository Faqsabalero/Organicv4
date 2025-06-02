from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def abs_value(value):
    """Returns the absolute value of a number"""
    try:
        return abs(value)
    except (TypeError, ValueError):
        return value

@register.filter
def split(value, delimiter=','):
    """Split a string into a list using the specified delimiter"""
    return [x.strip() for x in value.split(delimiter)]

@register.filter
def subtract(value, arg):
    """Subtracts the arg from the value"""
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except (TypeError, ValueError):
        return value
