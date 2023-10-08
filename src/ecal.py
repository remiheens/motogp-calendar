# -*- coding: utf-8 -*-
"""
ECAL API Client
"""
from urllib.parse import urlencode
import urllib3
import hashlib
import requests
import json

class EcalClient:
    def __init__(self):
        self._api_domain = "https://api.ecal.com"
        self._params = {}
        self._json = ""
        self._apikey = ""
    
    def setJson(self, json_data):
        self._original_json = json.dumps(json_data, separators=(", ", ':'))
        self._json = "{ " + self._original_json[1:]
    
    def setApiKey(self, key):
        self._apikey = key

    def setApiSecret(self, secret):
        self._apiSecret = secret

    def setParams(self, params):
        self._params.update(params)

    def sortParams(self):
        self._params = dict(sorted(self._params.items()))

    def get(self, url):
        qs = self.getQuery()
        if len(qs) > 0:
            url += "?"+qs
        print(f"URL : {self._api_domain+url}")
        self._params = {}
        http = urllib3.PoolManager()
        resp = http.request("GET", self._api_domain+url)
        if resp.status >= 400:
            raise Exception(f"HTTP error {resp.status}: {resp.data.decode('utf-8')}")
        if len(resp.data) > 0:
            return resp.json()
        return {}

    def delete(self, url):
        qs = self.getQuery()
        if len(qs) > 0:
            url += "?"+qs
        print(f"URL : {self._api_domain+url}")
        self._params = {}
        http = urllib3.PoolManager()
        resp = http.request("DELETE", self._api_domain+url)
        if resp.status >= 400:
            raise Exception(f"HTTP error {resp.status}: {resp.data.decode('utf-8')}")
        return resp.json()

    def post(self, url):
        qs = self.getQuery()
        if len(qs) > 0:
            url += "?"+qs
        print(f"URL : {self._api_domain+url}")
        print(f"JSON : {self._json}")

        resp = urllib3.request(
            "POST",
            self._api_domain+url,
            headers={"Content-Type": "application/json", "Accept":"*/*", "User-Agent":"remiheens-ecal-client/0.0.0"},
            body=self._json
        )
        if resp.status >= 400:
            raise Exception(f"HTTP error {resp.status}: {resp.data} \n URL = {url} \n data = {self._json} \n params = {qs} \n headers = {resp.headers}")

        self._params = {}
        self._json = ""
        print(f"{resp.headers}")
        return resp.json()
            
    def put(self, url):
        qs = self.getQuery()
        if len(qs) > 0:
            url += "?"+qs
        print(f"URL : {self._api_domain+url}")
        print(f"JSON : {self._json}")

        resp = urllib3.request(
            "PUT",
            self._api_domain+url,
            headers={"Content-Type": "application/json", "Accept":"*/*", "User-Agent":"remiheens-ecal-client/0.0.0"},
            body=self._json
        )
        if resp.status >= 400:
            raise Exception(f"HTTP error {resp.status}: {resp.data} \n URL = {url} \n data = {self._json} \n params = {qs} \n headers = {resp.headers}")

        self._params = {}
        self._json = ""
        print(f"{resp.headers}")
        return resp.json()
            
    def getSign(self):
        self.sortParams()
        s = ""
        for k, v in self._params.items():
            s += k+""+str(v)

        text = self._apiSecret+""+s
        if len(self._json) > 0:
            text += self._json
            
        print(f">>> Text before encryption : {text}")
        md5 = hashlib.md5()
        md5.update(text.encode('utf-8'))
        md5_hash = md5.hexdigest()
        print(f">>> Hash md5 : {md5_hash}")
        return md5_hash
    
    def getQuery(self):
        self.setParams({"apiKey": self._apikey})
        return urlencode(self._params)+"&apiSign="+self.getSign()

