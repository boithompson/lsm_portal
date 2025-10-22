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


@register.filter(name="get_attribute")
def get_attribute(obj, attr_name):
    """
    Safely gets an attribute from an object.
    Usage: {{ object|get_attribute:attr_name }}
    """
    return getattr(obj, attr_name, "")


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
    teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    thousands = ["", "Thousand", "Million", "Billion"]

    def _convert_chunk(n):
        words = []
        if n >= 100:
            words.append(units[n // 100] + " Hundred")
            n %= 100
        if n > 0: # Add "and" if there are tens/units after hundreds
            if words: # Only add "and" if "Hundred" was added
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
