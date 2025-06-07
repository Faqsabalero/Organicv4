from django import template

register = template.Library()

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
