from django.contrib import admin
from .models import *
# Register your models here.

class tbl_usersAdmin(admin.ModelAdmin):
    list_display = ("id","First_name","Last_name","Email","Mobile","Password","Profile_pic","Reg_date")

admin.site.register(tbl_users,tbl_usersAdmin)



class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('Name', 'Email', 'Subject','Message', 'Date')
    search_fields = ('Name', 'Email', 'Subject', 'Message')
    list_filter = ('Date',)


admin.site.register(ContactMessage,ContactMessageAdmin)