import json
import urllib.request
import urllib.error


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            body = r.read(200).decode(errors='ignore')
            print(f'GET {url} -> {r.status}')
            print(body)
    except Exception as e:
        print(f'GET {url} -> ERROR: {e}')


def post(url, data):
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode(errors='ignore')
            print(f'POST {url} -> {r.status}')
            print(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='ignore')
        print(f'POST {url} -> HTTPError {e.code}')
        print(body)
    except Exception as e:
        print(f'POST {url} -> ERROR: {e}')


if __name__ == '__main__':
    print('--- FRONTEND ROOT ---')
    get('http://127.0.0.1:3000/')
    print('--- BACKEND ROOT ---')
    get('http://127.0.0.1:8000/')
    print('--- BACKEND QUERY ---')
    post('http://127.0.0.1:8000/query', {'user_id':'student_001', 'question':'Hello backend', 'top_k':1})
