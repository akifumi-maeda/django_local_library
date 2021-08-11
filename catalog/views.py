from django.shortcuts import render

# Create your views here.
from .models import Book, Author, BookInstance, Genre, Language

def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    # The 'all()' is implied by default
    num_authors = Author.objects.count()

    # Genres
    num_genres = Genre.objects.all().count()

    #  books that contain a word "a"
    # num_books_contain_a = Book.objects.filter(title__contains='a').count()

    # Number of visits to this view, as in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances_available,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_genres': num_genres,
        # 'num_books_contain_a': num_books_contain_a,
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with data in the context variable
    return render(request, 'index.html', context=context)

from django.views import generic
from django.db.models import Q
from .forms import BookFilterForm, PaginateByForm

class BookListView(generic.ListView):
    model = Book
    paginate_by = 5

    def get_queryset(self):

        book_list = Book.objects.all()

        '''グローバル検索値を取得'''
        search = self.request.GET.get('search')

        '''フィルター検索値を取得'''
        f_kwargs ={}

        filter_title =  self.request.GET.get('book_title')
        if filter_title:
            f_kwargs['title__icontains'] = filter_title

        filter_first_name =  self.request.GET.get('author_first_name')
        if filter_first_name:
            f_kwargs['author__first_name__icontains'] = filter_first_name

        filter_last_name =  self.request.GET.get('author_last_name')
        if filter_last_name:
            f_kwargs['author__last_name__icontains'] = filter_last_name

        filter_genre = self.request.GET.get('genre_select')
        if filter_genre:
            f_kwargs['genre__pk'] = filter_genre

        filter_language =  self.request.GET.get('language_select')
        if filter_language:
            f_kwargs['language__pk'] = filter_language

        queries = [] # Qオブジェクトを格納するリスト

        if f_kwargs:
            q = Q(**f_kwargs)
            queries.append(q)

        if queries:
            # filter(Q(...) & Q(...) & Q(...))を動的に行っている。
            base_query = queries.pop()
            for query in queries:
                base_query &= query
            book_list = book_list.filter(base_query)

        print(book_list)

        if search:
            # グローバル検索値からクエリを返す
            return Book.objects.filter(Q(title__icontains=search) | Q(author__first_name__icontains=search) | Q(author__last_name__icontains=search))
        elif search == '':
            # グローバル検索値が空白の時、すべてのオブジェクトを返す
            return Book.objects.all()
        else:
            # Filterの検索値からクエリを返す
            return book_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['book_filter_form'] = BookFilterForm(self.request.GET)
        context['paginate_by_form'] = PaginateByForm(self.request.session)
        return context

    def get_paginate_by(self, queryset):
        if 'paginate_by' in self.request.GET:
            self.request.session['paginate_by'] = int(self.request.GET.get('paginate_by'))
        if 'paginate_by' in self.request.session:
            return self.request.session.get('paginate_by')
        else:
            print(int(self.request.GET.get('paginate_by', self.paginate_by)))
            return int(self.request.GET.get('paginate_by', self.paginate_by))

class BookDetailView(generic.DetailView):
    model = Book

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 5

    def get_queryset(self):
        search = self.request.GET.get('search')

        if search:
            return Author.objects.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search))
        else:
            return Author.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["paginate_by_form"] = PaginateByForm(self.request.session)
        return context

    def get_paginate_by(self, queryset):
        if 'paginate_by' in self.request.GET:
            self.request.session['paginate_by'] = int(self.request.GET.get('paginate_by'))
        if 'paginate_by' in self.request.session:
            return self.request.session.get('paginate_by')
        else:
            print(int(self.request.GET.get('paginate_by', self.paginate_by)))
            return int(self.request.GET.get('paginate_by', self.paginate_by))

class AuthorDetailView(generic.DetailView):
    model = Author

from django.contrib.auth.mixins import LoginRequiredMixin

class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')

from django.contrib.auth.mixins import PermissionRequiredMixin

class LoanedBooksAllListView(PermissionRequiredMixin, generic.ListView):
    model = BookInstance
    permission_required = 'catalog.can_mark_returned'
    template_name = 'catalog/bookinstance_list_borrowed_all.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')

import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from catalog.forms import RenewBookForm

@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # if this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            # redirect to a new URL
            return HttpResponseRedirect(reverse('all-borrowed'))

    # if this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from .forms import AuthorCreateForm, BookCreateForm

class AuthorCreate(PermissionRequiredMixin, CreateView):
    model = Author
    form_class = AuthorCreateForm
    # fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial =  {'date_of_death': '11/06/2020'}
    permission_required = 'catalog.can_mark_returned'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Authorを新規作成'
        context['create'] = True
        return context

class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    model = Author
    form_class = AuthorCreateForm
    # fields = '__all__' # Not recommended (potential security issue if more fields added)
    permission_required = 'catalog.can_mark_returned'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Authorを更新'
        context['update'] = True
        return context

class AuthorDelete(PermissionRequiredMixin, DeleteView):
    model = Author
    success_url = reverse_lazy('authors')
    permission_required = 'catalog.can_mark_returned'

class BookCreate(PermissionRequiredMixin, CreateView):
    model = Book
    form_class = BookCreateForm
    # fields =  ['title', 'author', 'summary', 'isbn', 'genre', 'language']
    permission_required = 'catalog.can_mark_returned'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Bookを新規作成'
        context['create'] = True
        return context

class BookUpdate(PermissionRequiredMixin, UpdateView):
    model = Book
    form_class = BookCreateForm
    # fields =  ['title', 'author', 'summary', 'isbn', 'genre', 'language']
    permission_required = 'catalog.can_mark_returned'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Bookを更新'
        context['update'] = True
        return context

class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy('books')
    permission_required = 'catalog.can_mark_returned'