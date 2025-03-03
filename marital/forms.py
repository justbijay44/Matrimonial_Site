from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile,Preference

class UserRegistrationForm(UserCreationForm):

    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

class UserProfileForm(forms.ModelForm):
    
    class Meta:
        model = UserProfile
        fields = ['profile_image', 'dob', 'bio', 'gender', 'marital_status', 'height', 'religion', 'location', 'occupation', 'education']
        widgets = {
            'dob' : forms.DateInput(attrs={'type':'date'}),
            'bio' : forms.Textarea(attrs={'rows':4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set user field as hidden or remove it if managed by the view
        if 'user' in self.fields:
            self.fields.pop('user')  # Remove user field since it’s set via the view
        # Disable non-editable fields
        for field in ['created_at', 'updated_at', 'is_profile_complete']:
            if field in self.fields:
                self.fields.pop(field)

class LandingPreferenceForm(forms.ModelForm):
    GENDER_CHOICES = Preference.GENDER_CHOICES
    AGE_CHOICES = [(i, i) for i in range(18, 101)]
    
    prefered_gender = forms.ChoiceField(
        choices=[('', 'I am looking for')] + list(GENDER_CHOICES),
        required=True,
        label='I’m looking for a'
    )

    min_age = forms.ChoiceField(
        choices=AGE_CHOICES,
        initial=20,
        label='Age From'
    )
    max_age = forms.ChoiceField(
        choices=AGE_CHOICES,
        initial=50,
        label='Age To'
    )
    prefered_religion = forms.ChoiceField(
        choices=[('', 'Religion')] + list(Preference.RELIGION_CHOICE),
        required=False,
        label='Religion'
    )
    prefered_marital_status = forms.ChoiceField(
        choices=[('', 'Marital Status')] + list(Preference.MARITAL_STATUS_CHOICE),
        required=False,
        label='Marital Status'
    )

    class Meta:
        model = Preference
        fields = ['prefered_gender', 'min_age', 'max_age', 'prefered_religion', 'prefered_marital_status']

    def clean(self):
        cleaned_data = super().clean()
        min_age = cleaned_data.get('min_age')
        max_age = cleaned_data.get('max_age')
        if min_age and max_age and int(min_age) > int(max_age):
            raise forms.ValidationError("Minimum age cannot be greater than maximum age.")
        return cleaned_data

class PreferenceForm(forms.ModelForm):

    GENDER_CHOICES = Preference.GENDER_CHOICES
    RELIGION_CHOICE = Preference.RELIGION_CHOICE
    MARITAL_STATUS_CHOICE = Preference.MARITAL_STATUS_CHOICE
    
    AGE_CHOICES = [(i,i) for i in range(20,50)]

    prefered_gender = forms.ChoiceField(
        choices=[('', 'I am looking for')] + list(GENDER_CHOICES), required=True, label='Looking for')
    
    min_age = forms.ChoiceField(choices=AGE_CHOICES, initial=20, label='Age From')
    
    max_age = forms.ChoiceField(choices=AGE_CHOICES, initial=50, label='Age To')

    prefered_religion = forms.ChoiceField(choices=[('', 'Religion')] + list(RELIGION_CHOICE), required=False)

    prefered_marital_status = forms.ChoiceField(choices=[('', 'Marital Status')] + list(MARITAL_STATUS_CHOICE), required=False)

    prefered_location = forms.CharField(max_length=100, required=False, label='Preferred Location')

    prefered_height = forms.IntegerField(required=False, label='Preferred Height (cm)', min_value=100, max_value=250,
        widget=forms.NumberInput(attrs={'placeholder': 'Height in cm'})
    )

    prefered_education = forms.CharField(max_length=100, required=False, label='Preferred Education')
    
    prefered_occupation = forms.CharField(max_length=100, required=False, label='Preferred Occupation')

    other_preference = forms.CharField(max_length=500, required=False, label='Other Preferences',
        widget=forms.Textarea(attrs={'rows': 3})
    )

    class Meta:
        model = Preference
        fields = ['prefered_gender', 'min_age', 'max_age', 'prefered_religion', 'prefered_marital_status',
                   'prefered_location', 'prefered_height', 'prefered_education', 'prefered_occupation', 'other_preference']
        
    def clean(self):
        clean_data = super().clean()
        min_age = clean_data.get('min_age')
        max_age = clean_data.get('max_age')
        if min_age and max_age and int(min_age) > int(max_age):
            raise forms.ValidationError("Minimum age cann't be greater than the maximum age")
        return clean_data
