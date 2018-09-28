import os
import json
from django.core.management.base import BaseCommand, CommandError
from django.template import loader, Context
from wbhb.viewer.models import *


class Command(BaseCommand):

    def handle(self, *args, **options):

        if os.path.exists('fields.json'):
            print('yup')
        else:
            print('nope')

        sources = Source.objects.all()

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
                "<a href='/detail?id=" + str(source.id) + "'>" + source.title + "</a>",
                people,
                source.pub_year,
                source.language.__str__(),
                countries,
                fields,
                source.notes
            ]
            sources_json['data'].append(s_data)

        with open('sources_datatables.json', 'w') as fout:
            json.dump(sources_json, fout)

        template = loader.get_template('export.txt')
        context = Context({'sources': sources})

        with open('export.txt', 'w') as fout:
            fout.write(template.render(context).replace('\n', '\r\n'))
