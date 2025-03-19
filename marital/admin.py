from django.contrib import admin
from .models import UserProfile,Preference, Match, Message

admin.site.register(UserProfile)
admin.site.register(Preference)
admin.site.register(Match)
admin.site.register(Message)


