from django.contrib import admin
from .models import *
# Register your models here.

class tbl_filesAdmin(admin.ModelAdmin):
    list_display = ("id","Email","File","Upload_Date","Description","File_Name")

admin.site.register(tbl_files,tbl_filesAdmin)