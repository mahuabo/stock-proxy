from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            params = json.loads(body) if body else {}
            
            code = params.get('code', '')
            start_date = params.get('start_date', '')
            end_date = params.get('end_date', '')
            
            if not all([code, start_date, end_date]):
                self.send_error_response(400, '需要code, start_date, end_date')
                return
            
            data = self.fetch_eastmoney(code, start_date, end_date)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'data': data}, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_error_response(500, str(e))
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        info = {'service': 'Stock Proxy', 'status': 'running', 'usage': 'POST with code, start_date, end_date'}
        self.wfile.write(json.dumps(info).encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'success': False, 'error': message}).encode('utf-8'))
    
    def fetch_eastmoney(self, code, start_date, end_date):
        if code.startswith('6'):
            secid = f"1.{code}"
        else:
            secid = f"0.{code}"
        
        url = "http://push2his.eastmoney.com/api/qt/stock/kline/get?" + urllib.parse.urlencode({
            'secid': secid,
            'fields1': 'f1,f2,f3,f4,f5,f6',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
            'klt': '101', 'fqt': '1',
            'beg': start_date.replace('-', ''),
            'end': end_date.replace('-', ''),
            'lmt': '10000',
        })
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'http://quote.eastmoney.com/'
        })
        
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        data = []
        for line in result.get('data', {}).get('klines', []):
            parts = line.split(',')
            if len(parts) >= 9:
                data.append({
                    'date': parts[0], 'open': float(parts[1]), 'close': float(parts[2]),
                    'high': float(parts[3]), 'low': float(parts[4]), 'vol': float(parts[5]),
                    'amount': float(parts[6]), 'pct_chg': float(parts[8])
                })
        return data
