from __future__ import unicode_literals
from html import unescape
from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, HttpResponse
from django.utils.html import escape
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from home import SiteResponse, _contains, _clean
from .models import *
from . import get_datetime
from mutagen.mp3 import MP3
from datetime import datetime
import os


@login_required
def create_blog_post(request):
    res = SiteResponse(request.user)
    blog_post = {
        'id': 'new',
        'title': '',
        'tags': '',
        'content': 'Lorem ipsum...',
        'published': False,
        'pub_date': datetime.now()
    }
    authors = User.objects.filter(Q(is_superuser=True) | Q(profile__can_blog=True)).order_by('last_name', 'first_name')

    # DELETE EXISTING POST
    if request.method == 'GET' and _contains(request.GET, ['post-id', 'delete']):
        blog_post = BlogEntry.objects.get(id=_clean(request.GET, 'post-id'))
        blog_post.delete()
        return redirect('/blog')

    # EDIT EXISTING POST
    if request.method == 'GET' and _contains(request.GET, ['post-id']):
        blog_post = BlogEntry.objects.get(id=_clean(request.GET, 'post-id'))

    # SAVE POST
    elif request.method == 'POST' and _contains(request.POST, ['post-id', 'title', 'author-id', 'tags', 'content', 'pub-date']):
        author = User.objects.get(id=_clean(request.POST, 'author-id'))

        if _clean(request.POST, 'post-id') == 'new':
            blog_post = BlogEntry.objects.create(user=author)
        else:
            blog_post = BlogEntry.objects.get(id=_clean(request.POST, 'post-id'))

        blog_post.user = author
        blog_post.title = _clean(request.POST, 'title')
        blog_post.content = unescape(_clean(request.POST, 'content'))
        blog_post.pub_date = datetime.strptime(_clean(request.POST, 'pub-date'), '%m/%d/%Y %I:%M %p')
        blog_post.set_tags(_clean(request.POST, 'tags'))
        blog_post.published = 'published' in request.POST
        blog_post.save()

        return redirect('/blog')

    return render(
        request,
        settings.THEME_TEMPLATES['create_blog'],
        {
            'page_id': 0,
            'authors': authors,
            'is_admin': request.user.is_superuser,
            'user_id': request.user.id,
            'response': res,
            'blog_post': blog_post,
        }
    )


def blog(request):
    res = SiteResponse(request.user)
    user = None
    is_admin = False
    can_blog = False
    if request.user.is_authenticated:
        user = User.objects.get(id=request.user.id)
        is_admin = user.is_superuser
        can_blog = user.profile.can_blog

    post_list = []
    page = int(_clean(request.GET, 'page', '1'))
    per_page = int(_clean(request.GET, 'perpage', '5'))

    if request.method == 'GET' and 'tag-id' in request.GET:
        if is_admin or can_blog:
            post_list = BlogEntry.objects.filter(tags__id=_clean(request.GET, 'tag-id')).order_by('-pub_date')
        else:
            post_list = BlogEntry.objects.filter(tags__id=_clean(request.GET, 'tag-id'), published=True, pub_date__lte=datetime.now()).order_by('-pub_date')
    else:
        if is_admin or can_blog:
            post_list = BlogEntry.objects.all().order_by('-pub_date')
        else:
            post_list = BlogEntry.objects.filter(published=True, pub_date__lte=datetime.now()).order_by('-pub_date')

    paginator = Paginator(post_list, per_page)
    posts = paginator.get_page(page)

    return render(
        request,
        settings.THEME_TEMPLATES['blog'],
        {
            'page_id': 0,
            'posts': posts,
            'num_posts': paginator.count,
            'num_pages': paginator.num_pages,
            'is_admin': is_admin,
            'can_blog': can_blog,
            'response': res
        }
    )


def create_podcast(request):
    res = SiteResponse(request.user)
    podcast = {
        'id': 'new',
        'title': '',
        'tags': '',
        'summary': 'Lorem ipsum...',
        'url': '',
        'published': False,
        'pub_date': datetime.now()
    }
    authors = User.objects.filter(Q(is_superuser=True) | Q(profile__can_cast=True)).order_by('last_name', 'first_name')

    # DELETE EXISTING POST
    if request.method == 'GET' and _contains(request.GET, ['post-id', 'delete']):
        podcast = PodCast.objects.get(id=_clean(request.GET, 'post-id'))
        podcast.delete()
        return redirect('/podcast')

    # EDIT EXISTING POST
    if request.method == 'GET' and _contains(request.GET, ['post-id']):
        podcast = PodCast.objects.get(id=_clean(request.GET, 'post-id'))

    # SAVE POST
    elif request.method == 'POST' and _contains(request.POST,
                                                ['post-id', 'title', 'author-id', 'url', 'summary', 'pub-date']):
        author = User.objects.get(id=_clean(request.POST, 'author-id'))

        if _clean(request.POST, 'post-id') == 'new':
            podcast = PodCast.objects.create(user=author)
        else:
            podcast = PodCast.objects.get(id=_clean(request.POST, 'post-id'))

        podcast.user = author
        podcast.title = _clean(request.POST, 'title')
        podcast.summary = unescape(_clean(request.POST, 'summary'))

        podcast_path = settings.MEDIA_ROOT + '/' + _clean(request.POST, 'url')
        audio = MP3(podcast_path)
        podcast.set_duration(audio.info.length)
        podcast.byte_size = str(os.path.getsize(podcast_path))

        podcast.pub_date = datetime.strptime(_clean(request.POST, 'pub-date'), '%m/%d/%Y %I:%M %p')
        podcast.url = _clean(request.POST, 'url')
        podcast.published = 'published' in request.POST
        podcast.save()

        return redirect('/podcast')

    return render(
        request,
        settings.THEME_TEMPLATES['create_podcast'],
        {
            'page_id': 0,
            'authors': authors,
            'is_admin': request.user.is_superuser,
            'user_id': request.user.id,
            'response': res,
            'podcast': podcast,
        }
    )


def podcast(request):
    res = SiteResponse(request.user)
    user = None
    is_admin = False
    can_cast = False
    if request.user.is_authenticated:
        user = User.objects.get(id=request.user.id)
        is_admin = user.is_superuser
        can_cast = user.profile.can_cast

    podcast_list = []
    page = int(_clean(request.GET, 'page', '1'))
    per_page = int(_clean(request.GET, 'perpage', '5'))

    if is_admin or can_cast:
        podcast_list = PodCast.objects.all().order_by('title')
    else:
        podcast_list = PodCast.objects.filter(published=True, pub_date__lte=datetime.now()).order_by('title')

    paginator = Paginator(podcast_list, per_page)
    podcasts = paginator.get_page(page)

    return render(
        request,
        settings.THEME_TEMPLATES['podcast'],
        {
            'page_id': 0,
            'podcasts': podcasts,
            'num_posts': paginator.count,
            'num_pages': paginator.num_pages,
            'is_admin': is_admin,
            'can_cast': can_cast,
            'response': res
        }
    )


def podcast_feed(request):
    items = PodCast.objects.filter(published=True, pub_date__lte=datetime.now()).order_by('title')[:5]

    return render(
        request,
        settings.THEME_TEMPLATES['podcast_feed'],
        {
            'items': items,
            'language': settings.PODCAST_LANGUAGE,
            'title': settings.PODCAST_TITLE,
            'link': settings.PODCAST_LINK,
            'description': settings.PODCAST_DESCRIPTION,
            'owner_name': settings.PODCAST_OWNER_NAME,
            'owner_email': settings.PODCAST_OWNER_EMAIL,
            'copyright': settings.PODCAST_COPYRIGHT,
            'author': settings.PODCAST_AUTHOR,
            'image_url': settings.PODCAST_IMAGE_URL,
            'explicit': settings.PODCAST_EXPLICIT
        },
        content_type='text/xml'
    )

@login_required
def create_resource(request):
    res = SiteResponse(request.user)
    resource = {
        'id': 'new',
        'title': '',
        'tags': '',
        'content': 'Lorem ipsum...',
        'published': False,
        'pub_date': datetime.now()
    }
    user = User.objects.get(id=request.user.id)

    # DELETE EXISTING RESOURCE
    if request.method == 'GET' and _contains(request.GET, ['resource-id', 'delete']):
        resource = Resource.objects.get(id=_clean(request.GET, 'resource-id'))
        resource.delete()
        return redirect('/resources')

    # EDIT EXISTING RESOURCE
    if request.method == 'GET' and _contains(request.GET, ['resource-id']):
        resource = Resource.objects.get(id=_clean(request.GET, 'resource-id'))

    # SAVE POST
    elif request.method == 'POST' and _contains(request.POST, ['resource-id', 'title', 'tags', 'content']):

        if _clean(request.POST, 'resource-id') == 'new':
            resource = Resource.objects.create(user=user)
        else:
            resource = Resource.objects.get(id=_clean(request.POST, 'resource-id'))

        resource.user = user
        resource.title = _clean(request.POST, 'title')
        resource.content = unescape(_clean(request.POST, 'content'))
        resource.set_tags(_clean(request.POST, 'tags'))
        resource.published = 'published' in request.POST
        resource.save()

        return redirect('/resources')

    return render(
        request,
        settings.THEME_TEMPLATES['create_resource'],
        {
            'page_id': 0,
            'is_admin': user.is_superuser,
            'user_id': user.id,
            'response': res,
            'resource': resource,
        }
    )


def resources(request):
    res = SiteResponse(request.user)
    user = None
    is_admin = False
    if request.user.is_authenticated:
        user = User.objects.get(id=request.user.id)
        is_admin = user.is_superuser

    resource_list = []
    page = int(_clean(request.GET, 'page', '1'))
    per_page = int(_clean(request.GET, 'perpage', '5'))

    if request.method == 'GET' and 'tag-id' in request.GET:
        if is_admin:
            resource_list = Resource.objects.filter(tags__id=_clean(request.GET, 'tag-id')).order_by('-pub_date')
        else:
            resource_list = Resource.objects.filter(tags__id=_clean(request.GET, 'tag-id'), published=True, pub_date__lte=datetime.now()).order_by('-pub_date')
    else:
        if is_admin:
            resource_list = Resource.objects.all().order_by('-pub_date')
        else:
            resource_list = Resource.objects.filter(published=True, pub_date__lte=datetime.now()).order_by('-pub_date')

    paginator = Paginator(resource_list, per_page)
    resources = paginator.get_page(page)

    return render(
        request,
        settings.THEME_TEMPLATES['resources'],
        {
            'page_id': 0,
            'resources': resources,
            'num_posts': paginator.count,
            'num_pages': paginator.num_pages,
            'is_admin': is_admin,
            'response': res
        }
    )
