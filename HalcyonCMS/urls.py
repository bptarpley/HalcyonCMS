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
from django.urls import path, re_path
from filebrowser.sites import site
from home import views as home_views
from post import views as post_views
from bibliography import views as bib_views

urlpatterns = [
    path('admin/filebrowser/', site.urls),
    path('grappelli/', include('grappelli.urls')),
    path('admin/', admin.site.urls),
    re_path('accounts/login/?$', home_views.login),
    re_path('accounts/register/?$', home_views.register),
    path('', home_views.index),
    re_path('get-section/?$', home_views.get_section),
    re_path('check-nice-url/?$', post_views.check_nice_url),
    re_path('blog/?$', post_views.blog),
    re_path('blog/create/?$', post_views.create_blog_post),
    re_path('blog/feed.rss', post_views.blog_feed),
    path('blog/<str:nice_url>', post_views.view_blog),
    re_path('podcast/?$', post_views.podcast),
    re_path('podcast/create/?$', post_views.create_podcast),
    re_path('podcast/feed.rss', post_views.podcast_feed),
    path('podcast/<str:nice_url>', post_views.view_podcast),
    re_path('bibliography/?$', bib_views.index),
    re_path('bibliography/detail/?$', bib_views.source_detail),
    re_path('bibliography/export/?$', bib_views.export),
    re_path('bibliography/sources/?$', bib_views.sources),
    re_path('bibliography/locations/?$', bib_views.locations),
    re_path('bibliography/roles/?$', bib_views.roles),
    re_path('bibliography/people/?$', bib_views.people),
    re_path('bibliography/fields/?$', bib_views.fields),
    re_path('bibliography/publishers/?$', bib_views.publishers),
    re_path('resources/?$', post_views.resources),
    re_path('resources/create/?$', post_views.create_resource),
    path('resources/<str:nice_url>', post_views.view_resource),
    re_path('search/?$', home_views.search),
    path('<str:nice_url>', home_views.pages)
]
