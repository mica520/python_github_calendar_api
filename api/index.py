# -*- coding: UTF-8 -*-
import requests
import re
import os
from http.server import BaseHTTPRequestHandler
import json

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
        """根据请求的 Origin 判断是否允许跨域，返回允许的 Origin 或 None"""
        origin = self.headers.get('Origin')
        if not origin:
            return None
        allowed_origins_env = os.environ.get('CORS_ALLOWED_ORIGINS', '')
        if allowed_origins_env:
            allowed = [o.strip() for o in allowed_origins_env.split(',')]
            if origin in allowed:
                return origin
            else:
                return None
        else:
            # 未配置环境变量时，允许所有域名（等同于 *）
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
        # 解析 URL: 期望格式 /api/?username
        # 提取问号后面的部分作为用户名
        path = self.path
        user = None
        if '?' in path:
            # 取第一个 ? 之后的所有内容
            query = path.split('?', 1)[1]
            # 如果查询字符串不为空，且不以 & 开头（即没有其他参数），则整个 query 就是用户名
            # 如果包含 &，可能用户错误地传了多个参数，我们只取第一个 & 之前的部分作为用户名
            if query:
                user = query.split('&')[0]  # 去掉可能的额外参数
        if not user:
            self.send_response(400)
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing username in query string, expected /api/?username"}).encode('utf-8'))
            return

        data = getdata(user)

        self.send_response(200)
        self._set_cors_headers()
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))