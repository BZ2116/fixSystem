"""
全局异常处理。统一返回 {code, message, request_id} 格式，禁止泄露堆栈/SQL。
"""
import logging
import traceback
from flask import jsonify, g
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify(_payload(400, '请求参数错误')), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify(_payload(401, '未登录或登录已过期')), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify(_payload(403, '无权限')), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(_payload(404, '资源不存在')), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify(_payload(405, '请求方法不允许')), 405

    @app.errorhandler(413)
    def too_large(e):
        return jsonify(_payload(413, '文件过大')), 413

    @app.errorhandler(HTTPException)
    def http_exception(e):
        return jsonify(_payload(e.code, e.description or '请求异常')), e.code

    @app.errorhandler(Exception)
    def internal_error(e):
        request_id = getattr(g, 'request_id', None)
        logger.error(
            'unhandled exception [request_id=%s]: %s\n%s',
            request_id, e, traceback.format_exc(),
        )
        return jsonify(_payload(500, '服务异常', request_id=request_id)), 500


def _payload(code: int, message: str, request_id: str = None):
    payload = {'code': code, 'message': message}
    if request_id is None:
        request_id = getattr(g, 'request_id', None)
    if request_id:
        payload['request_id'] = request_id
    return payload