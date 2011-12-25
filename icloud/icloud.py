import json
import time
import urllib.request
from urllib.parse import urlencode
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
        self.opener.open(Request(url, data=data, headers=HEADERS))
        auth_cookie = [cookie for cookie in self.cookiejar
                       if cookie.name == 'X-APPLE-WEBAUTH-TOKEN'][0]
        auth_cookie_dict = dict(item.split('=') for item
                                in auth_cookie.value.split(':'))
        self.dsid = auth_cookie_dict['d']

    def get(self, url):
        resp = self.opener.open(Request(url, headers=HEADERS))
        return json.loads(resp.read().decode('utf-8'))

    def get_node(self, node_id):
        url = ('https://p04-ubiquityws.icloud.com/ws/{dsid}/item/{node_id}?'
               'dsid={dsid}'.format(dsid=self.dsid, node_id=node_id))
        return iCloudNode(self, **self.get(url))

    def get_children(self, node_id):
        url = ('https://p04-ubiquityws.icloud.com/ws/{dsid}/parent/{node_id}?'
               'dsid={dsid}'.format(dsid=self.dsid, node_id=node_id))
        items = self.get(url)['item_list']
        return [iCloudNode(self, **item) for item in items]

    @property
    @memoize
    def root(self):
        return self.get_node(0)

    def download_file(self, node, file_type):
        if node.type != 'package':
            raise Exception('Can not download type "{}"'.format(node.type))
        
        # Export document
        query = urlencode({
            'dsid': self.dsid,
            'document_guid': node.item_id,
            'document_type': file_type,  #TODO: Validate
            'format': 'com.apple.iwork.pages.sffpages',
            })
        url = ('https://p04-ubiquityws.icloud.com/iw/export/{}/'
               'export_document?'.format(self.dsid) + query)
        job_id = self.get(url)['job_id']

        # Check export status
        params = urlencode({'job_id': job_id})
        url = ('https://p04-ubiquityws.icloud.com/iw/export/{}/'
               'check_export_status?'.format(self.dsid) + params)
        while True:
            job_status = self.get(url)['job_status']
            if job_status == 'success':
                break
            time.sleep(1)

        # Download exported document
        params = urlencode({'job_id': job_id})
        url = ('https://p04-ubiquityws.icloud.com/iw/export/{}/'
               'download_exported_document?'.format(self.dsid) + params)
        return self.opener.open(Request(url, headers=HEADERS)).read()


class iCloudNode(object):

    def __init__(self, conn, **kwargs):
        self.__dict__.update(kwargs)
        self.conn = conn

    @property
    @memoize
    def children(self):
        return self.conn.get_children(self.item_id)

    @memoize
    def get_child_by_name(self, name):
        return [child for child in self.children if child.name == name][0]


    def download(self, file_type):
        return self.conn.download_file(self, file_type)
