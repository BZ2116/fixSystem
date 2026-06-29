"""统一分页参数解析与查询封装。"""
from flask import request


def get_page_params(default_per_page=20, max_per_page=200):
    """从 request.args 解析 page/per_page，带边界保护。"""
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = int(request.args.get('per_page', default_per_page))
        per_page = max(1, min(per_page, max_per_page))
    except (TypeError, ValueError):
        page, per_page = 1, default_per_page
    return page, per_page


def paginate_query(query, default_per_page=20, max_per_page=200):
    """对 SQLAlchemy query 执行分页，返回 (items, total, page, per_page)。"""
    page, per_page = get_page_params(default_per_page, max_per_page)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return pagination.items, pagination.total, page, per_page
