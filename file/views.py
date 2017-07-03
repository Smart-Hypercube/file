from os import listdir
from hashlib import sha1 as hash_method

from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

data_dir = '/data/file'
hash_len = hash_method().digest_size * 2

guess_table = {
    'atom':     'application/atom+xml',
    'js':       'application/javascript',
    'json':     'application/json',
    'pdf':      'application/pdf',
    'xhtml':    'application/xhtml+xml',
    'xht':      'application/xhtml+xml',
    'torrent':  'application/x-bittorrent',
    'm3u8':     'application/x-mpegURL',
    'rss':      'application/x-rss+xml',
    'flac':     'audio/flac',
    'mid':      'audio/midi',
    'midi':     'audio/midi',
    'mpga':     'audio/mpeg',
    'mp2':      'audio/mpeg',
    'mp3':      'audio/mpeg',
    'm4a':      'audio/mpeg',
    'm3u':      'audio/mpegurl',
    'ogg':      'audio/ogg',
    'oga':      'audio/ogg',
    'wma':      'audio/x-ms-wma',
    'rm':       'audio/x-pn-realaudio',
    'wav':      'audio/x-wav',
    'gif':      'image/gif',
    'jpeg':     'image/jpeg',
    'jpg':      'image/jpeg',
    'png':      'image/png',
    'svg':      'image/svg+xml',
    'tiff':     'image/tiff',
    'tif':      'image/tiff',
    'ico':      'image/vnd.microsoft.icon',
    'bmp':      'image/x-ms-bmp',
    'psd':      'image/x-photoshop',
    'eml':      'message/rfc822',
    'css':      'text/css',
    'csv':      'text/csv',
    'html':     'text/html',
    'htm':      'text/html',
    'shtml':    'text/html',
    'rtx':      'text/richtext',
    'vcf':      'text/vcard',
    'vcard':    'text/vcard',
    'wml':      'text/vnd.wap.wml',
    'wmls':     'text/vnd.wap.wmlscript',
    'vcs':      'text/x-vcalendar',
    '3gp':      'video/3gpp',
    'mpeg':     'video/mpeg',
    'mpg':      'video/mpeg',
    'mpe':      'video/mpeg',
    'mp4':      'video/mp4',
    'qt':       'video/quicktime',
    'mov':      'video/quicktime',
    'ogv':      'video/ogg',
    'webm':     'video/webm',
    'flv':      'video/x-flv',
    'wmv':      'video/x-ms-wmv',
    'avi':      'video/x-msvideo',
    'mpv':      'video/x-matriska',
    'mkv':      'video/x-matriska',
}

@require_http_methods(["HEAD", "GET", "POST"])
@csrf_exempt
def mainview(request):
    if request.method == 'POST':
        f = request.FILES['file']
        obj = hash_method()
        for chunk in f.chunks():
            obj.update(chunk)
        hash_value = obj.hexdigest()
        with open(data_dir + '/' + hash_value, 'wb') as dest:
            for chunk in f.chunks():
                dest.write(chunk)
        if request.path != '/':
            if not os.fork():
                os.execlp('mkdir', 'mkdir', '-p', data_dir + request.path)
                exit()
            os.wait()
            with open(data_dir + request.path, 'a') as namespace:
                namespace.write('<li><a href="/%s/%s">%s/%s</a></li>\n' %
                        (hash_value, f.name, hash_value, f.name))
        postfix = f.name.split('.')[-1].lower()
        guess_type = guess_table.get_default(postfix, '')
        return render(request, 'upload.html',
                {'hash_value': hash_value, 'name': f.name, 'type': guess_type})
    else:
        path = request.get_full_path()[1:]
        if len(path) > hash_len and path[hash_len] in './?#':
            sep = path.find('/')
            return redirect('/' + path[:sep].lower() + path[sep:], permanent=True)
        if os.path.exists(data_dir + request.path):
            if len(request.path) == hash_len + 1:
                sep = path.find('/')
                return redirect('/' + path[:sep].lower() + path[sep:], permanent=True)
            return render(request, 'index.html', {namespace: request.path})
        if len(hash_value) < 10:
            return render(request, 'index.html', {namespace: request.path})
        l = list(filter(lambda s: s.startswith(hash_value) and len(s) == hash_len,
                listdir(data_dir)))
        if len(l) == 1:
            sep = path.find('/')
            return redirect('/' + l[0] + path[sep:], permanent=False)
        return render(request, 'index.html', {namespace: request.path})
