import datetime
import logging
import random
import time

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import DatabaseError
from django.db.models import Q
from django.forms import forms
from django.shortcuts import render
from django.views.decorators.http import require_POST

from GenomelEditor.annotation_logic import assign_melody_and_chant_to_annotator, create_new_melody_from_chant
from GenomelEditor.forms import UploadChantsForm, UploadSourcesForm, SaveAnnotationForm
from GenomelEditor.models import Chant, Melody, Source
from GenomelEditor.utils import get_full_text_for_cantus_id


# Create your views here.

def index(request):
    n_chants = Chant.objects.count()
    n_melodies = Melody.objects.count()
    n_sources = Source.objects.count()
    percent_done = 0
    if n_chants > 0:
        percent_done = n_melodies / n_chants
    context = {'n_melodies': n_melodies,
               'n_chants': n_chants,
               'n_sources': n_sources,
               'percent_done': percent_done}

    # Statistics for the annotator dahsboard
    annotator_names = User.objects.filter(groups__name='annotators').values_list('username', flat=True)
    annotator_stats = {name: 0 for name in annotator_names}
    melodies = Melody.objects.all()
    for melody in melodies:
        if melody.user_transcriber is not None:
            # Some melodies may have been transcribed by non-annotators.
            if melody.user_transcriber.username in annotator_stats:
                annotator_stats[melody.user_transcriber.username] += 1
    sorted_annotator_stats = sorted(annotator_stats.items(), key=lambda x: x[1], reverse=True)
    context['sorted_annotator_stats'] = sorted_annotator_stats

    return render(request, 'index.html', context)


@login_required
def annotate(request):
    context = {'chant': None,
               'melody': None}

    chant, melody = None, None

    print('views.annotate(): request.user: {}'.format(request.user))

    # Assign the next chant to be annotated to the user.
    # This involves a database transaction, which may fail due to concurrency issues,
    # hence the retries.
    n_retries = 0
    max_retries = 5
    while n_retries < max_retries:
        try:
            chant, melody = assign_melody_and_chant_to_annotator(request.user)
            break
        except DatabaseError:
            n_retries += 1
            time.sleep(0.1)
            continue

    # Here we should create the Melody in the DB already, because
    # otherwise we have no way to prevent assigning the same chant
    # to different users.

    context['chant'] = chant
    context['melody'] = melody
    return render(request, 'annotate.html', context)


@login_required
@require_POST
def save_annotation(request):

    # Get the form data.
    save_annotation_form = SaveAnnotationForm(request.POST)

    logging.debug('POST data: {}'.format(request.POST))

    # print(save_annotation_form.cleaned_data)
    if save_annotation_form.is_valid():
        logging.debug('Form is valid.')
        logging.debug(save_annotation_form.cleaned_data)
    else:
        logging.debug('Form is not valid!')
        # Check the melody ID value
        melody_id_field = save_annotation_form['melody_id']
        logging.debug('...melody_id_field: {}'.format(melody_id_field))
        logging.debug('...melody_id_field value: {}'.format(melody_id_field.value()))
        logging.debug('...melody_id_field is None? {}'.format(melody_id_field is None))

    # Create the Melody object.
    annotation_data = save_annotation_form.cleaned_data

    if annotation_data['melody_id'] is not None:
        print('views.save_annotation(): Updating existing melody with id={}'.format(annotation_data['melody_id']))

        melody = Melody.objects.get(id=annotation_data['melody_id'])

        # Sanity check: make sure the current transcriber is the same as the previous
        # transcriber. Only one user should be transcribing a melody.
        if melody.user_transcriber != request.user:
            raise ValueError('Melody must be only transcribed by one user!'
                             ' Previous transcriber: {},'
                             ' current user: {}'.format(melody.user_transcriber, request.user))

        melody.volpiano = annotation_data['volpiano']
        melody.syllabized_text = annotation_data['syllabized_text']

        melody.user_transcriber = request.user

        # Other properties
        melody.is_adiastematic = annotation_data['is_adiastematic']
        melody.is_incomplete_in_source = annotation_data['is_incomplete_in_source']

        # State management: valid situations.

        # 1. Annotator worked on the melody but did not complete the transcription.
        if melody.is_in_transcription and not annotation_data['is_transcribed']:
            melody.move_to_transcription()
        # 2. Annotator worked on the melody and completed the transcription.
        if melody.is_in_transcription and annotation_data['is_transcribed']:
            logging.debug('...melody transcribed!')
            melody.move_to_checks()
        # 3. Checking is in progress but is not finished.
        if melody.is_in_checks and not annotation_data['is_checked'] and annotation_data['is_transcribed']:
            melody.move_to_checks()
        # 4. Check was performed and the melody is fine.
        if melody.is_in_checks and annotation_data['is_checked'] and annotation_data['is_transcribed']:
            melody.move_to_finalized()
        # 5. Check was performed and the melody needs to be revised.
        if melody.is_in_checks and annotation_data['is_checked'] and not annotation_data['is_transcribed']:
            melody.move_to_transcription()

        # State management: invalid situations.
        if melody.is_finalized:
            raise ValueError('How did a finalized melody ever make it into the annotation page?')
        if melody.is_in_checks and not annotation_data['is_checked'] and not annotation_data['is_transcribed']:
            raise ValueError('Checker cannot send a melody back to transcription without completing the check!')
        if melody.is_in_transcription and annotation_data['is_checked']:
            raise ValueError('A transcription must be finished first before a melody can be checked,'
                             ' and the transcriber cannot perform the check at the same time as the transcription.')

        melody.save()

    else:
        print('views.save_annotation(): Creating a new melody from annotation form.')
        logging.debug('...number of melodies in database: {}'.format(Melody.objects.count()))
        melody = Melody(chant=Chant.objects.get(id=annotation_data['chant_id']),
                        user_transcriber=request.user,
                        user_checker=None,
                        volpiano=annotation_data['volpiano'],
                        syllabized_text=annotation_data['syllabized_text'],
                        is_adiastematic=annotation_data['is_adiastematic'],
                        is_incomplete_in_source=annotation_data['is_incomplete_in_source'])
        logging.debug('...after __init__ call: number of melodies in database: {}, melody ID: {}'.format(Melody.objects.count(), melody.id))
        if annotation_data['is_transcribed']:
            melody.move_to_checks()  # The annotator transcribed the whole melody in their first pass.
        else:
            melody.move_to_transcription()
        melody.save()
        logging.debug('...after save() call: number of melodies in database: {}, melody ID: {}'.format(Melody.objects.count(), melody.id))

    logging.debug('...Starting new annotation.')
    return annotate(request)


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

    logging.debug('Form: {}'.format(form))
    logging.debug('Cleaned data: {}'.format(form.cleaned_data))
    chants_csv = form.cleaned_data['chants_csv']

    chants = Chant.chants_from_csv_file(chants_csv)
    logging.info('views.upload_chants(): Creating {} chants.'.format(len(chants)))

    Chant.objects.bulk_create(chants)

    return index(request)


@user_passes_test(lambda u: u.is_superuser)
@require_POST
def upload_sources(request):
    """Upload sources CSV file and import into database."""
    logging.debug('Request files: {}'.format(request.FILES))

    form = UploadSourcesForm(request.POST, request.FILES)
    logging.debug('Form: {}'.format(form))
    logging.debug('Cleaned data: {}'.format(form.cleaned_data))

    sources_csv = form.cleaned_data['sources_csv']
    sources = Source.sources_from_csv_file(sources_csv)
    logging.info('views.upload_sources():Creating {} sources.'.format(len(sources)))

    Source.objects.bulk_create(sources)

    return index(request)


def help(request):
    """Documentation for users: primarily annotators."""
    return render(request, 'help.html')


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
