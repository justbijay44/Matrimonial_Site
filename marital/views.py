from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages
from django.db.models import Q, F, IntegerField, ExpressionWrapper
from django.db.models.functions import ExtractYear

from .models import UserProfile, Preference, Match, Message, Testimonial
from .forms import UserRegistrationForm, UserProfileForm, PreferenceForm, TestimonialForm

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Preference
from .forms import PreferenceForm,LandingPreferenceForm, TestimonialForm

from datetime import datetime
from django.utils import timezone

from django.shortcuts import render
from django.contrib import messages
from django.db.models import Q
from .models import Preference, Match
from .forms import LandingPreferenceForm

def home(request):
    preference_form = None
    testimonial_form = None  # Initialize as None first
    approved_testimonials = Testimonial.objects.filter(is_approved=True).order_by('-created_at')

    if request.user.is_authenticated:
        try:
            preference = Preference.objects.get(user=request.user)
            preference_form = LandingPreferenceForm(instance=preference)
        except Preference.DoesNotExist:
            preference_form = LandingPreferenceForm()
    else:
        preference_form = LandingPreferenceForm()

    if request.method == 'POST':
        if 'preference_submit' in request.POST:
            if request.user.is_authenticated:
                preference_form = LandingPreferenceForm(request.POST)
                if preference_form.is_valid():
                    preference = preference_form.save(commit=False)
                    preference.user = request.user
                    preference.save()
                    messages.success(request, "Your preferences were saved!")
                    return redirect('marital:home')
                else:
                    messages.error(request, "There were errors setting up your preferences. Please check the form.")
            else:
                messages.error(request, "Please log in to submit your preferences.")
                return redirect('marital:login')
            
        elif 'testimonial_submit' in request.POST:
            testimonial_form = TestimonialForm(request.POST, request.FILES)
            if testimonial_form.is_valid():
                testimonial = testimonial_form.save(commit=False)
                testimonial.user = request.user if request.user.is_authenticated else None
                testimonial.save()
                messages.success(request, "Thank you for sharing your testimonial! It will be reviewed by our team.")
                return redirect('marital:home')
            else:
                messages.error(request, "There was an error submitting your testimonial.")
                
    # Always create a new form instance for GET requests or after successful submission
    if testimonial_form is None:
        testimonial_form = TestimonialForm()

    context = {
        "preference_form": preference_form,
        "testimonial_form": testimonial_form,
        "approved_testimonials": approved_testimonials
    }
    return render(request, 'marital/home.html', context)

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

    current_year = datetime.today().year
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

    match_list = []
    for match_profile in matches:
        match, created = Match.objects.get_or_create(
            user1=request.user,
            user2=match_profile.user,
            defaults={'status': 'pending'}
        )
        reversed_match = Match.objects.filter(user1=match_profile.user, user2=request.user).first()

        # if match.status == 'pending':
        #     match_list.append({
        #         'profile': match_profile,
        #         'match': match
        #     })

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
            messages.error(request, f"One more possibility decreased. {match.user2.username} Eliminated ❤️‍🩹")
        match.save()
        return redirect('marital:matches')
    return redirect('marital:matches')

def chat_room(request, room_name):
    """
    View for rendering the chat interface using room_name (username of the other user).
    """
    # Get the other user by username (room_name)
    other_user = get_object_or_404(User, username=room_name)

    # Check if there's a valid 'matched' status between the users
    match = Match.objects.filter(
        (Q(user1=request.user, user2=other_user) | Q(user2=request.user, user1=other_user)),
        status='matched'
    ).first()

    if not match:
        messages.error(request, "You can only message users you've matched with.")
        return redirect('marital:matches')

    # Determine the other user for display
    if request.user == match.user1:
        other_user = match.user2
    else:
        other_user = match.user1

    # Search query for filtering messages
    search_query = request.GET.get('search', '')

    # Get all matched users for the sidebar
    matched_users = User.objects.filter(
        Q(user1_matches__user2=request.user, user1_matches__status='matched') |
        Q(user2_matches__user1=request.user, user2_matches__status='matched')
    ).distinct().exclude(id=request.user.id)

    # Get chat history for the selected user
    chats = Message.objects.filter(
        (Q(sender=request.user, receiver=other_user) | Q(receiver=request.user, sender=other_user))
    )
    if search_query:
        chats = chats.filter(Q(content__icontains=search_query))
    chats = chats.order_by('timestamp')

    # Get last messages for all matched users (sidebar)
    user_last_messages = []
    for user in matched_users:
        last_message = Message.objects.filter(
            (Q(sender=request.user, receiver=user) | Q(receiver=request.user, sender=user))
        ).order_by('-timestamp').first()
        user_last_messages.append({
            'user': user,
            'last_message': last_message
        })
    user_last_messages.sort(
        key=lambda x: x['last_message'].timestamp if x['last_message'] else timezone.now(),
        reverse=True
    )

    context = {
        'room_name': room_name,
        'chats': chats,
        'match': match,
        'user_last_messages': user_last_messages,
        'search_query': search_query,
        'slug': room_name  # For WebSocket script
    }
    return render(request, 'marital/message.html', context)
    
def match_messages(request, match_id):
    match = get_object_or_404(Match, id=match_id)

    if match.status != 'matched':
        messages.error(request, "You can only message users you've matched with.")
        return redirect('marital:matches')
    
    if request.user == match.user1:
        other_user = match.user2
    else:
        other_user = match.user1

    room_name = other_user.username
    search_query = request.GET.get('search', '')

    matched_users = User.objects.filter(
        Q(user1_matches__user2=request.user, user1_matches__status='matched') |
        Q(user2_matches__user1=request.user, user2_matches__status='matched')
    ).distinct().exclude(id=request.user.id)

    # Get chat history for selected user
    chats = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(receiver=request.user) & Q(sender=other_user))
    )
    if search_query:
        chats = chats.filter(Q(content__icontains=search_query))
    chats = chats.order_by('timestamp')

    # Get last messages for all matched users
    user_last_messages = []
    for user in matched_users:
        last_message = Message.objects.filter(
            (Q(sender=request.user, receiver=user) | Q(receiver=request.user, sender=user))
        ).order_by('-timestamp').first()  # Get the latest message
        user_last_messages.append({
            'user': user,
            'last_message': last_message
        })
    
    # Sort by most recent message
    user_last_messages.sort(
        key=lambda x: x['last_message'].timestamp if x['last_message'] else timezone.now(),
        reverse=True
    )

    context = {
        'room_name': room_name,
        'chats': chats,
        'match': match,
        'user_last_messages': user_last_messages,
        'search_query': search_query,
        'slug': room_name
    }
    return render(request, 'marital/message.html', context)

# def submit_testimonial(request):
#     form = TestimonialForm()
#     if request.method == 'POST':
#         form = TestimonialForm(request.POST)
#         if form.is_valid():
#             testimonial = form.save(commit=False)
#             testimonial.user = request.user
#             testimonial.save()
#             return redirect("marital:home")
#     return render(request, 'marital/testimonials_form.html', {'form': form})