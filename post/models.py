from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from home import _get_model_query
from django.utils.html import strip_tags
import re


def search_blog(query):
    search_results = []
    search_terms, model_query = _get_model_query(query, ['title', 'content'])

    posts = BlogEntry.objects.filter(published=True).filter(model_query)
    for post in posts:
        context = ""
        full_text = strip_tags(post.content)

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
            'type': 'blog',
            'title': post.title,
            'url': '/blog/' + post.nice_url,
            'context': context
        })

    return search_results


def search_resources(query):
    search_results = []
    search_terms, model_query = _get_model_query(query, ['title', 'content'])

    resources = Resource.objects.filter(published=True).filter(model_query)
    for resource in resources:
        context = ""
        full_text = strip_tags(resource.content)

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
            'type': 'resource',
            'title': resource.title,
            'url': '/resources/' + resource.nice_url,
            'context': context
        })

    return search_results


def search_podcasts(query):
    search_results = []
    search_terms, model_query = _get_model_query(query, ['title', 'summary'])

    podcasts = PodCast.objects.filter(published=True).filter(model_query)
    for cast in podcasts:
        context = ""
        full_text = strip_tags(cast.summary)

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
            'type': 'resource',
            'title': cast.title,
            'url': '/podcast/' + cast.nice_url,
            'context': context
        })

    return search_results


class Tag(models.Model):
    text = models.CharField(max_length=100)

    def __str__(self):
        return self.text


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    pub_date = models.DateTimeField(auto_now_add=True)


class Post(models.Model):
    title = models.CharField(max_length=255, default='New Post')
    nice_url = models.CharField(max_length=255, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)
    comments = models.ManyToManyField(Comment, blank=True)
    pub_date = models.DateTimeField(auto_now_add=True)
    sticky = models.BooleanField(default=False)
    featured_image = models.CharField(max_length=255, blank=True, null=True)

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
    itunes_summary = models.TextField(default='Lorem ipsum')
    guid = models.CharField(max_length=100)
    duration = models.CharField(max_length=10, blank=True, null=True)
    explicit = models.CharField(max_length=5)
    url = models.CharField(max_length=255, blank=True, null=True)
    byte_size = models.IntegerField(default=0, blank=True, null=True)
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
    ratings = models.ManyToManyField(Rating)