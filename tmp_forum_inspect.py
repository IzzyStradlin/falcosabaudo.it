import urllib.request, ssl, re

ctx = ssl.create_default_context()
url = 'https://falcosabaudo.forumfree.it/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
    html = r.read(200000).decode('utf-8', 'replace')

patterns = [r'href=["\']([^"\']*\?t=[^"\']*)["\']', r'href=["\']([^"\']*\?f=[^"\']*)["\']', r'href=["\']([^"\']*thread[^"\']*)["\']', r'href=["\']([^"\']*topic[^"\']*)["\']']
for p in patterns:
    print('PATTERN', p)
    matches = re.findall(p, html, flags=re.I)
    print('count', len(matches))
    print('\n'.join(matches[:20]))
    print('---')
