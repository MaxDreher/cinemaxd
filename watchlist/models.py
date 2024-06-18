from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

# ===================================
# 1-2-Many Models
# ===================================

class Franchise(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'moviedb'
        managed = True


class Oscar(models.Model):
    year_film = models.IntegerField()
    year_ceremony = models.IntegerField()
    ceremony = models.IntegerField()
    category = models.CharField(max_length=255)
    film_title = models.CharField(max_length=255, null=True)
    name = models.CharField(max_length=255, null=True)
    winner = models.BooleanField()

    def __str__(self):
        return f'({self.year_film}) {self.name}'


# ===================================
# M2M Models
# ===================================

class Person(models.Model):
    TMDB_ID = models.IntegerField(primary_key=True)
    IMDB_ID = models.CharField(max_length=255,null=True)
    name = models.CharField(max_length=255,null=True)
    bio = models.TextField(null=True)
    gender = models.IntegerField() # New
    birthday = models.DateField(null=True)
    imgLink = models.CharField(max_length=255,null=True)

    class Meta:
        abstract = True


class Actor(Person):

    def __str__(self):
        return f'{self.name}'

    class Meta:
        app_label = 'moviedb'
        managed = True


class Director(Person):

    def __str__(self):
        return f'{self.name}'

    class Meta:
        app_label = 'moviedb'
        managed = True


class ProdCompany(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255,null=True)
    logo = models.CharField(max_length=255,null=True)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        app_label = 'moviedb'
        managed = True


class Genre(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        app_label = 'moviedb'
        managed = True


class Provider(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        app_label = 'moviedb'
        managed = True


class Keyword(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        app_label = 'moviedb'
        managed = True


class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'moviedb'
        managed = True


class External_ID(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'moviedb'
        managed = True


class Language(models.Model):
    name = models.CharField(max_length=255, unique=True)
    iso_639_1 = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'moviedb'
        managed = True


class Country(models.Model):
    name = models.CharField(max_length=255, unique=True)
    iso_3166_1 = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'moviedb'
        managed = True


class Award(models.Model):
    movie_id = models.IntegerField(null=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    year = models.IntegerField(null=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    recipient = models.CharField(max_length=255, null=True, blank=True)
    recipient_id = models.IntegerField(null=True)
    ceremony = models.IntegerField(null=True)
    year_ceremony = models.IntegerField(null=True)
    win = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

    class Meta:
        app_label = 'moviedb'
        managed = True


class List(models.Model):
    name = models.CharField(max_length=255)
    movies = models.ManyToManyField('Movie', through='MovieList')

    def __str__(self):
        return f'{self.name}'


class Rating(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'moviedb'
        managed = True


# ===================================
# Primary Models
# ===================================


class Movie(models.Model):
    TMDB_ID = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    year = models.IntegerField()
    type_choices = [('movie', 'Movie'), ('series', 'Series')]
    type = models.CharField(max_length=255, choices=type_choices)
    status = models.CharField(max_length=255, null=True, blank=True)  # New
    slug = models.CharField(max_length=255, null=True, blank=True)
    posterLink = models.CharField(max_length=255, blank=True)
    bgLink = models.CharField(max_length=255, null=True, blank=True) # New
    trailerLink = models.CharField(max_length=255, null=True, blank=True) # New
    plot = models.TextField(null=True, blank=True)
    tagline = models.CharField(max_length=255,null=True, blank=True)
    releaseDate = models.DateField()
    decade = models.CharField(max_length=255)
    MPA = models.CharField(max_length=255,null=True, blank=True)
    runtime = models.IntegerField(default=0)
    seasons = models.IntegerField(default=0)
    episodes = models.IntegerField(default=0)
    avg_critical_rating  = models.FloatField(null=True, blank=True)
    franchise  = models.CharField(max_length=255,null=True, blank=True)
    bechdel = models.BooleanField(default=False, null=True, blank=True)
    budget = models.IntegerField(null=True, blank=True)
    revenue = models.IntegerField(null=True, blank=True)
    original_language = models.CharField(max_length=255,null=True, blank=True)
    datetime_added = models.DateTimeField(null=True, blank=True)
    elo = models.FloatField(null=True, blank=True)
    eloMatches = models.IntegerField(default=0)
    eloInclude = models.BooleanField(default=True)

    date = models.DateField(blank=True, null=True)
    favorite = models.BooleanField(default=False)
    rating_choices = [(i / 2, str(i / 2)) for i in range(1, 11)]
    rating = models.FloatField(validators=[MinValueValidator(0.5), MaxValueValidator(5)], choices=rating_choices, null=True)
    review = models.TextField(null=True, blank=True)
    datetime_added = models.DateTimeField(null=True, blank=True)
    seen = models.BooleanField(default=True)
    timesSeen = models.IntegerField()
    service = models.CharField(max_length=255, null=True, blank=True)
    theaters = models.BooleanField(default=False, null=True, blank=True)
    tags = models.ManyToManyField(Tag, through="MovieTag")

    cast = models.ManyToManyField(Actor, through="MovieActor")
    director = models.ManyToManyField(Director, through="MovieDirector")
    genres = models.ManyToManyField(Genre, through="MovieGenre")
    prodCompany = models.ManyToManyField(ProdCompany, through="MovieCompany")
    provider = models.ManyToManyField(Provider, through="MovieProvider")
    awards = models.ManyToManyField(Award, through="MovieAward")
    keywords = models.ManyToManyField(Keyword, through="MovieKeyword")
    external_ids = models.ManyToManyField(External_ID, through="MovieExternal_ID")
    languages = models.ManyToManyField(Language, through="MovieLanguage")
    countries = models.ManyToManyField(Country, through="MovieCountry")
    ratings = models.ManyToManyField(Rating, through="MovieRating")

    def __str__(self):
        return f'{self.title} ({self.year})'

    class Meta:
        unique_together = [['title', 'releaseDate']]  # Enforce uniqueness of title and releaseDate combination
        app_label = 'moviedb'
        managed = True

# ===================================
# Intermediary Models (Movie)
# ===================================
        
class MovieGenre(models.Model):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    class Meta:
        app_label = 'moviedb'
        managed = True


class MovieKeyword(models.Model):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    keyword = models.ForeignKey(Keyword, on_delete=models.CASCADE)
    class Meta:
        app_label = 'moviedb'
        managed = True


class MovieCompany(models.Model):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    company = models.ForeignKey(ProdCompany, on_delete=models.CASCADE)
    class Meta:
        app_label = 'moviedb'
        managed = True


class MovieDirector(models.Model):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    director = models.ForeignKey(Director, on_delete=models.CASCADE)
    class Meta:
        app_label = 'moviedb'
        managed = True


class MovieActor(models.Model):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE)
    role = models.CharField(max_length=255,null=True)
    class Meta:
        app_label = 'moviedb'
        managed = True


class MovieList(models.Model):
    list = models.ForeignKey(List, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    order = models.IntegerField()

    class Meta:
        ordering = ['order']


class MovieTag(models.Model):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    class Meta:
        app_label = 'moviedb'
        managed = True


class MovieAward(models.Model):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    award = models.ForeignKey(Award, on_delete=models.CASCADE)
    class Meta:
        app_label = 'moviedb'
        managed = True


class MovieProvider(models.Model):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    class Meta:
        app_label = 'moviedb'
        managed = True


class MovieExternal_ID(models.Model):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    external_id = models.ForeignKey(External_ID, on_delete=models.CASCADE)
    id_value = models.CharField(max_length=255,null=True)
    url = models.CharField(max_length=255,null=True)

    class Meta:
        app_label = 'moviedb'
        managed = True


class MovieLanguage(models.Model):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    class Meta:
        app_label = 'moviedb'
        managed = True


class MovieCountry(models.Model):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    class Meta:
        app_label = 'moviedb'
        managed = True


class MovieRating(models.Model):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    rating = models.ForeignKey(Rating, on_delete=models.CASCADE)
    value = models.FloatField(null=True)
    standardized = models.FloatField(null=True)

    class Meta:
        app_label = 'moviedb'
        managed = True

