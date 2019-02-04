from __future__ import unicode_literals
from django.conf import settings
from django.contrib.auth import authenticate, logout
from django.contrib.auth import login as auth_login
from django.utils.html import escape
from django.shortcuts import render, redirect, HttpResponse
from django.template import loader, Context
from .models import *
from post.models import BlogEntry, PodCast, Resource
from bibliography.models import Source
from home import SiteResponse, _contains, _clean
from datetime import datetime
from html import unescape

import base64
import json
import traceback


def index(request):
    res = SiteResponse(request)

    page, sections, editing, res = process_CMS(request, res, '/')

    # GET RECENT POST, PODCAST, BIB ENTRY, AND RESOURCE
    try:
        post = BlogEntry.objects.filter(published=True, pub_date__lte=datetime.now()).order_by('-pub_date')[0:1][0]
    except:
        post = None

    try:
        podcast = PodCast.objects.filter(published=True, pub_date__lte=datetime.now()).order_by('-pub_date')[0:1][0]
    except:
        podcast = None

    try:
        source = Source.objects.filter().order_by('-id')[0:1][0]
    except:
        source = None

    try:
        resource = Resource.objects.filter(published=True, pub_date__lte=datetime.now()).order_by('-pub_date')[0:1][0]
    except:
        resource = None

    recent = {
        'post': post,
        'podcast': podcast,
        'source': source,
        'resource': resource
    }

    return render(
        request,
        settings.THEME_TEMPLATES['home_index'],
        {
            'response': res,
            'recent': recent,
            'page': page,
            'sections': sections,
            'editing': editing
        }
    )


def pages(request, nice_url='/'):
    res = SiteResponse(request)

    page, sections, editing, res = process_CMS(request, res, nice_url)

    return render(
        request,
        settings.THEME_TEMPLATES['pages'],
        {
            'response': res,
            'page': page,
            'sections': sections,
            'editing': editing
        }
    )


def search(request):
    res = SiteResponse(request)
    results = []

    if 'q' in request.GET:
        query = _clean(request.GET, 'q')

        if 'pages' in settings.SEARCH_INCLUDES:
            results += search_pages(query)
        if 'posts' in settings.SEARCH_INCLUDES:
            # importing like this because post module optional
            from post.models import search_blog, search_podcasts, search_resources
            results += search_blog(query)
            results += search_resources(query)
            results += search_podcasts(query)

    return render(
        request,
        settings.THEME_TEMPLATES['search'],
        {
            'response': res,
            'results': results
        }
    )


def login(request):
    res = SiteResponse(request)
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
    res = SiteResponse(request)
    next_url = '/'
    new_user = True
    if 'next' in request.GET:
        next_url = request.GET['next']

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

    if is_admin and 'impersonate-username' in request.GET:
        user = User.objects.get(username=_clean(request.GET, 'impersonate-username'))
        new_user = False

    elif is_admin and 'create' in request.GET:
        pass

    elif request.user.is_authenticated:
        new_user = False
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
                if next_url:
                    auth_login(request, user)
                    return redirect(next_url)
                elif new_user:
                    auth_login(request, user)
                    res.success = 'Registration complete!'
                else:
                    res.success = 'Profile updated.'

    return render(
        request,
        settings.THEME_TEMPLATES['create_user'],
        {
            'response': res,
            'page_id': 0,
            'user': user,
            'next': next_url,
            'is_admin': is_admin
        }
    )


def get_section(request):
    section = {}
    is_admin = request.user.is_superuser

    if is_admin and request.method == 'GET' and _contains(request.GET, ['section-id']):
        try:
            section = SiteSection.objects.get(id=_clean(request.GET, 'section-id'))
            section = section.dict
        except:
            section = {}

    return HttpResponse(
        json.dumps(section),
        content_type='application/json'
    )


def process_CMS(request, res, nice_url):
    page = None
    editing = False
    sections = []

    try:
        page = SitePage.objects.get(url=escape(nice_url))
    except:
        res.errors.append('Unable to find the page you requested.')

    if 'editing' in request.GET and res.is_admin:
        editing = True

    if res.is_admin and page and _contains(request.GET, ['editing', 'section', 'move']):
        section_id = _clean(request.GET, 'section')
        direction = _clean(request.GET, 'move')
        sections = SiteSection.objects.filter(page_id=page.id).order_by('order')
        swapped = False

        for x in range(0, len(sections)):
            if str(sections[x].id) == section_id:
                if direction == 'up':
                    if x > 0:
                        swap_order = sections[x - 1].order
                        sections[x - 1].order = sections[x].order
                        sections[x - 1].save()
                        sections[x].order = swap_order
                        sections[x].save()
                        swapped = True
                        break
                elif direction == 'down':
                    if x < len(sections) - 1:
                        swap_order = sections[x + 1].order
                        sections[x + 1].order = sections[x].order
                        sections[x + 1].save()
                        sections[x].order = swap_order
                        sections[x].save()
                        swapped = True
                        break

        if swapped:
            redirect('/{0}?editing=true'.format(nice_url))

    if page and request.method == 'POST':

        # HANDLE INLINE EDITOR SUBMISSION
        if res.is_admin and _contains(
                request.POST,
                [
                    'content_save',
                    'editabledata',
                    'editorID',
                ]):

            new_html = request.POST['editabledata']
            column_id = _clean(request.POST, 'editorID').replace('section-content-', '')

            ContentVersion.objects.create(
                column_id=column_id,
                html=new_html)

            #return HttpResponse('')

        # HANDLE CUSTOM EDITOR SUBMISSION
        elif res.is_admin and _contains(
                request.POST,
                [
                    'column-id',
                    'new-content',
                    'custom-content-save'
                ]
        ):
            column_id = _clean(request.POST, 'column-id')
            new_html = unescape(_clean(request.POST, 'new-content'))

            ContentVersion.objects.create(
                column_id=column_id,
                html=new_html
            )

        # HANDLE SECTION EDITOR SUBMISSION
        elif res.is_admin and _contains(
                request.POST,
                [
                    'page-id',
                    'sec-id',
                    'sec-order',
                    'layout-json',
                    'header-text',
                    'header-css',
                    'header-name'
                ]):

            sec_id = _clean(request.POST, 'sec-id')
            sec_order = int(_clean(request.POST, 'sec-order'))
            layout_json = request.POST['layout-json']

            if 'delete-section' in request.POST:
                section = section = SiteSection.objects.get(page=page, id=_clean(request.POST, 'sec-id'))
                section.delete()
            else:
                try:
                    sec_header_text = unescape(_clean(request.POST, 'header-text'))
                    sec_header_css = _clean(request.POST, 'header-css')
                    sec_header_name = _clean(request.POST, 'header-name')
                    sec_show_header = 'show-header' in request.POST
                    sec_full_width = 'full-width' in request.POST

                    section = None
                    if sec_id == 'new':
                        section = SiteSection.objects.create(
                            page_id=page.id,
                            order=sec_order,
                            header_css_class=sec_header_css,
                            header_text=sec_header_text,
                            name=sec_header_name,
                        )
                    else:
                        section = SiteSection.objects.get(page_id=page.id, id=sec_id)
                        section.header_text = sec_header_text
                        section.header_css_class = sec_header_css
                        section.name = sec_header_name
                        section.show_header = sec_show_header
                        section.full_width = sec_full_width
                        section.save()

                    if section:
                        layout = json.loads(layout_json)
                        existing_row_ids = []
                        existing_col_ids = []

                        for row in layout['rows']:
                            sec_row = None
                            if 'new' in row['id']:
                                sec_row = SectionRow.objects.create(
                                    section=section,
                                    css=row['css'],
                                    order=row['order']
                                )
                            else:
                                sec_row = SectionRow.objects.get(section=section, id=row['id'])
                                sec_row.css = row['css']
                                sec_row.order = row['order']
                                sec_row.save()
                            existing_row_ids.append(sec_row.id)

                            if sec_row:
                                for col in row['cols']:
                                    sec_col = None
                                    if 'new' in col['id']:
                                        sec_col = SectionColumn.objects.create(
                                            row=sec_row,
                                            width=col['size'],
                                            css=col['css'],
                                            is_custom=col['is_custom'],
                                            order=col['order']
                                        )
                                    else:
                                        sec_col = SectionColumn.objects.get(row=sec_row, id=col['id'])
                                        sec_col.width = col['size']
                                        sec_col.css = col['css']
                                        sec_col.is_custom = col['is_custom']
                                        sec_col.order = col['order']
                                        sec_col.save()
                                    existing_col_ids.append(sec_col.id)

                        # Delete any rows or cols that shouldn't exist anymore
                        rows_to_delete = SectionRow.objects.filter(section=section).exclude(pk__in=existing_row_ids)
                        for row in rows_to_delete:
                            row.delete()

                        cols_to_delete = SectionColumn.objects.filter(row__section=section).exclude(
                            pk__in=existing_col_ids)
                        for col in cols_to_delete:
                            col.delete()

                except:
                    res.errors.append(traceback.format_exc())

    # GET THE SECTIONS AND LOAD CONTENT
    try:
        sections = SiteSection.objects.filter(page_id=page.id).order_by('order')
        order = -1
        for section in sections:
            if 'section' in settings.THEME_TEMPLATES:
                template = loader.get_template(settings.THEME_TEMPLATES['section'])
                context = {
                    'section': section,
                    'response': res,
                    'editing': editing,
                    'page': page}
                section.html = template.render(context)

            if section.order == order:
                section.order += 1
                section.save()

            order = section.order

    except:
        res.errors.append(traceback.format_exc())
        sections = []

    return page, sections, editing, res
