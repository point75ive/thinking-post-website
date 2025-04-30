from django.urls import path, include
from . import views
from .views import custom_login

app_name = 'user_management'
urlpatterns = [
    path('login/', custom_login, name='login'),
    path("accounts/", include("django.contrib.auth.urls")),
    #path("", views.home, name="home"),
    #path("about/", views.about, name="about"),
    #path("contact/", views.contact, name="contact"),
    path("sign_up/", views.sign_up, name="sign_up"),
]