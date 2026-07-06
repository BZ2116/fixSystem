"""接件单业务服务层。

把接件单模块的核心业务（结算 / 配件分配 / 报价 / 取消 / 完成 / 外店流程 / 检测 / 完工 / 测试 / 通知）
从路由层抽到这里。Service 层只放业务逻辑，不接受 Flask request 对象，
参数由调用方传入。

每个函数都假定自己处于 db.session 事务中（由路由层负责 commit/rollback）。
"""
import json
import logging
from datetime import datetime

from extensions import db
from app.utils import generate_code

logger = logging.getLogger(__name__)


# ============================================================
# 接件单号生成（与 app.py 147 行 generate_code 行为一致）
# ============================================================

def _generate_ro_no():
    """生成接件单号：RO + YYYYMMDD + 4位序号。"""
    from models.receive import ReceiveOrder
    today_str = datetime.now().strftime('%Y%m%d')
    today_prefix = f'RO{today_str}'
    last_order = ReceiveOrder.query.filter(
        ReceiveOrder.receive_no.like(f'{today_prefix}%')
    ).order_by(ReceiveOrder.id.desc()).first()
    if last_order:
        seq = int(last_order.receive_no[-4:]) + 1
    else:
        seq = 1
    return f'{today_prefix}{str(seq).zfill(4)}'


# ============================================================
# 日志辅助（与 app.py 3515 行 add_ro_log 等价）
# ============================================================

def add_ro_log(ro_id, action, old_status, new_status, content,
               operator_id=None, operator_name=None):
    """添加接件单操作日志。"""
    from models.receive import ReceiveOrderLog
    log = ReceiveOrderLog(
        receive_order_id=ro_id,
        action=action,
        old_status=old_status,
        new_status=new_status,
        content=content,
        operator_id=operator_id,
        operator_name=operator_name,
    )
    db.session.add(log)
    return log


# ============================================================
# 1. 接件结算（核心：价格/发票/收款链式触发，原 app.py 6495 行附近）
# ============================================================

def settle_receiveorder(order, data, user_id, user_name):
    """接件结算（待取件 7 -> 待结算 8）。

    - 自动计算已用备件 / 未用备件，未用退回库存
    - 创建销售单
    - 现金结算：写入账户余额 + 财务记录
    - 签单结算：生成应收记录（YS + YYYYMMDDxxxx）
    """
    from models.receive import ReceiveOrderPart
    from models.sales.order import SalesOrder
    from models.finance.account import FinanceAccount, FinanceRecord, FinanceReceivable

    settle_type = data.get('settle_type', 'cash')

    # 1. 处理已用/未用备件
    parts = ReceiveOrderPart.query.filter_by(receive_order_id=order.id).all()
    used_parts = []
    unused_parts = []
    parts_cost_total = 0.0

    for part in parts:
        used_qty = float(data.get(f'used_qty_{part.id}', part.used_quantity or part.quantity or 0))
        unused_qty = float(part.quantity or 0) - used_qty
        part.used_quantity = used_qty

        if used_qty > 0:
            part.status = 1
            used_parts.append({
                'product_name': part.product_name,
                'specification': part.specification,
                'quantity': used_qty,
                'unit_price': float(part.unit_price or 0),
                'total': used_qty * float(part.unit_price or 0),
            })
            parts_cost_total += used_qty * float(part.unit_price or 0)

        if unused_qty > 0:
            part.status = 2
            if part.product_id:
                # 退回库存（兼容历史 Product 模型，可能不存在）
                try:
                    from app import Product  # type: ignore
                    product = Product.query.get(part.product_id)
                    if product:
                        product.stock = float(product.stock or 0) + unused_qty
                except Exception as e:
                    logger.warning(f'退回库存失败: {str(e)}')
            unused_parts.append({
                'product_name': part.product_name,
                'specification': part.specification,
                'quantity': unused_qty,
            })

    # 2. 费用更新
    labor_hours = data.get('labor_hours')
    labor_unit_price = data.get('labor_unit_price')
    labor_cost = data.get('labor_cost')
    other_cost = data.get('other_cost', 0)
    account_id = data.get('account_id')

    if labor_hours is not None:
        order.labor_hours = labor_hours
    if labor_unit_price is not None:
        order.labor_unit_price = labor_unit_price
    if labor_cost is not None:
        order.labor_cost = labor_cost
    elif labor_hours and labor_unit_price:
        order.labor_cost = float(labor_hours) * float(labor_unit_price)

    if data.get('parts_cost') is not None:
        order.parts_cost = data.get('parts_cost')
    else:
        order.parts_cost = parts_cost_total

    total = (
        float(order.labor_cost or 0) + float(order.parts_cost or 0) +
        float(order.material_cost or 0) + float(order.transport_cost or 0) +
        float(other_cost or 0) + float(order.service_fee or 0)
    )
    order.total_cost = total

    # 3. 创建销售单
    last_so = SalesOrder.query.order_by(SalesOrder.id.desc()).first()
    so_no = generate_code('XS', last_so.id if last_so else 0)
    sales_order = SalesOrder(
        order_no=so_no,
        customer_id=order.customer_id,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        customer_address=order.customer_address,
        order_date=datetime.now().date(),
        total_amount=total,
        total_quantity=1,
        actual_amount=total,
        paid_amount=0,
        salesperson_id=user_id,
        salesperson_name=user_name,
        status=1,
        remark=f'接件单{order.receive_no}结算生成',
        created_by=user_id,
    )
    db.session.add(sales_order)
    db.session.flush()
    order.related_sales_id = sales_order.id

    # 4. 财务处理
    if settle_type == 'cash' and account_id:
        account = FinanceAccount.query.get(account_id)
        if account:
            balance_before = float(account.balance or 0)
            account.balance = balance_before + total
            record = FinanceRecord(
                account_id=account.id,
                account_name=account.account_name,
                record_type=1,
                amount=total,
                balance_before=balance_before,
                balance_after=balance_before + total,
                related_type='receive_order',
                related_id=order.id,
                related_no=order.receive_no,
                remark=f'接件单现金结算：{order.receive_no}',
                created_by=user_id,
            )
            db.session.add(record)
            db.session.flush()
            order.related_finance_id = record.id
    elif settle_type == 'credit':
        today = datetime.now().strftime('%Y%m%d')
        prefix_ys = 'YS' + today
        last_receivable = FinanceReceivable.query.filter(
            FinanceReceivable.receivable_no.like(prefix_ys + '%')
        ).order_by(FinanceReceivable.receivable_no.desc()).first()
        if last_receivable and last_receivable.receivable_no and \
                len(last_receivable.receivable_no) > len(prefix_ys):
            seq_ys = int(last_receivable.receivable_no[len(prefix_ys):]) + 1
        else:
            seq_ys = 1
        receivable_no = prefix_ys + str(seq_ys).zfill(4)

        receivable = FinanceReceivable(
            receivable_no=receivable_no,
            related_type='receive_order',
            related_id=order.id,
            related_no=order.receive_no,
            customer_id=order.customer_id,
            customer_name=order.customer_name,
            total_amount=total,
            received_amount=0,
            remaining_amount=total,
            status=0,
            remark=f'接件单签单结算：{order.receive_no}',
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.session.add(receivable)
        db.session.flush()

    # 5. 状态变更
    old_status = order.status
    order.status = 8
    order.settlement_status = 1
    order.settlement_account_id = account_id if settle_type == 'cash' else None
    order.settlement_time = datetime.now()

    # 6. 日志
    settle_type_text = '现金结算' if settle_type == 'cash' else '签单结算'
    log_content = f'完工{settle_type_text}，总费用：{total}元'
    if used_parts:
        used_str = '、'.join([f'{p["product_name"]}x{p["quantity"]}' for p in used_parts])
        log_content += f'。已用配件：{used_str}'
    if unused_parts:
        unused_str = '、'.join([f'{p["product_name"]}x{p["quantity"]}' for p in unused_parts])
        log_content += f'。已退回配件：{unused_str}'

    add_ro_log(
        ro_id=order.id, action='完工结算',
        old_status=old_status, new_status=8,
        content=log_content,
        operator_id=user_id, operator_name=user_name,
    )

    return {'status': 8, 'status_text': '待结算', 'total_cost': total}


# ============================================================
# 2. 领料/采购（原 app.py 6166 行附近，192 行）
# ============================================================

def allocate_receiveorder(order, data, user_id, user_name):
    """领料/采购（待领料 4 -> 维修中 5）。

    - 检查库存：有库存直接出库，无库存创建采购预订单
    - 扣减库存
    - 保存配件明细
    """
    from models.receive import ReceiveOrderPart
    from models.product.info import ProductInfo
    from models.inventory.stock import InventoryStock
    from models.inventory.flow import InventoryOut, InventoryOutItem
    from models.purchase.order import PurchaseOrder, PurchaseOrderItem

    items = data.get('items', [])
    if not items:
        raise ValueError('领料明细不能为空')

    out_items = []
    purchase_items = []
    all_in_stock = True

    for item in items:
        product_id = item.get('product_id')
        quantity = float(item.get('quantity', 1))
        product = ProductInfo.query.get(product_id) if product_id else None
        stock = InventoryStock.query.filter_by(product_id=product_id).first()
        available_qty = float(stock.available_quantity or 0) if stock else 0

        part_info = {
            'product_id': product_id,
            'product_name': product.product_name if product else item.get('product_name', ''),
            'product_code': product.product_code if product else item.get('product_code', ''),
            'specification': product.specification if product else item.get('specification', ''),
            'unit_name': product.unit_name if product else item.get('unit_name', ''),
            'quantity': quantity,
            'unit_price': float(item.get('unit_price', 0)),
            'cost_price': float(product.cost_price or 0) if product else 0,
            'remark': item.get('remark', ''),
        }
        part_info['total_price'] = part_info['quantity'] * part_info['unit_price']

        if available_qty >= quantity:
            part_info['source'] = 1
            part_info['status'] = 1
            out_items.append(part_info)
        else:
            part_info['source'] = 2
            part_info['status'] = 2
            purchase_items.append(part_info)
            all_in_stock = False

    # 创建出库单
    if out_items:
        last_out = InventoryOut.query.order_by(InventoryOut.id.desc()).first()
        out_no = generate_code('OUT', last_out.id if last_out else 0)
        out_order = InventoryOut(
            out_no=out_no,
            out_type=2,
            customer_id=order.customer_id,
            customer_name=order.customer_name,
            warehouse_id=1,
            warehouse_name='主仓库',
            status=1,
            auditor_id=user_id,
            auditor_name=user_name,
            audit_time=datetime.now(),
            remark=f'接件单{order.receive_no}维修领料',
            related_order_id=order.id,
            related_order_no=order.receive_no,
            created_by=user_id,
        )
        db.session.add(out_order)
        db.session.flush()

        for item in out_items:
            out_item = InventoryOutItem(
                out_id=out_order.id,
                product_id=item['product_id'],
                product_code=item['product_code'],
                product_name=item['product_name'],
                specification=item['specification'],
                unit_name=item['unit_name'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total_price=item['total_price'],
                cost_price=item['cost_price'],
                remark=item['remark'],
            )
            db.session.add(out_item)
            item['inventory_out_item_id'] = out_item.id

            stock = InventoryStock.query.filter_by(product_id=item['product_id']).first()
            if stock:
                stock.quantity = float(stock.quantity or 0) - item['quantity']
                stock.available_quantity = float(stock.available_quantity or 0) - item['quantity']

    # 创建采购预订单
    if purchase_items:
        last_po = PurchaseOrder.query.order_by(PurchaseOrder.id.desc()).first()
        po_no = generate_code('PO', last_po.id if last_po else 0)
        po_order = PurchaseOrder(
            order_no=po_no,
            supplier_id=data.get('supplier_id'),
            supplier_name=data.get('supplier_name', ''),
            order_date=datetime.now().date(),
            status=0,
            remark=f'接件单{order.receive_no}维修配件采购',
            created_by=user_id,
        )
        db.session.add(po_order)
        db.session.flush()

        for item in purchase_items:
            po_item = PurchaseOrderItem(
                order_id=po_order.id,
                product_id=item['product_id'],
                product_name=item['product_name'],
                specification=item['specification'],
                unit=item['unit_name'],
                quantity=int(item['quantity']),
                price=item['cost_price'],
                amount=item['quantity'] * item['cost_price'],
                remark=item['remark'],
            )
            db.session.add(po_item)
            item['purchase_order_item_id'] = po_item.id

    # 保存接件单配件明细
    all_items = out_items + purchase_items
    for item in all_items:
        part = ReceiveOrderPart(
            receive_order_id=order.id,
            product_id=item['product_id'],
            product_name=item['product_name'],
            product_code=item['product_code'],
            specification=item['specification'],
            unit_name=item['unit_name'],
            quantity=item['quantity'],
            unit_price=item['unit_price'],
            total_price=item['total_price'],
            cost_price=item['cost_price'],
            source=item['source'],
            inventory_out_item_id=item.get('inventory_out_item_id'),
            purchase_order_item_id=item.get('purchase_order_item_id'),
            status=item['status'],
            remark=item['remark'],
        )
        db.session.add(part)

    # 状态变更
    old_status = order.status
    order.status = 5
    if all_in_stock:
        content = f'领料完成（全部有库存），共{len(all_items)}项配件，状态变更为维修中'
    else:
        content = f'领料完成，{len(out_items)}项已出库，{len(purchase_items)}项已创建采购单，状态变更为维修中'

    add_ro_log(
        ro_id=order.id, action='领料/采购',
        old_status=old_status, new_status=order.status,
        content=content,
        operator_id=user_id, operator_name=user_name,
    )

    return {
        'status': order.status,
        'status_text': '维修中',
        'out_count': len(out_items),
        'purchase_count': len(purchase_items),
    }


# ============================================================
# 3. 外部报价流程（4-6 个相似函数共用）
# ============================================================

def external_quote_flow(order, target, items, user_id, user_name):
    """外部报价流程：根据 target 决定分支

    target:
      - 'quote': 内店报价（待报价 2 -> 待客户确认 3）[app.py 6026 行]
      - 'external_quote': 外店报价（送修外店 9 -> 外店已报价 10）[app.py 6814 行]
      - 'customer_quote': 给客户报价（外店已报价 10 -> 待客户确认 3）[app.py 6854 行]
    """
    from models.quote.order import QuoteOrder, QuoteOrderItem

    labor_cost = float(items.get('labor_cost', 0))
    material_cost = float(items.get('material_cost', 0))
    other_cost = float(items.get('other_cost', 0))

    old_status = order.status

    if target == 'quote':
        # 内店报价：创建 QuoteOrder + QuoteOrderItem
        order.quote_labor_cost = labor_cost
        order.quote_material_cost = material_cost
        order.quote_other_cost = other_cost
        order.quote_total = labor_cost + material_cost + other_cost
        order.total_amount = order.quote_total
        order.status = 3

        quote_items = items.get('items', [])
        if quote_items:
            last_quote = QuoteOrder.query.order_by(QuoteOrder.id.desc()).first()
            quote_no = generate_code('QO', last_quote.id if last_quote else 0)
            quote_order = QuoteOrder(
                quote_no=quote_no,
                customer_id=order.customer_id,
                customer_name=order.customer_name,
                customer_phone=order.customer_phone,
                total_amount=order.quote_total,
                status=0,
                related_type='receive_order',
                related_id=order.id,
                created_by=user_id,
            )
            db.session.add(quote_order)
            db.session.flush()

            for item in quote_items:
                qi = QuoteOrderItem(
                    quote_id=quote_order.id,
                    product_name=item.get('product_name', ''),
                    specification=item.get('specification', ''),
                    brand=item.get('brand', ''),
                    unit=item.get('unit', ''),
                    quantity=item.get('quantity', 1),
                    unit_price=item.get('unit_price', 0),
                    subtotal=float(item.get('quantity', 1)) * float(item.get('unit_price', 0)),
                    remark=item.get('remark', ''),
                )
                db.session.add(qi)

        new_status = 3
        action = '生成报价'
        content = (
            f'报价：人工费 {labor_cost}，材料费 {material_cost}，'
            f'其他费用 {other_cost}，合计 {order.quote_total}'
        )

    elif target == 'external_quote':
        # 外店报价
        order.external_quote = float(items.get('external_quote', 0))
        order.status = 10
        new_status = 10
        action = '外店报价'
        content = f'外店报价：{order.external_quote}元'

    elif target == 'customer_quote':
        # 给客户报价（外店流程）
        order.quote_labor_cost = labor_cost
        order.quote_material_cost = material_cost
        order.quote_other_cost = other_cost
        order.quote_total = labor_cost + material_cost + other_cost
        order.total_amount = order.quote_total
        order.status = 3
        new_status = 3
        action = '给客户报价'
        content = (
            f'给客户报价（外店流程）：人工费 {labor_cost}，材料费 {material_cost}，'
            f'其他费用 {other_cost}，合计 {order.quote_total}'
        )
    else:
        raise ValueError(f'未知的报价 target: {target}')

    add_ro_log(
        ro_id=order.id, action=action,
        old_status=old_status, new_status=new_status,
        content=content,
        operator_id=user_id, operator_name=user_name,
    )

    return {
        'status': new_status,
        'quote_total': float(order.quote_total) if order.quote_total is not None else None,
    }


# ============================================================
# 4. 完结（取件完成 + 财务记录，原 app.py 6701 行）
# ============================================================

def complete_receiveorder(order, data, user_id, user_name):
    """取件完成（待结算 8 -> 已完成 9）。"""
    from models.finance.account import FinanceAccount, FinanceRecord

    old_status = order.status
    order.status = 9
    order.complete_time = datetime.now()

    account_id = data.get('account_id')
    account = FinanceAccount.query.get(account_id) if account_id else None
    if account:
        balance_before = float(account.balance or 0)
        amount = float(order.quote_total or order.total_amount or 0)
        account.balance = balance_before + amount

        record = FinanceRecord(
            account_id=account.id,
            account_name=account.account_name,
            record_type=1,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_before + amount,
            related_type='receive_order',
            related_id=order.id,
            related_no=order.receive_no,
            remark=f'接件单结算：{order.receive_no}',
            created_by=user_id,
        )
        db.session.add(record)
        db.session.flush()
        order.finance_record_id = record.id
        order.paid_amount = amount

    add_ro_log(
        ro_id=order.id, action='取件完成',
        old_status=old_status, new_status=order.status,
        content=f'客户取件完成，接件单结算金额：{order.paid_amount or order.quote_total or order.total_amount}',
        operator_id=user_id, operator_name=user_name,
    )

    return {'status': order.status, 'status_text': '已完成'}


# ============================================================
# 5. 取消接件单（原 app.py 7067 行）
# ============================================================

def cancel_receiveorder(order, reason, user_id, user_name):
    """取消接件单：任意状态 -> 已取消 15（除已完成 9 和已取消 15）。"""
    if order.status == 9:
        raise ValueError('已完成的接件单不能取消')
    if order.status == 15:
        raise ValueError('接件单已取消，请勿重复操作')

    old_status = order.status
    order.status = 15

    add_ro_log(
        ro_id=order.id, action='取消',
        old_status=old_status, new_status=15,
        content=f'接件单已取消，原因：{reason or ""}',
        operator_id=user_id, operator_name=user_name,
    )

    return {'status': 15, 'status_text': '已取消'}