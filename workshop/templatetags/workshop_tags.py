from django import template

register = template.Library()


@register.filter
def lookup(dictionary, key):
    """Template filter to get value from dictionary using dynamic key"""
    return dictionary.get(key, "")
