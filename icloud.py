import json
import urllib.request


class iCloud(object):

    def __init__(self):
        cookie_processor = urllib.request.HTTPCookieProcessor()
        self.opener = urllib.request.build_opener(cookie_processor)
        self.cookiejar = cookie_processor.cookiejar

    def login(self, username, password):
        URL = 'https://setup.icloud.com/setup/ws/1/login'
        HEADERS = {
            'origin': 'https://www.icloud.com',
            'content-type': 'text/plain',
            }
        params = {
            'apple_id': username,
            'password': password,
            'extended_login': True,
            }
        data = bytes(json.dumps(params), 'utf-8')
        req = urllib.request.Request(URL, data, HEADERS)
        self.opener.open(req)
        auth_cookie = [cookie for cookie in self.cookiejar
                       if cookie.name == 'X-APPLE-WEBAUTH-TOKEN'][0]
        auth_cookie_dict = dict(item.split('=' for item
                                           in auth_cookie.value.split(':')))
        self.dsid = auth_cookie_dict['d']
