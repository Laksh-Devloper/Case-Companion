# sim/views.py
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings  # Add this
from google.oauth2 import id_token
from google.auth.transport import requests
from django.shortcuts import render

# sim/views.py
from django.shortcuts import render, redirect

def sign_in(request):
    if request.user.is_authenticated:
        return redirect('index')  # Redirect to home page
    return render(request, 'google_login.html')