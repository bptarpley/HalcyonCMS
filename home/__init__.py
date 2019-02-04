from django.utils.html import escape
from django.db.models import Q
import re

class SiteResponse(object):

    def __init__(self, req=None):
        self.fname = ''
        self.is_admin = False

        if req.user:
            if req.user.is_authenticated:
                self.fname = req.user.first_name
                self.is_admin = req.user.is_superuser

        self.browser = ""
        if _contains(req.META['HTTP_USER_AGENT'], [
            'Mozilla',
            'Pixel Build',
            'Chrome'
        ]):
            self.browser = "PIXEL_CHROME"

        self.messages = []
        self.errors = []
        self.success = ""


def _contains(obj, keys):
    has_keys = True
    for k in keys:
        if not k in obj:
            has_keys = False
    return has_keys


def _clean(obj, key, default_value=''):
    return escape(obj.get(key, default_value))


def _get_model_query(query_string, search_fields):
    query = None
    findterms = re.compile(r'"([^"]+)"|(\S+)').findall
    normspace = re.compile(r'\s{2,}').sub
    terms = [normspace('', (t[0] or t[1]).strip()) for t in findterms(query_string)]
    print(terms)

    for term in terms:
        or_query = None  # Query to search for a given term in each field
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query | or_query

    return terms, query


def _paginate(list, per_page, current_page):
    num_items = len(list)

    if per_page > num_items:
        per_page = num_items

    if num_items > 0:
        num_pages = -(-num_items // per_page)
    else:
        num_pages = 0

    if current_page > num_pages:
        current_page = num_pages
    elif current_page < 1:
        current_page = 1

    previous_page = current_page - 1
    has_previous = previous_page > 0

    next_page = current_page + 1
    has_next = next_page <= num_pages

    paginator = {
        'has_previous': has_previous,
        'previous_page_number': previous_page,
        'has_next': has_next,
        'next_page_number': next_page,
        'number': current_page,
        'num_pages': num_pages
    }

    start_index = (current_page - 1) * per_page
    stop_index = start_index + per_page
    return list[start_index:stop_index], paginator
