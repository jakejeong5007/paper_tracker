from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(UserProfile)
admin.site.register(Topic)
admin.site.register(Institution)
admin.site.register(Author)
admin.site.register(Paper)
admin.site.register(ReadingList)
admin.site.register(SavedPaper)
admin.site.register(Follow)