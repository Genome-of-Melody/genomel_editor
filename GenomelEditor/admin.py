from django.contrib import admin

# Register your models here.
from .models import Chant, Source, Melody

admin.site.register(Chant)
admin.site.register(Source)
admin.site.register(Melody)
