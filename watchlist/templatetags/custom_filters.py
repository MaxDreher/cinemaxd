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
    ret = f"<small class='roboto'> {len(obj)} Oscar Nominations in {obj[0].award.year + 1}<br>"
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

@register.filter(name='parse_birthday')
def parse_year(obj):
    try:
        return f"{obj.name} war born on this day in {obj.birthday.year}."
    except ValueError:
        return ""

@register.filter(name='parse_count')
def parse_year(value):
    try:
        return f"{value} movies"
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
    data = {    "With Abby": {"name": "With Abby", "class": "text-bg-pink", "icon": "bi-heart-fill"},
                "Abby": {"name": "Abby", "class": "text-bg-pink2", "icon": "bi-chat-left-heart"},
                "Andrew": {"name": "Andrew", "class": "text-bg-black-gold", "icon": "bi-git"},
                "Colton": {"name": "Colton", "class": "text-bg-orange", "icon": "bi-rocket-takeoff-fill"},
                "Gaven": {"name": "Gaven", "class": "text-bg-pondering", "icon": "bi-magic"},
                "Mom": {"name": "Mom", "class": "text-bg-mom", "icon": "bi-person-standing-dress"},
                "Dad": {"name": "Dad", "class": "text-bg-dad", "icon": "bi-person-standing"},
                "r/Letterboxd": {"name": "r/Letterboxd", "class": "text-bg-reddit", "icon": "bi-reddit"},
                "IMDB Poster": {"name": "IMDB Poster", "class": "text-bg-imdb", "icon": "bi-play-fill"},
                "Tik Tok": {"name": "Tik Tok", "class": "text-bg-tiktok", "icon": "bi-tiktok"},
                "Gooby": {"name": "Gooby", "class": "text-bg-gooby", "icon": "bi-globe-americas"},
                "Mia": {"name": "Mia", "class": "text-bg-mia", "icon": "bi-palette-fill"},
                "The Yard": {"name": "The Yard", "class": "text-bg-yt", "icon": "bi-youtube"},
                "Will Neff": {"name": "Will Neff", "class": "text-bg-yt", "icon": "bi-youtube"},
                "Schaffarillis": {"name": "Schaffarillis", "class": "text-bg-yt", "icon": "bi-youtube"},
                "Nando v Movies": {"name": "Nando v Movies", "class": "text-bg-yt", "icon": "bi-youtube"},
            }
    try:
        return data[name] 
    except: 
        return {"name": name, "class": "text-bg-secondary", "icon": "bi-tag-fill"}
    