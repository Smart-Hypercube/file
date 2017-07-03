from os import listdir
from hashlib import sha1 as hash_method

from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

data_dir = 'data'
hash_len = hash_method().digest_size * 2


def index(request):
    return redirect('/0000000000000000000000000000000000000000?type=text/html', permanent=True)


@csrf_exempt
def upload(request):
    f = request.FILES['file']
    obj = hash_method()
    for chunk in f.chunks():
        obj.update(chunk)
    hash_value = obj.hexdigest()
    with open(data_dir + '/' + hash_value, 'wb') as dest:
        for chunk in f.chunks():
            dest.write(chunk)
    with open('log.txt', 'a') as logfile:
        logfile.write(hash_value + '/' + f.name + '\0\n')
    try:
        with open('/data/mail/file-' + hash_value, 'w', newline='\r\n') as mail:
            mail.write('http://file.0x01.me/' + hash_value + '/' + f.name)
    except:
        pass
    return render(request, 'upload.html', {'hash_value': hash_value, 'name': f.name})


def download(request, hash_value: str):
    if len(hash_value) == hash_len:
        path = request.get_full_path()
        sep = path.find('/', 1)
        path = path[:sep].lower() + path[sep:]
        return redirect(path, permanent=True)
    if len(hash_value) < 10:
        path = request.get_full_path()
        sep = path.find('/', 1)
        path = path[sep:]
        return render(request, 'too_short.html', {'hash_value': hash_value, 'path': path}, status=300)
    l = list(filter(lambda s: s.startswith(hash_value), listdir(data_dir)))
    if len(l) == 1:
        path = request.get_full_path()
        sep = path.find('/', 1)
        path = '/' + l[0] + path[sep:]
        return redirect(path, permanent=False)
    path = request.get_full_path()
    sep = path.find('/', 1)
    path = path[sep:]
    return render(request, 'too_short.html', {'hash_value': hash_value, 'path': path}, 'text/html', 300)
