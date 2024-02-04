# custom_filters.py
from django import template

register = template.Library()

@register.filter
def convert_to_stars(value):
    try:
        integer_part = int(value)
        decimal_part = value - integer_part

        stars = '★' * integer_part  # Full stars for the integer part
        half_star = '½' if decimal_part >= 0.5 else ''  # Half star if the decimal part is >= 0.5

        return stars + half_star
    except:
        return ""
    
@register.filter
def convert_to_hrs(value):
    try:
        hrs = value // 60
        mins = int(value % 60)
        return f"{hrs}hr {mins}min"
    except:
        return value

@register.filter(name='parse_year')
def parse_year(value):
    try:
        return int(value)
    except ValueError:
        return value
    
@register.filter
def split_string(value, delimiter):
    return value.split(delimiter)
