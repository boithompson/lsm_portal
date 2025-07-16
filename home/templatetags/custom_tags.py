from django import template

register = template.Library()


@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ""


@register.filter(name="naira")
def naira(value):
    try:
        value = float(value)
        return f"₦{value:,.2f}"  # Adds commas and 2 decimal places
    except (ValueError, TypeError):
        return value
