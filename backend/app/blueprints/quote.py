"""报价管理 CRUD + 状态机转换（确认/转工单/转接件/转销售）+ 导出。

迁移自 source-code/app.py 中 7133-7475 行（CRUD + 状态机）和
18311-18360 行附近（导出）的原始路由代码。保持行为完全一致：
- 分页 page/page_size，响应键 list/total/page/page_size
- 报价单单号 QT 前缀 + generate_code 生成
- 状态机：confirm/to-workorder/to-receive/to-sales
- 状态码：0=待确认 1=已确认 2=已失效 3=已转工单 4=已转接件 5=已转销售
- 删除为软删除（status=2）
- 跨子域依赖：WorkOrder/ReceiveOrder/InventoryOut/InventoryOutItem/SysUser
  均已迁移至 models/，直接导入

注意：app.py 中 QUOTE_STATUS_MAP 仍保留（可能被其他端点引用），本蓝图
使用模块级副本避免对 app.py 全局变量产生依赖。
"""
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from app.utils import generate_code, to_dict

bp = Blueprint('quote', __name__, url_prefix='/api/quotes')


# 状态映射（与原 app.py QUOTE_STATUS_MAP 行为一致；独立副本避免对未迁移的常量产生依赖）
QUOTE_STATUS_MAP = {
    0: '待确认',
    1: '已确认',
    2: '已失效',
    3: '已转工单',
    4: '已转接件',
    5: '已转销售',
}


# ============================================
# 报价单 CRUD
# ============================================

@bp.route('', methods=['GET'])
@jwt_required()
def list_quotes():
    """获取报价单列表。"""
    from models.quote import QuoteOrder

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '')
    status = request.args.get('status', type=int)

    query = QuoteOrder.query

    if keyword:
        query = query.filter(
            db.or_(
                QuoteOrder.quote_no.contains(keyword),
                QuoteOrder.customer_name.contains(keyword),
                QuoteOrder.customer_phone.contains(keyword),
            )
        )

    if status is not None:
        query = query.filter_by(status=status)

    total = query.count()
    orders = query.order_by(QuoteOrder.created_at.desc()).paginate(
        page=page, per_page=page_size, error_out=False
    )

    return {
        'code': 200,
        'data': {
            'list': [{
                'id': o.id,
                'quote_no': o.quote_no,
                'customer_name': o.customer_name,
                'customer_phone': o.customer_phone,
                'total_amount': float(o.total_amount) if o.total_amount else 0.00,
                'status': o.status,
                'status_text': QUOTE_STATUS_MAP.get(o.status, '未知'),
                'quote_date': o.quote_date.strftime('%Y-%m-%d') if o.quote_date else None,
                'valid_until': o.valid_until.strftime('%Y-%m-%d') if o.valid_until else None,
                'created_at': o.created_at.strftime('%Y-%m-%d %H:%M:%S') if o.created_at else None,
            } for o in orders.items],
            'total': total,
            'page': page,
            'page_size': page_size,
        },
    }, 200


@bp.route('/<int:oid>', methods=['GET'])
@jwt_required()
def get_quote(oid):
    """获取报价单详情。"""
    from models.quote import QuoteOrder, QuoteOrderItem

    order = QuoteOrder.query.get(oid)
    if not order:
        return {'code': 404, 'message': '报价单不存在'}, 404

    items = QuoteOrderItem.query.filter_by(quote_id=oid).all()

    result = to_dict(order)
    result['status_text'] = QUOTE_STATUS_MAP.get(order.status, '未知')
    result['items'] = [to_dict(i) for i in items]

    return {'code': 200, 'data': result}, 200


@bp.route('', methods=['POST'])
@jwt_required()
def create_quote():
    """创建报价单。"""
    from models.quote import QuoteOrder, QuoteOrderItem

    data = request.get_json()
    user_id = get_jwt_identity()

    last_order = QuoteOrder.query.order_by(QuoteOrder.id.desc()).first()
    quote_no = generate_code('QT', last_order.id if last_order else 0)

    order = QuoteOrder(
        quote_no=quote_no,
        customer_id=data.get('customer_id'),
        customer_name=data.get('customer_name'),
        customer_phone=data.get('customer_phone'),
        contact_name=data.get('contact_name'),
        address=data.get('address'),
        quote_date=data.get('quote_date'),
        valid_until=data.get('valid_until'),
        total_amount=0,
        remark=data.get('remark'),
        created_by=user_id,
    )

    db.session.add(order)
    db.session.flush()

    # 添加明细
    items = data.get('items', [])
    total_amount = 0
    for item_data in items:
        qty = float(item_data.get('quantity', 1))
        price = float(item_data.get('unit_price', 0))
        subtotal = qty * price
        total_amount += subtotal

        item = QuoteOrderItem(
            quote_id=order.id,
            product_name=item_data.get('product_name'),
            specification=item_data.get('specification'),
            brand=item_data.get('brand'),
            unit=item_data.get('unit'),
            quantity=qty,
            unit_price=price,
            subtotal=subtotal,
            remark=item_data.get('remark'),
        )
        db.session.add(item)

    order.total_amount = total_amount
    db.session.commit()

    return {
        'code': 200,
        'message': '创建成功',
        'data': {'id': order.id, 'quote_no': quote_no},
    }, 200


@bp.route('/<int:oid>', methods=['PUT'])
@jwt_required()
def update_quote(oid):
    """更新报价单。"""
    from models.quote import QuoteOrder, QuoteOrderItem

    order = QuoteOrder.query.get(oid)
    if not order:
        return {'code': 404, 'message': '报价单不存在'}, 404

    if order.status != 0:
        return {'code': 400, 'message': '只有待确认的报价单可以修改'}, 400

    data = request.get_json()

    for field in ['customer_id', 'customer_name', 'customer_phone',
                  'contact_name', 'address', 'quote_date', 'valid_until', 'remark']:
        if field in data:
            setattr(order, field, data[field])

    # 更新明细
    if 'items' in data:
        # 删除旧明细
        QuoteOrderItem.query.filter_by(quote_id=oid).delete()
        total_amount = 0
        for item_data in data['items']:
            qty = float(item_data.get('quantity', 1))
            price = float(item_data.get('unit_price', 0))
            subtotal = qty * price
            total_amount += subtotal
            item = QuoteOrderItem(
                quote_id=oid,
                product_name=item_data.get('product_name'),
                specification=item_data.get('specification'),
                brand=item_data.get('brand'),
                unit=item_data.get('unit'),
                quantity=qty,
                unit_price=price,
                subtotal=subtotal,
                remark=item_data.get('remark'),
            )
            db.session.add(item)
        order.total_amount = total_amount

    db.session.commit()
    return {'code': 200, 'message': '更新成功'}, 200


@bp.route('/<int:oid>', methods=['DELETE'])
@jwt_required()
def delete_quote(oid):
    """删除报价单（软删除 status=2）。"""
    from models.quote import QuoteOrder

    order = QuoteOrder.query.get(oid)
    if not order:
        return {'code': 404, 'message': '报价单不存在'}, 404

    if order.status in [1, 3, 4, 5]:
        return {'code': 400, 'message': '该报价单已确认或已转换，不能删除'}, 400

    order.status = 2  # 标记为已失效
    db.session.commit()
    return {'code': 200, 'message': '删除成功'}, 200


# ============================================
# 状态机转换
# ============================================

@bp.route('/<int:oid>/confirm', methods=['POST'])
@jwt_required()
def confirm_quote(oid):
    """确认报价单（status 0 → 1）。"""
    from models.quote import QuoteOrder

    order = QuoteOrder.query.get(oid)
    if not order:
        return {'code': 404, 'message': '报价单不存在'}, 404

    if order.status != 0:
        return {'code': 400, 'message': '只有待确认的报价单可以确认'}, 400

    order.status = 1
    db.session.commit()

    return {'code': 200, 'message': '报价单已确认'}, 200


@bp.route('/<int:oid>/to-workorder', methods=['POST'])
@jwt_required()
def quote_to_workorder(oid):
    """报价单转工单（status 1 → 3）。"""
    from models.quote import QuoteOrder
    from models.workorder.order import WorkOrder

    order = QuoteOrder.query.get(oid)
    if not order:
        return {'code': 404, 'message': '报价单不存在'}, 404

    if order.status != 1:
        return {'code': 400, 'message': '只有已确认的报价单可以转工单'}, 400

    data = request.get_json()
    user_id = get_jwt_identity()

    # 生成工单号
    last_wo = WorkOrder.query.order_by(WorkOrder.id.desc()).first()
    wo_no = generate_code('WO', last_wo.id if last_wo else 0)

    wo = WorkOrder(
        wo_no=wo_no,
        wo_type=data.get('wo_type', '维修'),
        customer_id=order.customer_id,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        fault_desc=order.remark,
        labor_cost=data.get('labor_cost', 0),
        parts_cost=float(order.total_amount or 0) - float(data.get('labor_cost', 0)),
        total_cost=order.total_amount,
        status=0,
        created_by=user_id,
    )

    db.session.add(wo)

    order.status = 3
    order.related_type = 'work_order'
    order.related_id = wo.id
    db.session.flush()

    db.session.commit()

    return {'code': 200, 'message': '已转工单', 'data': {'wo_id': wo.id, 'wo_no': wo_no}}, 200


@bp.route('/<int:oid>/to-receive', methods=['POST'])
@jwt_required()
def quote_to_receive(oid):
    """报价单转接件单（status 1 → 4）。"""
    from models.quote import QuoteOrder
    from models.receive.order import ReceiveOrder

    order = QuoteOrder.query.get(oid)
    if not order:
        return {'code': 404, 'message': '报价单不存在'}, 404

    if order.status != 1:
        return {'code': 400, 'message': '只有已确认的报价单可以转接件单'}, 400

    data = request.get_json()
    user_id = get_jwt_identity()

    last_ro = ReceiveOrder.query.order_by(ReceiveOrder.id.desc()).first()
    receive_no = generate_code('RO', last_ro.id if last_ro else 0)

    ro = ReceiveOrder(
        receive_no=receive_no,
        customer_id=order.customer_id,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        total_amount=order.total_amount,
        remark=order.remark,
        created_by=user_id,
    )

    db.session.add(ro)

    order.status = 4
    order.related_type = 'receive_order'
    order.related_id = ro.id
    db.session.flush()

    db.session.commit()

    return {
        'code': 200,
        'message': '已转接件单',
        'data': {'receive_order_id': ro.id, 'receive_no': receive_no},
    }, 200


@bp.route('/<int:oid>/to-sales', methods=['POST'])
@jwt_required()
def quote_to_sales(oid):
    """报价单转销售单（status 1 → 5，创建 InventoryOut + InventoryOutItem）。"""
    from models.quote import QuoteOrder, QuoteOrderItem
    from models.inventory.flow import InventoryOut, InventoryOutItem

    order = QuoteOrder.query.get(oid)
    if not order:
        return {'code': 404, 'message': '报价单不存在'}, 404

    if order.status != 1:
        return {'code': 400, 'message': '只有已确认的报价单可以转销售单'}, 400

    data = request.get_json()
    user_id = get_jwt_identity()

    # 创建出库单（销售出库）
    last_out = InventoryOut.query.order_by(InventoryOut.id.desc()).first()
    out_no = generate_code('OUT', last_out.id if last_out else 0)

    out_order = InventoryOut(
        out_no=out_no,
        out_type=1,  # 销售出库
        customer_id=order.customer_id,
        customer_name=order.customer_name,
        warehouse_id=data.get('warehouse_id', 1),
        warehouse_name=data.get('warehouse_name', '主仓库'),
        total_amount=order.total_amount,
        remark=f'报价单 {order.quote_no} 转销售',
        created_by=user_id,
    )

    db.session.add(out_order)

    # 添加出库明细
    items = QuoteOrderItem.query.filter_by(quote_id=oid).all()
    for item in items:
        out_item = InventoryOutItem(
            out_id=out_order.id,
            product_name=item.product_name,
            specification=item.specification,
            unit_name=item.unit,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.subtotal,
            remark=item.remark,
        )
        db.session.add(out_item)

    order.status = 5
    order.related_type = 'inventory_out'
    order.related_id = out_order.id
    db.session.flush()

    db.session.commit()

    return {
        'code': 200,
        'message': '已转销售单',
        'data': {'out_id': out_order.id, 'out_no': out_no},
    }, 200


# ============================================
# 导出
# ============================================

@bp.route('/export', methods=['GET'])
@jwt_required()
def export_quotes():
    """导出报价单 Excel（保留原 app.py 行为）。"""
    import logging
    from flask import Response
    from app.utils import export_to_excel
    from models.quote import QuoteOrder
    from models.workorder.order import WorkOrder
    from models.receive.order import ReceiveOrder
    from models.system.user import SysUser

    logger = logging.getLogger(__name__)

    try:
        keyword = request.args.get('keyword', '')
        status = request.args.get('status', type=int)

        query = QuoteOrder.query
        if keyword:
            query = query.filter(
                db.or_(
                    QuoteOrder.quote_no.contains(keyword),
                    QuoteOrder.customer_name.contains(keyword),
                    QuoteOrder.customer_phone.contains(keyword),
                )
            )
        if status is not None:
            query = query.filter(QuoteOrder.status == status)

        orders = query.order_by(QuoteOrder.created_at.desc()).all()

        data = []
        for o in orders:
            # 获取创建者用户名
            creator = ''
            if o.created_by:
                user = SysUser.query.get(o.created_by)
                if user:
                    creator = user.username or ''

            # 获取关联工单号或接件单号
            related_no = ''
            if o.related_type and o.related_id:
                if o.related_type == 'work_order':
                    wo = WorkOrder.query.get(o.related_id)
                    related_no = wo.wo_no if wo else ''
                elif o.related_type == 'receive_order':
                    ro = ReceiveOrder.query.get(o.related_id)
                    related_no = ro.receive_no if ro else ''

            data.append({
                '报价单号': o.quote_no or '',
                '工单号/接件单号': related_no,
                '客户名称': o.customer_name or '',
                '故障描述': '',
                '人工费': float(o.total_amount or 0) if o.total_amount else 0,
                '材料费': 0,
                '其他费': 0,
                '总计': float(o.total_amount) if o.total_amount else 0.00,
                '报价人': creator,
                '状态': QUOTE_STATUS_MAP.get(o.status, '未知'),
                '创建时间': o.created_at.strftime('%Y-%m-%d %H:%M:%S') if o.created_at else '',
            })

        columns = (
            list(data[0].keys()) if data else [
                '报价单号', '工单号/接件单号', '客户名称', '故障描述', '人工费',
                '材料费', '其他费', '总计', '报价人', '状态', '创建时间',
            ]
        )
        excel_bytes = export_to_excel(data, columns, sheet_name='报价单')
        filename = f'报价单_{datetime.now().strftime("%Y%m%d")}.xlsx'
        return Response(
            excel_bytes,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        logger.error(f'导出报价单失败: {str(e)}')
        return {'code': 500, 'message': f'导出失败: {str(e)}'}, 500
