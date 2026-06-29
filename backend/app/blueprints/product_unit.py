"""商品单位管理 CRUD。

迁移自 source-code/app.py 中 932-1090 行附近的原始路由代码。
保持行为完全一致：单位名称/编码查重、unit_code 为空时回退到 unit_name、
重复时追加数字后缀、删除前检查 ProductUnitRel 关联。
"""
import re

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from extensions import db

bp = Blueprint('product_unit', __name__, url_prefix='/api/product/units')


def _next_unique_code(base_code: str) -> str:
    """当 unit_code 冲突时，剥离末尾数字并追加递增后缀。"""
    from models.product.info import ProductUnit

    base = re.sub(r'\d+$', '', base_code)
    counter = 1
    new_code = f'{base}{counter}'
    while ProductUnit.query.filter_by(unit_code=new_code).first():
        counter += 1
        new_code = f'{base}{counter}'
    return new_code


@bp.route('', methods=['GET'])
@jwt_required()
def list_units():
    """获取单位列表。"""
    from models.product.info import ProductUnit

    keyword = request.args.get('keyword', '')
    status = request.args.get('status', type=int)

    query = ProductUnit.query

    if keyword:
        query = query.filter(ProductUnit.unit_name.contains(keyword))

    if status is not None:
        query = query.filter_by(status=status)

    units = query.order_by(
        ProductUnit.sort_order.asc(),
        ProductUnit.created_at.desc(),
    ).all()

    return {
        'code': 200,
        'data': [{
            'id': u.id,
            'unit_name': u.unit_name,
            'unit_code': u.unit_code,
            'conversion_rate': float(u.conversion_rate) if u.conversion_rate else 1.0000,
            'is_base': u.is_base,
            'sort_order': u.sort_order,
            'status': u.status,
            'created_at': u.created_at.strftime('%Y-%m-%d %H:%M:%S') if u.created_at else None,
        } for u in units],
    }, 200


@bp.route('', methods=['POST'])
@jwt_required()
def create_unit():
    """创建单位。"""
    from models.product.info import ProductUnit

    data = request.get_json()

    if not data.get('unit_name'):
        return {'code': 400, 'message': '单位名称不能为空'}, 400

    # 检查单位名称是否已存在
    existing = ProductUnit.query.filter_by(unit_name=data.get('unit_name')).first()
    if existing:
        return {'code': 400, 'message': '单位名称已存在'}, 400

    # 处理 unit_code，如果为空则使用 unit_name
    unit_code = data.get('unit_code')
    if not unit_code or str(unit_code).strip() == '':
        unit_code = data.get('unit_name')

    # 检查 unit_code 是否已存在（如果有值）
    if unit_code:
        existing_code = ProductUnit.query.filter_by(unit_code=unit_code).first()
        if existing_code:
            unit_code = _next_unique_code(unit_code)

    unit = ProductUnit(
        unit_name=data.get('unit_name'),
        unit_code=unit_code,
        conversion_rate=data.get('conversion_rate', 1.0000),
        is_base=data.get('is_base', 0),
        sort_order=data.get('sort_order', 0),
        status=data.get('status', 1),
    )

    db.session.add(unit)
    db.session.commit()

    return {'code': 200, 'message': '创建成功', 'data': {'id': unit.id}}, 200


@bp.route('/<int:uid>', methods=['PUT'])
@jwt_required()
def update_unit(uid):
    """更新单位。"""
    from models.product.info import ProductUnit

    unit = ProductUnit.query.get(uid)
    if not unit:
        return {'code': 404, 'message': '单位不存在'}, 404

    data = request.get_json()

    # 检查单位名称是否与其他单位重复
    if 'unit_name' in data and data['unit_name'] != unit.unit_name:
        existing = ProductUnit.query.filter_by(unit_name=data['unit_name']).first()
        if existing:
            return {'code': 400, 'message': '单位名称已存在'}, 400
        unit.unit_name = data['unit_name']

    if 'unit_code' in data:
        unit_code = data['unit_code']
        if not unit_code or str(unit_code).strip() == '':
            unit_code = unit.unit_name
        # 检查是否与其他单位重复
        if unit_code != unit.unit_code:
            existing_code = ProductUnit.query.filter_by(unit_code=unit_code).first()
            if existing_code:
                unit_code = _next_unique_code(unit_code)
        unit.unit_code = unit_code
    if 'conversion_rate' in data:
        unit.conversion_rate = data['conversion_rate']
    if 'is_base' in data:
        unit.is_base = data['is_base']
    if 'sort_order' in data:
        unit.sort_order = data['sort_order']
    if 'status' in data:
        unit.status = data['status']

    db.session.commit()
    return {'code': 200, 'message': '更新成功'}, 200


@bp.route('/<int:uid>', methods=['DELETE'])
@jwt_required()
def delete_unit(uid):
    """删除单位（拒绝被商品使用的）。"""
    from models.product.info import ProductUnit, ProductUnitRel

    unit = ProductUnit.query.get(uid)
    if not unit:
        return {'code': 404, 'message': '单位不存在'}, 404

    # 检查是否有关联的商品
    rel_count = ProductUnitRel.query.filter_by(unit_id=uid).count()
    if rel_count > 0:
        return {'code': 400, 'message': '该单位已被商品使用，无法删除'}, 400

    db.session.delete(unit)
    db.session.commit()
    return {'code': 200, 'message': '删除成功'}, 200
