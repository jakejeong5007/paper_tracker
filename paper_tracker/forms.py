# File: forms.py
# Author: Jake Jeong
# Description:
#   Defines form classes for creating and updating user profiles,
#   creating reading lists, and saving papers to user-owned reading lists.

from django import forms
from .models import UserProfile, ReadingList, SavedPaper


class CreateProfileForm(forms.ModelForm):
    """
    Form used when a new user creates a profile.

    This form stores project-specific profile information.
    The Django User account itself is created separately using UserCreationForm
    inside CreateProfileView.
    """
    class Meta:
        model = UserProfile
        fields = ['display_name', 'email', 'affiliation', 'research_interests']


class UpdateProfileForm(forms.ModelForm):
    """
    Form used by a logged-in user to update their profile information.
    """
    class Meta:
        model = UserProfile
        fields = ['display_name', 'email', 'affiliation', 'research_interests']


class ReadingListForm(forms.ModelForm):
    """
    Form used to create or update a reading list.

    The user_profile field is intentionally excluded because reading lists
    should always belong to the currently logged-in user.
    """
    class Meta:
        model = ReadingList
        fields = ['name', 'description']


class SavePaperForm(forms.ModelForm):
    """
    Form used to save a paper to one of the logged-in user's reading lists.

    The reading_list field is filtered in __init__ so users can only select
    their own reading lists.
    """
    class Meta:
        model = SavedPaper
        fields = ['reading_list']

    def __init__(self, *args, **kwargs):
        """
        Limit the reading_list dropdown to the reading lists owned by the
        provided user_profile.
        """
        user_profile = kwargs.pop('user_profile', None)
        super().__init__(*args, **kwargs)

        if user_profile:
            self.fields['reading_list'].queryset = ReadingList.objects.filter(
                user_profile=user_profile
            )