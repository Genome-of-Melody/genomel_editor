import datetime
import logging
import time

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.forms import forms
from django.shortcuts import render
from django.views.decorators.http import require_POST

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
    return render(request, 'index.html', context)


@login_required
def annotate(request):
    context = {'chant': None,
               'melody': None}

    # Assign the next chant to be annotated to the user.
    # First, check if the user has a melody in transcription.
    # If so, retrieve its chant and use the "in progress" context.
    melody_in_transcription = Melody.objects.filter(user_transcriber=request.user).\
        filter(is_in_transcription=True).\
        order_by('timestamp').first()
    if melody_in_transcription is not None:
        print('...found melody of user {} in transcription: {}'.format(request.user, melody_in_transcription))
        context['melody'] = melody_in_transcription
        context['chant'] = Chant.objects.get(id=melody_in_transcription.chant.id)
        print('...found chant: {}'.format(context['chant']))
        return render(request, 'annotate.html', context)

    # Now we know that the user has no melody in progress. We assign the next chant.
    # We need a chant that has no associated volpiano and which has no associated
    # melody created yet.
    chant = Chant.objects.filter(Q(melody=None)).filter(Q(volpiano='')).first()

    print('Found chant: {}'.format(chant))
    if chant.volpiano is None:
        print('...volpiano is None')
    elif chant.volpiano == '':
        print('...volpiano is empty string')
    else:
        print('...volpiano is something else: {}'.format(chant.volpiano))
    context['chant'] = chant

    # Create a new Melody object for the user to annotate.

    # We try to make sure the melody has some text to syllabize.
    # If the full text is not available from the chant, we try to scrape it
    # from the Cantus Index based on cantus_id.
    # If that fails, we fall back to the incipit.
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
    # Here, we only create the Melody object as a container for data that should
    # be shown during annotation. (When a user resumes annotation of an existing
    # melody, then the Melody object is retrieved from the database.)
    melody = Melody(chant=chant,
                    user_transcriber=request.user,
                    user_checker=None,
                    volpiano=chant.volpiano,
                    syllabized_text=melody_text)
    melody.move_to_transcription()  # The melody was created to be annotated.
    # print('\n\n\nMelody created.')
    # print('Melody type: {}'.format(type(melody)))

    context['melody'] = melody

    ### DEBUG
    # print('...melody syllabized_text on the server side: {}'.format(type(context['melody'])))
    print('...created melody (but not added to DB): {}'.format(context['melody']))
    print('...number of melodies in database: {}'.format(Melody.objects.count()))
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
