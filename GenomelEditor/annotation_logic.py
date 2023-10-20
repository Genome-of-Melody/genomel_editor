'''This file contains functions that manage the annotation process.'''
import random

from django.db import transaction
from django.db.models import Q, Max

from GenomelEditor.models import Chant, Melody
from GenomelEditor.utils import get_full_text_for_cantus_id, get_defaul_volpiano_string


def assign_melody_and_chant_to_annotator(user) -> (Chant, Melody):
    """Selects which melody and chant to display for the annotator.
    Prioritizes assigning an unfinished melody.

    If all melodies are finished, assigns a random melody from
    the last source that the user had been annotating.

    If the source which the user annotated last time is finished,
    or the user has never annotated before, assigns a random melody.

    NOTE: This function modifies the database: selected chants are locked,
    and if a new Melody is created, it is save()d to the database.

    :param user: request.user from the annotate(request) view.
    """
    chant, melody = None, None

    # First, check if the user has a melody in transcription.
    # If so, retrieve its chant and use the "in progress" context.
    melody_in_transcription = Melody.objects.filter(user_transcriber=user).\
        filter(is_in_transcription=True).\
        order_by('timestamp').first()
    if melody_in_transcription is not None:
        # print('...found melody of user {} in transcription: {}'.format(user, melody_in_transcription))
        melody = melody_in_transcription
        # Here we do not need locking -- this chant already had a melody, so it will
        # never come up in a query set. (This is likely true, because it would
        # require two different users to have been assigned the same chant.)
        chant = Chant.objects.get(id=melody_in_transcription.chant.id)
        # print('...found chant: {}'.format(context['chant']))
        return chant, melody

    # The harder part: we will be creating a new melody, so the DB will be modified.
    with transaction.atomic():

        # If the user does not have a melody ongoing, find the most recent melody
        # they finished, and assign a chant from the same source.
        melodies_transcribed_by_user = Melody.objects.filter(user_transcriber=user)

        if len(melodies_transcribed_by_user) > 0:
            melody_last_transcribed = melodies_transcribed_by_user.order_by('timestamp').last()
            last_transcribed_chant = melody_last_transcribed.chant
            last_transcribed_source = last_transcribed_chant.source_id

            # Here we do need locking, because another user may have been transcribing
            # from the same source. So, two processes can arrive at this line at the same time.
            # We do skip_locked=True, because it's perfectly fine for another user to concurrently
            # get assigned a different chant from the same source.
            chants_from_last_transcribed_source = Chant.objects.select_for_update(skip_locked=True).\
                filter(Q(source_id=last_transcribed_source)).\
                filter(Q(melody=None)).\
                filter(Q(volpiano='')).order_by('?')
            if len(chants_from_last_transcribed_source):
                chant = chants_from_last_transcribed_source.first()
                melody = create_new_melody_from_chant(chant, user)

        # Last case: the last source the user has seen is complete,
        # or the user never transcribed anything
        if chant is None:
            # Lock the selected chant, so that any concurrent query will skip it.
            chant = Chant.objects.select_for_update(skip_locked=True).\
                filter(Q(melody=None)).\
                filter(Q(volpiano='')).\
                order_by('?').first()
            melody = create_new_melody_from_chant(chant, user)

    # end of transaction.atomic()

    return chant, melody


def create_new_melody_from_chant(chant, user) -> Melody:
    '''Creates a new melody from scratch and populates it with whatever
    data is available from the Chant object (and, if need be, scrapes full text
    from Cantus Index).'''

    # Pre-populating the new Melody: full text
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

    # Here we could also look at pre-existing syllabizations among finished (=checked)
    # melodies of the same CantusID.

    max_id = Melody.objects.all().aggregate(Max('id'))['id__max']
    next_id = 1
    if max_id is not None:
        next_id = max_id + 1
    print('create_new_melody_from_chant(): next ID for new melody: {}'.format(next_id))

    initial_volpiano = chant.volpiano
    if not initial_volpiano:
        initial_volpiano = get_defaul_volpiano_string()

    melody = Melody.objects.create(
                    id=next_id,
                    chant=chant,
                    user_transcriber=user,
                    user_checker=None,
                    volpiano=initial_volpiano,
                    syllabized_text=melody_text)
    melody.move_to_transcription()  # The melody was created to be annotated.
    melody.save() # Needs to be updated in DB to this state.
    print('create_new_melody_from_chant(): Created new melody from chant ID {}: melody ID {}'.format(chant.id, melody.id))
    # print('All melodies in DB: {}'.format(Melody.objects.all()))

    # But in order to get this ID, it needs to be refreshed from the DB, where it acquired
    # the ID upon creation.
    # melody.refresh_from_db()

    return melody
