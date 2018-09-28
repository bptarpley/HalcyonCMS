from __future__ import unicode_literals
from django.db import models, connection
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import json


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


class SitePage(models.Model):
    name = models.CharField(max_length=100)
    url = models.CharField(max_length=200)

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
    def site_layout(self):
        if not hasattr(self, '_site_layout'):
            layout = json.loads(getattr(self, 'layout', '{}'))
            for row_id in layout['rows'].keys():
                for col_id in layout['rows'][row_id]['cols'].keys():
                    if 'content_id' in layout['rows'][row_id]['cols'][col_id]:
                        content = SiteContent.objects.get(id=layout['rows'][row_id]['cols'][col_id]['content_id'])
                        layout['rows'][row_id]['cols'][col_id]['html'] = content.html
            self._site_layout = layout
        return self._site_layout

    def set_layout(self, layout):
        # the layout property allows you to create bootstrap
        # grids (cols have max width of 12) for this site section. a generic two-column
        # layout looks like this:

        '''
        {
            'rows': {
                '0': {
                    'cols': {
                        '0': {
                            'width': 6,
                            'is_custom': False,
                            'content_id': 0,
                        },
                        '1': {
                            'width': 6,
                            'content_id': 1,
                        }
                    }
                }
            }
        }
        '''

        self.layout = json.dumps(layout, sort_keys=True)

    def delete(self):
        content_ids = []
        if 'rows' in self.site_layout:
            for row in self.site_layout['rows'].keys():
                if 'cols' in self.site_layout['rows'][row]:
                    for col in self.site_layout['rows'][row]['cols'].keys():
                        content_ids.append(self.site_layout['rows'][row]['cols'][col]['content_id'])

        for content_id in content_ids:
            content = SiteContent.objects.get(id=content_id)
            content.delete()

        super(SiteSection, self).delete()

    class Meta:
        ordering = ['-order']


class SiteContent(models.Model):
    name = models.CharField(max_length=200)
    is_custom = models.BooleanField(default=False)

    @property
    def html(self):
        if not hasattr(self, '_html'):
            content_version, created = ContentVersion.objects.get_or_create(
                content_id=self.id,
                version=0
            )

            self._html = content_version.html
        return self._html

    def delete(self):
        versions = ContentVersion.objects.filter(content_id=self.id)
        for version in versions:
            version.delete()

        super(SiteContent, self).delete()

    def __str__(self):
        return str(self.id)


class ContentVersion(models.Model):
    content = models.ForeignKey(SiteContent, on_delete=models.CASCADE)
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
              content_id = {1}
              order by version desc
            '''.format(
                self._meta.db_table,
                self.content.id
            )
        )

        self.version = 0
        super(ContentVersion, self).save(*args, **kwargs)

    class Meta:
        unique_together = (("content", "version"),)