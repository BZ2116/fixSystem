"""商品分类管理 CRUD。

迁移自 source-code/app.py 中 1094-1195 行附近的原始路由代码。
保持行为完全一致：树形结构（递归构建）、父分类校验（不能自引用）、
删除前检查子分类与商品归属。
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from extensions import db

bp = Blueprint('product_category', __name__, url_prefix='/api/product/categories')


def build_category_tree(categories, parent_id=0):
    """构建分类树形结构。"""
    tree = []
    for cat in categories:
        if cat.parent_id == parent_id:
            node = {
                'id': cat.id,
                'category_name': cat.category_name,
                'parent_id': cat.parent_id,
                'sort_order': cat.sort_order,
                'status': cat.status,
                'created_at': cat.created_at.strftime('%Y-%m-%d %H:%M:%S') if cat.created_at else None,
                'children': build_category_tree(categories, cat.id),
            }
            tree.append(node)
    return tree


@bp.route('', methods=['GET'])
@jwt_required()
def list_categories():
    """获取分类列表（树形结构）。"""
    from models.product.info import ProductCategory

    status = request.args.get('status', type=int)

    query = ProductCategory.query

    if status is not None:
        query = query.filter_by(status=status)

    categories = query.order_by(
        ProductCategory.sort_order.asc(),
        ProductCategory.created_at.desc(),
    ).all()

    tree = build_category_tree(categories)

    return {'code': 200, 'data': tree}, 200


@bp.route('', methods=['POST'])
@jwt_required()
def create_category():
    """创建分类。"""
    from models.product.info import ProductCategory

    data = request.get_json()

    if not data.get('category_name'):
        return {'code': 400, 'message': '分类名称不能为空'}, 400

    category = ProductCategory(
        category_name=data.get('category_name'),
        parent_id=data.get('parent_id', 0),
        sort_order=data.get('sort_order', 0),
        status=data.get('status', 1),
    )

    db.session.add(category)
    db.session.commit()

    return {'code': 200, 'message': '创建成功', 'data': {'id': category.id}}, 200


@bp.route('/<int:cid>', methods=['PUT'])
@jwt_required()
def update_category(cid):
    """更新分类。"""
    from models.product.info import ProductCategory

    category = ProductCategory.query.get(cid)
    if not category:
        return {'code': 404, 'message': '分类不存在'}, 404

    data = request.get_json()

    if 'category_name' in data:
        category.category_name = data['category_name']
    if 'parent_id' in data:
        # 防止循环引用
        if data['parent_id'] == cid:
            return {'code': 400, 'message': '不能将自己设为上级分类'}, 400
        category.parent_id = data['parent_id']
    if 'sort_order' in data:
        category.sort_order = data['sort_order']
    if 'status' in data:
        category.status = data['status']

    db.session.commit()
    return {'code': 200, 'message': '更新成功'}, 200


@bp.route('/<int:cid>', methods=['DELETE'])
@jwt_required()
def delete_category(cid):
    """删除分类（拒绝有子分类或商品归属的）。"""
    from models.product.info import ProductCategory, ProductInfo

    category = ProductCategory.query.get(cid)
    if not category:
        return {'code': 404, 'message': '分类不存在'}, 404

    # 检查是否有子分类
    child_count = ProductCategory.query.filter_by(parent_id=cid).count()
    if child_count > 0:
        return {'code': 400, 'message': '该分类下有子分类，无法删除'}, 400

    # 检查是否有关联的商品
    product_count = ProductInfo.query.filter_by(category_id=cid).count()
    if product_count > 0:
        return {'code': 400, 'message': '该分类下有商品，无法删除'}, 400

    db.session.delete(category)
    db.session.commit()
    return {'code': 200, 'message': '删除成功'}, 200
