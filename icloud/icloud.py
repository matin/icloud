import json
import urllib.request
from urllib.request import Request

from .utils import memoize


__all__ = ['iCloud', 'iCloudNode']


HEADERS = {
    'origin': 'https://www.icloud.com',
    'content-type': 'text/plain',
    }


class iCloud(object):

    def __init__(self):
        cookie_processor = urllib.request.HTTPCookieProcessor()
        self.opener = urllib.request.build_opener(cookie_processor)
        self.cookiejar = cookie_processor.cookiejar

    def login(self, username, password):
        url = 'https://setup.icloud.com/setup/ws/1/login'
        params = {
            'apple_id': username,
            'password': password,
            'extended_login': True,
            }
        data = bytes(json.dumps(params), 'utf-8')
        req = Request(url, data=data, headers=HEADERS)
        self.opener.open(req)
        auth_cookie = [cookie for cookie in self.cookiejar
                       if cookie.name == 'X-APPLE-WEBAUTH-TOKEN'][0]
        auth_cookie_dict = dict(item.split('=') for item
                                in auth_cookie.value.split(':'))
        self.dsid = auth_cookie_dict['d']

    def get_node(self, node_id):
        url = ('https://p04-ubiquityws.icloud.com/ws/{dsid}/item/{node_id}?'
               'dsid={dsid}'.format(dsid=self.dsid, node_id=node_id))
        req = Request(url, headers=HEADERS)
        resp_body = self.opener.open(req).read()
        return iCloudNode(self, **json.loads(resp_body.decode('utf-8')))

    def get_children(self, node_id):
        url = ('https://p04-ubiquityws.icloud.com/ws/{dsid}/parent/{node_id}?'
               'dsid={dsid}'.format(dsid=self.dsid, node_id=node_id))
        req = Request(url, headers=HEADERS)
        resp_body = self.opener.open(req).read()
        items = json.loads(resp_body.decode('utf-8'))['item_list']
        return [iCloudNode(self, **item) for item in items]

    @property
    @memoize
    def root(self):
        return self.get_node(0)


class iCloudNode(object):

    def __init__(self, conn, **kwargs):
        self.__dict__.update(kwargs)
        self.conn = conn

    @property
    @memoize
    def children(self):
        return self.conn.get_children(self.item_id)
