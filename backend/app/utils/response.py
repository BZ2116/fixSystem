"""统一响应封装。所有路由统一返回 {code, message, data, request_id} 格式。"""
from flask import jsonify, g


def ok(data=None, message='ok', code=200):
    payload = {'code': code, 'message': message, 'data': data or {}}
    rid = getattr(g, 'request_id', None)
    if rid:
        payload['request_id'] = rid
    return jsonify(payload), 200


def fail(message='error', code=400, http_status=None):
    payload = {'code': code, 'message': message}
    rid = getattr(g, 'request_id', None)
    if rid:
        payload['request_id'] = rid
    return jsonify(payload), http_status or code


def page_ok(items, total, page, per_page, message='ok'):
    return ok({
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page if per_page else 0,
    }, message)
