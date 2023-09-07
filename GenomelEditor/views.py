import time

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.forms import forms
from django.shortcuts import render
from django.views.decorators.http import require_POST

from GenomelEditor.forms import UploadChantsForm, UploadSourcesForm
from GenomelEditor.models import Chant, Melody, Source
from GenomelEditor.utils import get_full_text_for_cantus_id


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
    # return render(request, 'index.html')

    context = {'chant': None,
               'melody': None}

    # Assign the next chant to be annotated to the user.
    # First, check if the user has a melody in transcription.
    # If so, retrieve its chant and use the "in progress" context.
    melody_in_transcription = Melody.objects.filter(user=request.user).\
        filter(is_in_transcription=True).\
        order_by('timestamp').first()
    if melody_in_transcription is not None:
        context['melody'] = melody_in_transcription
        context['chant'] = Chant.objects.fiilter(id=melody_in_transcription.chant)
        return render(request, 'annotate.html', context)

    # Now we know that the user has no melody in progress. We assign the next chant.
    chant = Chant.objects.filter(Q(volpiano='')).first()
    print('Found chant: {}'.format(chant))
    if chant.volpiano is None:
        print('...volpiano is None')
    elif chant.volpiano == '':
        print('...volpiano is empty string')
    else:
        print('...volpiano is something else: {}'.format(chant.volpiano))
    context['chant'] = chant

    # Create a new Melody object for the user to annotate.
    melody_text = chant.full_text
    if len(chant.full_text_manuscript) > 0:
        melody_text = chant.full_text_manuscript
    if len(melody_text) == 0:
        print('Cannot get full text from chant record, trying scrape from Cantus Index.')
        try:
            melody_text = get_full_text_for_cantus_id(chant.cantus_id)
        except Exception as e:
            print('Error getting full text for cantus_id {}: {}'.format(chant.cantus_id, e))
            melody_text = chant.incipit

    # It's not great to add the Melody object to the database at this point.
    # We should only do this when the user saves the annotation.
    context['melody'] = Melody.objects.create(chant=chant,
                                              user=request.user,
                                              volpiano=chant.volpiano,
                                              syllabized_text=melody_text,
                                              timestamp=time.time())
    ### DEBUG
    # print('...created melody: {}'.format(context['melody']))
    return render(request, 'annotate.html', context)


@login_required
@require_POST
def save_annotation(request):
    raise NotImplementedError()


@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    # This shows the dashboard for an admin.
    return render(request, 'admin_dashboard.html')


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
        if user.is_superuser:
            return admin_dashboard(request)
        return annotate(request)
    else:
        return index(request)


def logout_user(request):
    logout(request)
    return index(request)
