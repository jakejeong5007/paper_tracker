# File: views.py
# Author: Jake Jeong
# Description: Views for the paper tracking web app.

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.urls import reverse

from django.contrib.auth.mixins import LoginRequiredMixin as DjangoLoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

from .models import UserProfile, Topic, Institution, Author, Paper, ReadingList, SavedPaper, Follow
from .forms import CreateProfileForm, ReadingListForm, SavePaperForm

class PaperTrackerLoginRequiredMixin(DjangoLoginRequiredMixin):
    """Mixin for views that require a logged-in user profile."""

    def get_profile(self):
        user = self.request.user
        profile = UserProfile.objects.get(user=user)
        return profile

    def get_object(self):
        return self.get_profile()

    def get_login_url(self):
        return reverse('paper_tracker:login')

class ShowAllPapersView(ListView):
    """View to show all papers."""
    model = Paper
    template_name = "paper_tracker/show_all_papers.html"
    context_object_name = "papers"


class ShowPaperView(DetailView):
    """View to show one paper."""
    model = Paper
    template_name = "paper_tracker/show_paper.html"
    context_object_name = "paper"


class ShowTopicView(DetailView):
    """View to show one topic and all papers in that topic."""
    model = Topic
    template_name = "paper_tracker/show_topic.html"
    context_object_name = "topic"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        topic = self.get_object()

        context["papers"] = topic.get_papers()
        context["my_profile"] = None
        context["is_following"] = False

        if self.request.user.is_authenticated:
            profile = UserProfile.objects.get(user=self.request.user)
            context["my_profile"] = profile
            context["is_following"] = Follow.objects.filter(
                user_profile=profile,
                follow_type="topic",
                topic=topic,
            ).exists()

        return context


class ShowAuthorView(DetailView):
    """View to show one author and all papers by that author."""
    model = Author
    template_name = "paper_tracker/show_author.html"
    context_object_name = "author"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        author = self.get_object()

        context["papers"] = author.get_papers()
        context["my_profile"] = None
        context["is_following"] = False

        if self.request.user.is_authenticated:
            profile = UserProfile.objects.get(user=self.request.user)
            context["my_profile"] = profile
            context["is_following"] = Follow.objects.filter(
                user_profile=profile,
                follow_type="author",
                author=author,
            ).exists()

        return context


class ShowInstitutionView(DetailView):
    """View to show one institution, its authors, and its papers."""
    model = Institution
    template_name = "paper_tracker/show_institution.html"
    context_object_name = "institution"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        institution = self.get_object()

        context["authors"] = institution.get_authors()
        context["papers"] = institution.get_papers()
        context["my_profile"] = None
        context["is_following"] = False

        if self.request.user.is_authenticated:
            profile = UserProfile.objects.get(user=self.request.user)
            context["my_profile"] = profile
            context["is_following"] = Follow.objects.filter(
                user_profile=profile,
                follow_type="institution",
                institution=institution,
            ).exists()

        return context


class ShowProfileView(DetailView):
    """View to show one user profile, reading lists, and follows."""
    model = UserProfile
    template_name = "paper_tracker/show_profile.html"
    context_object_name = "profile"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.get_object()
        context["reading_lists"] = profile.get_reading_lists()
        context["follows"] = profile.get_follows()
        return context


class ShowReadingListView(DetailView):
    """View to show one reading list and the papers saved in it."""
    model = ReadingList
    template_name = "paper_tracker/show_reading_list.html"
    context_object_name = "reading_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reading_list = self.get_object()
        context["saved_papers"] = reading_list.get_saved_papers()
        return context

class CreateReadingListView(PaperTrackerLoginRequiredMixin, CreateView):
    """View to create a new reading list for the logged-in user."""
    model = ReadingList
    form_class = ReadingListForm
    template_name = "paper_tracker/create_reading_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = self.get_profile()
        return context

    def form_valid(self, form):
        form.instance.user_profile = self.get_profile()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("paper_tracker:show_reading_list", kwargs={"pk": self.object.pk})


class SavePaperView(PaperTrackerLoginRequiredMixin, CreateView):
    """View to save a paper to one of the logged-in user's reading lists."""
    model = SavedPaper
    form_class = SavePaperForm
    template_name = "paper_tracker/save_paper.html"

    def dispatch(self, request, *args, **kwargs):
        self.paper = get_object_or_404(Paper, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user_profile"] = self.get_profile()
        return kwargs

    def form_valid(self, form):
        reading_list = form.cleaned_data["reading_list"]

        saved_paper, created = SavedPaper.objects.get_or_create(
            paper=self.paper,
            reading_list=reading_list,
        )

        self.object = saved_paper

        return redirect(
            "paper_tracker:show_reading_list",
            pk=reading_list.pk
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["paper"] = self.paper
        context["profile"] = self.get_profile()
        return context
    
class FollowTopicView(PaperTrackerLoginRequiredMixin, TemplateView):
    """View for the logged-in user to follow a topic."""

    def dispatch(self, request, *args, **kwargs):
        profile = self.get_profile()
        topic = get_object_or_404(Topic, pk=kwargs["pk"])

        Follow.objects.get_or_create(
            user_profile=profile,
            follow_type="topic",
            topic=topic,
            author=None,
            institution=None,
        )

        return redirect("paper_tracker:show_topic", pk=topic.pk)


class FollowAuthorView(PaperTrackerLoginRequiredMixin, TemplateView):
    """View for the logged-in user to follow an author."""

    def dispatch(self, request, *args, **kwargs):
        profile = self.get_profile()
        author = get_object_or_404(Author, pk=kwargs["pk"])

        Follow.objects.get_or_create(
            user_profile=profile,
            follow_type="author",
            topic=None,
            author=author,
            institution=None,
        )

        return redirect("paper_tracker:show_author", pk=author.pk)


class FollowInstitutionView(PaperTrackerLoginRequiredMixin, TemplateView):
    """View for the logged-in user to follow an institution."""

    def dispatch(self, request, *args, **kwargs):
        profile = self.get_profile()
        institution = get_object_or_404(Institution, pk=kwargs["pk"])

        Follow.objects.get_or_create(
            user_profile=profile,
            follow_type="institution",
            topic=None,
            author=None,
            institution=institution,
        )

        return redirect("paper_tracker:show_institution", pk=institution.pk)
    
class UnfollowTopicView(PaperTrackerLoginRequiredMixin, TemplateView):
    """View for the logged-in user to unfollow a topic."""

    def dispatch(self, request, *args, **kwargs):
        profile = self.get_profile()
        topic = get_object_or_404(Topic, pk=kwargs["pk"])

        Follow.objects.filter(
            user_profile=profile,
            follow_type="topic",
            topic=topic,
        ).delete()

        return redirect("paper_tracker:show_topic", pk=topic.pk)


class UnfollowAuthorView(PaperTrackerLoginRequiredMixin, TemplateView):
    """View for the logged-in user to unfollow an author."""

    def dispatch(self, request, *args, **kwargs):
        profile = self.get_profile()
        author = get_object_or_404(Author, pk=kwargs["pk"])

        Follow.objects.filter(
            user_profile=profile,
            follow_type="author",
            author=author,
        ).delete()

        return redirect("paper_tracker:show_author", pk=author.pk)


class UnfollowInstitutionView(PaperTrackerLoginRequiredMixin, TemplateView):
    """View for the logged-in user to unfollow an institution."""

    def dispatch(self, request, *args, **kwargs):
        profile = self.get_profile()
        institution = get_object_or_404(Institution, pk=kwargs["pk"])

        Follow.objects.filter(
            user_profile=profile,
            follow_type="institution",
            institution=institution,
        ).delete()

        return redirect("paper_tracker:show_institution", pk=institution.pk)

class ShowDashboardView(DetailView):
    """View to show personalized papers based on followed topics, authors, and institutions."""
    model = UserProfile
    template_name = "paper_tracker/show_dashboard.html"
    context_object_name = "profile"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.get_object()

        follows = Follow.objects.filter(user_profile=profile)

        followed_topics = []
        followed_authors = []
        followed_institutions = []

        recommended_papers = []

        for follow in follows:
            if follow.follow_type == "topic" and follow.topic:
                followed_topics.append(follow.topic)

                topic_papers = Paper.objects.filter(topic=follow.topic)
                for paper in topic_papers:
                    if paper not in recommended_papers:
                        recommended_papers.append(paper)

            elif follow.follow_type == "author" and follow.author:
                followed_authors.append(follow.author)

                author_papers = follow.author.get_papers()
                for paper in author_papers:
                    if paper not in recommended_papers:
                        recommended_papers.append(paper)

            elif follow.follow_type == "institution" and follow.institution:
                followed_institutions.append(follow.institution)

                institution_papers = Paper.objects.filter(institution=follow.institution)
                for paper in institution_papers:
                    if paper not in recommended_papers:
                        recommended_papers.append(paper)

        context["follows"] = follows
        context["followed_topics"] = followed_topics
        context["followed_authors"] = followed_authors
        context["followed_institutions"] = followed_institutions
        context["recommended_papers"] = recommended_papers

        return context

 
class CreateProfileView(CreateView):
    """CreateView that creates a User and a UserProfile."""
    model = UserProfile
    template_name = "paper_tracker/create_profile_form.html"
    form_class = CreateProfileForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if "user_form" not in context:
            context["user_form"] = UserCreationForm()

        return context

    def form_valid(self, form):
        user_form = UserCreationForm(self.request.POST)

        if not user_form.is_valid():
            context = self.get_context_data(form=form)
            context["user_form"] = user_form
            return self.render_to_response(context)

        user = user_form.save()

        login(
            self.request,
            user,
            backend="django.contrib.auth.backends.ModelBackend"
        )

        form.instance.user = user

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("paper_tracker:show_profile", kwargs={"pk": self.object.pk})

class MyProfileView(PaperTrackerLoginRequiredMixin, DetailView):
    """View to show the logged-in user's own profile."""
    model = UserProfile
    template_name = "paper_tracker/show_profile.html"
    context_object_name = "profile"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.get_profile()

        context["reading_lists"] = profile.get_reading_lists()
        context["follows"] = profile.get_follows()

        return context

class SearchPapersView(ListView):
    """View to search and filter papers."""
    model = Paper
    template_name = "paper_tracker/search_papers.html"
    context_object_name = "papers"

    def get_queryset(self):
        papers = Paper.objects.all()

        query = self.request.GET.get("query", "").strip()
        topic_id = self.request.GET.get("topic", "").strip()
        author_id = self.request.GET.get("author", "").strip()
        institution_id = self.request.GET.get("institution", "").strip()

        if query:
            title_matches = Paper.objects.filter(title__icontains=query)
            abstract_matches = Paper.objects.filter(abstract__icontains=query)
            venue_matches = Paper.objects.filter(conference_or_journal_name__icontains=query)
            author_matches = Paper.objects.filter(authors__name__icontains=query)
            topic_matches = Paper.objects.filter(topic__name__icontains=query)
            institution_matches = Paper.objects.filter(institution__name__icontains=query)

            papers = (
                title_matches |
                abstract_matches |
                venue_matches |
                author_matches |
                topic_matches |
                institution_matches
            ).distinct()

        if topic_id:
            papers = papers.filter(topic__id=topic_id)

        if author_id:
            papers = papers.filter(authors__id=author_id)

        if institution_id:
            papers = papers.filter(institution__id=institution_id)

        return papers.distinct().order_by("-publication_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["topics"] = Topic.objects.all()
        context["authors"] = Author.objects.all()
        context["institutions"] = Institution.objects.all()

        context["query"] = self.request.GET.get("query", "")
        context["selected_topic"] = self.request.GET.get("topic", "")
        context["selected_author"] = self.request.GET.get("author", "")
        context["selected_institution"] = self.request.GET.get("institution", "")

        return context
