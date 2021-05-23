"""Sign2Speech URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from core.views import home, camera, history, speech, live_feed, stop_live_feed, delete_speech

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
    path('cam/', camera),
    path('history/', history),
    path('start_feed/', live_feed),
    path('stop_feed/', stop_live_feed),
    path('speech/<int:id>', speech),
    path('delete_speech/<int:id>', delete_speech),
    path('sw.js', (
        TemplateView.as_view(
            template_name="core/sw.js",
            content_type='application/javascript')), name='sw.js'),
    path('cam/sw.js', (
        TemplateView.as_view(
            template_name="core/sw.js",
            content_type='application/javascript')), name='sw.js'),
    path('history/sw.js', (
        TemplateView.as_view(
            template_name="core/sw.js",
            content_type='application/javascript')), name='sw.js'),

]
