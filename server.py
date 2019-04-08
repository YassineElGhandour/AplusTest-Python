#!/usr/bin/env python3
from aiohttp import web
from base64 import b64decode, b64encode
from hashlib import pbkdf2_hmac, sha256
from hmac import compare_digest
from os import urandom
from os.path import isfile
import jwt


def crypt(word, salt=None):
    """
    A minimal replacement for crypt.crypt [1], which is not available on Windows.
    For compatible implementation for windows, check passlib module [2].
    For a Python implementation of the hash function used by crypt, check passlib source [3].

    [1]: https://docs.python.org/3.7/library/crypt.html
    [2]: https://pypi.org/project/passlib/
    [3]: https://bitbucket.org/ecollins/passlib/src/849ab1e6b5d4ace4c727a63d4adec928d6d72c13/passlib/handlers/sha2_crypt.py#sha2_crypt.py-56
    """
    assert isinstance(word, str)
    assert salt is None or isinstance(salt, str)
    if not salt:
        algo_s = b'6'
        salt = urandom(12)
    else:
        _, algo_s, salt, _ = salt.encode('ascii').split(b'$', 3)
        salt = b64decode(salt)
    algo = {b'5': 'sha256', b'6': 'sha512'}[algo_s]
    hashed = pbkdf2_hmac(algo, word.encode('utf-8'), salt, 5000)
    return b'$'.join((b'', algo_s, b64encode(salt), b64encode(hashed))).decode('ascii')


USERS = {
    'admin': crypt('banana-monkey'),
}
STUDENTS = {
    '1234': ('Mikko', 80, 4.2),
    '5432': ('Matti', 120, 3.5),
    '8576': ('Jack', 125, 2.9),
}
SECRET = urandom(32)


routes = web.RouteTableDef()


@routes.get('/')
async def index(request):
    return web.FileResponse('./index.html')


@routes.post('/login')
async def login(request):
    data = await request.post()
    user = data.get('user')
    passwd = data.get('password')
    crypted = USERS.get(user)
    if (not crypted or not passwd or
        not compare_digest(crypt(passwd, crypted), crypted)):
        return web.HTTPUnauthorized()
    message = {
        'name': user,
        'students': list(STUDENTS.keys()),
    }
    token = jwt.encode(message, SECRET, 'HS256')
    return web.json_response({
        'token': token.decode('ascii'),
        'token_type': 'Bearer',
    })


@routes.get('/students')
@routes.get('/students/{sid}')
async def students(request):
    if 'Authorization' not in request.headers:
        return web.HTTPUnauthorized(reason="No authorization header")
    try:
        scheme, token = request.headers['Authorization'].strip().split(' ', 1)
        if scheme.lower() != 'bearer': raise ValueError()
    except ValueError:
        return web.HTTPForbidden(reason="Invalid authorization header")
    try:
        decoded = jwt.decode(token, SECRET, algorithms=['HS256'])
    except jwt.InvalidTokenError as exc:
        return web.HTTPForbidden(reason=str(exc))

    sid = request.match_info.get('sid')
    if sid is None:
        return web.json_response(list(STUDENTS.keys()))
    elif sid in STUDENTS:
        n, c, g = STUDENTS[sid]
        return web.json_response({'sid': sid, 'name': n, 'credits': c, 'gpa': g})
    return web.HTTPNotFound()


@routes.get('/freestudents')
@routes.get('/freestudents/{sid}')
async def freestudents(request):
    sid = request.match_info.get('sid')
    if sid is None:
        # return web.json_response(list(STUDENTS.keys()))
        return web.json_response(STUDENTS)
    elif sid in STUDENTS:
        n, c, g = STUDENTS[sid]
        return web.json_response({'sid': sid, 'name': n, 'credits': c, 'gpa': g})
    return web.HTTPNotFound()


@routes.get('/{filename}')
async def static(request):
    filename = request.match_info['filename']
    if not isfile(filename):
        return web.HTTPNotFound()
    return web.FileResponse(filename)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    app = web.Application()
    app.router.add_routes(routes)
    web.run_app(app, host='127.0.0.1', port=8888)
