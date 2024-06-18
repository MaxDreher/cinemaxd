import os
import csv
import json
import time
import requests
from slugify import slugify
from datetime import date, datetime
from moviedb.models import *
from moviedb.api_calls import *  
import concurrent.futures
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.db import transaction, IntegrityError
from moviedb.entry import entry

# ===============================================
# Logging and Backup Utility Functions
# ===============================================

# Add a line to a logging file
def add_line_to_log(file_path, line):
    # Read the contents of the file
    with open(file_path, 'r') as file:
        file_contents = file.readlines()

    # Open the file in write mode to overwrite its contents
    with open(file_path, 'w') as file:
        # Write the new line to the file
        file.write(line + '\n')

        # Write the previously stored contents of the file after the new line
        for content in file_contents:
            file.write(content)


# Download a CSV of a given queryset
def download_csv(request, queryset):
    if not request.user.is_staff:
        raise PermissionDenied
    
    model = queryset.model

    model_name = model.__name__
    model_fields = model._meta.fields
    field_names = [field.name for field in model_fields]

    # Generate the file path based on the model name
    file_name = f"{slugify(model_name)}_data.csv"
    file_path = os.path.join("moviedb", "data", "backups", file_name)

    # Write CSV data to a file
    with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
        # Create a CSV writer
        writer = csv.writer(csv_file, delimiter=";")
        
        # Write header row
        writer.writerow(field_names)

        # Write data rows
        for row in queryset:
            values = []
            for field in field_names:
                value = getattr(row, field)
                if callable(value):
                    try:
                        value = value() or ''
                    except:
                        value = 'Error retrieving value'
                if value is None:
                    value = ''
                values.append(value)
            writer.writerow(values)


# ===============================================
# Secondary API Call Processing Functions
# ===============================================

# Process and create an Actor object given an ID
def process_actor(actor_id):
    # Check if the actor with the provided TMDB ID already exists
    existing_actor = Actor.objects.filter(TMDB_ID=actor_id).first()

    if existing_actor:
        return existing_actor

    # If the actor doesn't exist, retrieve data from the API and create/update the actor
    actor_tmdb = get_person_TMDB(actor_id)
    if actor_tmdb:
        actor_data = {
            'TMDB_ID': actor_tmdb.get("id"),
            'IMDB_ID': actor_tmdb.get("imdb_id"),
            'name': actor_tmdb.get("name"),
            'gender': actor_tmdb.get("gender"),
            'bio': actor_tmdb.get("biography"),
            'birthday': actor_tmdb.get("birthday"),
            'imgLink': actor_tmdb.get("profile_path"),
        }

        try:
            actor, created = Actor.objects.get_or_create(TMDB_ID=actor_data['TMDB_ID'], defaults=actor_data)

            if not created:
                Actor.objects.filter(Q(TMDB_ID=actor_data['TMDB_ID']) | Q(IMDB_ID=actor_data['IMDB_ID'])).update(**actor_data)
        
        except Exception as e:
            print(f"Error processing actor: {e}")

        return actor
    else:
        pass


# Process and create a Director object given an ID
def process_director(director_id):
    # Check if the director with the provided TMDB ID already exists
    existing_director = Director.objects.filter(TMDB_ID=director_id).first()

    if existing_director:
        return existing_director

    # If the actor doesn't exist, retrieve data from the API and create/update the actor
    director_tmdb = get_person_TMDB(director_id)

    if director_tmdb:
        director_data = {
            'TMDB_ID': director_tmdb.get("id"),
            'IMDB_ID': director_tmdb.get("imdb_id"),
            'name': director_tmdb.get("name"),
            'gender': director_tmdb.get("gender"),
            'bio': director_tmdb.get("biography"),
            'birthday': director_tmdb.get("birthday"),
            'imgLink': director_tmdb.get("profile_path"),
        }

        try:
            director, created = Director.objects.get_or_create(TMDB_ID=director_data['TMDB_ID'], defaults=director_data)

            if not created:
                Director.objects.filter(Q(TMDB_ID=director_data['TMDB_ID']) | Q(IMDB_ID=director_data['IMDB_ID'])).update(**director_data)
        
        except Exception as e:
            print(f"Error processing director: {e}")

        return director
    else:
        pass


# Process production company data and save it to the database.
def process_prod_company(company_id):
    # Check if a company with the provided TMDB ID already exists
    existing_company = ProdCompany.objects.filter(pk=company_id).first()

    if existing_company:
        return existing_company

    # If the company doesn't exist, retrieve data from the API and create/update the company
    company_tmdb = get_company_TMDB(company_id)

    if company_tmdb:
        company_data = {
            'id': company_tmdb.get("id"),
            'name': company_tmdb.get("name"),
            'logo': company_tmdb.get("logo_path"),
        }

        # Create a ProdCompany instance
        company = ProdCompany(**company_data)

        try:
            company, created = ProdCompany.objects.get_or_create(id=company_data['id'], defaults=company_data)

            if not created:
                ProdCompany.objects.filter(Q(TMDB_ID=company_data['TMDB_ID']) | Q(IMDB_ID=company_data['IMDB_ID'])).update(**company_data)
        
        except Exception as e:
            print(f"Error processing production company: {e}")

        return company
    else:
        pass


def get_awards(title, year):
    with open('./moviedb/data/oscars/the_oscar_award.json') as f, open('./moviedb/data/oscars/the_oscar_map.json') as g:
        data = json.load(f)
        map = json.load(g)
        return [{'year': item.get('year_film'), 'award': map[(item.get('category'))], 'win': item.get('winner')} for item in data if (item.get('film') == title and item.get('year_film') == year)]


# ===============================================
# DATABASE UPDATE FUNCTIONS
# ===============================================

def handle_tags(data, movie):
    tags = data.get('tags')
    if tags:
        tag_names = set(tags)  # Using a set to avoid duplicate names
        existing_tags = {tag.name: tag for tag in Tag.objects.filter(name__in=tag_names)}
        new_tags = [Tag(name=t) for t in tag_names if t not in existing_tags]
        
        if new_tags:
            Tag.objects.bulk_create(new_tags)
        
        all_tags = list(Tag.objects.filter(name__in=tag_names))  # Query all tags again to ensure we have all the tags
        
        MovieTag.objects.bulk_create([MovieTag(movie=movie, tag=tag) for tag in all_tags])


def handle_many_to_many(many_to_many_data, new_movie):

    def handle_cast():
        cast = many_to_many_data.get('cast')
        if cast:
            cast_entries = [
                MovieActor(movie=new_movie, actor=process_actor(item.get('id')), role=item.get('role'))
                for item in cast
            ]
            MovieActor.objects.bulk_create(cast_entries)


    def handle_directors():
        directors = many_to_many_data.get('directors')
        if directors:
            director_entries = [
                MovieDirector(movie=new_movie, director=process_director(item.get('id')))
                for item in directors
            ]
            MovieDirector.objects.bulk_create(director_entries)


    def handle_companies():
        data = many_to_many_data.get('production_companies')
        if data:
            entries = [
                MovieCompany(movie=new_movie, company=process_prod_company(item.get('id')))
                for item in data
            ]
            MovieCompany.objects.bulk_create(entries)


    def handle_genres():
        genres = many_to_many_data.get('genres')
        if genres:
            genre_set = []
            for g in genres:
                genre, created = Genre.objects.get_or_create(**g)
                genre_set.append(genre)

            MovieGenre.objects.bulk_create([MovieGenre(movie=new_movie, genre=genre) for genre in genre_set])


    def handle_providers():
        data = many_to_many_data.get('providers')
        if data:
            data_set = []
            for x in data:
                item, created = Provider.objects.get_or_create(**x)
                data_set.append(item)

            MovieProvider.objects.bulk_create([MovieProvider(movie=new_movie, provider=item) for item in data_set])


    def handle_keywords():
        data = many_to_many_data.get('keywords')
        if data:
            data_set = []
            for x in data:
                item, created = Keyword.objects.get_or_create(**x)
                data_set.append(item)

            MovieKeyword.objects.bulk_create([MovieKeyword(movie=new_movie, keyword=item) for item in data_set])


    def handle_languages():
        data = many_to_many_data.get('languages')
        if data:
            data_set = []
            for x in data:
                item, created = Language.objects.get_or_create(**x)
                data_set.append(item)

            MovieLanguage.objects.bulk_create([MovieLanguage(movie=new_movie, language=item) for item in data_set])


    def handle_countries():
        data = many_to_many_data.get('countries')
        if data:
            data_set = []
            for x in data:
                item, created = Country.objects.get_or_create(**x)
                data_set.append(item)

            MovieCountry.objects.bulk_create([MovieCountry(movie=new_movie, country=item) for item in data_set])


    def handle_externalids():
        data = many_to_many_data.get('external_ids')
        if data:
            data_set = []
            for x in data:
                item, created = External_ID.objects.get_or_create(name=x.get('name'))
                data_set.append({'item': item, 'id': x.get('id'), 'url': x.get('url')})

            MovieExternal_ID.objects.bulk_create([MovieExternal_ID(movie=new_movie, external_id=item.get('item'), id_value=item.get('id'), url=item.get('url')) for item in data_set])


    def handle_ratings():
        data = many_to_many_data.get('ratings')
        if data:
            data_set = []
            for x in data:
                item, created = Rating.objects.get_or_create(name=x.get('name'))
                data_set.append({'item': item, 'value': x.get('value'), 'standardized': x.get('standardized')})

            MovieRating.objects.bulk_create([MovieRating(movie=new_movie, rating=item.get('item'), value=item.get('value'), standardized=item.get('standardized')) for item in data_set])


    handle_tags(many_to_many_data, new_movie)
    handle_cast()
    handle_directors()
    handle_companies()
    handle_genres()
    handle_providers()
    handle_keywords()
    handle_languages()
    handle_countries()
    handle_externalids()
    handle_ratings()


def make_api_calls_and_update_watchlist(input_package):
    movie = entry(input_package)
    full_data = movie.parse_data()
    main_data = {k: v for k, v in full_data.items() if k != 'many-to-many'}
    many_to_many_data = full_data.get('many-to-many')

    if main_data:
        with transaction.atomic():
            new_movie = Movie.objects.create(**main_data)
            handle_many_to_many(many_to_many_data, new_movie)

    return


def make_api_calls_and_update_database(input_package):
    start_time = time.time()

    id = input_package.get('id', None)
    type = input_package.get('type', None)

    existing = Movie.objects.filter(TMDB_ID=id, type=type).first()

    if existing and existing.releaseDate < existing.date:
        data = {**input_package, **{'datetime_added': timezone.now()}}
        for attr, value in data.items(): 
            if attr == "tags":
                continue
            setattr(existing, attr, value)
        if data.get('tags'):
            handle_tags({'tags': data.get('tags').split(',')}, existing)

        existing.save()
    else:
        print(f"No viable Watchlist data for Entry with ID: {id} ({type})). Processing API Calls...")
        if existing:
            existing.delete()

        make_api_calls_and_update_watchlist(input_package)

    parent = os.path.dirname(os.path.abspath(__file__))
    destination_path = os.path.join(parent, 'data', 'logs', 'watchlog_log.txt')

    movie = Movie.objects.get(pk=id)

    log = f"{datetime.today()}\t{movie.title} ({movie.year})\t{time.time() - start_time}s."
    add_line_to_log(destination_path, log)

    print(f"{movie.title} added to the Watchlog in {time.time() - start_time} seconds.")

