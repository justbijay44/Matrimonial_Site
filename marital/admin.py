from django.contrib import admin
from .models import UserProfile,Preference, Match

admin.site.register(UserProfile)
admin.site.register(Preference)
admin.site.register(Match)

