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
def convert_to_rating(value):
    try:
        return '★ ' + str(round(value,2)) +' avg'
    except ValueError:
        return ""

@register.filter
def convert_to_hrs(value):
    try:
        hrs = value // 60
        mins = int(value % 60)
        return f"{hrs}hr {mins}min"
    except:
        return value

@register.filter
def convert_to_eps(value):
    try:
        return f"{value} episodes"
    except:
        return value

@register.filter(name="parse_oscar")
def parse_oscar(obj):
    ret = "<small class='roboto'>"
    try:
        for item in obj:
            ret += f"{"<b>" if (item.winner) else ""}{item.award.year} {item.award.name} {"Winner" if (item.winner) else "Nominee"}{"</b>" if (item.winner) else ""}<br>"
        return (ret + "</small>")
    except:
        return ""

@register.filter(name='parse_year')
def parse_year(value):
    try:
        return int(value)
    except ValueError:
        return value
    
@register.filter
def split_string(value, delimiter):
    return value.split(delimiter)

