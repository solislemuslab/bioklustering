"""Mycovirus URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.urls import path, include
from mlmodel import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.PredictionView.as_view(template_name="index.html"), name="index"),
    path('result/', views.ResultView.as_view(template_name="result.html"), name="result"),
    path('process/', views.ResultView.process, name="process"),
    path('download_zip/', views.ResultView.download_zip, name='download_zip'),
    
    # path('download_pdf/', views.download_pdf, name='download_pdf'),
    # path('file/<int:pk>/', views.delete, name='delete'),
    # path('filelist/<int:pk>/', views.delete_filelists, name='delete_filelists'),

    path('testcookie/', views.cookie_session, name="cookie_session"),
    path('deletecookie/', views.cookie_delete, name="cookie_delete"),
    path('create/', views.create_session, name="create_session"),
    path('access/', views.access_session, name="access_session"),
    path('delete/', views.delete_session, name="delete_session"),
    path('django_plotly_dash/', include('django_plotly_dash.urls'))
]

# for development purpose
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
