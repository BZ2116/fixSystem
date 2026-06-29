"""工单业务服务层。

把工单模块的核心业务（结算 / 配件分配 / 报价 / 取消 / 完成 / 通用状态变更）
从路由层抽到这里。Service 层只放业务逻辑，不接受 Flask request 对象，
不读 request.json / request.args，参数由调用方传入。

每个函数都假定自己处于 db.session 事务中（由路由层负责 commit/rollback）。
"""
import logging
from datetime import datetime

from extensions import db
from app.utils import generate_code

logger = logging.getLogger(__name__)


# ============================================================
# 日志辅助（与 app.py 1320 行 add_wo_log 等价）
# ============================================================

def add_wo_log(wo_id, action, old_status, new_status, content,
               operator_id=None, operator_name=None):
    """添加工单操作日志。"""
    from models.workorder import WorkOrderLog
    log = WorkOrderLog(
        wo_id=wo_id,
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
# 工单号生成
# ============================================================

def _generate_wo_no():
    """生成工单号：WO + YYYYMMDD + 4位序号。"""
    from models.workorder import WorkOrder
    today_str = datetime.now().strftime('%Y%m%d')
    today_prefix = f'WO{today_str}'
    last_order = WorkOrder.query.filter(
        WorkOrder.wo_no.like(f'{today_prefix}%')
    ).order_by(WorkOrder.id.desc()).first()
    if last_order:
        seq = int(last_order.wo_no[-4:]) + 1
    else:
        seq = 1
    return f'{today_prefix}{str(seq).zfill(4)}'


# ============================================================
# 1. 通用状态变更
# ============================================================

def change_workorder_status(order, new_status, content, operator_id, operator_name,
                            assigned_user_id=None):
    """通用状态变更（含状态流转合法性校验）。

    特殊状态处理：
    - 3(待备件) + assigned_user_id: 设置 assigned_user
    - 8(待结算): 自动计算 parts_cost + total_cost
    - 9(已完成): 写入 actual_time
    """
    from app.blueprints.workorder import WO_STATUS_MAP, WO_STATUS_TRANSITIONS

    if new_status is None:
        raise ValueError('状态不能为空')

    old_status = order.status
    allowed = WO_STATUS_TRANSITIONS.get(old_status, [])
    if new_status not in allowed:
        raise ValueError(
            f'不允许从【{WO_STATUS_MAP.get(old_status, "未知")}】'
            f'变更为【{WO_STATUS_MAP.get(new_status, "未知")}】'
        )

    order.status = new_status
    order.status_name = WO_STATUS_MAP.get(new_status, '')

    if new_status == 3 and assigned_user_id:  # 开始处理
        from models.system import SysUser
        order.assigned_user_id = assigned_user_id
        user_obj = SysUser.query.get(assigned_user_id)
        if user_obj:
            order.assigned_user_name = user_obj.real_name or user_obj.username
        order.assigned_time = datetime.now()
    elif new_status == 8:  # 待结算
        from models.workorder import WorkOrderPart
        parts = WorkOrderPart.query.filter_by(wo_id=order.id, status=1).all()
        parts_cost = sum(float(p.total_price or 0) for p in parts)
        order.parts_cost = parts_cost
        order.total_cost = (
            float(order.labor_cost or 0) + parts_cost
            + float(order.material_cost or 0) + float(order.transport_cost or 0)
        )
    elif new_status == 9:  # 已完成
        order.actual_time = datetime.now()

    add_wo_log(
        wo_id=order.id,
        action='状态变更',
        old_status=old_status,
        new_status=new_status,
        content=content or f'状态从【{WO_STATUS_MAP.get(old_status, "未知")}】'
                           f'变更为【{WO_STATUS_MAP.get(new_status, "未知")}】',
        operator_id=operator_id,
        operator_name=operator_name,
    )
    return old_status


# ============================================================
# 2. 配件分配（领用）
# ============================================================

def allocate_parts(order, parts_list, user_id, user_name):
    """领用配件 - 检查库存，有库存出库，无库存创建采购预订单。

    返回 dict {allocated: [...], need_purchase: [...]}。
    """
    from models.product import ProductInfo
    from models.inventory import InventoryStock, InventoryOut, InventoryOutItem
    from models.inventory.flow import PreOrder, PreOrderItem
    from models.workorder import WorkOrderPart
    from app.blueprints.workorder import WO_STATUS_MAP

    allocated_parts = []
    need_purchase_parts = []

    for item in parts_list:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 1)
        if not product_id:
            continue

        product = ProductInfo.query.get(product_id)
        if not product:
            continue

        # 检查库存
        stock = InventoryStock.query.filter_by(product_id=product_id).first()
        available_qty = float(stock.available_quantity or 0) if stock else 0

        if available_qty >= quantity:
            # 有库存：创建出库单(out_type=2维修领料)
            last_out = InventoryOut.query.order_by(InventoryOut.id.desc()).first()
            out_no = generate_code('CK', last_out.id if last_out else 0)

            out_order = InventoryOut(
                out_no=out_no,
                out_type=2,
                customer_id=order.customer_id,
                customer_name=order.customer_name,
                total_quantity=quantity,
                total_amount=float(product.sale_price or 0) * quantity,
                status=1,
                related_order_id=order.id,
                related_order_no=order.wo_no,
                remark=f'工单{order.wo_no}维修领料',
                created_by=user_id,
            )
            db.session.add(out_order)
            db.session.flush()

            out_item = InventoryOutItem(
                out_id=out_order.id,
                product_id=product_id,
                product_code=product.product_code,
                product_name=product.product_name,
                specification=product.specification,
                unit_name=product.unit_name,
                quantity=quantity,
                unit_price=product.sale_price,
                total_price=float(product.sale_price or 0) * quantity,
                cost_price=product.cost_price,
            )
            db.session.add(out_item)

            # 锁定库存
            if stock:
                stock.frozen_quantity = float(stock.frozen_quantity or 0) + quantity
                stock.available_quantity = float(stock.quantity or 0) - float(stock.frozen_quantity or 0)

            wo_part = WorkOrderPart(
                wo_id=order.id,
                product_id=product_id,
                product_name=product.product_name,
                product_code=product.product_code,
                specification=product.specification,
                quantity=quantity,
                unit_price=product.sale_price,
                total_price=float(product.sale_price or 0) * quantity,
                cost_price=product.cost_price,
                is_own=1,
                status=1,
                remark='维修领料',
            )
            db.session.add(wo_part)

            allocated_parts.append({'product_name': product.product_name,
                                    'quantity': quantity, 'source': '库存'})
        else:
            need_purchase_parts.append({
                'product_id': product_id,
                'product_name': product.product_name,
                'product_code': product.product_code,
                'quantity': quantity,
                'available': available_qty,
            })

            wo_part = WorkOrderPart(
                wo_id=order.id,
                product_id=product_id,
                product_name=product.product_name,
                product_code=product.product_code,
                specification=product.specification,
                quantity=quantity,
                unit_price=product.purchase_price,
                total_price=float(product.purchase_price or 0) * quantity,
                cost_price=product.cost_price,
                is_own=1,
                status=0,
                remark='待采购',
            )
            db.session.add(wo_part)

    # 需采购：创建预订单
    if need_purchase_parts:
        last_pre = PreOrder.query.order_by(PreOrder.id.desc()).first()
        pre_no = generate_code('YD', last_pre.id if last_pre else 0)

        total_amount = 0
        pre_order = PreOrder(
            pre_no=pre_no,
            pre_type=1,
            total_quantity=sum(p['quantity'] for p in need_purchase_parts),
            total_amount=0,
            status=0,
            remark=f'工单{order.wo_no}配件采购预订单',
            created_by=user_id,
        )
        db.session.add(pre_order)
        db.session.flush()

        for p in need_purchase_parts:
            product = ProductInfo.query.get(p['product_id'])
            price = float(product.purchase_price or 0) if product else 0
            total_amount += price * p['quantity']

            pre_item = PreOrderItem(
                pre_id=pre_order.id,
                product_id=p['product_id'],
                product_code=p['product_code'],
                product_name=p['product_name'],
                quantity=p['quantity'],
                unit_price=price,
                total_price=price * p['quantity'],
                remark=f'工单{order.wo_no}需要',
            )
            db.session.add(pre_item)

        pre_order.total_amount = total_amount
        order.related_purchase_id = pre_order.id

    add_wo_log(
        wo_id=order.id,
        action='领用配件',
        old_status=order.status,
        new_status=order.status,
        content=f'领用配件{len(allocated_parts)}项（库存），{len(need_purchase_parts)}项需采购',
        operator_id=user_id,
        operator_name=user_name,
    )

    # 没有需采购的配件：自动进入"待上门"
    if not need_purchase_parts:
        old_status = order.status
        order.status = 3
        order.status_name = WO_STATUS_MAP.get(3, '待上门')
        add_wo_log(
            wo_id=order.id,
            action='状态变更',
            old_status=old_status,
            new_status=3,
            content='配件已全部从库存领取，状态变更为【待上门】',
            operator_id=user_id,
            operator_name=user_name,
        )

    return {
        'allocated': allocated_parts,
        'need_purchase': need_purchase_parts,
    }


# ============================================================
# 3. 工单结算（226 行核心逻辑，事务完整性原样保留）
# ============================================================

def settle_workorder(order, data, user_id, user_name):
    """工单结算 - 计算费用、创建销售单和财务/应收记录，状态 4/5 -> 6。
    自动计算已用备件和未用备件，未用备件自动退回库存。
    支持现金结算（直接入账）和签单结算（生成应收）。

    返回 dict 给路由层做响应。
    """
    from models.workorder import WorkOrderPart
    from models.sales import SalesOrder
    from models.finance import FinanceAccount, FinanceRecord, FinanceReceivable
    from app.blueprints.workorder import WO_STATUS_MAP

    if order.status not in (4, 5):
        raise ValueError(
            f'当前状态【{WO_STATUS_MAP.get(order.status, "未知")}】'
            f'不允许结算，需为处理中或待结算'
        )

    settle_type = data.get('settle_type', 'cash')

    # ----- 计算已用 / 未用备件 -----
    parts = WorkOrderPart.query.filter_by(wo_id=order.id).all()
    used_parts = []
    unused_parts = []
    parts_cost_total = 0.0

    for part in parts:
        used_qty = float(
            data.get(f'used_qty_{part.id}', part.used_quantity or part.quantity or 0)
        )
        unused_qty = float(part.quantity or 0) - used_qty
        part.used_quantity = used_qty

        if used_qty > 0:
            part.status = 1  # 已用
            used_parts.append({
                'product_name': part.product_name,
                'specification': part.specification,
                'quantity': used_qty,
                'unit_price': float(part.unit_price or 0),
                'total': used_qty * float(part.unit_price or 0),
            })
            parts_cost_total += used_qty * float(part.unit_price or 0)

        if unused_qty > 0:
            part.status = 2  # 已退
            if part.is_own == 1 and part.product_id:
                try:
                    from models.product import ProductInfo as Product
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

    # ----- 更新费用信息 -----
    labor_hours = data.get('labor_hours')
    labor_unit_price = data.get('labor_unit_price')
    labor_cost = data.get('labor_cost')
    material_cost = data.get('material_cost')
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

    if material_cost is not None:
        order.material_cost = material_cost

    # ----- 总费用 -----
    total = (
        float(order.labor_cost or 0)
        + float(order.parts_cost or 0)
        + float(order.material_cost or 0)
        + float(order.transport_cost or 0)
        + float(other_cost or 0)
        + float(order.service_fee or 0)
    )
    order.total_cost = total

    # ----- 创建销售单 -----
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
        remark=f'工单{order.wo_no}结算生成',
        created_by=user_id,
    )
    db.session.add(sales_order)
    db.session.flush()
    order.related_sales_id = sales_order.id

    # ----- 财务 / 应收 -----
    finance_record = None
    receivable_record = None

    if settle_type == 'cash' and account_id:
        account = FinanceAccount.query.get(account_id)
        if account:
            balance_before = float(account.balance or 0)
            account.balance = balance_before + total
            finance_record = FinanceRecord(
                account_id=account.id,
                account_name=account.account_name,
                record_type=1,
                amount=total,
                balance_before=balance_before,
                balance_after=balance_before + total,
                related_type='work_order',
                related_id=order.id,
                related_no=order.wo_no,
                remark=f'工单现金结算：{order.wo_no}',
                created_by=user_id,
            )
            db.session.add(finance_record)
            db.session.flush()
            order.related_finance_id = finance_record.id
    elif settle_type == 'credit':
        today = datetime.now().strftime('%Y%m%d')
        prefix_ys = 'YS' + today
        last_receivable = (
            FinanceReceivable.query
            .filter(FinanceReceivable.receivable_no.like(prefix_ys + '%'))
            .order_by(FinanceReceivable.receivable_no.desc())
            .first()
        )
        if last_receivable and last_receivable.receivable_no and len(last_receivable.receivable_no) > len(prefix_ys):
            seq_ys = int(last_receivable.receivable_no[len(prefix_ys):]) + 1
        else:
            seq_ys = 1
        receivable_no = prefix_ys + str(seq_ys).zfill(4)
        receivable_record = FinanceReceivable(
            receivable_no=receivable_no,
            related_type='work_order',
            related_id=order.id,
            related_no=order.wo_no,
            customer_id=order.customer_id,
            customer_name=order.customer_name,
            total_amount=total,
            received_amount=0,
            remaining_amount=total,
            status=0,
            remark=f'工单签单结算：{order.wo_no}',
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.session.add(receivable_record)
        db.session.flush()

    # ----- 结算信息 + 状态 -----
    order.settlement_status = 1
    order.settlement_account_id = account_id if settle_type == 'cash' else None
    order.settlement_time = datetime.now()
    order.settlement_type = settle_type
    old_status = order.status
    order.status = 6
    order.status_name = '已完成'
    order.actual_time = datetime.now()

    # ----- 日志 -----
    settle_type_text = '现金结算' if settle_type == 'cash' else '签单结算'
    log_content = (
        f'工单{settle_type_text}，总费用：{total}元，'
        f'人工费：{order.labor_cost}，配件费：{order.parts_cost}，'
        f'材料费：{order.material_cost}'
    )
    if used_parts:
        used_str = '、'.join([f'{p["product_name"]}x{p["quantity"]}' for p in used_parts])
        log_content += f'。已用配件：{used_str}'
    if unused_parts:
        unused_str = '、'.join([f'{p["product_name"]}x{p["quantity"]}' for p in unused_parts])
        log_content += f'。已退回配件：{unused_str}'
    if settle_type == 'credit' and receivable_record:
        log_content += f'。生成应收单：{receivable_no}'

    add_wo_log(
        wo_id=order.id,
        action='结算',
        old_status=old_status,
        new_status=6,
        content=log_content,
        operator_id=user_id,
        operator_name=user_name,
    )

    return {
        'status': 6,
        'status_text': '已完成',
        'total_cost': total,
        'parts_cost': order.parts_cost,
        'used_parts': used_parts,
        'unused_parts': unused_parts,
        'sales_order_id': sales_order.id,
        'finance_record_id': finance_record.id if finance_record else None,
    }


# ============================================================
# 4. 工单报价
# ============================================================

def workorder_quote(order, data, user_id, user_name):
    """工单报价 - 提交报价费用和客户确认状态。

    状态 3(待备件) / 4(处理中) -> 5(待审核) 客户确认
                            -> 7(已取消) 客户拒绝
    """
    from models.workorder import WorkOrderQuoteItem
    from app.blueprints.workorder import WO_STATUS_MAP

    if order.status not in (3, 4):
        raise ValueError('当前工单状态不允许报价')

    labor_cost = float(data.get('labor_cost', 0) or 0)
    parts_cost = float(data.get('parts_cost', 0) or 0)
    other_cost = float(data.get('other_cost', 0) or 0)
    total_cost = float(data.get('total_cost', 0) or 0)
    items = data.get('items', [])
    customer_confirm = data.get('customer_confirm', 1)
    reject_reason = data.get('reject_reason', '')

    order.labor_cost = labor_cost
    order.parts_cost = parts_cost
    order.other_cost = other_cost
    order.total_cost = total_cost

    # 替换报价明细
    WorkOrderQuoteItem.query.filter_by(work_order_id=order.id).delete()
    for item in items:
        quote_item = WorkOrderQuoteItem(
            work_order_id=order.id,
            product_name=item.get('product_name', ''),
            spec=item.get('spec', ''),
            unit=item.get('unit', ''),
            quantity=float(item.get('quantity', 1) or 1),
            unit_price=float(item.get('unit_price', 0) or 0),
            subtotal=float(item.get('subtotal', 0) or 0),
        )
        db.session.add(quote_item)

    if customer_confirm == 1:
        order.status = 5
        add_wo_log(
            wo_id=order.id, action='客户确认报价',
            old_status=order.status, new_status=5,
            content=f'报价总额: ¥{total_cost:.2f}',
            operator_id=user_id, operator_name=user_name,
        )
    else:
        order.status = 7
        add_wo_log(
            wo_id=order.id, action='客户拒绝报价',
            old_status=order.status, new_status=7,
            content=f'拒绝原因: {reject_reason}',
            operator_id=user_id, operator_name=user_name,
        )

    return {
        'status': order.status,
        'status_text': WO_STATUS_MAP.get(order.status, '未知'),
        'total_cost': total_cost,
    }


# ============================================================
# 5. 取消工单
# ============================================================

def cancel_workorder(order, reason, user_id, user_name):
    """取消工单。状态 9(已结算) / 10(?) 不允许取消（与原 app.py 一致）。"""
    from app.blueprints.workorder import WO_STATUS_MAP

    if order.status in (9, 10):
        raise ValueError(
            f'当前状态【{WO_STATUS_MAP.get(order.status, "未知")}】不允许取消'
        )

    old_status = order.status
    order.status = 10
    order.status_name = '已取消'
    add_wo_log(
        wo_id=order.id,
        action='取消工单',
        old_status=old_status,
        new_status=10,
        content=f'取消工单，原因：{reason}' if reason else '取消工单',
        operator_id=user_id,
        operator_name=user_name,
    )
    return {'status': 10, 'status_text': '已取消'}


# ============================================================
# 6. 完工提交
# ============================================================

def complete_workorder(order, data, user_id, user_name):
    """完工提交 - 状态 2(处理中) -> 3(待结算)。"""
    from app.blueprints.workorder import WO_STATUS_MAP
    import json as _json

    if order.status != 2:
        raise ValueError(
            f'当前状态【{WO_STATUS_MAP.get(order.status, "未知")}】'
            f'不允许完工提交，需为处理中'
        )

    if 'finish_report' in data:
        order.finish_report = data['finish_report']
    if 'finish_photos' in data:
        photos = data['finish_photos']
        order.finish_photos = _json.dumps(photos, ensure_ascii=False) \
            if isinstance(photos, (list, dict)) else photos
    if 'test_result' in data:
        order.test_result = data['test_result']
    if 'test_remark' in data:
        order.test_remark = data['test_remark']

    old_status = order.status
    order.status = 3
    order.status_name = '待结算'

    test_result = data.get('test_result', 0)
    add_wo_log(
        wo_id=order.id,
        action='完工提交',
        old_status=old_status,
        new_status=3,
        content=f'完工提交，测试结果：{["待测试", "通过", "未通过"][test_result]}',
        operator_id=user_id,
        operator_name=user_name,
    )
    return {'status': 3, 'status_text': '待结算'}
