from django.db import models
from django.contrib.auth.hashers import make_password

# Create your models here.

class tbl_users(models.Model):
    First_name = models.CharField(max_length=30,null=True)
    Last_name = models.CharField(max_length=30,null=True)
    Email = models.EmailField(max_length=30,null=True)
    Mobile = models.IntegerField(null=True)
    Password = models.CharField(max_length=128,null=True)
    Profile_pic = models.ImageField(upload_to="static/profile_pics",blank=True,null=True)
    Reg_date = models.DateField(null=True)
    def __str__(self):
        return self.Email

    def get_initials(self):
        return f"{self.First_name[0].upper()}{self.Last_name[0].upper()}"


class ContactMessage(models.Model):
    Name = models.CharField(max_length=100)
    Email = models.EmailField()
    Subject = models.CharField(max_length=150)
    Message = models.TextField()
    Date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.Name} - {self.Subject}"
