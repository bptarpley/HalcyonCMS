from django import template
from django.conf import settings
import re


register = template.Library()


@register.filter(name='datetimeparse')
def datetimeparse(value):
    return value.strftime("%m/%d/%Y")


@register.filter('startswith')
def startswith(text, starts):
    if isinstance(text, str):
        return text.startswith(starts)
    return False


@register.filter('feeddate')
def feeddate(value):
    return value.strftime("%a, %-d %b %Y %H:%M:%S %z")


@register.filter('cleanhtml')
def cleanhtml(value):
    clean = re.sub(r'data-cke-saved-src=\"[^\"]*\"', '', value)
    clean = re.sub(r'data-cke-saved-href=\"[^\"]*\"', '', clean)
    clean = re.sub(r'class=\"[^\"]*"', '', clean)
    clean = re.sub(r'src=\"\/', 'src="{0}/'.format(settings.SITE_PREFIX), clean)
    clean = re.sub(r'href=\"\/', 'href="{0}/'.format(settings.SITE_PREFIX), clean)
    return clean
