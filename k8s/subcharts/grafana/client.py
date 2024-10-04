import logging
import sys
from copy import copy

import requests

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def log_operation(f):
    def wrapper(*args, **kwargs):
        resp = f(*args, **kwargs)
        logger.info(f'{f.__name__} run successfully')
        return resp
    return wrapper


class GrafanaRequestException(Exception):

    def __init__(self, resp: requests.Response):
        self.resp = resp

    def __str__(self):
        return f'GrafanaRequestException. Status: {self.resp.status_code}. Details: {self.resp.text}'


class GrafanaClient:

    # gets the password field name
    password_mapper = {
        'elasticsearch': 'basicAuthPassword',
        'grafana-postgresql-datasource': 'password'
    }

    def __init__(self, base_url, user, password):
        self.base_url = base_url
        self.user = user
        self.password = password

    def _url_construct(self, ep):
        return f'http://{self.user}:{self.password}@{self.base_url}{ep}'

    @staticmethod
    def _manage_resp(resp):
        if resp.status_code >= 400:
            raise GrafanaRequestException(resp)
        return resp.json()

    def _post(self, ep: str, body: dict):
        resp = requests.post(self._url_construct(ep), json=body, verify=False)
        return self._manage_resp(resp)

    def _get(self, ep: str, params: dict = None):
        resp = requests.get(self._url_construct(ep), params=params, verify=False)
        return self._manage_resp(resp)

    @log_operation
    def add_dashboard(self, dash_data: dict):
        req = {
            'dashboard': dash_data
        }
        response = self._post('/api/dashboards/db', body=req)
        logger.info(response)

    @log_operation
    def add_datasource(self, data: dict, password: str = None):
        d = copy(data)
        if password is not None:
            d['secureJsonData'] = {
                self.password_mapper[d['type']]: password
            }
        return self._post('/api/datasources', body=d)['datasource']['uid']

    @log_operation
    def get_datasources(self):
        resp = self._get('/api/datasources')
        return resp
