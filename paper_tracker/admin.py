from django.contrib import admin
from .models import *

# Expose all app models in Django admin for manual data entry and review.
admin.site.register(UserProfile)
admin.site.register(Topic)
admin.site.register(Institution)
admin.site.register(Author)
admin.site.register(Paper)
admin.site.register(ReadingList)
admin.site.register(SavedPaper)
admin.site.register(Follow)
