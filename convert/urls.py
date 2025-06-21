from django.urls import path

from . import views

urlpatterns = [
    path("",views.conversion_type,name="conversion_type"),
    path("upload/",views.upload_file,name="upload_file"),
]