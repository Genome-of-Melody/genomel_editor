from django import forms


class UploadChantsForm(forms.Form):
    title = forms.CharField(max_length=255)
    chants_csv = forms.FileField(label='Chants CSV file')


class UploadSourcesForm(forms.Form):
    title = forms.CharField(max_length=255)
    sources_csv = forms.FileField(label='Sources CSV file')


class SaveAnnotationForm(forms.Form):
    chant_id = forms.IntegerField()
    melody_id = forms.IntegerField(required=False)
    # melody_id is None unless resuming annotation of an existing melody.

    # The "valuable" data:
    volpiano = forms.CharField(max_length=65025)
    syllabized_text = forms.CharField(max_length=65025)

    # melody_timestamp = forms.DateTimeField(required=False)
    # ...didn't find a way to create a valid timestamp and pass it through the form.

    is_adiastematic = forms.BooleanField(required=False)
    is_incomplete_in_source = forms.BooleanField(required=False)

    is_transcribed = forms.BooleanField(required=False)
    is_checked = forms.BooleanField(required=False)
