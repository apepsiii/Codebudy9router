import urllib.request
import json

# Login
login_url = 'http://localhost:20128/api/auth/login'
password = 'PutihAbu123!'
body = json.dumps({'password': password}).encode('utf-8')
req = urllib.request.Request(login_url, data=body, headers={'Content-Type': 'application/json'}, method='POST')

resp = urllib.request.urlopen(req, timeout=10)
auth_token = None
for cookie in resp.headers.get_all('Set-Cookie'):
    if cookie.startswith('auth_token='):
        auth_token = cookie.split(';')[0].split('=', 1)[1]
        break

# Get providers
providers_url = 'http://localhost:20128/api/providers'
req2 = urllib.request.Request(providers_url, headers={'Cookie': f'auth_token={auth_token}'})
resp2 = urllib.request.urlopen(req2, timeout=10)
data = json.loads(resp2.read())

print('Kiro tokens di 9router:')
print('=' * 60)
count = 0
for conn in data['connections']:
    if conn['provider'] == 'kiro':
        count += 1
        status = conn.get('testStatus', 'unknown')
        email = conn.get('email') or '(no email)'
        print(f'{count}. {email} - Status: {status}')

print('=' * 60)
print(f'Total: {count} akun Kiro di 9router')
