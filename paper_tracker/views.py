# File: views.py
# Author: Jake Jeong
# Description: Views for the paper tracking web app.

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse
from datetime import timedelta
from django.utils import timezone

from django.contrib.auth.mixins import LoginRequiredMixin as DjangoLoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

from .models import UserProfile, Topic, Institution, Author, Paper, ReadingList, SavedPaper, Follow
from .forms import CreateProfileForm, UpdateProfileForm, ReadingListForm, SavePaperForm

class PaperTrackerLoginRequiredMixin(DjangoLoginRequiredMixin):
    """
    Custom login-required mixin for the paper tracker app.

    Provides a helper method, get_profile(), that returns the UserProfile
    associated with the currently logged-in Django User.
    """

    def get_profile(self):
        """
        Return the UserProfile for the currently logged-in user.
        """
        user = self.request.user
        profile = UserProfile.objects.get(user=user)
        return profile

    def get_login_url(self):
        """
        Redirect unauthenticated users to the paper tracker login page.
        """
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

        # Follow controls are only shown for authenticated users with profiles.
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

        # Follow controls are only shown for authenticated users with profiles.
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

        # Follow controls are only shown for authenticated users with profiles.
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

        # Avoid duplicate saves if the user submits the same paper/list pair again.
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

        # Build a simple deduplicated recommendation list from all followed items.
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
    """
    View to show the logged-in user's own profile.
    """
    model = UserProfile
    template_name = "paper_tracker/show_profile.html"
    context_object_name = "profile"

    def get_object(self):
        """
        Return the logged-in user's own UserProfile.
        """
        return self.get_profile()

    def get_context_data(self, **kwargs):
        """
        Add the logged-in user's reading lists and follows to the profile page.
        """
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
            # Search across the main paper metadata and related model names.
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

class UpdateReadingListView(PaperTrackerLoginRequiredMixin, UpdateView):
    """
    View that allows a logged-in user to update one of their own reading lists.

    The queryset is restricted so users cannot update reading lists that belong
    to other users.
    """
    model = ReadingList
    form_class = ReadingListForm
    template_name = "paper_tracker/update_reading_list.html"
    context_object_name = "reading_list"

    def get_queryset(self):
        """
        Only allow the logged-in user to access their own reading lists.
        """
        return ReadingList.objects.filter(user_profile=self.get_profile())

    def get_success_url(self):
        """
        After updating, return to the updated reading list detail page.
        """
        return reverse("paper_tracker:show_reading_list", kwargs={"pk": self.object.pk})


class DeleteReadingListView(PaperTrackerLoginRequiredMixin, DeleteView):
    """
    View that allows a logged-in user to delete one of their own reading lists.

    Deleting a reading list also deletes the SavedPaper records inside it
    because SavedPaper has a ForeignKey to ReadingList with on_delete=CASCADE.
    """
    model = ReadingList
    template_name = "paper_tracker/delete_reading_list.html"
    context_object_name = "reading_list"

    def get_queryset(self):
        """
        Only allow the logged-in user to delete their own reading lists.
        """
        return ReadingList.objects.filter(user_profile=self.get_profile())

    def get_success_url(self):
        """
        After deleting, return to the logged-in user's profile page.
        """
        return reverse("paper_tracker:my_profile")

class RemoveSavedPaperView(PaperTrackerLoginRequiredMixin, DeleteView):
    """
    View that removes a saved paper from one of the logged-in user's reading lists.

    This deletes the SavedPaper object, not the original Paper object.
    """
    model = SavedPaper
    template_name = "paper_tracker/remove_saved_paper.html"
    context_object_name = "saved_paper"

    def get_queryset(self):
        """
        Only allow users to remove saved papers from their own reading lists.
        """
        return SavedPaper.objects.filter(
            reading_list__user_profile=self.get_profile()
        )

    def get_success_url(self):
        """
        After removing the saved paper, return to the reading list page.
        """
        return reverse(
            "paper_tracker:show_reading_list",
            kwargs={"pk": self.object.reading_list.pk}
        )
    
class UpdateProfileView(PaperTrackerLoginRequiredMixin, UpdateView):
    """
    View that allows the logged-in user to update their own profile.
    """
    model = UserProfile
    form_class = UpdateProfileForm
    template_name = "paper_tracker/update_profile_form.html"
    context_object_name = "profile"

    def get_object(self):
        """
        Return the logged-in user's own UserProfile.
        This prevents users from editing another user's profile.
        """
        return self.get_profile()

    def form_valid(self, form):
        """
        Save the UserProfile update.

        Also synchronizes the email field with the associated Django User object.
        """
        response = super().form_valid(form)

        self.request.user.email = form.cleaned_data["email"]
        self.request.user.save()

        return response

    def get_success_url(self):
        """
        After updating, return to the logged-in user's profile page.
        """
        return reverse("paper_tracker:my_profile")

class ResearchDigestView(PaperTrackerLoginRequiredMixin, TemplateView):
    """
    View that creates a personalized research digest for the logged-in user.

    The digest uses the user's followed topics, authors, and institutions to
    find recent relevant papers. It also includes high-influence recent papers.
    Each paper receives a simple digest score and a list of reasons explaining
    why it was included.
    """
    template_name = "paper_tracker/research_digest.html"

    def get_days(self):
        """
        Return the selected time window in days.

        The user can choose this with a GET parameter, for example:
        /paper_tracker/digest/?days=30
        """
        try:
            days = int(self.request.GET.get("days", 90))
        except ValueError:
            days = 90

        if days not in [7, 30, 90, 365]:
            days = 90

        return days

    def add_digest_entry(self, digest_entries, paper, reason, score_points):
        """
        Add a paper to the digest.

        If the paper is already in the digest, this method adds another reason
        and increases the score instead of duplicating the paper.
        """
        if paper.pk not in digest_entries:
            digest_entries[paper.pk] = {
                "paper": paper,
                "reasons": [],
                "score": 0,
            }

        if reason not in digest_entries[paper.pk]["reasons"]:
            digest_entries[paper.pk]["reasons"].append(reason)

        digest_entries[paper.pk]["score"] += score_points

    def get_context_data(self, **kwargs):
        """
        Build the personalized digest context.

        The digest is based on:
        - followed topics
        - followed authors
        - followed institutions
        - recent high-influence papers
        """
        context = super().get_context_data(**kwargs)

        profile = self.get_profile()
        days = self.get_days()
        cutoff_date = timezone.localdate() - timedelta(days=days)

        follows = Follow.objects.filter(user_profile=profile)

        followed_topics = []
        followed_authors = []
        followed_institutions = []

        digest_entries = {}

        # Each matching follow adds a reason and score to the digest entry.
        for follow in follows:
            if follow.follow_type == "topic" and follow.topic:
                topic = follow.topic
                followed_topics.append(topic)

                papers = Paper.objects.filter(
                    topic=topic,
                    publication_date__gte=cutoff_date
                )

                for paper in papers:
                    self.add_digest_entry(
                        digest_entries,
                        paper,
                        f"Matches followed topic: {topic.name}",
                        2
                    )

            elif follow.follow_type == "author" and follow.author:
                author = follow.author
                followed_authors.append(author)

                papers = author.get_papers().filter(
                    publication_date__gte=cutoff_date
                )

                for paper in papers:
                    self.add_digest_entry(
                        digest_entries,
                        paper,
                        f"Written by followed author: {author.name}",
                        3
                    )

            elif follow.follow_type == "institution" and follow.institution:
                institution = follow.institution
                followed_institutions.append(institution)

                papers = Paper.objects.filter(
                    institution=institution,
                    publication_date__gte=cutoff_date
                )

                for paper in papers:
                    self.add_digest_entry(
                        digest_entries,
                        paper,
                        f"From followed institution: {institution.name}",
                        1
                    )

        high_influence_papers = Paper.objects.filter(
            publication_date__gte=cutoff_date
        ).order_by("-influence_score", "-publication_date")[:5]

        # Add broadly important recent papers even when they do not match a follow.
        for paper in high_influence_papers:
            self.add_digest_entry(
                digest_entries,
                paper,
                f"High-influence recent paper with score {paper.influence_score}",
                1
            )

        digest_list = list(digest_entries.values())

        # Higher digest scores win, then influence and publication date break ties.
        digest_list.sort(
            key=lambda entry: (
                entry["score"],
                entry["paper"].influence_score,
                entry["paper"].publication_date,
            ),
            reverse=True
        )

        context["profile"] = profile
        context["days"] = days
        context["cutoff_date"] = cutoff_date

        context["followed_topics"] = followed_topics
        context["followed_authors"] = followed_authors
        context["followed_institutions"] = followed_institutions

        context["digest_entries"] = digest_list
        context["high_influence_papers"] = high_influence_papers

        context["num_followed_topics"] = len(followed_topics)
        context["num_followed_authors"] = len(followed_authors)
        context["num_followed_institutions"] = len(followed_institutions)
        context["num_digest_papers"] = len(digest_list)

        return context
