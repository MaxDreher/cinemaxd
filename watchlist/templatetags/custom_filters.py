# custom_filters.py
from django import template
import math
from datetime import *

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


@register.filter
def convert_to_eps(value):
    try:
        return f"{value} episodes"
    except:
        return value


@register.filter
def convert_elo_to_stars(value):
    if value <= 1000:
        return f"★ {round(0.0 + ((value / 1000) * 0.50),2)} "
    elif 1000 < value < 2000:
        range_start = (value - 1000) // 100 * 0.5
        return f"★ {round((range_start + ((value - 1000) % 100 / 100) * 0.49) + 0.50,2)} "
    else:
        return f"★ {round(5.0 + ((value / 2000) * 0.50),2)} "


@register.filter(name="parse_oscar")
def parse_oscar(obj):
    ceremony = obj[0].award.ceremony

    ret = f"<small class='roboto'>{len(obj)} Nominations at the {to_ordinal(ceremony)} Oscars.<hr class='my-1'>"
    try:
        for item in obj:
            ret += f"{"<b>" if (item.award.win) else ""}{item.award.year} {item.award.category} {"Winner" if (item.award.win) else "Nominee"}{"</b>" if (item.award.win) else ""}<br>"
        return (ret + "</small>")
    except:
        return ""


@register.filter(name='parse_year')
def parse_year(value):
    try:
        return int(value)
    except ValueError:
        return value


@register.filter(name='parse_birthday')
def parse_year(obj):
    try:
        return f"{obj.name} war born on this day in {obj.birthday.year}."
    except ValueError:
        return ""


@register.filter(name='parse_count')
def parse_year(value):
    try:
        return f"<i class='bi bi-film'></i> {value}"
    except ValueError:
        return ""


@register.filter(name="parse_nominees")
def parse_nominees(obj):
    ret = "<small class='roboto'>"
    try:
        for item in obj:
            ret += f"{"<b>" if (item['seen']) else ""}{"<i class='bi bi-trophy'></i>" if (item['win']) else ""} {item['title']} ({item['year']}){"</b>" if (item['seen']) else ""}<br>"
        return (ret + "</small>")
    except:
        return ""


@register.filter
def split_string(value, delimiter):
    return value.split(delimiter)


@register.filter
def process_badge(name):
    data = {    
        "With Abby": {"name": "With Abby", "class": "text-bg-pink", "icon": "bi-people-fill"},
        "Abby": {"name": "Abby", "class": "text-bg-pink2", "icon": "bi-heart-fill"},

        "With Andrew": {"name": "With Andrew", "class": "text-bg-black-gold", "icon": "bi-people-fill"},
        "Andrew": {"name": "Andrew", "class": "text-bg-black-gold", "icon": "bi-git"},

        "With Mom": {"name": "With Mom", "class": "text-bg-mom", "icon": "bi-people-fill"},
        "Mom": {"name": "Mom", "class": "text-bg-mom", "icon": "bi-person-standing-dress"},

        "With Dad": {"name": "With Dad", "class": "text-bg-dad", "icon": "bi-people-fill"},
        "Dad": {"name": "Dad", "class": "text-bg-dad", "icon": "bi-person-standing"},

        "With Mia": {"name": "With Mia", "class": "text-bg-mia", "icon": "bi-people-fill"},
        "Mia": {"name": "Mia", "class": "text-bg-mia", "icon": "bi-palette-fill"},

        "Colton": {"name": "Colton", "class": "text-bg-orange", "icon": "bi-rocket-takeoff-fill"},
        "Gaven": {"name": "Gaven", "class": "text-bg-pondering", "icon": "bi-magic"},
        "Hayden": {"name": "Hayden", "class": "text-bg-hayden", "icon": "bi-calculator-fill"},
        "Gooby": {"name": "Gooby", "class": "text-bg-gooby", "icon": "bi-globe-americas"},

        "Reddit": {"name": "Reddit", "class": "text-bg-reddit", "icon": "bi-reddit"},
        "IMDB Poster": {"name": "IMDB Poster", "class": "text-bg-imdb", "icon": "bi-play-fill"},

        "The Yard": {"name": "The Yard", "class": "text-bg-yard", "icon": "bi-mic-fill"},
        "The Ringer": {"name": "The Ringer", "class": "text-bg-ringer", "icon": "bi-mic-fill"},

        "Schaffarillis": {"name": "Schaffarillis", "class": "text-bg-yt", "icon": "bi-youtube"},
        "Nando v Movies": {"name": "Nando v Movies", "class": "text-bg-yt", "icon": "bi-youtube"},
        "Tik Tok": {"name": "Tik Tok", "class": "text-bg-tiktok", "icon": "bi-tiktok"},
    }

    try:
        return data[name] 
    except: 
        return {"name": name, "class": "text-bg-secondary", "icon": "bi-tag-fill"}


@register.filter
def to_ordinal(value):
    if 11 <= (value % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(value % 10, 4)]
    return str(value) + suffix


@register.filter
def convert_to_elorating(value):
    try:
        return '★ ' + str(round(value,2))
    except:
        return ""


@register.filter
def convert_to_elorating_prediciton(value):
    try:
        return f"Predicted  ★ {str(round(value,2))}"
    except:
        return ""


@register.filter
def convert_to_elorating_diff(value, bool):
    try:
        return f"{"↑" if bool else "↓"} ★ {str(round(value,2))}"
    except:
        return ""


@register.filter
def absolute(value):
    return abs(value)


@register.filter
def on_this_day(value):
    today = date.today()
    if today.year - value == 0:
        return f"Releasing Today!"
    else:
        return f"Released {today.year - value} Years Ago on This Day in {value}."


@register.filter
def rating_format(value, name):
    if "Rotten Tomatoes" in name:
        return f"{int(float(value))}%"
    elif "Metacritic" in name:
        return f"{int(float(value))}"
    else:
        return value
