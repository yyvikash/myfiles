from django.urls import path
from . import views
urlpatterns = [
    path('',views.home,name="home"),
    path('about/',views.about,name="about"),
    path('login/',views.login,name="login"),
    path('logout/',views.logout,name="logout"),
    path('signup/',views.signup,name="signup"),
    path('contact/', views.contact_view, name='contact'),
    path('dashboard/',views.dashboard,name="dashboard"),
    path('download/<int:file_id>/', views.secure_download, name='secure_download'),
    path('all_files/', views.all_files, name='all_files'),
    path('features/', views.features, name='features'),
    path('delete/<int:file_id>/', views.delete_file, name='delete_file'),
    path('profile/', views.profile, name='profile'),
    path("change-password/", views.change_password, name="change_password"),
    path("forget_password",views.forget_password,name="forget_password"),
]