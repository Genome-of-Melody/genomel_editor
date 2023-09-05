from django import forms


class UploadChantsForm(forms.Form):
    title = forms.CharField(max_length=255)
    chants_csv = forms.FileField(label='Chants CSV file')


class UploadSourcesForm(forms.Form):
    title = forms.CharField(max_length=255)
    sources_csv = forms.FileField(label='Sources CSV file')
