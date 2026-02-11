from django import template
from django import forms  # Import forms

register = template.Library()


@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ""


@register.filter
def divide(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return ""


@register.filter
def add(value, arg):
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return ""


@register.filter(name="naira")
def naira(value):
    try:
        value = float(value)
        return f"₦{value:,.2f}"  # Adds commas and 2 decimal places
    except (ValueError, TypeError):
        return value


@register.filter(name="get_attribute")
def get_attribute(obj, attr_name):
    """
    Safely gets an attribute from an object.
    Usage: {{ object|get_attribute:attr_name }}
    """
    return getattr(obj, attr_name, "")


@register.filter(name="get_item")
def get_item(obj, key):
    """
    Allows accessing dictionary items by key or form fields by name in templates.
    Usage: {{ dictionary|get_item:key }} or {{ form|get_item:field_name }}
    """
    if isinstance(obj, forms.Form):
        return obj[key]  # Access BoundField directly
    if hasattr(obj, "get"):  # For dictionaries and other objects with a .get method
        return obj.get(key)
    return None  # Or raise an error, depending on desired behavior


@register.filter(name="num_to_words")
def num_to_words(value):
    """
    Converts a number to its English word representation.
    Handles numbers up to 999,999,999.
    """
    try:
        num = int(value)
    except (ValueError, TypeError):
        return str(value)

    if num == 0:
        return "Zero"

    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    teens = [
        "Ten",
        "Eleven",
        "Twelve",
        "Thirteen",
        "Fourteen",
        "Fifteen",
        "Sixteen",
        "Seventeen",
        "Eighteen",
        "Nineteen",
    ]
    tens = [
        "",
        "",
        "Twenty",
        "Thirty",
        "Forty",
        "Fifty",
        "Sixty",
        "Seventy",
        "Eighty",
        "Ninety",
    ]
    thousands = ["", "Thousand", "Million", "Billion"]

    def _convert_chunk(n):
        words = []
        if n >= 100:
            words.append(units[n // 100] + " Hundred")
            n %= 100
        if n > 0:  # Add "and" if there are tens/units after hundreds
            if words:  # Only add "and" if "Hundred" was added
                words.append("and")
            if n >= 20:
                words.append(tens[n // 10])
                n %= 10
            elif n >= 10:
                words.append(teens[n - 10])
                n = 0
            if n > 0:
                words.append(units[n])
        return " ".join(words)

    word_parts = []
    for i, scale in enumerate(thousands):
        if num == 0:
            break
        chunk = num % 1000
        if chunk > 0:
            chunk_words = _convert_chunk(chunk)
            if scale:
                word_parts.append(chunk_words + " " + scale)
            else:
                word_parts.append(chunk_words)
        num //= 1000

    # Join parts with commas, but only if there are multiple thousand/million chunks
    result = []
    for i, part in enumerate(reversed(word_parts)):
        result.append(part)
        if i < len(word_parts) - 1:
            result.append(",")

    return " ".join(result).strip()


@register.simple_tag(takes_context=True)
def url_replace(context, path=None, **kwargs):
    """
    Returns the current URL (or a specified path) with updated GET parameters.
    Usage: {% url_replace path=request.path page=page_obj.next_page_number category='cash' %}
    """
    query = context["request"].GET.copy()
    for key, value in kwargs.items():
        query[key] = value

    # Construct the base path
    base_path = path if path is not None else context["request"].path

    # Reconstruct the URL with the new query string
    return f"{base_path}?{query.urlencode()}" if query else base_path
