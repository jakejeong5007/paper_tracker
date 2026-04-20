from django.urls import path
from django.conf import settings
from .views import *


 
 
urlpatterns = [ 
    path(r'', ProfileDetailView.as_view(), name="home"),
]
 