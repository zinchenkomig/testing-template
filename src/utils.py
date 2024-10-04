import re


def make_search_query(search: str):
    pattern = re.compile('[\W_]+')
    search = pattern.sub(' ', search)
    search = ':* | '.join(search.strip().lower().split(' ')) + ':*'
    return search
