"""采购管理蓝图。

迁移自 source-code/app.py 中以下区段的原始路由代码：
- /api/purchase/orders  CRUD + 详情                       8324-8535 行附近
- /api/purchase/orders/<id>/audit  审核（自动入库+应付+流水）  8546-8731 行附近
- /api/purchase/orders/export  导出                            14407 行附近
- /api/purchase/invoices  发票 CRUD                           13491-13750 行附近
- /api/purchase/invoices/<id>/certify, /deduct  认证/抵扣     13753-13780 行附近
- /api/purchase/orders/<id>/invoice  为采购单创建发票         17367 行附近

按子资源分 2 个 section：
  1. 采购单  (orders CRUD + audit + export + invoice)
  2. 采购发票  (invoices CRUD + certify + deduct)

跨蓝图依赖：
- PurchaseOrder / PurchaseOrderItem (models.purchase.order)
- PurchaseInvoice (models.finance)
- InventoryIn / InventoryInItem / InventoryStock / InventoryLog (models.inventory)
- ProductInfo (models.product.info)
- FinancePayable / FinanceRecord (models.finance)
- SysUser (models.system) — 仅查询操作人
- PO_STATUS_MAP 沿用 app.py 5803-5808 行的常量

注意：audit 函数 ~186 行（事务 + 库存扣减 + 应付 + 财务流水）保持原样迁移，
不做任何重构以保证业务行为完全一致。
"""
import io
import logging
from datetime import datetime

import openpyxl
from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from app.security import permission
from app.utils import generate_code, to_dict

logger = logging.getLogger(__name__)

bp = Blueprint('purchase', __name__)


# ============================================
# 常量
# ============================================

# 采购单状态映射（与原 app.py 5803-5808 行一致）
PO_STATUS_MAP = {
    0: '待审核',
    1: '已审核',
    2: '已完成',
    3: '已取消',
}

# 采购发票状态映射
PO_INVOICE_STATUS_MAP = {0: '待认证', 1: '已认证', 2: '已抵扣', 3: '已作废'}
# 采购发票类型映射
PO_INVOICE_TYPE_MAP = {1: '普通发票', 2: '增值税专用发票'}


# ============================================
# 工具函数
# ============================================

def _get_current_user_name():
    """获取当前登录用户姓名。迁移期兼容（app.py 顶层也定义同名函数）。"""
    from models.system import SysUser
    user_id = get_jwt_identity()
    user = SysUser.query.get(user_id)
    if user:
        return user.real_name or user.username
    return ''


# ============================================
# 1. 采购单
# ============================================

@bp.route('/api/purchase/orders', methods=['GET'])
@permission('purchase:view')
def get_purchase_orders():
    """获取采购单列表"""
    from models.purchase.order import PurchaseOrder
    from models.system import SysUser

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '')
    status = request.args.get('status', type=int)
    supplier_id = request.args.get('supplier_id', type=int)
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = PurchaseOrder.query

    if keyword:
        query = query.filter(
            db.or_(
                PurchaseOrder.order_no.contains(keyword),
                PurchaseOrder.supplier_name.contains(keyword)
            )
        )

    if status is not None:
        query = query.filter_by(status=status)

    if supplier_id:
        query = query.filter_by(supplier_id=supplier_id)

    if start_date:
        query = query.filter(PurchaseOrder.order_date >= start_date)

    if end_date:
        query = query.filter(PurchaseOrder.order_date <= end_date)

    total = query.count()
    orders = query.order_by(PurchaseOrder.created_at.desc()).paginate(
        page=page, per_page=page_size, error_out=False
    )

    # 批量查询操作人名称
    user_ids = [o.created_by for o in orders.items if o.created_by]
    users_map = {}
    if user_ids:
        users = SysUser.query.filter(SysUser.id.in_(user_ids)).all()
        users_map = {u.id: (u.real_name or u.username) for u in users}

    return jsonify({
        'code': 200,
        'data': {
            'list': [{
                'id': o.id,
                'purchase_no': o.order_no,
                'order_no': o.order_no,
                'supplier_id': o.supplier_id,
                'supplier_name': o.supplier_name,
                'purchase_date': o.order_date.strftime('%Y-%m-%d') if o.order_date else None,
                'order_date': o.order_date.strftime('%Y-%m-%d') if o.order_date else None,
                'delivery_date': o.delivery_date.strftime('%Y-%m-%d') if o.delivery_date else None,
                'total_amount': float(o.total_amount) if o.total_amount else 0,
                'paid_amount': 0,
                'total_quantity': o.total_quantity,
                'status': o.status,
                'status_text': PO_STATUS_MAP.get(o.status, '未知'),
                'has_invoice': o.has_invoice,
                'operator_name': users_map.get(o.created_by, ''),
                'remark': o.remark,
                'created_at': o.created_at.strftime('%Y-%m-%d %H:%M:%S') if o.created_at else None
            } for o in orders.items],
            'total': total,
            'page': page,
            'page_size': page_size
        }
    })


@bp.route('/api/purchase/orders/<int:id>', methods=['GET'])
@permission('purchase:view')
def get_purchase_order(id):
    """获取采购单详情"""
    from models.purchase.order import PurchaseOrder, PurchaseOrderItem

    order = PurchaseOrder.query.get(id)
    if not order:
        return jsonify({'code': 404, 'message': '采购单不存在'}), 404

    items = PurchaseOrderItem.query.filter_by(order_id=id).all()

    result = to_dict(order)
    result['status_text'] = PO_STATUS_MAP.get(order.status, '未知')
    result['items'] = [to_dict(i) for i in items]

    return jsonify({'code': 200, 'data': result})


@bp.route('/api/purchase/orders', methods=['POST'])
@permission('purchase:add')
def create_purchase_order():
    """创建采购单"""
    from models.purchase.order import PurchaseOrder, PurchaseOrderItem

    data = request.get_json()
    user_id = get_jwt_identity()

    # 生成采购单号
    last_order = PurchaseOrder.query.order_by(PurchaseOrder.id.desc()).first()
    order_no = generate_code('PO', last_order.id if last_order else 0)

    order = PurchaseOrder(
        order_no=order_no,
        supplier_id=data.get('supplier_id'),
        supplier_name=data.get('supplier_name'),
        order_date=data.get('order_date'),
        delivery_date=data.get('delivery_date'),
        remark=data.get('remark'),
        has_invoice=data.get('has_invoice', 0),
        created_by=user_id
    )

    db.session.add(order)
    db.session.flush()

    # 添加明细
    items = data.get('items', [])
    total_amount = 0
    total_quantity = 0

    for item_data in items:
        qty = int(item_data.get('quantity', 0))
        price = float(item_data.get('price') or item_data.get('unit_price') or 0)
        amount = qty * price
        total_amount += amount
        total_quantity += qty

        item = PurchaseOrderItem(
            order_id=order.id,
            product_id=item_data.get('product_id'),
            product_name=item_data.get('product_name'),
            specification=item_data.get('specification'),
            unit=item_data.get('unit'),
            quantity=qty,
            price=price,
            amount=amount,
            remark=item_data.get('remark')
        )
        db.session.add(item)

    order.total_amount = total_amount
    order.total_quantity = total_quantity
    db.session.commit()

    return jsonify({'code': 200, 'message': '创建成功', 'data': {'id': order.id, 'order_no': order_no}})


@bp.route('/api/purchase/orders/<int:id>', methods=['PUT'])
@permission('purchase:edit')
def update_purchase_order(id):
    """更新采购单"""
    from models.purchase.order import PurchaseOrder, PurchaseOrderItem

    order = PurchaseOrder.query.get(id)
    if not order:
        return jsonify({'code': 404, 'message': '采购单不存在'}), 404

    if order.status != 0:
        return jsonify({'code': 400, 'message': '只有待审核的采购单可以修改'}), 400

    data = request.get_json()

    for field in ['supplier_id', 'supplier_name', 'order_date', 'delivery_date', 'remark']:
        if field in data:
            setattr(order, field, data[field])

    if 'has_invoice' in data:
        order.has_invoice = data['has_invoice']

    # 更新明细
    if 'items' in data:
        # 删除旧明细
        PurchaseOrderItem.query.filter_by(order_id=id).delete()
        total_amount = 0
        total_quantity = 0

        for item_data in data['items']:
            qty = int(item_data.get('quantity', 0))
            price = float(item_data.get('price') or item_data.get('unit_price') or 0)
            amount = qty * price
            total_amount += amount
            total_quantity += qty

            item = PurchaseOrderItem(
                order_id=id,
                product_id=item_data.get('product_id'),
                product_name=item_data.get('product_name'),
                specification=item_data.get('specification'),
                unit=item_data.get('unit'),
                quantity=qty,
                price=price,
                amount=amount,
                remark=item_data.get('remark')
            )
            db.session.add(item)

        order.total_amount = total_amount
        order.total_quantity = total_quantity

    db.session.commit()
    return jsonify({'code': 200, 'message': '更新成功'})


@bp.route('/api/purchase/orders/<int:id>', methods=['DELETE'])
@permission('purchase:delete')
def delete_purchase_order(id):
    """删除采购单"""
    from models.purchase.order import PurchaseOrder

    order = PurchaseOrder.query.get(id)
    if not order:
        return jsonify({'code': 404, 'message': '采购单不存在'}), 404

    if order.status == 2:
        return jsonify({'code': 400, 'message': '已完成的采购单不能删除'}), 400

    # 软删除
    order.status = 3  # 已取消
    db.session.commit()
    return jsonify({'code': 200, 'message': '删除成功'})


@bp.route('/api/purchase/orders/<int:id>/audit', methods=['POST'])
@permission('purchase:edit')
def audit_purchase_order(id):
    """审核采购单 - 自动入库、更新库存、生成应付账款和财务流水"""
    from models.purchase.order import PurchaseOrder, PurchaseOrderItem
    from models.inventory.flow import InventoryIn, InventoryInItem
    from models.inventory.stock import InventoryStock, InventoryLog
    from models.product.info import ProductInfo
    from models.finance import FinancePayable, FinanceRecord

    order = PurchaseOrder.query.get(id)
    if not order:
        return jsonify({'code': 404, 'message': '采购单不存在'}), 404

    if order.status != 0:
        return jsonify({'code': 400, 'message': '只有待审核的采购单可以审核'}), 400

    try:
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()
        today = datetime.now().strftime('%Y%m%d')

        # 1. 更新采购单状态
        order.status = 1  # 已审核

        # 2. 检查是否已有入库单（避免重复创建）
        existing_in = InventoryIn.query.filter_by(related_order_id=id).first()
        if existing_in:
            db.session.commit()
            return jsonify({'code': 200, 'message': '审核成功（入库单已存在）'})

        # 3. 获取采购单明细
        items = PurchaseOrderItem.query.filter_by(order_id=id).all()
        if not items:
            db.session.commit()
            return jsonify({'code': 200, 'message': '审核成功（无明细商品）'})

        # 4. 生成入库单号 RK + YYYYMMDD + 4位序号
        prefix_rk = 'RK' + today
        last_in = InventoryIn.query.filter(InventoryIn.in_no.like(prefix_rk + '%')).order_by(InventoryIn.in_no.desc()).first()
        if last_in and last_in.in_no and len(last_in.in_no) > len(prefix_rk):
            seq = int(last_in.in_no[len(prefix_rk):]) + 1
        else:
            seq = 1
        in_no = prefix_rk + str(seq).zfill(4)

        # 5. 创建入库单
        inventory_in = InventoryIn(
            in_no=in_no,
            in_type=1,  # 采购入库
            supplier_id=order.supplier_id,
            supplier_name=order.supplier_name,
            warehouse_id=1,
            warehouse_name='主仓库',
            total_quantity=sum(item.quantity or 0 for item in items),
            total_amount=float(order.total_amount or 0),
            status=2,  # 直接入库
            auditor_id=user_id,
            auditor_name=user_name,
            audit_time=datetime.now(),
            related_order_id=id,
            related_order_no=order.order_no,
            created_by=user_id
        )
        db.session.add(inventory_in)
        db.session.flush()  # 获取 in_id

        # 6. 创建入库单明细 + 更新库存 + 写入库存日志 + 更新商品现存量
        for item in items:
            # 入库明细
            in_item = InventoryInItem(
                in_id=inventory_in.id,
                product_id=item.product_id,
                product_code=None,
                product_name=item.product_name,
                specification=item.specification,
                unit_name=item.unit,
                quantity=item.quantity,
                unit_price=item.price,
                total_price=item.amount,
                cost_price=item.price
            )
            db.session.add(in_item)

            # 更新库存
            stock = InventoryStock.query.filter_by(product_id=item.product_id).first()
            before_qty = stock.quantity if stock else 0
            if stock:
                stock.quantity = (stock.quantity or 0) + (item.quantity or 0)
                stock.available_quantity = (stock.available_quantity or 0) + (item.quantity or 0)
                if item.price:
                    stock.cost_price = item.price
            else:
                # 自动创建库存记录
                product = ProductInfo.query.get(item.product_id) if item.product_id else None
                stock = InventoryStock(
                    product_id=item.product_id,
                    product_code=product.product_code if product else None,
                    product_name=item.product_name,
                    warehouse_id=1,
                    warehouse_name='主仓库',
                    quantity=item.quantity or 0,
                    available_quantity=item.quantity or 0,
                    cost_price=item.price or 0
                )
                db.session.add(stock)
                before_qty = 0

            after_qty = (stock.quantity or 0)

            # 写入库存日志
            inv_log = InventoryLog(
                product_id=item.product_id,
                product_code=stock.product_code if stock else None,
                product_name=item.product_name,
                warehouse_id=1,
                warehouse_name='主仓库',
                change_type='in',
                order_type='采购入库',
                order_id=inventory_in.id,
                order_no=in_no,
                quantity_change=item.quantity or 0,
                before_quantity=before_qty,
                after_quantity=after_qty,
                cost_price=item.price,
                amount=item.amount,
                related_party=order.supplier_name,
                operator_id=user_id,
                operator_name=user_name,
                remark=f'采购单{order.order_no}审核自动入库'
            )
            db.session.add(inv_log)

            # 更新商品现存量
            if item.product_id:
                product_info = ProductInfo.query.get(item.product_id)
                if product_info:
                    product_info.current_stock = (product_info.current_stock or 0) + (item.quantity or 0)

        # 7. 生成应付编号 YF + YYYYMMDD + 4位序号
        prefix_yf = 'YF' + today
        last_payable = FinancePayable.query.filter(FinancePayable.payable_no.like(prefix_yf + '%')).order_by(FinancePayable.payable_no.desc()).first()
        if last_payable and last_payable.payable_no and len(last_payable.payable_no) > len(prefix_yf):
            seq_yf = int(last_payable.payable_no[len(prefix_yf):]) + 1
        else:
            seq_yf = 1
        payable_no = prefix_yf + str(seq_yf).zfill(4)

        # 8. 生成应付账款
        total_amount = float(order.total_amount or 0)
        payable = FinancePayable(
            payable_no=payable_no,
            related_type='purchase',
            related_id=id,
            related_no=order.order_no,
            supplier_id=order.supplier_id,
            supplier_name=order.supplier_name,
            total_amount=total_amount,
            paid_amount=0,
            remaining_amount=total_amount,
            status=0,  # 待付款
            remark=f'采购单{order.order_no}审核自动生成'
        )
        db.session.add(payable)

        # 9. 生成财务流水（支出）
        finance_record = FinanceRecord(
            account_id=None,
            account_name='',
            record_type=2,  # 支出
            amount=total_amount,
            balance_before=0,
            balance_after=0,
            related_type='purchase',
            related_id=id,
            related_no=order.order_no,
            remark=f'采购单{order.order_no}审核，应付金额{total_amount}',
            created_at=datetime.now(),
            created_by=user_id
        )
        db.session.add(finance_record)

        db.session.commit()
        return jsonify({'code': 200, 'message': '审核成功，已自动入库并生成应付账款'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'审核失败：{str(e)}'}), 500


@bp.route('/api/purchase/orders/export', methods=['GET'])
@permission('purchase:view')
def export_purchase_orders():
    """导出采购单"""
    from models.purchase.order import PurchaseOrder

    keyword = request.args.get('keyword', '')
    status = request.args.get('status', type=int)
    date_start = request.args.get('date_start', '')
    date_end = request.args.get('date_end', '')

    query = PurchaseOrder.query
    if keyword:
        query = query.filter(db.or_(PurchaseOrder.order_no.contains(keyword), PurchaseOrder.supplier_name.contains(keyword)))
    if status is not None:
        query = query.filter(PurchaseOrder.status == status)
    if date_start:
        query = query.filter(PurchaseOrder.created_at >= date_start)
    if date_end:
        query = query.filter(PurchaseOrder.created_at <= date_end + ' 23:59:59')

    orders = query.order_by(PurchaseOrder.created_at.desc()).all()

    data = []
    for o in orders:
        data.append({
            '采购单号': o.order_no,
            '供应商': o.supplier_name,
            '总金额': float(o.total_amount or 0),
            '状态': {0: '待审核', 1: '已审核', 2: '已入库', 3: '已取消'}.get(o.status, str(o.status)),
            '备注': o.remark or '',
            '创建时间': o.created_at.strftime('%Y-%m-%d %H:%M') if o.created_at else ''
        })

    output = io.BytesIO()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = '采购单列表'
    # 定义表头
    headers = ['采购单号', '供应商', '总金额', '状态', '备注', '创建时间']
    ws.append(headers)
    for row in data:
        ws.append(list(row.values()))
    wb.save(output)
    output.seek(0)

    return send_file(output, as_attachment=True, download_name=f'采购单列表_{datetime.now().strftime("%Y%m%d")}.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@bp.route('/api/purchase/orders/<int:order_id>/invoice', methods=['POST'])
@permission('purchase:edit')
def create_purchase_order_invoice(order_id):
    """为采购单创建发票"""
    from models.purchase.order import PurchaseOrder
    from models.finance import PurchaseInvoice

    order = PurchaseOrder.query.get(order_id)
    if not order:
        return jsonify({'code': 404, 'message': '采购单不存在'}), 404

    data = request.get_json()

    # 生成发票号
    date_str = datetime.now().strftime('%Y%m%d')
    last_invoice = PurchaseInvoice.query.filter(
        PurchaseInvoice.invoice_no.like(f'PI{date_str}%')
    ).order_by(PurchaseInvoice.id.desc()).first()

    if last_invoice:
        last_no = int(last_invoice.invoice_no[-4:])
        new_no = f'PI{date_str}{last_no + 1:04d}'
    else:
        new_no = f'PI{date_str}0001'

    # 计算税额和合计
    amount = float(data.get('amount', 0))
    tax_rate = float(data.get('tax_rate', 0))
    tax_amount = amount * tax_rate / 100
    total_amount = amount + tax_amount

    invoice = PurchaseInvoice(
        invoice_no=new_no,
        invoice_code=data.get('invoice_code'),
        invoice_type=data.get('invoice_type', 1),
        purchase_order_id=order.id,
        purchase_order_no=order.order_no,
        supplier_id=order.supplier_id,
        supplier_name=order.supplier_name,
        amount=amount,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        total_amount=total_amount,
        invoice_date=data.get('invoice_date'),
        status=0,  # 待认证
        remark=data.get('remark'),
        created_by=get_jwt_identity()
    )

    # 更新采购单has_invoice
    order.has_invoice = 1

    db.session.add(invoice)
    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '发票创建成功',
        'data': {'id': invoice.id, 'invoice_no': invoice.invoice_no}
    })


# ============================================
# 2. 采购发票
# ============================================

@bp.route('/api/purchase/invoices', methods=['GET'])
@permission('purchase:view')
def get_purchase_invoices():
    """采购发票列表"""
    from models.finance import PurchaseInvoice

    try:
        supplier_id = request.args.get('supplier_id', type=int)
        status = request.args.get('status', type=int)
        keyword = request.args.get('keyword', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        query = PurchaseInvoice.query.filter(PurchaseInvoice.status != 3)

        if supplier_id:
            query = query.filter(PurchaseInvoice.supplier_id == supplier_id)
        if status is not None:
            query = query.filter(PurchaseInvoice.status == status)
        if keyword:
            query = query.filter(db.or_(
                PurchaseInvoice.invoice_no.like(f'%{keyword}%'),
                PurchaseInvoice.supplier_name.like(f'%{keyword}%'),
                PurchaseInvoice.purchase_order_no.like(f'%{keyword}%')
            ))
        if start_date:
            query = query.filter(PurchaseInvoice.invoice_date >= start_date)
        if end_date:
            query = query.filter(PurchaseInvoice.invoice_date <= end_date)

        query = query.order_by(PurchaseInvoice.created_at.desc())
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        items = []
        for inv in pagination.items:
            items.append({
                'id': inv.id,
                'invoice_no': inv.invoice_no,
                'invoice_code': inv.invoice_code,
                'invoice_type': inv.invoice_type,
                'invoice_type_name': PO_INVOICE_TYPE_MAP.get(inv.invoice_type, ''),
                'purchase_order_id': inv.purchase_order_id,
                'purchase_order_no': inv.purchase_order_no,
                'supplier_id': inv.supplier_id,
                'supplier_name': inv.supplier_name,
                'amount': float(inv.amount) if inv.amount else 0,
                'tax_rate': float(inv.tax_rate) if inv.tax_rate else 0,
                'tax_amount': float(inv.tax_amount) if inv.tax_amount else 0,
                'total_amount': float(inv.total_amount) if inv.total_amount else 0,
                'invoice_date': inv.invoice_date.strftime('%Y-%m-%d') if inv.invoice_date else None,
                'status': inv.status,
                'status_name': PO_INVOICE_STATUS_MAP.get(inv.status, ''),
                'remark': inv.remark,
                'created_at': inv.created_at.strftime('%Y-%m-%d %H:%M:%S') if inv.created_at else None
            })

        return jsonify({
            'code': 200,
            'message': '查询成功',
            'data': {
                'total': pagination.total,
                'page': page,
                'page_size': page_size,
                'items': items
            }
        })
    except Exception as e:
        logger.error(f'查询采购发票列表失败：{str(e)}')
        return jsonify({'code': 500, 'message': f'查询失败：{str(e)}'}), 500


@bp.route('/api/purchase/invoices/<int:id>', methods=['GET'])
@permission('purchase:view')
def get_purchase_invoice_detail(id):
    """采购发票详情"""
    from models.finance import PurchaseInvoice

    try:
        invoice = PurchaseInvoice.query.get(id)
        if not invoice:
            return jsonify({'code': 404, 'message': '发票不存在'}), 404

        return jsonify({
            'code': 200,
            'message': '查询成功',
            'data': {
                'id': invoice.id,
                'invoice_no': invoice.invoice_no,
                'invoice_code': invoice.invoice_code,
                'invoice_type': invoice.invoice_type,
                'invoice_type_name': PO_INVOICE_TYPE_MAP.get(invoice.invoice_type, ''),
                'purchase_order_id': invoice.purchase_order_id,
                'purchase_order_no': invoice.purchase_order_no,
                'supplier_id': invoice.supplier_id,
                'supplier_name': invoice.supplier_name,
                'amount': float(invoice.amount) if invoice.amount else 0,
                'tax_rate': float(invoice.tax_rate) if invoice.tax_rate else 0,
                'tax_amount': float(invoice.tax_amount) if invoice.tax_amount else 0,
                'total_amount': float(invoice.total_amount) if invoice.total_amount else 0,
                'invoice_date': invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else None,
                'status': invoice.status,
                'status_name': PO_INVOICE_STATUS_MAP.get(invoice.status, ''),
                'remark': invoice.remark,
                'created_at': invoice.created_at.strftime('%Y-%m-%d %H:%M:%S') if invoice.created_at else None,
                'updated_at': invoice.updated_at.strftime('%Y-%m-%d %H:%M:%S') if invoice.updated_at else None,
                'created_by': invoice.created_by
            }
        })
    except Exception as e:
        logger.error(f'查询采购发票详情失败：{str(e)}')
        return jsonify({'code': 500, 'message': f'查询失败：{str(e)}'}), 500


@bp.route('/api/purchase/invoices', methods=['POST'])
@permission('purchase:edit')
def create_purchase_invoice():
    """创建采购发票"""
    from models.purchase.order import PurchaseOrder
    from models.finance import PurchaseInvoice

    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()

        # 自动生成发票号码
        today_str = datetime.now().strftime('%Y%m%d')
        prefix = f'PI{today_str}'
        last_invoice = PurchaseInvoice.query.filter(
            PurchaseInvoice.invoice_no.like(f'{prefix}%')
        ).order_by(PurchaseInvoice.id.desc()).first()

        if last_invoice:
            last_seq = int(last_invoice.invoice_no[-4:])
            new_seq = last_seq + 1
        else:
            new_seq = 1

        invoice_no = f'{prefix}{new_seq:04d}'

        purchase_order_id = data.get('purchase_order_id')
        purchase_order_no = data.get('purchase_order_no', '')
        supplier_id = data.get('supplier_id')
        supplier_name = data.get('supplier_name', '')

        # 如果提供了采购单ID，自动查询采购单信息
        if purchase_order_id:
            purchase_order = PurchaseOrder.query.get(purchase_order_id)
            if purchase_order:
                purchase_order_no = purchase_order.order_no
                if not supplier_id:
                    supplier_id = purchase_order.supplier_id
                if not supplier_name:
                    supplier_name = purchase_order.supplier_name

        invoice = PurchaseInvoice(
            invoice_no=invoice_no,
            invoice_code=data.get('invoice_code', ''),
            invoice_type=data.get('invoice_type', 1),
            purchase_order_id=purchase_order_id,
            purchase_order_no=purchase_order_no,
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            amount=data.get('amount', 0),
            tax_rate=data.get('tax_rate', 0),
            tax_amount=data.get('tax_amount', 0),
            total_amount=data.get('total_amount', 0),
            invoice_date=data.get('invoice_date'),
            remark=data.get('remark', ''),
            created_by=current_user_id
        )

        db.session.add(invoice)
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '创建成功',
            'data': {'id': invoice.id, 'invoice_no': invoice.invoice_no}
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'创建采购发票失败：{str(e)}')
        return jsonify({'code': 500, 'message': f'创建失败：{str(e)}'}), 500


@bp.route('/api/purchase/invoices/<int:id>', methods=['PUT'])
@permission('purchase:edit')
def update_purchase_invoice(id):
    """更新采购发票"""
    from models.finance import PurchaseInvoice

    try:
        invoice = PurchaseInvoice.query.get(id)
        if not invoice:
            return jsonify({'code': 404, 'message': '发票不存在'}), 404

        data = request.get_json()

        if 'invoice_code' in data:
            invoice.invoice_code = data['invoice_code']
        if 'invoice_type' in data:
            invoice.invoice_type = data['invoice_type']
        if 'purchase_order_id' in data:
            invoice.purchase_order_id = data['purchase_order_id']
        if 'purchase_order_no' in data:
            invoice.purchase_order_no = data['purchase_order_no']
        if 'supplier_id' in data:
            invoice.supplier_id = data['supplier_id']
        if 'supplier_name' in data:
            invoice.supplier_name = data['supplier_name']
        if 'amount' in data:
            invoice.amount = data['amount']
        if 'tax_rate' in data:
            invoice.tax_rate = data['tax_rate']
        if 'tax_amount' in data:
            invoice.tax_amount = data['tax_amount']
        if 'total_amount' in data:
            invoice.total_amount = data['total_amount']
        if 'invoice_date' in data:
            invoice.invoice_date = data['invoice_date']
        if 'remark' in data:
            invoice.remark = data['remark']

        invoice.updated_at = datetime.now()

        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '更新成功',
            'data': {'id': invoice.id}
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新采购发票失败：{str(e)}')
        return jsonify({'code': 500, 'message': f'更新失败：{str(e)}'}), 500


@bp.route('/api/purchase/invoices/<int:id>', methods=['DELETE'])
@permission('purchase:delete')
def delete_purchase_invoice(id):
    """删除采购发票（软删除，设为已作废）"""
    from models.finance import PurchaseInvoice

    try:
        invoice = PurchaseInvoice.query.get(id)
        if not invoice:
            return jsonify({'code': 404, 'message': '发票不存在'}), 404

        invoice.status = 3
        invoice.updated_at = datetime.now()

        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '删除成功',
            'data': {'id': invoice.id}
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除采购发票失败：{str(e)}')
        return jsonify({'code': 500, 'message': f'删除失败：{str(e)}'}), 500


@bp.route('/api/purchase/invoices/<int:id>/certify', methods=['POST'])
@permission('purchase:edit')
def certify_purchase_invoice(id):
    """采购发票认证"""
    from models.finance import PurchaseInvoice

    try:
        invoice = PurchaseInvoice.query.get(id)
        if not invoice:
            return jsonify({'code': 404, 'message': '发票不存在'}), 404

        if invoice.status != 0:
            return jsonify({'code': 400, 'message': '只有待认证状态的发票才能进行认证操作'}), 400

        invoice.status = 1
        invoice.updated_at = datetime.now()

        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '认证成功',
            'data': {'id': invoice.id, 'status': invoice.status}
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'采购发票认证失败：{str(e)}')
        return jsonify({'code': 500, 'message': f'认证失败：{str(e)}'}), 500


@bp.route('/api/purchase/invoices/<int:id>/deduct', methods=['POST'])
@permission('purchase:edit')
def deduct_purchase_invoice(id):
    """采购发票抵扣"""
    from models.finance import PurchaseInvoice

    try:
        invoice = PurchaseInvoice.query.get(id)
        if not invoice:
            return jsonify({'code': 404, 'message': '发票不存在'}), 404

        if invoice.status != 1:
            return jsonify({'code': 400, 'message': '只有已认证状态的发票才能进行抵扣操作'}), 400

        invoice.status = 2
        invoice.updated_at = datetime.now()

        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '抵扣成功',
            'data': {'id': invoice.id, 'status': invoice.status}
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'采购发票抵扣失败：{str(e)}')
        return jsonify({'code': 500, 'message': f'抵扣失败：{str(e)}'}), 500