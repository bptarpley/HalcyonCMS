import os
import json
from django.shortcuts import render, HttpResponse
from django.db.models import prefetch_related_objects
from django.utils.html import escape
from django.conf import settings
from django.template import loader, Context
from django.contrib.auth.models import User
from .models import *
from home import SiteResponse


def index(request):
    res = SiteResponse(request.user)
    is_admin = False
    can_blog = False
    if request.user.is_authenticated:
        is_admin = request.user.is_superuser
        user = User.objects.get(id=request.user.id)
        can_blog = user.profile.can_blog

    return render(
        request,
        settings.THEME_TEMPLATES['bib_index'],
        {
            'page_id': 40,
            'response': res,
            'is_admin': is_admin,
            'can_blog': can_blog
        }
    )


def source_detail(request):
    res = SiteResponse(request.user)
    source = None

    if request.method == 'GET':
        id = _clean(request, 'id')
        source = Source.objects.get(id=id)

    return render(
        request,
        settings.THEME_TEMPLATES['bib_detail'],
        {
            'source': source,
            'response': res
        }
    )


def export(request):
    sources = None
    ids = []

    response = HttpResponse(content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="export.txt"'

    if request.method == 'POST':
        ids = _clean(request, 'ids', '', 'POST')
        if ids:
            ids = ids.split(',')

    if ids:
        sources = Source.objects.filter(id__in=ids)
    else:
        if os.path.exists('export.txt'):
            with open('export.txt', 'r') as fin:
                response.write(fin.read())
            return response
        else:
            sources = Source.objects.all()

    template = loader.get_template(settings.THEME_TEMPLATES['bib_export'])
    context = {'sources': sources}
    response.write(template.render(context).replace('\n', '\r\n'))

    return response


def sources(request):
    format = 'default'
    filter_string = None
    sources_json = []
    sources = []

    if request.method == 'GET':
        format = _clean(request, 'format', 'default')
        filter_string = _clean(request, 'filter')

    sources = Source.objects.filter()

    if filter_string:
        filters = filter_string.split(",")
        for f in filters:
            f_parts = f.split("_")
            if len(f_parts) == 2:
                filter_type = f_parts[0]
                filter_id = f_parts[1]

                if filter_type == "person":
                    sources = sources.filter(roleperson__person__id=filter_id).distinct()
                if filter_type == "role":
                    sources = sources.filter(roleperson__role__id=filter_id).distinct()
                elif filter_type == "location":
                    sources = sources.filter(locations__id=filter_id)
                elif filter_type == "language":
                    sources = sources.filter(language__id=filter_id)
                elif filter_type == "publisher":
                    sources = sources.filter(publisher__id=filter_id)
                elif filter_type == "field":
                    sources = sources.filter(fields__id=filter_id)

    if format == 'default':
        for source in sources:
            sources_json.append(source.to_dict())
    elif format == 'datatables':

        if not filter_string:
            if os.path.exists(settings.TABLE_CACHE_FILE):
                with open(settings.TABLE_CACHE_FILE, 'r') as fin:
                    sources_json = json.load(fin)

        if not sources_json:
            sources_json = {
                'data': []
            }
            for source in sources:
                people = ""
                for person in source.roleperson_set.all():
                    people += person.person.__str__() + " (" + person.role.function + ")<br>"
                if len(people) > 2:
                    people = people[:-2]

                countries = ""
                for location in source.locations.all():
                    countries += location.__str__() + ", "
                if len(countries) > 2:
                    countries = countries[:-2]

                fields = ""
                for field in source.fields.all():
                    fields += field.__str__() + ", "
                if len(fields) > 2:
                    fields = fields[:-2]

                s_data = [
                    str(source.id),
                    "<a href='/bibliography/detail?id=" + str(source.id) + "'>" + source.title + "</a>",
                    people,
                    source.pub_year,
                    source.publisher.__str__(),
                    fields,
                    source.notes
                ]
                sources_json['data'].append(s_data)

    return HttpResponse(
        json.dumps(sources_json),
        content_type='application/json'
    )


def people(request):
    format = 'default'
    people_json = []

    if request.method == 'GET':
        format = _clean(request, 'format', 'default')

    people = Person.objects.all()

    if format == 'default':
        for person in people:
            people_json.append(person.to_dict())

    elif format == 'datatables':
        people_json = {'data': []}
        for person in people:
            people_json['data'].append(
                [
                    "<a href='javascript: filter(\"person\", " + str(person.id) + ", \"" + person.__str__().replace('"',
                                                                                                                    '').replace(
                        "'", "&apos;") + "\");'>" + person.__str__() + "</a>"
                ]
            )

    return HttpResponse(
        json.dumps(people_json),
        content_type='application/json'
    )


def locations(request):
    format = 'default'
    loc_json = []

    if request.method == 'GET':
        format = _clean(request, 'format', 'default')

    locs = Location.objects.all()

    if format == 'default':
        for loc in locs:
            loc_json.append(loc.to_dict())
    elif format == 'datatables':
        loc_json = {'data': []}
        for loc in locs:
            loc_json['data'].append(
                [
                    "<a href='javascript: filter(\"location\", " + str(loc.id) + ", \"" + loc.__str__().replace('"',
                                                                                                                '').replace(
                        "'", "&apos;") + "\");'>" + loc.__str__() + "</a>"
                ]
            )

    return HttpResponse(
        json.dumps(loc_json),
        content_type='application/json'
    )


def languages(request):
    format = 'default'
    lang_json = []

    if request.method == 'GET':
        format = _clean(request, 'format', 'default')

    langs = Language.objects.all()

    if format == 'default':
        for lang in langs:
            lang_json.append(lang.to_dict())
    elif format == 'datatables':
        lang_json = {'data': []}
        for lang in langs:
            lang_json['data'].append(
                [
                    "<a href='javascript: filter(\"language\", " + str(lang.id) + ", \"" + lang.__str__().replace('"',
                                                                                                                  '').replace(
                        "'", "&apos;") + "\");'>" + lang.__str__() + "</a>"
                ]
            )

    return HttpResponse(
        json.dumps(lang_json),
        content_type='application/json'
    )


def publishers(request):
    format = 'default'
    pub_json = []

    if request.method == 'GET':
        format = _clean(request, 'format', 'default')

    pubs = Publisher.objects.all()

    if format == 'default':
        for pub in pubs:
            pub_json.append(pub.to_dict())
    elif format == 'datatables':
        pub_json = {'data': []}
        for pub in pubs:
            pub_json['data'].append(
                [
                    "<a href='javascript: filter(\"publisher\", " + str(pub.id) + ", \"" + pub.__str__().replace('"',
                                                                                                                 '').replace(
                        "'", "&apos;") + "\");'>" + pub.__str__() + "</a>"
                ]
            )

    return HttpResponse(
        json.dumps(pub_json),
        content_type='application/json'
    )


def roles(request):
    format = 'default'
    rl_json = []

    if request.method == 'GET':
        format = _clean(request, 'format', 'default')

    rls = Role.objects.all()

    if format == 'default':
        for rl in rls:
            rl_json.append(rl.to_dict())
    elif format == 'datatables':
        rl_json = {'data': []}
        for rl in rls:
            rl_json['data'].append(
                [
                    "<a href='javascript: filter(\"role\", " + str(rl.id) + ", \"" + rl.__str__().replace('"',
                                                                                                          '').replace(
                        "'", "&apos;") + "\");'>" + rl.__str__() + "</a>"
                ]
            )

    return HttpResponse(
        json.dumps(rl_json),
        content_type='application/json'
    )


def fields(request):
    format = 'default'
    field_json = []

    if request.method == 'GET':
        format = _clean(request, 'format', 'default')

    fields = Field.objects.all()

    if format == 'default':
        for field in fields:
            field_json.append(field.to_dict())
    elif format == 'datatables':
        field_json = {'data': []}
        for field in fields:
            field_json['data'].append(
                [
                    "<a href='javascript: filter(\"field\", " + str(field.id) + ", \"" + field.__str__().replace('"',
                                                                                                                 '').replace(
                        "'", "&apos;") + "\");'>" + field.__str__() + "</a>"
                ]
            )

    return HttpResponse(
        json.dumps(field_json),
        content_type='application/json'
    )


def periods(request):
    format = 'default'
    period_json = []

    if request.method == 'GET':
        format = _clean(request, 'format', 'default')

    periods = Period.objects.all()

    if format == 'default':
        for period in periods:
            period_json.append(period.to_dict())
    elif format == 'datatables':
        period_json = {'data': []}
        for period in periods:
            period_json['data'].append(
                [
                    "<a href='javascript: filter(\"period\", " + str(period.id) + ", \"" + period.__str__().replace('"',
                                                                                                                    '').replace(
                        "'", "&apos;") + "\");'>" + period.__str__() + "</a>"
                ]
            )

    return HttpResponse(
        json.dumps(period_json),
        content_type='application/json'
    )


def _clean(request, param, default='', method='GET'):
    clean_value = None

    if method == 'GET':
        clean_value = escape(request.GET.get(param, default))
    elif method == 'POST':
        clean_value = escape(request.POST.get(param, default))

    return clean_value