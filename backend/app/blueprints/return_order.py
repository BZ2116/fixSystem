"""退货单管理蓝图（CRUD + 审核 + 入库）。

迁移自 source-code/app.py 中 12530-13000 行附近的原始路由代码。

业务规则：
- audit (审核)：~272 行的长事务函数，处理库存回流 / 退款 / 财务冲销
- stock-in (入库)：将退货商品回收到库存
- 退货单关联原销售单/采购单

跨子域依赖：
- ReturnOrder / ReturnOrderItem (models.purchase.return_order)
- PurchaseOrder / PurchaseOrderItem (models.purchase.order)
- SalesOrder / SalesOrderItem (models.sales.order)
- BaseSupplier / BaseCustomer (models.supplier / models.customer)
- InventoryStock / InventoryLog (models.inventory)
- FinanceReceivable / FinancePayable / FinanceRecord (models.finance.account)
- SysUser (models.system)

直接 import 当前蓝图用得到的本地 helper，其他跨子域模型按"函数内懒加载"惯例。
"""
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from extensions import db
from app.utils import to_dict, generate_code
from app.security import get_current_user_id

bp = Blueprint('return_order', __name__)
logger = logging.getLogger(__name__)


def _get_current_user_name():
    """获取当前登录用户姓名。迁移期兼容（app.py 顶层也定义同名函数）。"""
    from models.system import SysUser
    user_id = get_current_user_id()
    user = SysUser.query.get(user_id)
    if user:
        return user.real_name or user.username
    return ''


@bp.route('/api/return-orders', methods=['GET'])
@jwt_required()
def get_return_orders():
    """获取退货单列表"""
    from models.purchase.return_order import ReturnOrder
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    keyword = request.args.get('keyword', '')
    return_type = request.args.get('return_type', type=int)
    status = request.args.get('status', type=int)

    query = ReturnOrder.query
    if keyword:
        query = query.filter(db.or_(
            ReturnOrder.return_no.contains(keyword),
            ReturnOrder.customer_name.contains(keyword),
            ReturnOrder.supplier_name.contains(keyword)
        ))
    if return_type is not None:
        query = query.filter(ReturnOrder.return_type == return_type)
    if status is not None:
        query = query.filter(ReturnOrder.status == status)

    total = query.count()
    orders = query.order_by(ReturnOrder.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({'code': 200, 'data': {'list': [to_dict(o) for o in orders], 'total': total}})

@bp.route('/api/return-orders/<int:id>', methods=['GET'])
@jwt_required()
def get_return_order(id):
    """获取退货单详情"""
    from models.purchase.return_order import ReturnOrder, ReturnOrderItem
    order = ReturnOrder.query.get_or_404(id)
    items = ReturnOrderItem.query.filter_by(return_id=id).all()
    order_dict = to_dict(order)
    order_dict['items'] = [to_dict(i) for i in items]
    return jsonify({'code': 200, 'data': order_dict})

@bp.route('/api/return-orders', methods=['POST'])
@jwt_required()
def create_return_order():
    """创建退货单"""
    from models.purchase.return_order import ReturnOrder, ReturnOrderItem
    data = request.get_json()
    user_id = get_current_user_id()

    last = ReturnOrder.query.order_by(ReturnOrder.id.desc()).first()
    return_no = generate_code('R', last.id if last else 0)

    order = ReturnOrder(
        return_no=return_no,
        return_type=data.get('return_type', 1),
        related_order_id=data.get('related_order_id'),
        related_order_no=data.get('related_order_no'),
        supplier_id=data.get('supplier_id'),
        supplier_name=data.get('supplier_name'),
        customer_id=data.get('customer_id'),
        customer_name=data.get('customer_name'),
        refund_amount=data.get('refund_amount', 0),
        reason=data.get('reason'),
        remark=data.get('remark'),
        created_by=user_id
    )
    db.session.add(order)
    db.session.flush()

    items = data.get('items', [])
    total_quantity = 0
    total_amount = 0
    for item_data in items:
        qty = item_data.get('quantity', 0)
        price = item_data.get('unit_price', 0)
        item = ReturnOrderItem(
            return_id=order.id,
            product_id=item_data.get('product_id'),
            product_code=item_data.get('product_code'),
            product_name=item_data.get('product_name'),
            quantity=qty,
            unit_price=price,
            total_price=qty * price,
            remark=item_data.get('remark')
        )
        db.session.add(item)
        total_quantity += qty
        total_amount += qty * price

    order.total_quantity = total_quantity
    order.total_amount = total_amount
    if not order.refund_amount:
        order.refund_amount = total_amount
    db.session.commit()

    return jsonify({'code': 200, 'message': '创建成功', 'data': {'id': order.id, 'return_no': return_no}})

@bp.route('/api/return-orders/<int:id>/audit', methods=['POST'])
@jwt_required()
def audit_return_order(id):
    """审核退货单 - 自动处理库存、冲减应收/应付账款并生成财务流水"""
    from models.purchase.return_order import ReturnOrder, ReturnOrderItem
    from models.inventory.stock import InventoryStock, InventoryLog
    from models.inventory.flow import InventoryOut, InventoryOutItem, InventoryIn, InventoryInItem
    from models.finance.account import FinancePayable, FinanceReceivable, FinanceRecord
    from models.product.info import ProductInfo
    order = ReturnOrder.query.get_or_404(id)
    if order.status != 0:
        return jsonify({'code': 400, 'message': '只有待审核的退货单可以审核'}), 400

    try:
        user_id = get_current_user_id()
        user_name = _get_current_user_name()
        refund_amount = float(order.refund_amount or order.total_amount or 0)
        today = datetime.now().strftime('%Y%m%d')

        items = ReturnOrderItem.query.filter_by(return_id=id).all()

        if order.return_type == 1:
            # ========== 采购退货：自动出库扣减库存 ==========
            for item in items:
                # 检查库存是否充足
                stock = InventoryStock.query.filter_by(product_id=item.product_id).first()
                available = (stock.available_quantity or 0) if stock else 0
                if available < (item.quantity or 0):
                    return jsonify({'code': 400, 'message': f'商品"{item.product_name}"库存不足，可用库存{available}，需要{item.quantity}'}), 400

            # 生成出库单号 CK + YYYYMMDD + 4位序号
            prefix_ck = 'CK' + today
            last_out = InventoryOut.query.filter(InventoryOut.out_no.like(prefix_ck + '%')).order_by(InventoryOut.out_no.desc()).first()
            if last_out and last_out.out_no and len(last_out.out_no) > len(prefix_ck):
                seq = int(last_out.out_no[len(prefix_ck):]) + 1
            else:
                seq = 1
            out_no = prefix_ck + str(seq).zfill(4)

            # 创建出库单
            inventory_out = InventoryOut(
                out_no=out_no,
                out_type=5,  # 其他出库（采购退货）
                warehouse_id=1,
                warehouse_name='主仓库',
                total_quantity=sum(i.quantity or 0 for i in items),
                total_amount=sum((i.quantity or 0) * (i.unit_price or 0) for i in items),
                status=2,  # 已出库
                related_order_id=id,
                related_order_no=order.return_no,
                remark=f'采购退货单{order.return_no}出库',
                created_by=user_id,
                created_at=datetime.now()
            )
            db.session.add(inventory_out)
            db.session.flush()

            # 处理出库明细并扣减库存
            for item in items:
                # 创建出库明细
                out_item = InventoryOutItem(
                    out_id=inventory_out.id,
                    product_id=item.product_id,
                    product_code=item.product_code,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                    remark=f'采购退货'
                )
                db.session.add(out_item)

                # 扣减库存
                stock = InventoryStock.query.filter_by(product_id=item.product_id).first()
                before_qty = stock.quantity if stock else 0
                if stock:
                    stock.quantity = (stock.quantity or 0) - (item.quantity or 0)
                    stock.available_quantity = (stock.available_quantity or 0) - (item.quantity or 0)
                after_qty = (stock.quantity or 0) if stock else 0

                # 写入库存日志
                inv_log = InventoryLog(
                    product_id=item.product_id,
                    product_code=item.product_code,
                    product_name=item.product_name,
                    warehouse_id=1,
                    warehouse_name='主仓库',
                    change_type='out',
                    order_type='采购退货出库',
                    order_id=inventory_out.id,
                    order_no=out_no,
                    quantity_change=-(item.quantity or 0),
                    before_quantity=before_qty,
                    after_quantity=after_qty,
                    cost_price=item.unit_price,
                    amount=item.total_price,
                    related_party=order.supplier_name,
                    operator_id=user_id,
                    operator_name=user_name,
                    remark=f'采购退货单{order.return_no}出库'
                )
                db.session.add(inv_log)

                # 更新商品现存量
                if item.product_id:
                    product_info = ProductInfo.query.get(item.product_id)
                    if product_info:
                        product_info.current_stock = max(0, (product_info.current_stock or 0) - (item.quantity or 0))

            # 冲减应付账款
            payable = FinancePayable.query.filter_by(
                related_type='purchase',
                related_id=order.related_order_id
            ).first()
            if payable and payable.status != 3:
                payable.total_amount = max(0, float(payable.total_amount or 0) - refund_amount)
                payable.remaining_amount = max(0, float(payable.remaining_amount or 0) - refund_amount)
                if payable.remaining_amount <= 0:
                    payable.status = 2
                elif float(payable.paid_amount or 0) > 0:
                    payable.status = 1
                else:
                    payable.status = 0

            # 生成财务流水
            finance_record = FinanceRecord(
                account_id=None,
                account_name='',
                record_type=1,
                amount=refund_amount,
                balance_before=0,
                balance_after=0,
                related_type='return_purchase',
                related_id=id,
                related_no=order.return_no,
                remark=f'采购退货单{order.return_no}审核，冲减应付{refund_amount}元',
                created_at=datetime.now(),
                created_by=user_id
            )
            db.session.add(finance_record)

            order.status = 2  # 已完成（已出库）

        elif order.return_type == 2:
            # ========== 销售退货：自动入库增加库存 ==========
            # 生成入库单号 RK + YYYYMMDD + 4位序号
            prefix_rk = 'RK' + today
            last_in = InventoryIn.query.filter(InventoryIn.in_no.like(prefix_rk + '%')).order_by(InventoryIn.in_no.desc()).first()
            if last_in and last_in.in_no and len(last_in.in_no) > len(prefix_rk):
                seq = int(last_in.in_no[len(prefix_rk):]) + 1
            else:
                seq = 1
            in_no = prefix_rk + str(seq).zfill(4)

            # 创建入库单
            inventory_in = InventoryIn(
                in_no=in_no,
                in_type=2,  # 退货入库
                warehouse_id=1,
                warehouse_name='主仓库',
                total_quantity=sum(i.quantity or 0 for i in items),
                total_amount=sum((i.quantity or 0) * (i.unit_price or 0) for i in items),
                status=2,  # 已入库
                related_order_id=id,
                related_order_no=order.return_no,
                remark=f'销售退货单{order.return_no}入库',
                created_by=user_id,
                created_at=datetime.now()
            )
            db.session.add(inventory_in)
            db.session.flush()

            # 处理入库明细并增加库存
            for item in items:
                # 创建入库明细
                in_item = InventoryInItem(
                    in_id=inventory_in.id,
                    product_id=item.product_id,
                    product_code=item.product_code,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                    remark=f'销售退货'
                )
                db.session.add(in_item)

                # 增加库存
                stock = InventoryStock.query.filter_by(product_id=item.product_id).first()
                before_qty = (stock.quantity or 0) if stock else 0
                if stock:
                    stock.quantity = (stock.quantity or 0) + (item.quantity or 0)
                    stock.available_quantity = (stock.available_quantity or 0) + (item.quantity or 0)
                else:
                    stock = InventoryStock(
                        product_id=item.product_id,
                        product_code=item.product_code,
                        product_name=item.product_name,
                        warehouse_id=1,
                        warehouse_name='主仓库',
                        quantity=item.quantity or 0,
                        available_quantity=item.quantity or 0,
                        cost_price=item.unit_price or 0
                    )
                    db.session.add(stock)
                    before_qty = 0

                after_qty = (stock.quantity or 0)

                # 写入库存日志
                inv_log = InventoryLog(
                    product_id=item.product_id,
                    product_code=item.product_code,
                    product_name=item.product_name,
                    warehouse_id=1,
                    warehouse_name='主仓库',
                    change_type='in',
                    order_type='销售退货入库',
                    order_id=inventory_in.id,
                    order_no=in_no,
                    quantity_change=item.quantity or 0,
                    before_quantity=before_qty,
                    after_quantity=after_qty,
                    cost_price=item.unit_price,
                    amount=item.total_price,
                    related_party=order.customer_name,
                    operator_id=user_id,
                    operator_name=user_name,
                    remark=f'销售退货单{order.return_no}入库'
                )
                db.session.add(inv_log)

                # 更新商品现存量
                if item.product_id:
                    product_info = ProductInfo.query.get(item.product_id)
                    if product_info:
                        product_info.current_stock = (product_info.current_stock or 0) + (item.quantity or 0)

            # 冲减应收账款
            receivable = FinanceReceivable.query.filter_by(
                related_type='sale',
                related_id=order.related_order_id
            ).first()
            if receivable and receivable.status != 3:
                receivable.total_amount = max(0, float(receivable.total_amount or 0) - refund_amount)
                receivable.remaining_amount = max(0, float(receivable.remaining_amount or 0) - refund_amount)
                if receivable.remaining_amount <= 0:
                    receivable.status = 2
                elif float(receivable.received_amount or 0) > 0:
                    receivable.status = 1
                else:
                    receivable.status = 0

            # 生成财务流水
            finance_record = FinanceRecord(
                account_id=None,
                account_name='',
                record_type=2,
                amount=refund_amount,
                balance_before=0,
                balance_after=0,
                related_type='return_sale',
                related_id=id,
                related_no=order.return_no,
                remark=f'销售退货单{order.return_no}审核，冲减应收{refund_amount}元',
                created_at=datetime.now(),
                created_by=user_id
            )
            db.session.add(finance_record)

            order.status = 2  # 已完成（已入库）

        db.session.commit()
        return jsonify({'code': 200, 'message': '审核成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'审核失败：{str(e)}'}), 500

@bp.route('/api/return-orders/<int:id>/stock-in', methods=['POST'])
@jwt_required()
def stock_in_return_order(id):
    """退货入库 - 更新库存、写入库存日志、更新商品现存量"""
    from models.purchase.return_order import ReturnOrder, ReturnOrderItem
    from models.inventory.stock import InventoryStock, InventoryLog
    from models.inventory.flow import InventoryIn
    from models.product.info import ProductInfo
    order = ReturnOrder.query.get_or_404(id)
    if order.status != 1:
        return jsonify({'code': 400, 'message': '只有已审核的退货单可以入库'}), 400

    try:
        user_id = get_current_user_id()
        user_name = _get_current_user_name()
        order_type_text = '采购退货入库' if order.return_type == 1 else '销售退货入库'
        related_party = order.supplier_name if order.return_type == 1 else order.customer_name

        items = ReturnOrderItem.query.filter_by(return_id=id).all()
        for item in items:
            # 更新库存
            stock = InventoryStock.query.filter_by(product_id=item.product_id).first()
            before_qty = (stock.quantity or 0) if stock else 0
            if stock:
                stock.quantity = (stock.quantity or 0) + item.quantity
                stock.available_quantity = (stock.available_quantity or 0) + item.quantity
            else:
                # 自动创建库存记录
                product = ProductInfo.query.get(item.product_id) if item.product_id else None
                stock = InventoryStock(
                    product_id=item.product_id,
                    product_code=item.product_code or (product.product_code if product else None),
                    product_name=item.product_name,
                    warehouse_id=1,
                    warehouse_name='主仓库',
                    quantity=item.quantity or 0,
                    available_quantity=item.quantity or 0,
                    cost_price=item.unit_price or 0
                )
                db.session.add(stock)
                before_qty = 0

            after_qty = (stock.quantity or 0)

            # 记录入库流水
            in_record = InventoryIn(
                in_type=2,  # 退货入库
                product_id=item.product_id,
                product_code=item.product_code,
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                related_type='return_order',
                related_id=id,
                remark=f'退货单{order.return_no}入库'
            )
            db.session.add(in_record)

            # 写入库存日志
            inv_log = InventoryLog(
                product_id=item.product_id,
                product_code=item.product_code,
                product_name=item.product_name,
                warehouse_id=1,
                warehouse_name='主仓库',
                change_type='in',
                order_type=order_type_text,
                order_id=id,
                order_no=order.return_no,
                quantity_change=item.quantity or 0,
                before_quantity=before_qty,
                after_quantity=after_qty,
                cost_price=item.unit_price,
                amount=item.total_price,
                related_party=related_party,
                operator_id=user_id,
                operator_name=user_name,
                remark=f'退货单{order.return_no}入库'
            )
            db.session.add(inv_log)

            # 更新商品现存量
            if item.product_id:
                product_info = ProductInfo.query.get(item.product_id)
                if product_info:
                    product_info.current_stock = (product_info.current_stock or 0) + (item.quantity or 0)

        order.status = 2
        db.session.commit()
        return jsonify({'code': 200, 'message': '入库成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'入库失败：{str(e)}'}), 500

@bp.route('/api/return-orders/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_return_order(id):
    """取消退货单"""
    from models.purchase.return_order import ReturnOrder
    order = ReturnOrder.query.get_or_404(id)
    if order.status != 0:
        return jsonify({'code': 400, 'message': '只有待审核的退货单可以取消'}), 400
    order.status = 3
    db.session.commit()
    return jsonify({'code': 200, 'message': '已取消'})