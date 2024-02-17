from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

# ===================================
# M2M Models
# ===================================

class Actor(models.Model):
    TMDB_ID = models.IntegerField(primary_key=True)
    IMDB_ID = models.CharField(max_length=255,null=True)
    name = models.CharField(max_length=255,null=True)
    bio = models.TextField(null=True)
    gender = models.IntegerField() # New
    birthday = models.DateField(null=True)
    imgLink = models.CharField(max_length=255,null=True)

    class Meta:
        db_table = 'ACTORS'
        app_label = 'watchlist'
        managed = True


class Director(models.Model):
    TMDB_ID = models.IntegerField(primary_key=True)
    IMDB_ID = models.CharField(max_length=255,null=True)
    name = models.CharField(max_length=255,null=True)
    bio = models.TextField(null=True)
    gender = models.IntegerField() # New
    birthday = models.DateField(null=True)
    imgLink = models.CharField(max_length=255,null=True)

    class Meta:
        db_table = 'DIRECTORS'
        app_label = 'watchlist'
        managed = True


class ProdCompany(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255,null=True)
    logo = models.CharField(max_length=255,null=True)

    class Meta:
        db_table = 'PRODUCTION_COMPANIES'
        app_label = 'watchlist'
        managed = True


class Genre(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'GENRES'
        app_label = 'watchlist'
        managed = True


class Provider(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'PROVIDERS'
        app_label = 'watchlist'
        managed = True


class Keyword(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'KEYWORDS'
        app_label = 'watchlist'
        managed = True


class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'TAGS'
        app_label = 'watchlist'
        managed = True


class Award(models.Model):
    name = models.CharField(max_length=255)
    year = models.IntegerField()
    
    def __str__(self):
        return self.name

    class Meta:
        db_table = 'AWARDS'
        app_label = 'watchlist'
        managed = True
        unique_together = ('name', 'year')


class List(models.Model):
    name = models.CharField(max_length=255)
    movies = models.ManyToManyField('Movie', through='MovieList')

# ===================================
# Primary Models
# ===================================

class Movie(models.Model):
    TMDB_ID = models.IntegerField(primary_key=True)
    IMDB_ID = models.CharField(max_length=255)

    type_choices = [('movie', 'Movie'),('series', 'Series'),]
    type = models.CharField(max_length=255, choices=type_choices)
    status = models.CharField(max_length=255, null=True) # New

    title = models.CharField(max_length=255)
    year = models.IntegerField()
    rating_choices = [(i / 2, str(i / 2)) for i in range(1, 11)]
    rating = models.FloatField(validators=[MinValueValidator(0.5), MaxValueValidator(5)], choices=rating_choices, null=True)
    review = models.TextField(null=True)
    date = models.DateField(null=True)
    favorite = models.BooleanField(null=True)
    datetime_added = models.DateTimeField(null=True)

    timesSeen = models.IntegerField()
    seasonsSeen = models.IntegerField(null=True) # New
    episodesSeen = models.IntegerField(null=True) # New

    posterLink = models.CharField(max_length=255)
    bgLink = models.CharField(max_length=255, null=True) # New
    trailerLink = models.CharField(max_length=255, null=True) # New

    plot = models.TextField(null=True)
    tagline = models.CharField(max_length=255,null=True)
    releaseDate = models.DateField()
    decade = models.CharField(max_length=255)
    MPA = models.CharField(max_length=255,null=True)

    runtime = models.IntegerField(null=True)
    seasons = models.IntegerField(null=True)
    episodes = models.IntegerField(null=True)
    
    languages = models.CharField(max_length=255,null=True)
    countrys = models.CharField(max_length=255,null=True)

    IMDB = models.FloatField(null=True)
    TMDB = models.FloatField(null=True)
    MC = models.IntegerField(null=True)
    RTCritic = models.IntegerField(null=True)
    RTUser = models.IntegerField(null=True)
    LBXD = models.FloatField(null=True)
    avg_critical_rating  = models.FloatField(null=True)

    service = models.TextField(null=True)
    theaters = models.BooleanField(null=True)

    genres = models.ManyToManyField(Genre, through="MovieGenre")
    keywords = models.ManyToManyField(Keyword, through="MovieKeyword")
    cast = models.ManyToManyField(Actor, through="MovieActor")
    director = models.ManyToManyField(Director, through="MovieDirector")
    prodCompany = models.ManyToManyField(ProdCompany, through="MovieCompany")
    tags = models.ManyToManyField(Tag, through="MovieTag")
    awards = models.ManyToManyField(Award, through="MovieAward")


    elo = models.FloatField(null=True)
    eloMatches = models.IntegerField()
        
    class Meta:
        db_table = 'WATCHLOG'  # Set the table name to WATCHLIST
        unique_together = [['title', 'releaseDate']]  # Enforce uniqueness of title and releaseDate combination
        app_label = 'watchlist'
        managed = True


class WatchlistMovie(models.Model):
    TMDB_ID = models.IntegerField(primary_key=True)
    IMDB_ID = models.CharField(max_length=255)

    type_choices = [('movie', 'Movie'),('series', 'Series'),]
    type = models.CharField(max_length=255, choices=type_choices)
    status = models.CharField(max_length=255, null=True) # New

    title = models.CharField(max_length=255)
    year = models.IntegerField()
    date = models.DateField(null=True)
    favorite = models.BooleanField(null=True)
    reason = models.TextField(null=True)

    posterLink = models.CharField(max_length=255)
    bgLink = models.CharField(max_length=255, null=True) # New
    trailerLink = models.CharField(max_length=255, null=True) # New

    plot = models.TextField(null=True)
    tagline = models.CharField(max_length=255,null=True)
    releaseDate = models.DateField()
    decade = models.CharField(max_length=255)
    MPA = models.CharField(max_length=255,null=True)

    runtime = models.IntegerField(null=True)
    seasons = models.IntegerField(null=True)
    episodes = models.IntegerField(null=True)

    languages = models.CharField(max_length=255,null=True)
    countrys = models.CharField(max_length=255,null=True)

    IMDB = models.FloatField(null=True)
    TMDB = models.FloatField(null=True)
    MC = models.IntegerField(null=True)
    RTCritic = models.IntegerField(null=True)
    RTUser = models.IntegerField(null=True)
    LBXD = models.FloatField(null=True)
    avg_critical_rating  = models.FloatField(null=True)

    tags = models.ManyToManyField(Tag, through="WatchlistTag")
    genres = models.ManyToManyField(Genre, through="WatchlistGenre")
    keywords = models.ManyToManyField(Keyword, through="WatchlistKeyword")
    cast = models.ManyToManyField(Actor, through="WatchlistActor")
    director = models.ManyToManyField(Director, through="WatchlistDirector")
    prodCompany = models.ManyToManyField(ProdCompany, through="WatchlistCompany")
    provider = models.ManyToManyField(Provider, through="WatchlistProvider")
    awards = models.ManyToManyField(Award, through="WatchlistAward")

    class Meta:
        db_table = 'WATCHLIST'  # Set the table name to WATCHLIST
        unique_together = [['title', 'releaseDate']]  # Enforce uniqueness of title and releaseDate combination
        app_label = 'watchlist'
        managed = True

# ===================================
# Intermediary Models (Movie)
# ===================================
        
class MovieGenre(models.Model):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    class Meta:
        db_table = 'MOVIE_GENRE'  # Set the table name to WATCHLIST
        app_label = 'watchlist'
        managed = True


class MovieKeyword(models.Model):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    keyword = models.ForeignKey(Keyword, on_delete=models.CASCADE)
    class Meta:
        db_table = 'MOVIE_KEYWORD'  # Set the table name to WATCHLIST
        app_label = 'watchlist'
        managed = True


class MovieCompany(models.Model):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    company = models.ForeignKey(ProdCompany, on_delete=models.CASCADE)
    class Meta:
        db_table = 'MOVIE_COMPANY'  # Set the table name to WATCHLIST
        app_label = 'watchlist'
        managed = True


class MovieDirector(models.Model):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    director = models.ForeignKey(Director, on_delete=models.CASCADE)
    class Meta:
        db_table = 'MOVIE_DIRECTOR'  # Set the table name to WATCHLIST
        app_label = 'watchlist'
        managed = True


class MovieActor(models.Model):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE)
    role = models.CharField(max_length=255,null=True)
    class Meta:
        db_table = 'MOVIE_ACTOR'  # Set the table name to WATCHLIST
        app_label = 'watchlist'
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
        db_table = 'MOVIE_TAG' 
        app_label = 'watchlist'
        managed = True


class MovieAward(models.Model):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    award = models.ForeignKey(Award, on_delete=models.CASCADE)
    winner = models.BooleanField()
    class Meta:
        db_table = 'MOVIE_AWARD'  # Set the table name to WATCHLIST
        app_label = 'watchlist'
        managed = True

# ===================================
# Intermediary Models (Watchlist)
# ===================================     

class WatchlistTag(models.Model):
    movie = models.ForeignKey('WatchlistMovie', on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    class Meta:
        db_table = 'WATCHLIST_TAG'  # Set the table name to WATCHLIST
        app_label = 'watchlist'
        managed = True


class WatchlistGenre(models.Model):
    movie = models.ForeignKey('WatchlistMovie', on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    class Meta:
        db_table = 'WATCHLIST_GENRE'  # Set the table name to WATCHLIST
        app_label = 'watchlist'
        managed = True


class WatchlistKeyword(models.Model):
    movie = models.ForeignKey('WatchlistMovie', on_delete=models.CASCADE)
    keyword = models.ForeignKey(Keyword, on_delete=models.CASCADE)
    class Meta:
        db_table = 'WATCHLIST_KEYWORD'  # Set the table name to WATCHLIST
        app_label = 'watchlist'
        managed = True


class WatchlistCompany(models.Model):
    movie = models.ForeignKey('WatchlistMovie', on_delete=models.CASCADE)
    company = models.ForeignKey(ProdCompany, on_delete=models.CASCADE)
    class Meta:
        db_table = 'WATCHLIST_COMPANY'  # Set the table name to WATCHLIST
        app_label = 'watchlist'
        managed = True


class WatchlistDirector(models.Model):
    movie = models.ForeignKey('WatchlistMovie', on_delete=models.CASCADE)
    director = models.ForeignKey(Director, on_delete=models.CASCADE)
    class Meta:
        db_table = 'WATCHLIST_DIRECTOR'  # Set the table name to WATCHLIST
        app_label = 'watchlist'
        managed = True


class WatchlistActor(models.Model):
    movie = models.ForeignKey('WatchlistMovie', on_delete=models.CASCADE)
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE)
    role = models.CharField(max_length=255,null=True)
    class Meta:
        db_table = 'WATCHLIST_ACTOR'  # Set the table name to WATCHLIST
        app_label = 'watchlist'
        managed = True


class WatchlistProvider(models.Model):
    movie = models.ForeignKey('WatchlistMovie', on_delete=models.CASCADE)
    actor = models.ForeignKey(Provider, on_delete=models.CASCADE)
    class Meta:
        db_table = 'WATCHLIST_PROVIDER' 
        app_label = 'watchlist'
        managed = True


class WatchlistAward(models.Model):
    movie = models.ForeignKey('WatchlistMovie', on_delete=models.CASCADE)
    award = models.ForeignKey(Award, on_delete=models.CASCADE)
    winner = models.BooleanField()
    class Meta:
        db_table = 'WATCHLIST_AWARD'  # Set the table name to WATCHLIST
        app_label = 'watchlist'
        managed = True
