from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.db.models import Q, F, IntegerField, ExpressionWrapper
from django.db.models.functions import ExtractYear

from .models import UserProfile, Preference, Match
from .forms import UserRegistrationForm, UserProfileForm, PreferenceForm

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Preference
from .forms import PreferenceForm,LandingPreferenceForm

from datetime import date

def home(request):
    """
    View for the landing page, showing a preference form for all logged-in users (to view/update preferences)
    or a preview for anonymous users. Requires login to submit the form.
    """
    preference_form = None
    if request.user.is_authenticated:
        try:
            preference = Preference.objects.get(user=request.user)
            preference_form = LandingPreferenceForm(instance=preference)  
        except Preference.DoesNotExist:
            if request.method == 'POST':
                preference_form = LandingPreferenceForm(request.POST)
                if preference_form.is_valid():
                    preference = preference_form.save(commit=False)
                    preference.user = request.user
                    preference.save()
                    messages.success(request, "Your preferences were saved!")
                    return redirect('/')  
                else:
                    messages.error(request, "There were errors setting up your preferences. Please check the form.")
            else:
                preference_form = LandingPreferenceForm()
    else:
        if request.method == 'POST':
            messages.error(request, "Please log in to submit your preferences.")
            return redirect('login')
        preference_form = LandingPreferenceForm() 
    return render(request, "marital/home.html", {"preference_form": preference_form})

# def prefer(request):

#     try:
#         user_preference = Preference.objects.get(user=request.user)
#         messages.info(request, "Preferences already set. Update them in your profile.")
#         return redirect("/")
#     except Preference.DoesNotExist:
#         if request.method == 'POST':
#             preference_form = PreferenceForm(request.POST)
#             if preference_form.is_valid():
#                 user_preference = preference_form.save(commit=False)
#                 user_preference.user = request.user
#                 user_preference.save()
#                 messages.success(request, "Your preferences were saved!")
#                 return redirect('/') 
#             else:
#                 messages.error(request, "There was an error saving your preferences. Please check the form.")
#         else:
#             preference_form = PreferenceForm()
#         return render(request, 'marital/prefer.html', {'preference_form': preference_form})

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                UserProfile.objects.create(user = user)
                # Preference.objects.create(user = user)
                messages.success(request, "Registration Successful! Please Login")
                return redirect('marital:login')
            except Exception as e:
                messages.error(request, f"Registration failed due to an error: {str(e)}")
                return redirect('marital:register')
        else:
            messages.error(request, "Registration was unsuccesful" + str(form.errors))
    else:
        form = UserRegistrationForm()
    return render(request, 'marital/register.html', {'form': form})

def custom_logout(request):
    logout(request)
    return redirect('marital:login')

def edit_profile(request):
    """
    View for editing a user's profile and preferences.
    """
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        preference, created = Preference.objects.get_or_create(user=request.user)
    except Exception as e:
        messages.error(request, f"Error retrieving profile or preferences: {str(e)}")
        return redirect('marital:edit_profile')

    if request.method == 'POST':
        if 'profile_submit' in request.POST:
            profile_form = UserProfileForm(request.POST, request.FILES, instance = profile)
            if profile_form.is_valid():
                profile = profile_form.save()
                profile.is_profile_complete = profile.is_complete()
                profile.save()
                messages.success(request,'Profile updated succesfully')
                return redirect('marital:edit_profile')
            else:
                messages.error(request, 'There was an error updating your profile')
        else:
            preference_form = PreferenceForm(request.POST, instance=preference)
            if preference_form.is_valid():
                preference_form.save()
                messages.success(request,'Preference updated succesfully')
                return redirect('marital:edit_profile')
            else:
                messages.error(request, 'There was an error updating your preference')
    else:
        profile_form = UserProfileForm(instance=profile)
        preference_form = PreferenceForm(instance=preference)

    return render(request, "marital/edit_profile.html", {
        'profile_form' : profile_form,
        'preference_form' : preference_form,
    })

def matches(request):

    try:
        preference = get_object_or_404(Preference, user=request.user)
        profile = get_object_or_404(UserProfile, user=request.user)
    except Exception as e:
        messages.error(request, f"Error retrieving profile or preferences: {str(e)}")
        return redirect('marital:edit_profile')

    current_year = date.today().year
    # matches_query = Q(age__gte = preference.min_age, age__lte = preference.max_age)
    matches_query = Q()

    if preference.prefered_gender != 'B':
        matches_query &= Q(gender = preference.prefered_gender)
    else:
        matches_query &= Q(gender__in = ['M','F','O'])

    if preference.prefered_marital_status:
        matches_query &= Q(marital_status=preference.prefered_marital_status)

    if preference.prefered_location:
        matches_query &= Q(location__icontains=preference.prefered_location) | Q(location__isnull = True)

    if preference.prefered_height:
        matches_query &= Q(height=preference.prefered_height)

    if preference.prefered_education:
        matches_query &= Q(education=preference.prefered_education)

    if preference.prefered_occupation:
        matches_query &= Q(occupation=preference.prefered_occupation)

    matches = UserProfile.objects.annotate(
        calculated_age=ExpressionWrapper(
            current_year - ExtractYear('dob'),
            output_field=IntegerField()
        )
    ).filter(matches_query,
            calculated_age__gte=preference.min_age,
            calculated_age__lte=preference.max_age).exclude(user = request.user)   

    # excluded_users = Match.objects.filter(user1=request.user, status__in=['liked','rejected']).values('user2')
    # matches = matches.exclude(user__in = excluded_users)

    # Check for existing matches or create new ones
    match_list = []

    for match_profile in matches:
        match, created = Match.objects.get_or_create(
            
            #requested user
            user1 = request.user,
            #possible matches
            user2 = match_profile.user,

            defaults={'status':'pending'}
        )
        reversed_match = Match.objects.filter(user1=match_profile.user, user2=request.user).first()
        # and (not reversed_match or reversed_match.status == 'pending')
        if match.status == 'pending':
            match_list.append((match_profile, match))

    return render(request, 'marital/matches.html', {'matches': match_list})


def match_action(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'like':
            match.status = 'liked'
            messages.success(request, f"You liked {match.user2.username}! Waiting for their response. 💕")
            reverse_match = Match.objects.filter(user1 = match.user2, user2 = match.user1).first()

            if reverse_match and reverse_match.status == 'liked':
                match.status = 'matched'
                reverse_match.status = 'matched'
                match.save()
                reverse_match.save()
                messages.success(request, f"Mutual match with {match.user2.username}! You can now message each other. 🎉")
                return redirect('marital:messages', match_id=match.id)
        elif action == 'reject':
            match.status = 'rejected'
            messages.error(request, f"One more possibility decreased. {match.user2.username} Eliminated❤️‍🩹")
        match.save()
        return redirect('marital:matches')
    return redirect('marital:matches')


def match_messages(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    return render(request, 'marital/message.html', {'match': match})