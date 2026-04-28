# File: forms.py
# Author: Jake Jeong
# Description: Forms for the paper tracking web app.

from django import forms
from .models import UserProfile, ReadingList, SavedPaper


class CreateProfileForm(forms.ModelForm):
    """Form to create a UserProfile after creating a Django User."""
    class Meta:
        model = UserProfile
        fields = ['display_name', 'email', 'affiliation', 'research_interests']


class ReadingListForm(forms.ModelForm):
    """Form to create a reading list for the logged-in user."""
    class Meta:
        model = ReadingList
        fields = ['name', 'description']


class SavePaperForm(forms.ModelForm):
    """Form to save a paper to one of the logged-in user's reading lists."""
    class Meta:
        model = SavedPaper
        fields = ['reading_list']

    def __init__(self, *args, **kwargs):
        user_profile = kwargs.pop('user_profile', None)
        super().__init__(*args, **kwargs)

        if user_profile:
            self.fields['reading_list'].queryset = ReadingList.objects.filter(
                user_profile=user_profile
            )