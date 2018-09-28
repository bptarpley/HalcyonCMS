from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache


class Publisher(models.Model):
    press = models.CharField(max_length=200)

    def __str__(self):
        return self.press

    def to_dict(self):
        return {
            'id': self.id,
            'press': self.press
        }

    class Meta:
        ordering = ['press']


class Language(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }

    class Meta:
        ordering = ['name']


class Field(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }

    class Meta:
        verbose_name = 'Genre'
        verbose_name_plural = 'Genres'
        ordering = ['name']


class Format(models.Model):
    type = models.CharField(max_length=40)

    def __str__(self):
        return self.type

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type
        }

    class Meta:
        ordering = ['type']


class Role(models.Model):
    function = models.CharField(max_length=50)

    def __str__(self):
        return self.function

    def to_dict(self):
        return {
            'id': self.id,
            'function': self.function
        }

    class Meta:
        ordering = ['function']


class Person(models.Model):
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50)
    title = models.CharField(max_length=35, blank=True, null=True)

    def __str__(self):
        name = ''
        title = ''
        if self.title:
            title = self.title
        first_name = ''
        if self.first_name:
            first_name = self.first_name

        if first_name or title:
            name = "{last}, {first} {title}".format(
                title=title,
                first=first_name,
                last=self.last_name
            ).strip()
        else:
            name = self.last_name

        return name

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'title': self.title
        }

    class Meta:
        ordering = ['last_name', 'first_name']


class RolePerson(models.Model):
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    source = models.ForeignKey('Source', on_delete=models.PROTECT)
    person = models.ForeignKey(Person, on_delete=models.PROTECT)

    def to_dict(self):
        return {
            'role': self.role.to_dict(),
            'person': self.person.to_dict(),
        }


class PersonAlias(models.Model):
    person = models.ForeignKey(Person, on_delete=models.PROTECT)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50)
    title = models.CharField(max_length=35, null=True)

    def __str__(self):
        title = ''
        if self.title:
            title = self.title
        first_name = ''
        if self.first_name:
            first_name = self.first_name

        return "{title} {first} {last}".format(
            title=title,
            first=first_name,
            last=self.last_name
        ).strip()

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'title': self.title
        }

    class Meta:
        ordering = ['last_name', 'first_name']


class Location(models.Model):
    country = models.CharField(max_length=50)

    def __str__(self):
        return self.country

    def to_dict(self):
        return {
            'id': self.id,
            'country': self.country
        }

    class Meta:
        ordering = ['country']


class LocationAlias(models.Model):
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    country = models.CharField(max_length=50)

    def __str__(self):
        return self.country

    def to_dict(self):
        return {
            'id': self.id,
            'country': self.country
        }

    class Meta:
        ordering = ['country']


class Period(models.Model):
    years = models.CharField(max_length=20)
    common_name = models.CharField(max_length=40)

    def __str__(self):
        return "{name} ({years})".format(
            name=self.common_name,
            years=self.years
        )

    def to_dict(self):
        return {
            'id': self.id,
            'years': self.years,
            'common_name': self.common_name
        }

    class Meta:
        ordering = ['common_name']


class Source(models.Model):
    title = models.CharField(max_length=400)
    container = models.CharField(max_length=200, blank=True, null=True)
    institution = models.CharField(max_length=50, blank=True, null=True)
    series_title = models.CharField(max_length=100, blank=True, null=True)
    series_number = models.IntegerField(blank=True, null=True)
    volume = models.IntegerField(blank=True, null=True)
    volume_number = models.IntegerField(blank=True, null=True)
    issue = models.IntegerField(blank=True, null=True)
    edition = models.IntegerField(blank=True, null=True)
    pages = models.CharField(max_length=10, blank=True, null=True)
    publisher = models.ForeignKey(Publisher, blank=True, null=True, on_delete=models.PROTECT)
    pub_year = models.CharField(max_length=50, blank=True, null=True, verbose_name='Date')
    doi = models.CharField(max_length=20, blank=True, null=True)
    language = models.ForeignKey(Language, blank=True, null=True, on_delete=models.PROTECT)
    fields = models.ManyToManyField(Field, blank=True, null=True, verbose_name='Genre')
    formats = models.ManyToManyField(Format, blank=True, null=True)
    roles = models.ManyToManyField(Role, through=RolePerson, blank=True, null=True)
    locations = models.ManyToManyField(Location, blank=True, null=True)
    periods = models.ManyToManyField(Period, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title[:200]

    def to_dict(self):
        pub_year = ''
        if self.pub_year:
            pub_year = str(self.pub_year.year)

        return {
            'id': self.id,
            'title': self.title,
            'container': self.container,
            'institution': self.institution,
            'series_title': self.series_title,
            'series_number': self.series_number,
            'volume': self.volume,
            'volume_number': self.volume_number,
            'issue': self.issue,
            'edition': self.edition,
            'pages': self.pages,
            'publisher': getattr(self, 'publisher', '').__str__(),
            'pub_year': pub_year,
            'doi': self.doi,
            'language': getattr(self, 'language', '').__str__(),
            'fields': [f.to_dict() for f in self.fields.all()],
            'formats': [f.to_dict() for f in self.formats.all()],
            'roles': [r.to_dict() for r in self.roleperson_set.all()],
            'locations': [l.to_dict() for l in self.locations.all()],
            'periods': [p.to_dict() for p in self.periods.all()]
        }

    class Meta:
        ordering = ['title']


def _clear_cache():
    cache.set('sources_datatables', [])

@receiver(post_save, sender=Source)
def source_post_save(sender, instance, **kwargs):
    _clear_cache()

@receiver(post_save, sender=Person)
def person_post_save(sender, instance, **kwargs):
    _clear_cache()