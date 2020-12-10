from django.contrib import admin

# Register your models here.
from .models import FileInfo, FileListInfo

admin.site.register(FileInfo)
admin.site.register(FileListInfo)