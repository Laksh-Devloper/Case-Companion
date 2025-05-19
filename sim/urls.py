# sim/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.sign_in, name='sign_in'),  # Now /sim/
]