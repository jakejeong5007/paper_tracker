from django.urls import path
from django.conf import settings
from .views import *
from django.contrib.auth.views import LoginView, LogoutView

app_name = "paper_tracker"
 
urlpatterns = [
    # Public browsing and discovery pages.
    path("", ShowAllPapersView.as_view(), name="show_all_papers"),
    path("paper/<int:pk>/", ShowPaperView.as_view(), name="show_paper"),
    path("paper/<int:pk>/save/", SavePaperView.as_view(), name="save_paper"),
    path("topic/<int:pk>/", ShowTopicView.as_view(), name="show_topic"),
    path("author/<int:pk>/", ShowAuthorView.as_view(), name="show_author"),
    path("institution/<int:pk>/", ShowInstitutionView.as_view(), name="show_institution"),
    path("profile/<int:pk>/", ShowProfileView.as_view(), name="show_profile"),
    path("reading_list/<int:pk>/", ShowReadingListView.as_view(), name="show_reading_list"),
    path("reading_list/create/", CreateReadingListView.as_view(), name="create_reading_list"),
    path("topic/<int:pk>/follow/", FollowTopicView.as_view(), name="follow_topic"),
    path("author/<int:pk>/follow/", FollowAuthorView.as_view(), name="follow_author"),
    path("institution/<int:pk>/follow/", FollowInstitutionView.as_view(), name="follow_institution"),
    path("profile/<int:pk>/dashboard/", ShowDashboardView.as_view(), name="show_dashboard"),
    path("search/", SearchPapersView.as_view(), name="search_papers"),

    # Authenticated profile, reading-list, and digest actions.
    path("profile/update/", UpdateProfileView.as_view(), name="update_profile"),
    path("reading_list/<int:pk>/update/",UpdateReadingListView.as_view(),name="update_reading_list"),
    path("reading_list/<int:pk>/delete/",DeleteReadingListView.as_view(),name="delete_reading_list"),
    path("saved_paper/<int:pk>/remove/",RemoveSavedPaperView.as_view(),name="remove_saved_paper"),
    path("digest/", ResearchDigestView.as_view(), name="research_digest"),

    path("login/", LoginView.as_view(template_name="paper_tracker/login.html"), name="login"),
    path("logout/", LogoutView.as_view(next_page="paper_tracker:show_all_papers"), name="logout"),
    path("profile/create/", CreateProfileView.as_view(), name="create_profile"),
    path("profile/", MyProfileView.as_view(), name="my_profile"),

    # Follow and unfollow endpoints redirect back to the detail page they modify.
    path("topic/<int:pk>/follow/", FollowTopicView.as_view(), name="follow_topic"),
    path("topic/<int:pk>/unfollow/", UnfollowTopicView.as_view(), name="unfollow_topic"),

    path("author/<int:pk>/follow/", FollowAuthorView.as_view(), name="follow_author"),
    path("author/<int:pk>/unfollow/", UnfollowAuthorView.as_view(), name="unfollow_author"),

    path("institution/<int:pk>/follow/", FollowInstitutionView.as_view(), name="follow_institution"),
    path("institution/<int:pk>/unfollow/", UnfollowInstitutionView.as_view(), name="unfollow_institution"),


]
 
