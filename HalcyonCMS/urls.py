"""HalcyonCMS URL Configuration

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
from django.conf.urls import url, include
from django.urls import path
from filebrowser.sites import site
from home import views as home_views
from post import views as post_views
from bibliography import views as bib_views

urlpatterns = [
    path('admin/filebrowser/', site.urls),
    path('accounts/login/', home_views.login),
    path('accounts/register/', home_views.register),
    path('grappelli/', include('grappelli.urls')),
    path('admin/', admin.site.urls),
    path('', home_views.index),
    path('get-section/', home_views.get_section),
    path('blog/', post_views.blog),
    path('blog/create', post_views.create_blog_post),
    path('podcast/create', post_views.create_podcast),
    path('podcast/', post_views.podcast),
    path('podcast/feed.xml', post_views.podcast_feed),
    path('bibliography/', bib_views.index),
    path('bibliography/detail', bib_views.source_detail),
    path('bibliography/export', bib_views.export),
    path('bibliography/sources', bib_views.sources),
    path('bibliography/locations', bib_views.locations),
    path('bibliography/roles', bib_views.roles),
    path('bibliography/people', bib_views.people),
    path('bibliography/fields', bib_views.fields),
    path('bibliography/languages', bib_views.languages),
    path('resources/', post_views.resources),
    path('resources/create', post_views.create_resource),
]
