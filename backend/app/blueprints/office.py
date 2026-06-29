"""办公室管理 CRUD。

迁移自 source-code/app.py 中 4457-4535 行附近的原始路由代码。
保持行为完全一致：按 sort_order + id 升序、code 唯一性校验、
删除前关联资产（Asset）检查等。
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from extensions import db
from models.system.office import Office

bp = Blueprint('office', __name__, url_prefix='/api/offices')


@bp.route('', methods=['GET'])
@jwt_required()
def list_offices():
    """获取办公室列表（按 sort_order asc, id asc 排序，无分页）。"""
    offices = Office.query.order_by(Office.sort_order.asc(), Office.id.asc()).all()
    return jsonify({
        'code': 200,
        'data': [o.to_dict() for o in offices]
    })


@bp.route('', methods=['POST'])
@jwt_required()
def create_office():
    """创建办公室。"""
    data = request.get_json()
    if not data.get('name'):
        return jsonify({'code': 400, 'message': '办公室名称不能为空'}), 400

    # 检查编码是否重复
    if data.get('code'):
        existing = Office.query.filter_by(code=data['code']).first()
        if existing:
            return jsonify({'code': 400, 'message': '办公室编码已存在'}), 400

    office = Office(
        name=data['name'],
        code=data.get('code', ''),
        sort_order=data.get('sort_order', 0),
        status=data.get('status', 1)
    )
    db.session.add(office)
    db.session.commit()
    return jsonify({'code': 200, 'message': '创建成功', 'data': office.to_dict()})


@bp.route('/<int:office_id>', methods=['PUT'])
@jwt_required()
def update_office(office_id):
    """更新办公室。"""
    office = Office.query.get(office_id)
    if not office:
        return jsonify({'code': 404, 'message': '办公室不存在'}), 404

    data = request.get_json()
    if 'name' in data:
        office.name = data['name']
    if 'code' in data:
        # 检查编码是否重复
        existing = Office.query.filter(Office.code == data['code'], Office.id != office_id).first()
        if existing:
            return jsonify({'code': 400, 'message': '办公室编码已存在'}), 400
        office.code = data['code']
    if 'sort_order' in data:
        office.sort_order = data['sort_order']
    if 'status' in data:
        office.status = data['status']

    db.session.commit()
    return jsonify({'code': 200, 'message': '更新成功', 'data': office.to_dict()})


@bp.route('/<int:office_id>', methods=['DELETE'])
@jwt_required()
def delete_office(office_id):
    """删除办公室（硬删除，前置检查关联资产）。"""
    office = Office.query.get(office_id)
    if not office:
        return jsonify({'code': 404, 'message': '办公室不存在'}), 404

    # 检查是否有关联资产
    from models.asset import Asset
    has_assets = Asset.query.filter_by(office_id=office_id).first()
    if has_assets:
        return jsonify({'code': 400, 'message': '该办公室有关联资产，无法删除'}), 400

    db.session.delete(office)
    db.session.commit()
    return jsonify({'code': 200, 'message': '删除成功'})
