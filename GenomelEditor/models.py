import csv
import logging

from django.db import models

# Create your models here.

class Chant(models.Model):
    """The first model is a Chant model. It will have the following fields derived
    from the /static/introits_20cids_chants.csv file:
    ,id,corpus_id,incipit,cantus_id,mode,finalis,differentia,siglum,position,folio,sequence,marginalia,cao_concordances,feast_id,genre_id,office_id,source_id,melody_id,drupal_path,full_text,full_text_manuscript,volpiano,notes,dataset_name,dataset_idx,image_link
    """
    id = models.IntegerField(primary_key=True)
    corpus_id = models.CharField(max_length=255, null=True, default=None)
    incipit = models.CharField(max_length=255, null=True, default=None)
    cantus_id = models.CharField(max_length=255, null=True, default=None)
    mode = models.CharField(max_length=255, null=True, default=None)
    finalis = models.CharField(max_length=255, null=True, default=None)
    differentia = models.CharField(max_length=255, null=True, default=None)
    siglum = models.CharField(max_length=255, null=True, default=None)
    position = models.CharField(max_length=255, null=True, default=None)
    folio = models.CharField(max_length=255, null=True, default=None)
    sequence = models.CharField(max_length=255, null=True, default=None)
    marginalia = models.CharField(max_length=255, null=True, default=None)
    cao_concordances = models.CharField(max_length=255, null=True, default=None)
    feast_id = models.CharField(max_length=255, null=True, default=None)
    genre_id = models.CharField(max_length=255, null=True, default=None)
    office_id = models.CharField(max_length=255, null=True, default=None)
    source_id = models.CharField(max_length=255, null=True, default=None)
    melody_id = models.CharField(max_length=255, null=True, default=None)
    drupal_path = models.CharField(max_length=255, null=True, default=None)
    full_text = models.CharField(max_length=65025, null=True, default=None)
    full_text_manuscript = models.CharField(max_length=65025, null=True, default=None)
    volpiano = models.CharField(max_length=65025, null=True, default=None)
    notes = models.CharField(max_length=65025, null=True, default=None)
    dataset_name = models.CharField(max_length=255, null=True, default=None)
    dataset_idx = models.CharField(max_length=255, null=True, default=None)
    image_link = models.CharField(max_length=511, null=True, default=None)

    @staticmethod
    def chant_from_csv_line(line, delimiter=','):
        """Parse a CSV line with the fields defined for Chant objects
        into a Chant object."""
        reader = csv.reader([line], delimiter=delimiter)
        fields = reader.__next__()

        chant = Chant(
            id=fields[0],
            corpus_id=fields[2],
            incipit=fields[3],
            cantus_id=fields[4],
            mode=fields[5],
            finalis=fields[6],
            differentia=fields[7],
            siglum=fields[8],
            position=fields[9],
            folio=fields[10],
            sequence=fields[11],
            marginalia=fields[12],
            cao_concordances=fields[13],
            feast_id=fields[14],
            genre_id=fields[15],
            office_id=fields[16],
            source_id=fields[17],
            melody_id=fields[18],
            drupal_path=fields[19],
            full_text=fields[20],
            full_text_manuscript=fields[21],
            volpiano=fields[22],
            notes=fields[23],
            dataset_name=fields[24],
            dataset_idx=fields[25],
            image_link=fields[26]
        )
        print('...created chant: {}'.format(chant))
        return chant

    def __str__(self):
        return 'Chant {} (Cantus ID: {}, source: {}, incipit: {})' \
               ''.format(self.id, self.cantus_id, self.siglum, self.incipit)

    @staticmethod
    def chants_from_csv_file(csv_file, delimiter=','):
        """Parse a CSV file with the fields defined for Chant objects
        into a list of Chant objects."""
        chants = []
        for i, line_bytes in enumerate(csv_file.readlines()):
            line_str = line_bytes.decode('utf-8').strip()
            # Discard header row (checks for starting comma).
            if i == 0:
                if line_str.startswith(','):
                    continue
            # print('Processing line {}: {}'.format(i, line_str))
            # Here we need more intelligent CSV processing.
            chant = Chant.chant_from_csv_line(line_str, delimiter)
            chants.append(chant)
        return chants


class Source(models.Model):
    """The second model is a Source model. It will have the following fields derived
    from the /static/introits_20cids_sources.csv file:
    title,siglum,description,rism,date,century,provenance,provenance_detail,segment,summary,indexing_notes,liturgical_occasions,indexing_date,drupal_path,cursus,image_link,n_cantus_chants,n_cantus_melodies"""
    title = models.CharField(max_length=255, null=True, default=None)
    siglum = models.CharField(max_length=255, null=True, default=None)
    description = models.CharField(max_length=65025, null=True, default=None)
    rism = models.CharField(max_length=255, null=True, default=None)
    date = models.CharField(max_length=255, null=True, default=None)
    century = models.CharField(max_length=255, null=True, default=None)
    provenance = models.CharField(max_length=255, null=True, default=None)
    provenance_detail = models.CharField(max_length=255, null=True, default=None)
    segment = models.CharField(max_length=255, null=True, default=None)
    summary = models.CharField(max_length=65025, null=True, default=None)
    indexing_notes = models.CharField(max_length=65025, null=True, default=None)
    liturgical_occasions = models.CharField(max_length=65025, null=True, default=None)
    indexing_date = models.CharField(max_length=255, null=True, default=None)
    # The URL path to the source page from which its data was scraped acts as the primary key.
    drupal_path = models.CharField(max_length=255, primary_key=True)
    cursus = models.CharField(max_length=255, null=True, default=None)
    image_link = models.CharField(max_length=511, null=True, default=None)
    n_cantus_chants = models.IntegerField(null=True, default=None)
    n_cantus_melodies = models.IntegerField(null=True, default=None)

    @staticmethod
    def source_from_csv_line(line, delimiter=','):
        """Parse a CSV line with the fields defined for Source objects
        into a Source object."""
        reader = csv.reader([line], delimiter=delimiter)
        fields = reader.__next__()

        n_cantus_chants = fields[16]
        if n_cantus_chants == '':
            n_cantus_chants = None
        n_cantus_melodies = fields[17]
        if n_cantus_melodies == '':
            n_cantus_melodies = None

        source = Source(
            title=fields[0],
            siglum=fields[1],
            description=fields[2],
            rism=fields[3],
            date=fields[4],
            century=fields[5],
            provenance=fields[6],
            provenance_detail=fields[7],
            segment=fields[8],
            summary=fields[9],
            indexing_notes=fields[10],
            liturgical_occasions=fields[11],
            indexing_date=fields[12],
            drupal_path=fields[13],
            cursus=fields[14],
            image_link=fields[15],
            n_cantus_chants=n_cantus_chants,
            n_cantus_melodies=n_cantus_melodies
        )
        print('...created source: {}'.format(source))
        return source

    @staticmethod
    def sources_from_csv_file(csv_file, delimiter=','):
        """Parse a CSV file with the fields defined for Source objects
        into a list of Source objects."""
        sources = []
        for i, line_bytes in enumerate(csv_file.readlines()):
            line_str = line_bytes.decode('utf-8').strip()
            # Discard header row (checks for starting field "title").
            if i == 0:
                if line_str.startswith('title'):
                    continue
            # print('Processing line {}: {}'.format(i, line_str))
            source = Source.source_from_csv_line(line_str, delimiter)
            sources.append(source)
        return sources


# So far we have covered the input data. Now, we need to create a model for the
# outputs: melodies of chants from the Chant model. We will call this model
# Melody. It will have the following fields:
class Melody(models.Model):
    id = models.IntegerField(primary_key=True)
    chant = models.ForeignKey(Chant, on_delete=models.CASCADE)
    volpiano = models.CharField(max_length=65025)
    syllabized_text = models.CharField(max_length=65025, null=True, default=None)

    timestamp = models.DateTimeField(auto_now_add=True)

    # The user fields are foreign keys to the User model of the Django.
    user_transcriber = models.ForeignKey("auth.User", on_delete=models.PROTECT, default=None,
                                         related_name='transcriber')
    user_checker = models.ForeignKey("auth.User", on_delete=models.PROTECT, default=None,
                                     related_name='checker', null=True)

    # Flag for data that cannot be transcribed.
    is_adiastematic = models.BooleanField(default=False)
    is_incomplete_in_source = models.BooleanField(default=False)

    # Flag for melody transcription state: in transcription, in checking, finalized.
    # Each of these states is at the same time a queue for actions of users (with the appropriate permissions).
    is_in_transcription = models.BooleanField(default=False)
    is_in_checks = models.BooleanField(default=False)
    is_finalized = models.BooleanField(default=False)

    def __str__(self):
        return 'Melody id={} of chant {}: volpiano={}, transcriber={}, checker={}, syllabized_text={}' \
                ''.format(self.id,
                          self.chant.id,
                          self.volpiano,
                          self.user_transcriber,
                          self.user_checker,
                          self.syllabized_text)

    def should_be_transcribed(self):
        return (not self.is_adiastematic) and (not self.is_incomplete_in_source)

    def move_to_checks(self):
        """State change: from transcription or finalization to checks."""
        self.is_in_transcription = False
        self.is_in_checks = True
        self.is_finalized = False

    def move_to_finalized(self):
        """State change: from checks to finalized.
        If the melody was not checked or finalized already, raises a ValueError."""
        if (not self.is_in_checks) or (not self.is_finalized):
            raise ValueError('Melody must go through checks before it can be finalized!')
        self.is_in_transcription = False
        self.is_in_checks = False
        self.is_finalized = True

    def move_to_transcription(self):
        if not self.should_be_transcribed():
            logging.warning('Melody being moved to transcription queue which should NOT be transcribed: {}'
                            ''.format(self))
        self.is_in_transcription = True
        self.is_in_checks = False
        self.is_finalized = False

    @property
    def show_as_transcribed(self):
        return self.is_in_checks or self.is_finalized

    @property
    def show_as_checked(self):
        return self.is_finalized
