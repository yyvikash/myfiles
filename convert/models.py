from user.models import *
from django.core.files import File
from datetime import date

# Create your models here.
class tbl_files(models.Model):
    #Here Email means the id(primary key of tbl_user table)
    Email = models.ForeignKey(tbl_users,on_delete=models.CASCADE)
    File = models.FileField(upload_to='converted/', null=True, blank=True)
    Upload_Date = models.DateField(null=True)
    File_Name = models.CharField(max_length=255, null=True, blank=True)
    Description = models.TextField(null=True)
    File_Type = models.CharField(max_length=20)


    def __str__(self):
        return self.File_Name