# case_companion/urls.py
from django.contrib import admin
from django.urls import path, include
from accounts import views  

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index_view, name='index'),  # Root is now home page
    path('accounts/', include('accounts.urls')),
    path('chat/', include('chat.urls')),
    path('sim/', include('sim.urls')),  # Move sim to /sim/
]