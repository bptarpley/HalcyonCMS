from __future__ import unicode_literals
from html import unescape
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, HttpResponse
from django.utils.html import escape
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from home import SiteResponse, _contains, _clean, _paginate
from .models import *
from mutagen.mp3 import MP3
from datetime import datetime
import traceback
import os
import json


@login_required
def check_nice_url(request):
    check_json = {
        'exists': False,
        'ids': []
    }

    if request.method == 'GET' and _contains(request.GET, ['nice-url']):
        nice_url = _clean(request.GET, 'nice-url')
        posts = Post.objects.filter(nice_url=nice_url)
        if posts:
            check_json['exists'] = True
            for post in posts:
                check_json['ids'].append(post.id)

    return HttpResponse(
        json.dumps(check_json),
        content_type='application/json'
    )

@login_required
def create_blog_post(request):
    res = SiteResponse(request.user)
    page = '1'
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
    elif request.method == 'POST' and _contains(request.POST, ['post-id', 'title', 'nice-url', 'author-id', 'tags', 'content', 'pub-date']):
        page = _clean(request.GET, 'page', page)
        author = User.objects.get(id=_clean(request.POST, 'author-id'))

        if _clean(request.POST, 'post-id') == 'new':
            blog_post = BlogEntry.objects.create(user=author)
        else:
            blog_post = BlogEntry.objects.get(id=_clean(request.POST, 'post-id'))

        blog_post.user = author
        blog_post.title = unescape(_clean(request.POST, 'title'))
        blog_post.nice_url = _clean(request.POST, 'nice-url')
        blog_post.content = unescape(_clean(request.POST, 'content'))
        blog_post.pub_date = datetime.strptime(_clean(request.POST, 'pub-date'), '%m/%d/%Y %I:%M %p')
        blog_post.set_tags(_clean(request.POST, 'tags'))
        blog_post.published = 'published' in request.POST
        blog_post.sticky = 'sticky' in request.POST
        blog_post.save()

        return redirect('/blog?page=' + page)
    elif request.method == 'POST':
        res.errors.append('Please fill out all required fields.')

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


def view_blog(request, nice_url):
    res = SiteResponse(request.user)
    user = None
    post = None
    full_url = "{0}{1}/blog/{2}".format(
        settings.PROTOCOL_PREFIX,
        settings.ALLOWED_HOSTS[0],
        nice_url
    )

    related_posts = []
    num_related = 5
    user = None
    is_admin = False
    if request.user.is_authenticated:
        user = User.objects.get(id=request.user.id)
        is_admin = user.is_superuser

    try:
        post = BlogEntry.objects.get(nice_url=escape(nice_url))
        related_posts = BlogEntry.objects.filter(
            tags__in=post.tags.all(),
            published=True
        ).exclude(id=post.id).order_by('tags__text', 'title')[0:num_related]
    except:
        res.errors.append(traceback.format_exc())

    if post and user and request.method == 'POST' and _contains(request.POST, ['comment-text']):
        comment = Comment.objects.create(user=user, text=_clean(request.POST, 'comment-text'))
        post.comments.add(comment)

    return render(
        request,
        settings.THEME_TEMPLATES['view_blog'],
        {
            'response': res,
            'page_id': 0,
            'user': user,
            'is_admin': is_admin,
            'post': post,
            'full_url': full_url,
            'related_posts': related_posts
        }
    )


def blog(request):
    res = SiteResponse(request.user)
    user = None
    tag_id = None
    is_admin = False
    can_blog = False
    if request.user.is_authenticated:
        user = User.objects.get(id=request.user.id)
        is_admin = user.is_superuser
        can_blog = user.profile.can_blog

    post_list = []
    tag_list = []
    page = int(_clean(request.GET, 'page', '1'))
    per_page = int(_clean(request.GET, 'perpage', '6'))

    if request.method == 'GET' and ('tag-id' in request.GET or 'tag' in request.GET):
        filtered = True

        filtering_tag = None
        if 'tag-id' in request.GET:
            filtering_tag = Tag.objects.get(id=_clean(request.GET, 'tag-id'))
        elif 'tag' in request.GET:
            filtering_tag = Tag.objects.get(text=_clean(request.GET, 'tag'))
        tag_id = filtering_tag.id

        if is_admin or can_blog:
            post_list = BlogEntry.objects.filter(tags__in=[filtering_tag]).order_by('-sticky', '-pub_date')
            tag_list = Tag.objects.filter(post__in=BlogEntry.objects.all()).order_by('text').distinct()
        else:
            post_list = BlogEntry.objects.filter(tags__in=[filtering_tag], published=True, pub_date__lte=datetime.now()).order_by('-sticky', '-pub_date')
            tag_list = Tag.objects.filter(post__in=BlogEntry.objects.filter(published=True, pub_date__lte=datetime.now())).order_by('text').distinct()
    else:
        if is_admin or can_blog:
            post_list = BlogEntry.objects.all().order_by('-sticky', '-pub_date')
        else:
            post_list = BlogEntry.objects.filter(published=True, pub_date__lte=datetime.now()).exclude(tags__text__in=settings.BLOG_HIDDEN_TAGS).order_by('-sticky', '-pub_date')

        tag_list = Tag.objects.filter(post__in=post_list).order_by('text').distinct()

    posts, paginator = _paginate(post_list, per_page, page)

    return render(
        request,
        settings.THEME_TEMPLATES['blog'],
        {
            'page_id': 0,
            'posts': posts,
            'tags': tag_list,
            'paginator': paginator,
            'is_admin': is_admin,
            'can_blog': can_blog,
            'tag_id': tag_id,
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
    if request.method == 'GET' and _contains(request.GET, ['podcast-id', 'delete']):
        podcast = PodCast.objects.get(id=_clean(request.GET, 'podcast-id'))
        podcast.delete()
        return redirect('/podcast')

    # EDIT EXISTING POST
    if request.method == 'GET' and _contains(request.GET, ['podcast-id']):
        podcast = PodCast.objects.get(id=_clean(request.GET, 'podcast-id'))

    # SAVE POST
    elif request.method == 'POST' and _contains(request.POST,
                                                ['podcast-id', 'title', 'nice-url', 'author-id', 'url', 'summary', 'pub-date']):
        author = User.objects.get(id=_clean(request.POST, 'author-id'))

        if _clean(request.POST, 'podcast-id') == 'new':
            podcast = PodCast.objects.create(user=author)
        else:
            podcast = PodCast.objects.get(id=_clean(request.POST, 'podcast-id'))

        podcast.user = author
        podcast.title = unescape(_clean(request.POST, 'title'))
        podcast.nice_url = _clean(request.POST, 'nice-url')
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


def view_podcast(request, nice_url):
    res = SiteResponse(request.user)
    user = None
    podcast = None
    full_url = "{0}{1}/podcast/{2}".format(
        settings.PROTOCOL_PREFIX,
        settings.ALLOWED_HOSTS[0],
        nice_url
    )

    related_podcasts = []
    num_related = 5
    user = None
    is_admin = False
    if request.user.is_authenticated:
        user = User.objects.get(id=request.user.id)
        is_admin = user.is_superuser

    try:
        podcast = PodCast.objects.get(nice_url=escape(nice_url))
        related_podcasts = PodCast.objects.filter(
            tags__in=podcast.tags.all(),
            published=True
        ).exclude(id=podcast.id).order_by('tags__text', 'title')[0:num_related]
    except:
        res.errors.append(traceback.format_exc())

    if podcast and user and request.method == 'POST' and _contains(request.POST, ['comment-text']):
        comment = Comment.objects.create(user=user, text=_clean(request.POST, 'comment-text'))
        podcast.comments.add(comment)

    return render(
        request,
        settings.THEME_TEMPLATES['view_podcast'],
        {
            'response': res,
            'page_id': 0,
            'user': user,
            'is_admin': is_admin,
            'podcast': podcast,
            'full_url': full_url,
            'related_podcasts': related_podcasts
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

    podcasts, paginator = _paginate(podcast_list, per_page, page)

    return render(
        request,
        settings.THEME_TEMPLATES['podcast'],
        {
            'page_id': 0,
            'podcasts': podcasts,
            'paginator': paginator,
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
    page = '1';
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
    elif request.method == 'POST' and _contains(request.POST, ['resource-id', 'title', 'nice-url', 'tags', 'content']):
        page = _clean(request.GET, 'page', page)
        if _clean(request.POST, 'resource-id') == 'new':
            resource = Resource.objects.create(user=user)
        else:
            resource = Resource.objects.get(id=_clean(request.POST, 'resource-id'))

        resource.user = user
        resource.title = unescape(_clean(request.POST, 'title'))
        resource.nice_url = _clean(request.POST, 'nice-url')
        resource.content = unescape(_clean(request.POST, 'content'))
        resource.set_tags(_clean(request.POST, 'tags'))
        resource.published = 'published' in request.POST
        resource.sticky = 'sticky' in request.POST
        resource.save()

        return redirect('/resources?page=' + page)

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


def view_resource(request, nice_url):
    res = SiteResponse(request.user)
    user = None
    resource = None
    related_resources = []
    num_related = 5
    user = None
    is_admin = False
    if request.user.is_authenticated:
        user = User.objects.get(id=request.user.id)
        is_admin = user.is_superuser

    full_url = "{0}{1}/resources/{2}".format(
        settings.PROTOCOL_PREFIX,
        settings.ALLOWED_HOSTS[0],
        nice_url
    )

    try:
        resource = Resource.objects.get(nice_url=escape(nice_url))
        related_resources = Resource.objects.filter(
            tags__in=resource.tags.all(),
            published=True
        ).exclude(id=resource.id).order_by('tags__text', 'title')[0:num_related]
    except:
        res.errors.append(traceback.format_exc())

    if resource and user and request.method == 'POST' and _contains(request.POST, ['comment-text']):
        comment = Comment.objects.create(user=user, text=_clean(request.POST, 'comment-text'))
        resource.comments.add(comment)

    return render(
        request,
        settings.THEME_TEMPLATES['view_resource'],
        {
            'response': res,
            'page_id': 0,
            'user': user,
            'is_admin': is_admin,
            'resource': resource,
            'related_resources': related_resources,
            'full_url': full_url
        }
    )


def resources(request):
    res = SiteResponse(request.user)
    user = None
    is_admin = False
    tag_id = None
    if request.user.is_authenticated:
        user = User.objects.get(id=request.user.id)
        is_admin = user.is_superuser

    resource_list = []
    tag_list = []
    page = int(_clean(request.GET, 'page', '1'))
    per_page = int(_clean(request.GET, 'perpage', '6'))

    if request.method == 'GET' and 'tag-id' in request.GET:
        tag_id = _clean(request.GET, 'tag-id')
        if is_admin:
            resource_list = Resource.objects.filter(tags__id=tag_id).order_by('-sticky', 'title')
            tag_list = Tag.objects.filter(post__in=Resource.objects.all()).order_by('text').distinct()
        else:
            resource_list = Resource.objects.filter(tags__id=tag_id, published=True).order_by('-sticky', 'title')
            tag_list = Tag.objects.filter(post__in=Resource.objects.filter(published=True)).order_by('text').distinct()

    else:
        if is_admin:
            resource_list = Resource.objects.all().order_by('tags__text', '-sticky', 'title')
        else:
            resource_list = Resource.objects.filter(published=True).order_by('tags__text', '-sticky', 'title')

        tag_list = Tag.objects.filter(post__in=resource_list).order_by('text').distinct()

    resources, paginator = _paginate(resource_list, per_page, page)

    return render(
        request,
        settings.THEME_TEMPLATES['resources'],
        {
            'page_id': 0,
            'resources': resources,
            'tags': tag_list,
            'tag_id': tag_id,
            'paginator': paginator,
            'is_admin': is_admin,
            'response': res
        }
    )
