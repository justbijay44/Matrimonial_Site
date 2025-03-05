from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class UserProfile(models.Model):

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    MARITAL_STATUS_CHOICE=[
        ('never_married', 'Never married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
        ('separated', 'Separated'),
    ]

    RELIGION_CHOICE = [
        ('hindu', 'Hindu'),
        ('muslim', 'Muslim'),
        ('christian', 'Christian'),
        ('buddhist', 'Buddhist'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_image = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    dob= models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    marital_status = models.CharField(max_length=50, choices=MARITAL_STATUS_CHOICE)
    height = models.IntegerField(help_text="Height in centimeters", null=True, blank=True,validators=[MinValueValidator(100), MaxValueValidator(250)])
    religion = models.CharField(max_length=50, choices=RELIGION_CHOICE)
    location = models.CharField(max_length=100, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    education = models.CharField(max_length=100, blank= True)
    is_profile_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        age = self.age if self.age is not None else "N/A"
        return f"{self.user.username} - {self.gender}, {self.age} years"
    
    @property
    def age(self):
        from datetime import date
        if self.dob:
            today = date.today()
            return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
        return None
    
    def is_complete(self):
        required_fields = [self.gender, self.marital_status, self.religion, self.location]
        return all(field for field in required_fields if field)
    
class Preference(models.Model):
    GENDER_CHOICES = UserProfile.GENDER_CHOICES
    MARITAL_STATUS_CHOICE = UserProfile.MARITAL_STATUS_CHOICE
    RELIGION_CHOICE = UserProfile.RELIGION_CHOICE

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preference')
    min_age = models.IntegerField(default=20, validators=[MinValueValidator(20)])
    max_age = models.IntegerField(default=50, validators=[MinValueValidator(20)])
    prefered_gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    prefered_marital_status = models.CharField(max_length=100, blank=True)
    prefered_religion = models.CharField(max_length=100, blank=True)
    prefered_location = models.CharField(max_length=100, blank=True)
    prefered_height = models.IntegerField(help_text="Height in centimeters", null=True, blank=True,validators=[MinValueValidator(100), MaxValueValidator(250)])
    prefered_education = models.CharField(max_length=100, blank=True)
    prefered_occupation = models.CharField(max_length=100, blank=True)
    other_preference = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s preferences"
    
    class Meta:
        verbose_name = "Preference"
        verbose_name_plural = "Preferences"
    
class Match(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('liked', 'Liked'),
        ('rejected', 'Rejected'),
        ('matched', 'Matched'),
    ]
    
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_initiated')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_received')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user1', 'user2')
    
    def __str__(self):
        return f"Match between {self.user1.username} and {self.user2.username}"