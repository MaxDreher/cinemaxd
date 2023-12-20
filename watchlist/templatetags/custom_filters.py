# custom_filters.py
from django import template

register = template.Library()

@register.filter
def convert_to_stars(value):
    integer_part = int(value)
    decimal_part = value - integer_part

    stars = '★' * integer_part  # Full stars for the integer part
    half_star = '½' if decimal_part >= 0.5 else ''  # Half star if the decimal part is >= 0.5

    return stars + half_star
