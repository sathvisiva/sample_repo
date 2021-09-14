import json
import kiteconnect.exceptions as ex
import logging
from six.moves.urllib.parse import urljoin
import requests
import pandas as pd
from os import path

from kiteconnect import KiteConnect, KiteTicker

log = logging.getLogger(__name__)


class KiteExt(KiteConnect):

    def login_with_credentials(self, userid, password, twofa):
        self.headers = {
            "x-kite-version": "3"
        }
        self.reqsession = requests.Session()
        r = self.reqsession.post(self.root + self._routes['api.login'], data={
            "user_id": userid,
            "password": password
        })

        r = self.reqsession.post(self.root + self._routes['api.twofa'], data={
            "request_id": r.json()['data']['request_id'],
            "twofa_value": twofa,
            "user_id": r.json()['data']['user_id']
        })

        self.headers = {
            "x-kite-version": "3"
        }

        enctoken = r.cookies.get('enctoken')
        with open('./config/enctoken.txt', 'w') as wr:
            wr.write(enctoken)

        self.public_token = r.cookies.get('public_token')
        self.user_id = r.cookies.get('user_id')

        self.headers['Authorization'] = 'enctoken {}'.format(enctoken)

    def __init__(self, *args, **kw):
        KiteConnect.__init__(self, api_key='kitefront', *args, **kw)

        self._routes.update({
            "api.login": "/api/login",
            "api.twofa": "/api/twofa",
            'api.misdata': "/margins/equity"
        })

    def set_headers(self, enctoken):
        self.public_token = enctoken
        self.user_id = 'AB1234'
        self.headers = {
            "x-kite-version": "3",
            'Authorization': 'enctoken {}'.format(enctoken)
        }

    def kws(self):
        return KiteTicker(api_key='kitefront', access_token=self.public_token+"&user_id="+self.user_id, root='wss://ws.zerodha.com')

    def get_misdata(self, symbol=None):
        df = pd.DataFrame()
        if path.exists("misdata.csv"):
            df = pd.read_csv("misdata.csv", index_col=0)
        else:
            r = self.reqsession.get(
                self._default_root_uri + self._routes['api.misdata'])
            df = pd.DataFrame(r.json(), index=None)
            df.to_csv("misdata.csv")
        if symbol is not None:
            return df.loc[df.tradingsymbol == symbol].head(1)
        return df

## NOTE NEW
    def _request(self, route, method, url_args=None, params=None, is_json=False):
        """Make an HTTP request."""
        # Form a restful URL
        if url_args:
            uri = self._routes[route].format(**url_args)
        else:
            uri = self._routes[route]

        url = urljoin(self.root, uri)

        headers = self.headers

        # Custom headers
        # headers = {
        #     "X-Kite-Version": "3",  # For version 3
        #     "User-Agent": self._user_agent()
        # }

        # if self.api_key and self.access_token:
        #     # set authorization header
        #     auth_header = self.api_key + ":" + self.access_token
        #     headers["Authorization"] = "token {}".format(auth_header)

        if self.debug:
            log.debug("Request: {method} {url} {params} {headers}".format(method=method, url=url, params=params, headers=headers))

        try:
            r = self.reqsession.request(method,
                                        url,
                                        json=params if (method in ["POST", "PUT"] and is_json) else None,
                                        data=params if (method in ["POST", "PUT"] and not is_json) else None,
                                        params=params if method in ["GET", "DELETE"] else None,
                                        headers=headers,
                                        verify=not self.disable_ssl,
                                        allow_redirects=True,
                                        timeout=self.timeout,
                                        proxies=self.proxies)
        # Any requests lib related exceptions are raised here - http://docs.python-requests.org/en/master/_modules/requests/exceptions/
        except Exception as e:
            raise e

        if self.debug:
            log.debug("Response: {code} {content}".format(code=r.status_code, content=r.content))

        # Validate the content type.
        if "json" in r.headers["content-type"]:
            try:
                data = json.loads(r.content.decode("utf8"))
            except ValueError:
                raise ex.DataException("Couldn't parse the JSON response received from the server: {content}".format(
                    content=r.content))

            # api error
            if data.get("error_type"):
                # Call session hook if its registered and TokenException is raised
                if self.session_expiry_hook and r.status_code == 403 and data["error_type"] == "TokenException":
                    self.session_expiry_hook()

                # native Kite errors
                exp = getattr(ex, data["error_type"], ex.GeneralException)
                raise exp(data["message"], code=r.status_code)

            return data["data"]
        elif "csv" in r.headers["content-type"]:
            return r.content
        else:
            raise ex.DataException("Unknown Content-Type ({content_type}) with response: ({content})".format(
                content_type=r.headers["content-type"],
                content=r.content))



