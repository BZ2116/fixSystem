"""预订单管理蓝图（CRUD + 转销售单）。

迁移自 source-code/app.py 中 12302-12525 行附近的原始路由代码。

业务规则：
- 预订单是销售前的"意向单"，可转为正式销售单
- convert 操作：创建 SalesOrder 关联，预订单状态切换
- 业务字段：客户/产品/数量/期望交付日期/价格快照

跨子域依赖：
- PreOrder / PreOrderItem (models.sales.preorder 或 models.purchase.preorder)
- SalesOrder (models.sales.order) — convert 时
- BaseCustomer (models.customer)
- ProductInfo (models.product.info)
- SysUser (models.system)

直接 import 当前蓝图用得到的本地 helper，其他跨子域模型按"函数内懒加载"惯例。
"""
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from extensions import db
from app.utils import to_dict, generate_code
from app.security import permission, get_current_user_id

bp = Blueprint('preorder', __name__)
logger = logging.getLogger(__name__)


@bp.route('/api/pre-orders', methods=['GET'])
@jwt_required()
@permission('preorder:view')
def get_preorders():
    """获取预订单列表"""
    from models.inventory.flow import PreOrder
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    keyword = request.args.get('keyword', '')
    pre_type = request.args.get('pre_type', type=int)
    status = request.args.get('status', type=int)

    query = PreOrder.query
    if keyword:
        query = query.filter(db.or_(
            PreOrder.pre_no.contains(keyword),
            PreOrder.customer_name.contains(keyword),
            PreOrder.supplier_name.contains(keyword)
        ))
    if pre_type is not None:
        query = query.filter(PreOrder.pre_type == pre_type)
    if status is not None:
        query = query.filter(PreOrder.status == status)

    total = query.count()
    orders = query.order_by(PreOrder.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        'code': 200,
        'data': {
            'list': [to_dict(o) for o in orders],
            'total': total
        }
    })

@bp.route('/api/pre-orders/<int:id>', methods=['GET'])
@jwt_required()
@permission('preorder:view')
def get_preorder(id):
    """获取预订单详情"""
    from models.inventory.flow import PreOrder, PreOrderItem
    order = PreOrder.query.get_or_404(id)
    items = PreOrderItem.query.filter_by(pre_id=id).all()
    order_dict = to_dict(order)
    order_dict['items'] = [to_dict(i) for i in items]
    return jsonify({'code': 200, 'data': order_dict})

@bp.route('/api/pre-orders', methods=['POST'])
@jwt_required()
@permission('preorder:add')
def create_preorder():
    """创建预订单"""
    from models.inventory.flow import PreOrder, PreOrderItem
    data = request.get_json()
    user_id = get_current_user_id()

    last = PreOrder.query.order_by(PreOrder.id.desc()).first()
    pre_no = generate_code('PRE', last.id if last else 0)

    order = PreOrder(
        pre_no=pre_no,
        pre_type=data.get('pre_type', 1),
        customer_id=data.get('customer_id'),
        customer_name=data.get('customer_name'),
        supplier_id=data.get('supplier_id'),
        supplier_name=data.get('supplier_name'),
        remark=data.get('remark'),
        created_by=user_id
    )
    db.session.add(order)
    db.session.flush()

    # 添加明细
    items = data.get('items', [])
    total_quantity = 0
    total_amount = 0
    for item_data in items:
        item = PreOrderItem(
            pre_id=order.id,
            product_id=item_data.get('product_id'),
            product_code=item_data.get('product_code'),
            product_name=item_data.get('product_name'),
            quantity=item_data.get('quantity', 0),
            unit_price=item_data.get('unit_price', 0),
            total_price=item_data.get('quantity', 0) * item_data.get('unit_price', 0),
            remark=item_data.get('remark')
        )
        db.session.add(item)
        total_quantity += item_data.get('quantity', 0)
        total_amount += item.total_price

    order.total_quantity = total_quantity
    order.total_amount = total_amount
    db.session.commit()

    return jsonify({'code': 200, 'message': '创建成功', 'data': {'id': order.id, 'pre_no': pre_no}})

@bp.route('/api/pre-orders/<int:id>', methods=['PUT'])
@jwt_required()
@permission('preorder:edit')
def update_preorder(id):
    """更新预订单"""
    from models.inventory.flow import PreOrder, PreOrderItem
    order = PreOrder.query.get_or_404(id)
    if order.status != 0:
        return jsonify({'code': 400, 'message': '只有待处理的预订单可以修改'}), 400

    data = request.get_json()
    if 'customer_name' in data: order.customer_name = data['customer_name']
    if 'supplier_name' in data: order.supplier_name = data['supplier_name']
    if 'remark' in data: order.remark = data['remark']

    # 更新明细
    if 'items' in data:
        PreOrderItem.query.filter_by(pre_id=id).delete()
        total_quantity = 0
        total_amount = 0
        for item_data in data['items']:
            item = PreOrderItem(
                pre_id=id,
                product_id=item_data.get('product_id'),
                product_code=item_data.get('product_code'),
                product_name=item_data.get('product_name'),
                quantity=item_data.get('quantity', 0),
                unit_price=item_data.get('unit_price', 0),
                total_price=item_data.get('quantity', 0) * item_data.get('unit_price', 0),
                remark=item_data.get('remark')
            )
            db.session.add(item)
            total_quantity += item_data.get('quantity', 0)
            total_amount += item.total_price
        order.total_quantity = total_quantity
        order.total_amount = total_amount

    db.session.commit()
    return jsonify({'code': 200, 'message': '更新成功'})

@bp.route('/api/pre-orders/<int:id>', methods=['DELETE'])
@jwt_required()
@permission('preorder:delete')
def delete_preorder(id):
    """删除预订单"""
    from models.inventory.flow import PreOrder
    order = PreOrder.query.get_or_404(id)
    if order.status != 0:
        return jsonify({'code': 400, 'message': '只有待处理的预订单可以删除'}), 400
    order.status = 2
    db.session.commit()
    return jsonify({'code': 200, 'message': '已取消'})

@bp.route('/api/pre-orders/<int:id>/convert', methods=['POST'])
@jwt_required()
@permission('preorder:edit')
def convert_preorder(id):
    """预订单转正式单据"""
    from models.inventory.flow import PreOrder, PreOrderItem
    order = PreOrder.query.get_or_404(id)
    if order.status != 0:
        return jsonify({'code': 400, 'message': '只有待处理的预订单可以转单'}), 400

    data = request.get_json()

    if order.pre_type == 1:
        # 采购预定 -> 采购单
        from models.purchase.order import PurchaseOrder, PurchaseOrderItem
        last_po = PurchaseOrder.query.order_by(PurchaseOrder.id.desc()).first()
        po_no = generate_code('PO', last_po.id if last_po else 0)

        po = PurchaseOrder(
            order_no=po_no,
            supplier_id=order.supplier_id,
            supplier_name=order.supplier_name,
            total_amount=order.total_amount,
            status=0,
            remark=f'由预订单{order.pre_no}转换',
            created_by=get_current_user_id()
        )
        db.session.add(po)
        db.session.flush()

        items = PreOrderItem.query.filter_by(pre_id=id).all()
        for item in items:
            po_item = PurchaseOrderItem(
                order_id=po.id,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=int(item.quantity) if item.quantity else 0,
                price=float(item.unit_price) if item.unit_price else 0,
                amount=float(item.total_price) if item.total_price else 0
            )
            db.session.add(po_item)

        order.related_order_id = po.id
        order.related_order_no = po_no

    elif order.pre_type == 2:
        # 销售预定 -> 销售单
        from models.sales.order import SalesOrder, SalesOrderItem
        last_so = SalesOrder.query.order_by(SalesOrder.id.desc()).first()
        so_no = generate_code('SO', last_so.id if last_so else 0)

        so = SalesOrder(
            order_no=so_no,
            customer_id=order.customer_id,
            customer_name=order.customer_name,
            total_amount=order.total_amount,
            total_quantity=int(order.total_quantity),
            status=0,
            remark=f'由预订单{order.pre_no}转换',
            created_by=get_current_user_id()
        )
        db.session.add(so)
        db.session.flush()

        items = PreOrderItem.query.filter_by(pre_id=id).all()
        for item in items:
            so_item = SalesOrderItem(
                order_id=so.id,
                product_id=item.product_id,
                product_name=item.product_name,
                specification='',
                unit='个',
                quantity=int(item.quantity),
                price=item.unit_price,
                amount=item.total_price
            )
            db.session.add(so_item)

        order.related_order_id = so.id
        order.related_order_no = so_no

    order.status = 1
    db.session.commit()

    return jsonify({'code': 200, 'message': '转单成功', 'data': {'related_order_no': order.related_order_no}})