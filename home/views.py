from __future__ import unicode_literals
from django.conf import settings
from django.contrib.auth import authenticate, logout
from django.contrib.auth import login as auth_login
from django.shortcuts import render, redirect, HttpResponse
from .models import *
from post.models import BlogEntry, PodCast, Resource
from bibliography.models import Source
from home import SiteResponse, _contains, _clean
from datetime import datetime

import base64
import json
import traceback


def index(request):
    res = SiteResponse(request.user)

    page_id = 1
    is_admin = False
    fname = ''
    if request.user.is_authenticated:
        is_admin = request.user.is_superuser
        fname = request.user.first_name

    if request.method == 'POST':

        # HANDLE INLINE EDITOR SUBMISSION
        if is_admin and _contains(
            request.POST,
            [
                'content_save',
                'editabledata',
                'editorID',
            ]):

            new_html = request.POST['editabledata']
            content_id = _clean(request.POST, 'editorID').replace('section-content-', '')

            ContentVersion.objects.create(
                content_id=content_id,
                html=new_html)

            return HttpResponse('')

        # HANDLE CUSTOM EDITOR SUBMISSION
        elif is_admin and _contains(
            request.POST,
            [
                'content-id',
                'new-content',
                'custom-content-save'
            ]
        ):
            content_id = _clean(request.POST, 'content-id')
            new_html = base64.b64decode(request.POST['new-content']).decode('utf-8')

            ContentVersion.objects.create(
                content_id=content_id,
                html=new_html
            )

        # HANDLE SECTION EDITOR SUBMISSION
        elif is_admin and _contains(
            request.POST,
            [
                'page-id',
                'sec-id',
                'layout-json',
                'header-text',
                'header-css',
                'header-name'
            ]):

            sec_id = _clean(request.POST, 'sec-id')
            layout_json = request.POST['layout-json']

            if 'delete-section' in request.POST:
                section = SiteSection.objects.get(page_id=page_id, id=sec_id)
                section.delete()
            else:
                try:
                    layout = json.loads(layout_json)

                    for row_id in layout['rows'].keys():
                        for col_id in layout['rows'][row_id]['cols'].keys():
                            if not layout['rows'][row_id]['cols'][col_id].get('content_id', False):
                                content = SiteContent.objects.create(
                                    name='New content',
                                    is_custom=layout['rows'][row_id]['cols'][col_id].get('is_custom', False)
                                )
                                layout['rows'][row_id]['cols'][col_id]['content_id'] = content.id
                            else:
                                content = SiteContent.objects.get(id=layout['rows'][row_id]['cols'][col_id]['content_id'])
                                if content.is_custom != layout['rows'][row_id]['cols'][col_id]['is_custom']:
                                    content.is_custom = layout['rows'][row_id]['cols'][col_id]['is_custom']
                                    content.save()
                except:
                    res.errors.append(traceback.format_exc())

                sec_header_text = _clean(request.POST, 'header-text')
                sec_header_css = _clean(request.POST, 'header-css')
                sec_header_name = _clean(request.POST, 'header-name')


                section = None
                if sec_id == 'new':
                    section = SiteSection.objects.create(
                        page_id=page_id,
                        header_css_class=sec_header_css,
                        header_text=sec_header_text,
                        name=sec_header_name,
                        layout=json.dumps(layout)
                    )
                else:
                    section = SiteSection.objects.get(page_id=page_id, id=sec_id)
                    section.header_text = sec_header_text
                    section.header_css_class = sec_header_css
                    section.name = sec_header_name
                    section.set_layout(layout)
                    section.save()

    # GET THE SECTIONS AND LOAD CONTENT
    try:
        sections = SiteSection.objects.filter(page_id=page_id)
    except:
        res.errors.append(traceback.format_exc())
        sections = []

    # GET RECENT POST, PODCAST, BIB ENTRY, AND RESOURCE
    recent = {
        'post': BlogEntry.objects.filter(published=True, pub_date__lte=datetime.now()).order_by('-pub_date')[0:1][0],
        'podcast': PodCast.objects.filter(published=True, pub_date__lte=datetime.now()).order_by('-pub_date')[0:1][0],
        'source': Source.objects.filter().order_by('-id')[0:1][0],
        'resource': Resource.objects.filter(published=True, pub_date__lte=datetime.now()).order_by('-pub_date')[0:1][0]
    }

    return render(
        request,
        settings.THEME_TEMPLATES['home_index'],
        {
            'response': res,
            'page_id': page_id,
            'sections': sections,
            'is_admin': is_admin,
            'fname': fname,
            'recent': recent,
            'tagline': "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed at enim bibendum, gravida orci eu, iaculis eros.",
            'lorem': "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed at enim bibendum, gravida orci eu, iaculis eros. Quisque accumsan, quam ac lacinia lobortis, risus urna commodo dui, et ultricies orci enim et metus. Duis sit amet odio ex."
        }
    )

def login(request):
    res = SiteResponse(request.user)
    next_url = '/'
    user = None

    if 'next' in request.GET:
        next_url = request.GET['next']

    if request.user.is_authenticated:
        return redirect(next_url)

    if request.method == 'POST' and _contains(request.POST, ['user', 'password']):
        user = authenticate(username=_clean(request.POST, 'user'), password=_clean(request.POST, 'password'))
        if user is not None:
            auth_login(request, user)
            return redirect(next_url)
        else:
            res.errors.append('Invalid username/password.')

    return render(
        request,
        settings.THEME_TEMPLATES['login'],
        {
            'response': res,
            'page_id': 0,
            'next_url': next_url
        }
    )

def register(request):
    res = SiteResponse(request.user)
    user = {
        'id': 'new',
        'username': '',
        'email': '',
        'first_name': '',
        'last_name': '',
        'is_superuser': False,
        'profile': {
            'website': '',
            'can_blog': False,
            'can_cast': False,
            'subscribe_newsletter': True,
        }
    }
    is_admin = request.user.is_superuser

    if is_admin and 'impersonate' in request.GET:
        user = User.objects.get(id=_clean(request.GET, 'impersonate'))

    elif is_admin and 'create' in request.GET:
        pass

    elif request.user.is_authenticated:
        user = User.objects.get(id=request.user.id)
        if request.method == 'GET' and 'logout' in request.GET:
            logout(request)
            return redirect('/')

    if request.method == 'POST' and _contains(request.POST, [
        'user',
        'password',
        'email',
        'fname',
        'lname',
        'website'
    ]):
        username = _clean(request.POST, 'user')
        password = _clean(request.POST, 'password')
        email = _clean(request.POST, 'email')
        fname = _clean(request.POST, 'fname')
        lname = _clean(request.POST, 'lname')
        website = _clean(request.POST, 'website')

        if 'password2' in request.POST:
            if not password == _clean(request.POST, 'password2'):
                user['username'] = username
                user['email'] = email
                user['first_name'] = fname
                user['last_name'] = lname
                user['profile']['website'] = website
                res.errors.append('Your passwords do not match.')

        if not res.errors:
            if hasattr(user, 'id'):
                user.username = username
                if password:
                    user.set_password(password)
                user.email = email
            else:
                user = User.objects.create_user(
                    username,
                    email,
                    password
                )

            user.first_name = fname
            user.last_name = lname
            user.is_superuser = 'is-admin' in request.POST
            user.profile.website = website
            user.profile.can_blog = 'can-blog' in request.POST
            user.profile.can_cast = 'can-cast' in request.POST
            if user.is_superuser or user.profile.can_blog or user.profile.can_cast:
                user.is_staff = True

            user.profile.subscribe_newsletter = 'subscribe' in request.POST
            user.save()

            if 'create' in request.GET:
                return redirect('/accounts/register/?impersonate=' + str(user.id))
            else:
                res.success = 'Profile updated.'

    return render(
        request,
        settings.THEME_TEMPLATES['create_user'],
        {
            'response': res,
            'page_id': 0,
            'user': user,
            'is_admin': is_admin
        }
    )


def get_section(request):
    section = {}
    is_admin = request.user.is_superuser

    if is_admin and request.method == 'GET' and _contains(request.GET, ['section-id']):
        try:
            site_section = SiteSection.objects.get(id=_clean(request.GET, 'section-id'))
            section = {
                'header_text': site_section.header_text,
                'header_css': site_section.header_css_class,
                'name': site_section.name,
                'layout': site_section.site_layout
            }
        except:
            section = {}

    return HttpResponse(
        json.dumps(
            {
                'section': section,
            }
        ),
        content_type='application/json'
    )

def edit_content(request):
    pass