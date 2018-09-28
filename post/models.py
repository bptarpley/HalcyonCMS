from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User
import json


class Tag(models.Model):
    text = models.CharField(max_length=100)

    def __str__(self):
        return self.text


class Post(models.Model):
    title = models.CharField(max_length=255, default='New Post')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)
    pub_date = models.DateTimeField(auto_now_add=True)

    def set_tags(self, comma_delimited_tags):
        tag_strings = comma_delimited_tags.split(',')

        current_tags = self.tags.all()
        for current_tag in current_tags:
            found = False
            for tag_string in tag_strings:
                tag_text = tag_string.strip().lower()
                if tag_text == current_tag.text:
                    found = True
            if not found:
                self.tags.remove(current_tag)

        for tag_string in tag_strings:
            tag = None
            tag_text = tag_string.strip().lower()

            try:
                tag = Tag.objects.get(text=tag_text)
            except:
                tag = Tag.objects.create(text=tag_text)

            if tag:
                self.tags.add(tag)

    @property
    def tag_string(self):
        if not hasattr(self, '_tag_string'):
            comma_delimited = ''
            current_tags = self.tags.all()
            for current_tag in current_tags:
                comma_delimited += current_tag.text + ', '
            if comma_delimited:
                comma_delimited = comma_delimited[:-2]
            self._tag_string = comma_delimited
        return self._tag_string



    def __str__(self):
        return self.title


class BlogEntry(Post):
    content = models.TextField(default='Lorem ipsum')
    published = models.BooleanField(default=False)


class PodCast(Post):
    summary = models.TextField(default='Lorem ipsum')
    guid = models.CharField(max_length=100)
    duration = models.CharField(max_length=10)
    explicit = models.CharField(max_length=5)
    url = models.CharField(max_length=255)
    byte_size = models.IntegerField(default=0)
    published = models.BooleanField(default=False)

    def set_duration(self, seconds):
        hours = int(seconds / 3600)
        minutes = int(seconds / 60)

        hr_str = str(hours)
        mn_str = str(minutes)
        sc_str = str(int(seconds - (hours * 3600) - (minutes * 60)))

        if len(hr_str) < 2:
            hr_str = '0' + hr_str

        if len(mn_str) < 2:
            mn_str = '0' + mn_str

        if len(sc_str) < 2:
            sc_str = '0' + sc_str

        self.duration = "{0}:{1}:{2}".format(hr_str, mn_str, sc_str)


class Resource(Post):
    content = models.TextField(default='Lorem ipsum')
    published = models.BooleanField(default=False)