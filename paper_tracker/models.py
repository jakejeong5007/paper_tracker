# File: models.py
# Author: Jake Jeong
# Description: Initial models for a paper tracking web app.

from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100)
    email = models.EmailField()
    affiliation = models.CharField(max_length=200, blank=True)
    research_interests = models.TextField(blank=True)
    date_joined = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.display_name

    def get_reading_lists(self):
        return ReadingList.objects.filter(user_profile=self)

    def get_follows(self):
        return Follow.objects.filter(user_profile=self)

    def get_num_reading_lists(self):
        return ReadingList.objects.filter(user_profile=self).count()


class Topic(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category_type = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    def get_papers(self):
        return Paper.objects.filter(topic=self)


class Institution(models.Model):
    name = models.CharField(max_length=200)
    institution_type = models.CharField(max_length=100)
    country = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return self.name

    def get_authors(self):
        return Author.objects.filter(institution=self)

    def get_papers(self):
        return Paper.objects.filter(institution=self)


class Author(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True)
    research_area = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name

    def get_papers(self):
        return self.paper_set.all()


class Paper(models.Model):
    title = models.CharField(max_length=300)
    authors = models.ManyToManyField(Author, blank=True)
    abstract = models.TextField()
    publication_date = models.DateField()
    conference_or_journal_name = models.CharField(max_length=200)
    paper_link = models.URLField()
    pdf_link = models.URLField(blank=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True)
    influence_score = models.IntegerField(default=0)
    thumbnail_image = models.ImageField(upload_to='paper_thumbnails/', blank=True, null=True)

    def __str__(self):
        return self.title

    def get_authors(self):
        return self.authors.all()

    def get_num_authors(self):
        return self.authors.count()

    def get_saved_lists(self):
        return SavedPaper.objects.filter(paper=self)


class ReadingList(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_saved_papers(self):
        return SavedPaper.objects.filter(reading_list=self)

    def get_num_saved_papers(self):
        return SavedPaper.objects.filter(reading_list=self).count()


class SavedPaper(models.Model):
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    reading_list = models.ForeignKey(ReadingList, on_delete=models.CASCADE)
    saved_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.paper.title} saved in {self.reading_list.name}"

    def get_paper(self):
        return self.paper

    def get_reading_list(self):
        return self.reading_list


class Follow(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    follow_type = models.CharField(max_length=50)   # topic, author, or institution
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, null=True, blank=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, null=True, blank=True)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, null=True, blank=True)
    followed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_profile.display_name} follows {self.follow_type}"

    def get_followed_object(self):
        if self.follow_type == "topic":
            return self.topic
        elif self.follow_type == "author":
            return self.author
        elif self.follow_type == "institution":
            return self.institution
        return None