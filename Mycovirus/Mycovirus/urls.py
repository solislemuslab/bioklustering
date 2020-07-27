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
    path('', views.PredictionView.as_view(template_name="predict.html"), name="index"),
    path('file/<int:pk>/', views.delete, name='delete'),
    path('filelist/<int:pk>/', views.delete_filelists, name='delete_filelists'),
    path('result/', views.result, name='result'),
    path('process/', views.process, name='process'),
    path('download_pdf/', views.download_pdf, name='download_pdf'),
    path('download_csv/', views.download_csv, name='download_csv'),
    # path('parameters/', views.updateParams, name='updateParams'),
    path('resetData/', views.resetData, name='resetData')
]

# for development purpose
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
