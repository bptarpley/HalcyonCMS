from django import template


register = template.Library()

@register.filter(name='datetimeparse')
def datetimeparse(value):
    return value.strftime("%Y-%m-%d %H:%M")
