from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import forms
from django.shortcuts import render
from django.views.decorators.http import require_POST

from GenomelEditor.forms import UploadChantsForm, UploadSourcesForm
from GenomelEditor.models import Chant, Melody, Source


# Create your views here.

def index(request):
    n_chants = Chant.objects.count()
    n_melodies = Melody.objects.count()
    percent_done = 0
    if n_chants > 0:
        percent_done = n_melodies / n_chants
    context = {'n_melodies': n_melodies,
               'n_chants': n_chants,
               'percent_done': percent_done}
    return render(request, 'index.html', context)


@login_required
def annotate(request):
    username = request.user.username
    # return render(request, 'index.html')
    # TODO Return the melody annotation page.
    return index(request)


@user_passes_test(lambda u: u.is_superuser)
@require_POST
def upload_chants(request):
    """Upload chants CSV file and import into database."""
    # Print the first 10 chants to the console.
    # print('Request files: {}'.format(request.FILES))

    form = UploadChantsForm(request.POST, request.FILES)

    # print('Form: {}'.format(form))
    # print('Cleaned data: {}'.format(form.cleaned_data))
    chants_csv = form.cleaned_data['chants_csv']

    chants = Chant.chants_from_csv_file(chants_csv)
    print('Created {} chants.'.format(len(chants)))
    Chant.objects.bulk_create(chants)

    return index(request)


@user_passes_test(lambda u: u.is_superuser)
@require_POST
def upload_sources(request):
    """Upload sources CSV file and import into database."""
    print('Request files: {}'.format(request.FILES))

    form = UploadSourcesForm(request.POST, request.FILES)
    print('Form: {}'.format(form))
    print('Cleaned data: {}'.format(form.cleaned_data))

    sources_csv = form.cleaned_data['sources_csv']
    sources = Source.sources_from_csv_file(sources_csv)
    print('Created {} sources.'.format(len(sources)))
    Source.objects.bulk_create(sources)

    return index(request)


def login_user(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        # A backend authenticated the credentials
        login(request, user)
        # TODO: redirect to the melody annotation page.
        return annotate(request)
    else:
        return index(request)


def logout_user(request):
    logout(request)
    return index(request)
