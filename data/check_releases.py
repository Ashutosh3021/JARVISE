import urllib.request, json

url = 'https://api.github.com/repos/thewh1teagle/kokoro-onnx/releases'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=15)
releases = json.loads(resp.read())
for r in releases[:3]:
    tag = r['tag_name']
    print(f'Tag: {tag}')
    for a in r.get('assets', []):
        name = a['name']
        size = a['size']
        print(f'  {name} ({size} bytes)')
