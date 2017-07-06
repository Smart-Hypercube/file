import os
import time
from hashlib import sha1 as hash_method
from urllib.parse import urlencode

from django.shortcuts import render, Http404, redirect as _redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .mime import MIME

DATA_DIR = '/data/file'
HASH_LEN = hash_method().digest_size * 2


def ishex(s):
    return all(map('0123456789abcdef'.__contains__, s))


def path_process(path) -> str:
    result = []
    for part in filter(None, path.split('/')):
        if part == '..':
            if result:
                result.pop()
        elif part != '.':
            result.append(part)
    return '/'.join(result)


def mkdir_p(path):
    if not os.path.exists(path):
        mkdir_p(os.path.split(path)[0])
        os.mkdir(path)


def put_data(file):
    hash_obj = hash_method()
    list(map(hash_obj.update, file.chunks()))
    hash_value = hash_obj.hexdigest()
    path = os.path.join(DATA_DIR, hash_value[:2], hash_value[2:])
    if not os.path.exists(path):
        mkdir_p(os.path.split(path)[0])
        with open(path, 'wb') as f:
            list(map(f.write, file.chunks()))
    return hash_value


def redirect(url, mime, permanent=False):
    query = {}
    if mime:
        query['type'] = mime
    query = '?' + urlencode(query) if query else ''
    return _redirect(url + query, permanent=permanent)


@require_http_methods(['HEAD', 'GET', 'POST'])
@csrf_exempt
def mainview(request):
    path = path_process(request.path)
    alias = path.replace('/', '\\')
    if alias:
        p = os.path.join(DATA_DIR, 'alias', alias)
        if os.path.exists(p):
            if time.time() - os.path.getmtime(p) > 86400:
                os.remove(p)
    if request.method == 'POST':
        file = request.FILES['file']
        hash_value = put_data(file)
        if alias and len(alias) < HASH_LEN:
            p = os.path.join(DATA_DIR, 'alias', alias)
            alias_r = not os.path.exists(p)
            if alias_r:
                mkdir_p(os.path.split(p)[0])
                with open(p, 'w') as f:
                    f.write(hash_value)
        else:
            alias_r = False
        result = dict(
            hash_value=hash_value,
            name=file.name,
            ext=os.path.splitext(file.name)[1],
            mime=MIME.get(file.name.split('.')[-1].lower(), ''),
            alias=alias,
            alias_r=alias_r)
        return render(request, 'upload.html', result)
    else:
        mime = request.GET.get('type', None)

        if len(path) >= HASH_LEN:
            hash_value, mid, tail = path.partition('/')
            if len(hash_value) == HASH_LEN:
                return redirect('/' + hash_value.lower() + mid + tail, mime, True)
            if len(hash_value) > HASH_LEN:
                raise Http404

        elif alias:
            p = os.path.join(DATA_DIR, 'alias', alias)
            if os.path.exists(p):
                with open(p) as f:
                    hash_value = f.read()
                return redirect('/' + hash_value, mime)

        hash_pre, mid, tail = path.partition('/')
        if len(hash_pre) >= 10:
            p = os.path.join(DATA_DIR, hash_pre[:2].lower())
            if os.path.exists(p):
                l = list(filter(lambda s: s.startswith(hash_pre[2:].lower()),
                                os.listdir(p)))
                if len(l) == 1:
                    return redirect('/' + hash_pre[:2].lower() + l[0] + mid + tail, mime)

        return render(request, 'index.html', {'alias': alias})
