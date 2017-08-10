import os
from hashlib import sha1 as hash_method

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .mime import MIME

DATA_DIR = '/data/file'
HASH_LEN = hash_method().digest_size * 2


def mkdir_p(path):
    if not os.path.exists(path):
        mkdir_p(os.path.split(path)[0])
        os.mkdir(path)


def put_data(file):
    hash_obj = hash_method()
    list(map(hash_obj.update, file.chunks()))
    hash_value = hash_obj.hexdigest()
    prefix = hash_value[:2]
    postfix = hash_value[2:]
    d = os.path.join(DATA_DIR, prefix)
    path = os.path.join(d, postfix)
    if not os.path.exists(path):
        mkdir_p(d)
        with open(path, 'wb') as f:
            list(map(f.write, file.chunks()))
        for short in [hash_value[2:i] for i in range(10, HASH_LEN)]:
            path = os.path.join(d, short)
            if os.path.exists(path):
                os.remove(path)
            else:
                os.symlink(postfix, path)
    return hash_value


@require_http_methods(['GET', 'HEAD', 'POST'])
@csrf_exempt
def mainview(request):
    if request.method == 'POST':
        file = request.FILES['file']
        hash_value = put_data(file)
        result = dict(
            hash_value=hash_value,
            name=file.name,
            mime=MIME.get(file.name.split('.')[-1].lower(), ''))
        return render(request, 'upload.html', result)
    else:
        return render(request, 'index.html')
