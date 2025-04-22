from django.contrib import admin
from .models import *

admin.site.register(UserProfile)
admin.site.register(Preference)
admin.site.register(Match)
admin.site.register(Message)

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('couple_name', 'email', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('couple_name', 'email', 'testimonial')
    list_editable = ('is_approved',)
    readonly_fields = ('created_at',)

