from __future__ import unicode_literals
from django.db import models, connection
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from home import _get_model_query
from django.utils.html import strip_tags
import re


def search_pages(query):
    search_results = []
    search_terms, model_query = _get_model_query(query, ['html'])

    pages = SitePage.objects.filter(published=True)
    for page in pages:
        contents = ContentVersion.objects.filter(
            version=0,
            column__row__section__page=page
        ).filter(model_query)

        if contents:
            context = ""
            full_text = ""

            for content in contents:
                full_text += " " + strip_tags(content.html)

            for term in search_terms:
                replacer = re.compile(re.escape(term), re.IGNORECASE)
                full_text = replacer.sub("<b>{0}</b>".format(term), full_text)

            for match in re.finditer("<b>", full_text):
                start = match.start() - settings.SEARCH_CONTEXT_SIZE
                if start < 0:
                    start = 0
                end = match.start() + settings.SEARCH_CONTEXT_SIZE
                context += full_text[start:end] + "</b> "

            if not context:
                context = full_text

            search_results.append({
                'type': 'page',
                'title': page.name,
                'url': '/' + page.url,
                'context': context
            })

    return search_results


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    website = models.CharField(max_length=255, blank=True)
    can_blog = models.BooleanField(default=False)
    can_cast = models.BooleanField(default=False)
    subscribe_newsletter = models.BooleanField(default=True)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()

    def __str__(self):
        return self.user.username


class SitePage(models.Model):
    name = models.CharField(max_length=100)
    url = models.CharField(max_length=200)
    published = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class SiteSection(models.Model):
    page = models.ForeignKey(SitePage, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    header_css_class = models.CharField(max_length=200)
    header_text = models.CharField(max_length=200)
    show_header = models.BooleanField(default=True)
    full_width = models.BooleanField(default=False)
    layout = models.TextField(default="{'rows': {}")
    order = models.IntegerField(default=0)

    def __str__(self):
        return str(self.id)

    @property
    def dict(self):
        if not hasattr(self, '_dict'):
            row_rows = SectionRow.objects.filter(section__id=self.id)
            rows = []
            for row in row_rows:
                cols = []
                col_rows = SectionColumn.objects.filter(row=row)
                for col in col_rows:
                    cols.append({
                        'id': col.id,
                        'width': col.width,
                        'css': col.css,
                        'is_custom': col.is_custom,
                        'order': col.order
                    })
                rows.append({
                    'id': row.id,
                    'css': row.css,
                    'order': row.order,
                    'cols': cols
                })

            self._dict = {
                'id': self.id,
                'name': self.name,
                'header_text': self.header_text,
                'header_css': self.header_css_class,
                'show_header': self.show_header,
                'full_width': self.full_width,
                'order': self.order,
                'rows': rows
            }
        return self._dict

    @property
    def rows(self):
        return SectionRow.objects.filter(section_id=self.id)

    class Meta:
        ordering = ['order']


class SectionRow(models.Model):
    section = models.ForeignKey(SiteSection, on_delete=models.CASCADE)
    css = models.CharField(max_length=200)
    order = models.IntegerField(default=0)

    @property
    def cols(self):
        return SectionColumn.objects.filter(row_id=self.id)

    class Meta:
        ordering = ['order']


class SectionColumn(models.Model):
    row = models.ForeignKey(SectionRow, on_delete=models.CASCADE)
    width = models.IntegerField()
    css = models.CharField(max_length=200)
    is_custom = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    def delete(self):
        versions = ContentVersion.objects.filter(column_id=self.id)
        for version in versions:
            version.delete()

        super(SectionColumn, self).delete()

    @property
    def html(self):
        if not hasattr(self, '_html'):
            content_version, created = ContentVersion.objects.get_or_create(
                column_id=self.id,
                version=0
            )

            self._html = content_version.html
        return self._html

    def __str__(self):
        return str(self.id)

    class Meta:
        ordering = ['order']


class ContentVersion(models.Model):
    column = models.ForeignKey(SectionColumn, on_delete=models.CASCADE)
    version = models.IntegerField(default=0)
    html = models.TextField(
        default='''Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed at enim bibendum, gravida orci eu, iaculis eros. Quisque accumsan, quam ac lacinia lobortis, risus urna commodo dui, et ultricies orci enim et metus. Duis sit amet odio ex.'''
    )

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        cursor = connection.cursor()
        cursor.execute(
            '''update {0} set version = version + 1 where
              column_id = {1}
              order by version desc
            '''.format(
                self._meta.db_table,
                self.column.id
            )
        )

        self.version = 0
        super(ContentVersion, self).save(*args, **kwargs)

    def search(self, query=None):
        qs = self.get_queryset()
        if query is not None:
            or_lookup = (Q(title__icontains=query) |
                         Q(description__icontains=query) |
                         Q(slug__icontains=query)
                         )
            qs = qs.filter(or_lookup).distinct()  # distinct() is often necessary with Q lookups
        return qs

    class Meta:
        unique_together = (("column", "version"),)