from django.contrib import admin
from .models import *


# PUBLISHER
@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    search_fields = ('press',)


# LANGUAGE
@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    pass


# FIELD
@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    verbose_name = 'Genre'
    verbose_name_plural = 'Genres'


#class FieldsInline(admin.TabularInline):
#    model = Source.fields.through
#    extra = 1
#    model._meta.verbose_name_plural = 'Genres'
#    model._meta.verbose_name = 'Genre'


# FORMAT
@admin.register(Format)
class FormatAdmin(admin.ModelAdmin):
    pass


# ROLE
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    pass


# PERSON
@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    search_fields = ('first_name', 'last_name', 'title',)


class RolePersonAdmin(admin.TabularInline):
    model = RolePerson
    extra = 1


@admin.register(PersonAlias)
class PersonAliasAdmin(admin.ModelAdmin):
    pass


# LOCATION
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    pass


@admin.register(LocationAlias)
class LocationAliasAdmin(admin.ModelAdmin):
    pass


# PERIOD
#@admin.register(Period)
#class PeriodAdmin(admin.ModelAdmin):
#    pass


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    #inlines = (RolePersonAdmin, FieldsInline)
    inlines = (RolePersonAdmin,)
    search_fields = ('title', 'container', 'institution', 'series_title', 'roleperson__person__last_name', 'doi')
    #exclude = ('fields', 'periods',)
    exclude = ('periods',)
