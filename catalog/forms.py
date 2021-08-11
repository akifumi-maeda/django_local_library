import datetime

from django import forms
from django.contrib.auth import models
from django.core.exceptions import ValidationError
from django.forms import fields
from django.utils.translation import ugettext_lazy as _

class RenewBookForm(forms.Form):
    renewal_date = forms.DateField(help_text="Enter a date between now and 4 weeks (default 3).")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control w-50"

    def clean_renewal_date(self):
        data = self.cleaned_data['renewal_date']

        # Check if date is not in the past.
        if data < datetime.date.today():
            raise ValidationError(_('Invalid date - renewal in past'))

        # Check if a date is in the allowed range (+4 weeks from today).
        if data > datetime.date.today() + datetime.timedelta(weeks=4):
            raise ValidationError(_('Invalid date - renewal more than 4 weeks ahead'))

        # Remember to always return the cleaned data.
        return data

from .models import Author, Book

class AuthorCreateForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control mb-3"

class BookCreateForm(forms.ModelForm):

    class Meta:
        model = Book
        fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control mb-3"

class PaginateByForm(forms.Form):
    '''ユーザー指定ぺージネイション'''
    paginate_by = forms.ChoiceField(
        choices=(
            (5, '5'),
            (10, '10'),
            (15, '15'),
            (25, '25'),
            (50, '50'),
        ),
        required=True,
        widget=forms.widgets.Select(attrs={'class': 'form-select'},),
    )

from .models import Genre, Language

class BookFilterForm(forms.Form):
    book_title = forms.CharField(
        max_length=200,
        required=False,
        label='Title',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    author_first_name = forms.CharField(
        max_length=100,
        required=False,
        label='First name',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    author_last_name = forms.CharField(
        max_length=100,
        required=False,
        label='Last name',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    genre_select = forms.ModelChoiceField(
        Genre.objects.all(),
        required=False,
        label='Genre',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    language_select = forms.ModelChoiceField(
        Language.objects.all(),
        required=False,
        label='Language',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )