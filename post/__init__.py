from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware, make_aware


def get_datetime(date_str):
    dt = parse_datetime(date_str)
    if not is_aware(dt):
        dt = make_aware(dt)
    return dt
