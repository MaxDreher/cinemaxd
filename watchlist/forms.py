from django import forms

SERVICES = [
    ('', ' '),  # Empty choice for the default/placeholder
    ('Netflix', 'Netflix'),
    ('Hulu', 'Hulu'),
    ('Max', 'Max'),
    ('Disney Plus', 'Disney Plus'),
    ('Apple TV Plus', 'Apple TV Plus'),
    ('Amazon Prime Video', 'Amazon Prime Video'),
    ('Peacock Premium', 'Peacock Premium'),
    ('Paramount Plus', 'Paramount Plus'),
    ('Paramount+ Amazon Channel', 'Paramount+ Amazon Channel'),
    ('Tubi TV', 'Tubi TV'),
    ('Freevee', 'Freevee'),
    ('TNT', 'TNT'),
    ('TBS', 'TBS'),
    ('Youtube', 'Youtube'),
    ('Youtube Movies', 'Youtube Movies'),
    ('Tik Tok', 'Tik Tok'),
]

class MovieForm(forms.Form):
    title = forms.CharField(label='Title', widget=forms.TextInput(attrs={'class': 'form-control input rounded-1 dark-input'}))
    year = forms.IntegerField(label='Year', widget=forms.TextInput(attrs={'class': 'form-control input rounded-1 dark-input'}))
    rating = forms.FloatField(label='Rating', widget=forms.TextInput(attrs={'class': 'form-control input rounded-1 dark-input'}))
    review = forms.CharField(label='Review', widget=forms.Textarea(attrs={'class': 'form-control input rounded-1 dark-input'}), required=False)
    date_watched = forms.DateField(label='Date Watched')
    service = forms.ChoiceField(label="Service", choices=SERVICES)
    theaters = forms.BooleanField(label = "Theater", required=False)

class WatchlistForm(forms.Form):
    title = forms.CharField(label='Title', widget=forms.TextInput(attrs={'class': 'form-control input rounded-1 dark-input'}))
    year = forms.IntegerField(label='Year', widget=forms.TextInput(attrs={'class': 'form-control input rounded-1 dark-input'}))
    date_added = forms.DateField(label='Date Added')
    reason = forms.CharField(label='Reason', widget=forms.Textarea(attrs={'class': 'form-control input rounded-1 dark-input'}), required=False)

class RankingForm(forms.Form):
    title = forms.CharField(label='Title', widget=forms.TextInput(attrs={'class': 'form-control input rounded-1 dark-input'}))
    year = forms.IntegerField(label='Year', widget=forms.TextInput(attrs={'class': 'form-control input rounded-1 dark-input'}))
