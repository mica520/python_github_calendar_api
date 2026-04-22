# -*- coding: UTF-8 -*-
import requests
import re
import os
from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, unquote

def list_split(items, n):
    return [items[i:i + n] for i in range(0, len(items), n)]

def getdata(name):
    headers = {
        'Referer': 'https://github.com/' + name,
        'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Microsoft Edge";v="122"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
        'X-Requested-With': 'XMLHttpRequest'
    }
    gitpage = requests.get("https://github.com/" + name + "?action=show&controller=profiles&tab=contributions&user_id=" + name, headers=headers)
    data = gitpage.text

    datadatereg = re.compile(r'data-date="(.*?)" id="contribution-day-component')
    datacountreg = re.compile(r'<tool-tip .*?class="sr-only position-absolute">(.*?) contribution')

    datadate = datadatereg.findall(data)
    datacount = datacountreg.findall(data)
    datacount = list(map(int, [0 if i == "No" else i for i in datacount]))

    if not datadate or not datacount:
        return {"total": 0, "contributions": []}

    sorted_data = sorted(zip(datadate, datacount))
    datadate, datacount = zip(*sorted_data)

    contributions = sum(datacount)
    datalist = []
    for index, item in enumerate(datadate):
        itemlist = {"date": item, "count": datacount[index]}
        datalist.append(itemlist)
    datalistsplit = list_split(datalist, 7)
    returndata = {
        "total": contributions,
        "contributions": datalistsplit
    }
    return returndata

class handler(BaseHTTPRequestHandler):
    def _get_allowed_origin(self):
        origin = self.headers.get('Origin')
        if not origin:
            return None
        allowed_origins_env = os.environ.get('CORS_ALLOWED_ORIGINS', '')
        if allowed_origins_env:
            allowed = [o.strip() for o in allowed_origins_env.split(',')]
            if origin in allowed:
                return origin
            return None
        return '*'

    def _set_cors_headers(self):
        allowed_origin = self._get_allowed_origin()
        if allowed_origin:
            self.send_header('Access-Control-Allow-Origin', allowed_origin)
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        # 解析用户名
        user = None
        parsed = urlparse(self.path)
        raw_query = parsed.query  # 例如 "octocat" 或 "user=xxx"
        
        # 方式1：查询字符串直接是用户名（无等号，且非空）
        if raw_query and '=' not in raw_query:
            user = unquote(raw_query)  # 解码 URL 编码
        
        # 方式2：显式参数 ?user=xxx （向后兼容）
        if not user and raw_query:
            # 手动解析简单 key=value，避免 parse_qs 的空键问题
            if '=' in raw_query:
                parts = raw_query.split('=', 1)
                if parts[0] == 'user' and parts[1]:
                    user = unquote(parts[1])
        
        # 方式3：路径参数 /api/username
        if not user:
            path = parsed.path.rstrip('/')
            parts = [p for p in path.split('/') if p]
            if parts and parts[-1] != 'api':
                user = unquote(parts[-1])
        
        if not user:
            self.send_response(400)
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing username in query or path"}).encode('utf-8'))
            return
        
        # 获取数据
        data = getdata(user)
        
        self.send_response(200)
        self._set_cors_headers()
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))