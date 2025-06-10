from django import template

register = template.Library()

@register.filter
def abs_value(value):
    """Returns the absolute value of a number"""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value

@register.filter
def split(value, delimiter=','):
    """Split a string into a list using the specified delimiter"""
    if value:
        return [x.strip() for x in value.split(delimiter)]
    return []

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def has_role(user, roles):
    """Check if user has any of the specified roles"""
    if not user or not hasattr(user, 'rol'):
        return False
    role_list = [r.strip() for r in roles.split(',')]
    return user.rol in role_list

@register.filter
def abs_value(value):
    """Returns the absolute value"""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value

@register.filter
def split(value, arg):
    """Split a string into a list using the specified delimiter"""
    return value.split(arg)

@register.filter
def subtract(value, arg):
    """Subtracts the argument from the value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value
