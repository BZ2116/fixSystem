"""工单状态机动作蓝图（拆分自 workorder.py）。

包含 13 个状态机路由：
- /api/workorders/<id>/status          通用状态变更
- /api/workorders/<id>/dispatch        派单
- /api/workorders/<id>/accept          接单
- /api/workorders/<id>/allocate-parts  领用配件
- /api/workorders/<id>/finish          完工提交
- /api/workorders/<id>/settle          结算（226行核心）
- /api/workorders/<id>/to-quote        转报价单
- /api/workorders/<id>/quote           工单报价
- /api/workorders/<id>/to-purchase     转采购预订单
- /api/workorders/<id>/to-sales        转销售单
- /api/workorders/<id>/return-visit    上门送回
- /api/workorders/<id>/acceptance      客户验收
- /api/workorders/<id>/cancel          取消工单

业务逻辑放在 backend/app/services/workorder_service.py。
本文件只做参数校验、状态检查、事务包装。
"""
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from app.services.workorder_service import (
    add_wo_log,
    change_workorder_status,
    allocate_parts,
    settle_workorder,
    workorder_quote,
    cancel_workorder,
    complete_workorder,
)
from app.blueprints.workorder import (
    WO_STATUS_MAP,
    _get_current_user_name,
    _auto_dispatch_engineer,
)

logger = logging.getLogger(__name__)

bp = Blueprint('workorder_actions', __name__)


# ============================================
# 1. 通用状态变更
# ============================================

@bp.route('/api/workorders/<int:id>/status', methods=['POST'])
@jwt_required()
def change_status(id):
    """通用状态变更接口 - 验证状态流转合法性"""
    try:
        from models.workorder import WorkOrder
        order = WorkOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '工单不存在'}), 404

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()
        new_status = data.get('status')
        content = data.get('content', '')

        try:
            change_workorder_status(
                order, new_status, content, user_id, user_name,
                assigned_user_id=data.get('assigned_user_id'),
            )
        except ValueError as e:
            return jsonify({'code': 400, 'message': str(e)}), 400

        db.session.commit()
        return jsonify({'code': 200, 'message': '状态变更成功', 'data': {
            'status': new_status,
            'status_text': WO_STATUS_MAP.get(new_status, '未知'),
        }})
    except Exception as e:
        db.session.rollback()
        logger.error(f'状态变更失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'状态变更失败: {str(e)}'}), 500


# ============================================
# 2. 派单
# ============================================

@bp.route('/api/workorders/<int:id>/dispatch', methods=['POST'])
@jwt_required()
def dispatch_workorder(id):
    """派单 - 支持手动选择工程师和自动派单"""
    try:
        from models.workorder import WorkOrder
        from models.dispatch import DispatchRecord, StaffStatus
        from models.system import SysUser

        order = WorkOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '工单不存在'}), 404

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        if order.status != 0:
            return jsonify({'code': 400, 'message': f'当前状态【{WO_STATUS_MAP.get(order.status, "未知")}】不允许派单'}), 400

        dispatch_type = data.get('dispatch_type', 'manual')
        staff_id = data.get('staff_id') or data.get('assigned_user_id')
        staff_name = data.get('staff_name')

        if dispatch_type == 'auto' and not staff_id:
            recommendations = _auto_dispatch_engineer(order.wo_type)
            if not recommendations:
                return jsonify({'code': 400, 'message': '没有可用的在线工程师'}), 400
            staff_id = recommendations[0]['staff_id']
            staff_name = recommendations[0]['staff_name']

        if dispatch_type == 'manual' and not staff_id:
            return jsonify({'code': 400, 'message': '请选择工程师'}), 400

        staff_user = SysUser.query.get(staff_id)
        if not staff_user:
            return jsonify({'code': 404, 'message': '工程师不存在'}), 404
        if not staff_name:
            staff_name = staff_user.real_name or staff_user.username

        dispatch_record = DispatchRecord(
            wo_id=id, dispatch_type=dispatch_type,
            dispatcher_id=user_id, dispatcher_name=user_name,
            staff_id=staff_id, staff_name=staff_name,
            staff_phone=staff_user.phone, accept_status=1,
        )
        db.session.add(dispatch_record)

        staff_status = StaffStatus.query.filter_by(staff_id=staff_id).first()
        if staff_status:
            staff_status.current_wo_id = id
            staff_status.today_count = (staff_status.today_count or 0) + 1
        else:
            db.session.add(StaffStatus(
                staff_id=staff_id, staff_name=staff_name,
                online_status=1, current_wo_id=id, today_count=1,
            ))

        old_status = order.status
        order.status = 1
        order.status_name = '已派单'
        order.assigned_user_id = staff_id
        order.assigned_user_name = staff_name
        order.assigned_time = datetime.now()
        order.auto_dispatch = 1 if dispatch_type == 'auto' else 0

        add_wo_log(
            wo_id=id, action='派单',
            old_status=old_status, new_status=1,
            content=f'{"自动" if dispatch_type == "auto" else "手动"}派单给工程师【{staff_name}】',
            operator_id=user_id, operator_name=user_name,
        )

        db.session.commit()
        return jsonify({'code': 200, 'message': '派单成功', 'data': {
            'staff_id': staff_id, 'staff_name': staff_name,
            'dispatch_type': dispatch_type, 'status': 1, 'status_text': '已派单',
        }})
    except Exception as e:
        db.session.rollback()
        logger.error(f'派单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'派单失败: {str(e)}'}), 500


# ============================================
# 3. 接单
# ============================================

@bp.route('/api/workorders/<int:id>/accept', methods=['POST'])
@jwt_required()
def accept_workorder(id):
    """工程师接单 - 状态从1(已派单)变为2(处理中)"""
    try:
        from models.workorder import WorkOrder
        order = WorkOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '工单不存在'}), 404

        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        if order.status != 1:
            return jsonify({'code': 400, 'message': f'当前状态【{WO_STATUS_MAP.get(order.status, "未知")}】不允许接单，需为已派单'}), 400

        old_status = order.status
        order.status = 2
        order.status_name = '处理中'
        order.accept_time = datetime.now()

        add_wo_log(
            wo_id=id, action='接单',
            old_status=old_status, new_status=2,
            content=f'工程师【{user_name}】已接单，开始处理',
            operator_id=user_id, operator_name=user_name,
        )

        db.session.commit()
        return jsonify({'code': 200, 'message': '接单成功', 'data': {
            'status': 2, 'status_text': '处理中',
            'accept_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }})
    except Exception as e:
        db.session.rollback()
        logger.error(f'接单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'接单失败: {str(e)}'}), 500


# ============================================
# 4. 领用配件
# ============================================

@bp.route('/api/workorders/<int:id>/allocate-parts', methods=['POST'])
@jwt_required()
def allocate_parts_route(id):
    """领用配件 - 检查库存，有库存出库，无库存创建采购预订单"""
    try:
        from models.workorder import WorkOrder
        order = WorkOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '工单不存在'}), 404

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()
        parts_list = data.get('parts', [])

        if not parts_list:
            return jsonify({'code': 400, 'message': '配件列表不能为空'}), 400

        result = allocate_parts(order, parts_list, user_id, user_name)
        db.session.commit()
        return jsonify({'code': 200, 'message': '配件分配完成', 'data': result})
    except Exception as e:
        db.session.rollback()
        logger.error(f'领用配件失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'领用配件失败: {str(e)}'}), 500


# ============================================
# 5. 完工提交
# ============================================

@bp.route('/api/workorders/<int:id>/finish', methods=['POST'])
@jwt_required()
def finish_workorder(id):
    """完工提交 - 提交完工报告、照片、测试结果，状态从2(处理中)变为3(待结算)"""
    try:
        from models.workorder import WorkOrder
        order = WorkOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '工单不存在'}), 404

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        try:
            result = complete_workorder(order, data, user_id, user_name)
        except ValueError as e:
            return jsonify({'code': 400, 'message': str(e)}), 400

        db.session.commit()
        return jsonify({'code': 200, 'message': '完工提交成功', 'data': result})
    except Exception as e:
        db.session.rollback()
        logger.error(f'完工提交失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'完工提交失败: {str(e)}'}), 500


# ============================================
# 6. 结算（226 行核心逻辑）
# ============================================

@bp.route('/api/workorders/<int:id>/settle', methods=['POST'])
@jwt_required()
def settle_workorder_route(id):
    """结算 - 计算费用、创建销售单和财务/应收记录。"""
    try:
        from models.workorder import WorkOrder
        order = WorkOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '工单不存在'}), 404

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        try:
            result = settle_workorder(order, data, user_id, user_name)
        except ValueError as e:
            return jsonify({'code': 400, 'message': str(e)}), 400

        db.session.commit()
        return jsonify({'code': 200, 'message': '结算成功', 'data': result})
    except Exception as e:
        db.session.rollback()
        logger.error(f'结算失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'结算失败: {str(e)}'}), 500


# ============================================
# 7. 转报价单
# ============================================

@bp.route('/api/workorders/<int:id>/to-quote', methods=['POST'])
@jwt_required()
def workorder_to_quote(id):
    """转报价单"""
    try:
        from models.workorder import WorkOrder
        from models.quote import QuoteOrder
        from app.utils import generate_code

        order = WorkOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '工单不存在'}), 404

        data = request.get_json() if request.is_json else {}
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        last_qo = QuoteOrder.query.order_by(QuoteOrder.id.desc()).first()
        quote_no = generate_code('QT', last_qo.id if last_qo else 0)

        quote_order = QuoteOrder(
            quote_no=quote_no,
            customer_id=order.customer_id,
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            address=order.customer_address,
            quote_date=datetime.now().date(),
            total_amount=data.get('total_amount', float(order.estimated_cost or 0)),
            remark=f'从工单{order.wo_no}转来',
            related_type='work_order',
            related_id=id,
            created_by=user_id,
        )
        db.session.add(quote_order)
        db.session.flush()
        order.related_quote_id = quote_order.id

        add_wo_log(
            wo_id=id, action='转报价单',
            old_status=order.status, new_status=order.status,
            content=f'转报价单，报价单号：{quote_no}',
            operator_id=user_id, operator_name=user_name,
        )

        db.session.commit()
        return jsonify({'code': 200, 'message': '转报价单成功',
                        'data': {'quote_id': quote_order.id, 'quote_no': quote_no}})
    except Exception as e:
        db.session.rollback()
        logger.error(f'转报价单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'转报价单失败: {str(e)}'}), 500


# ============================================
# 8. 工单报价
# ============================================

@bp.route('/api/workorders/<int:id>/quote', methods=['POST'])
@jwt_required()
def workorder_quote_route(id):
    """工单报价 - 提交报价费用和客户确认状态"""
    try:
        from models.workorder import WorkOrder
        order = WorkOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '工单不存在'}), 404

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        try:
            result = workorder_quote(order, data, user_id, user_name)
        except ValueError as e:
            return jsonify({'code': 400, 'message': str(e)}), 400

        db.session.commit()
        return jsonify({'code': 200, 'message': '报价提交成功', 'data': result})
    except Exception as e:
        db.session.rollback()
        logger.error(f'工单报价失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'报价失败: {str(e)}'}), 500


# ============================================
# 9. 转采购预订单
# ============================================

@bp.route('/api/workorders/<int:id>/to-purchase', methods=['POST'])
@jwt_required()
def workorder_to_purchase(id):
    """转采购预订单"""
    try:
        from models.workorder import WorkOrder
        from models.inventory import PreOrder, PreOrderItem
        from models.product import ProductInfo
        from app.utils import generate_code

        order = WorkOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '工单不存在'}), 404

        data = request.get_json() if request.is_json else {}
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        last_pre = PreOrder.query.order_by(PreOrder.id.desc()).first()
        pre_no = generate_code('YD', last_pre.id if last_pre else 0)

        items = data.get('items', [])
        total_amount = 0
        total_quantity = 0

        pre_order = PreOrder(
            pre_no=pre_no, pre_type=1,
            total_quantity=0, total_amount=0, status=0,
            remark=f'从工单{order.wo_no}转来',
            created_by=user_id,
        )
        db.session.add(pre_order)
        db.session.flush()

        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            unit_price = item.get('unit_price', 0)
            product = ProductInfo.query.get(product_id) if product_id else None

            total_amount += float(unit_price) * int(quantity)
            total_quantity += int(quantity)

            db.session.add(PreOrderItem(
                pre_id=pre_order.id,
                product_id=product_id,
                product_code=product.product_code if product else '',
                product_name=item.get('product_name', product.product_name if product else ''),
                quantity=quantity,
                unit_price=unit_price,
                total_price=float(unit_price) * int(quantity),
                remark=item.get('remark', ''),
            ))

        pre_order.total_quantity = total_quantity
        pre_order.total_amount = total_amount
        order.related_purchase_id = pre_order.id

        add_wo_log(
            wo_id=id, action='转采购预订单',
            old_status=order.status, new_status=order.status,
            content=f'转采购预订单，预订单号：{pre_no}',
            operator_id=user_id, operator_name=user_name,
        )

        db.session.commit()
        return jsonify({'code': 200, 'message': '转采购预订单成功',
                        'data': {'pre_order_id': pre_order.id, 'pre_no': pre_no}})
    except Exception as e:
        db.session.rollback()
        logger.error(f'转采购预订单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'转采购预订单失败: {str(e)}'}), 500


# ============================================
# 10. 转销售单
# ============================================

@bp.route('/api/workorders/<int:id>/to-sales', methods=['POST'])
@jwt_required()
def workorder_to_sales(id):
    """转销售单"""
    try:
        from models.workorder import WorkOrder
        from models.sales import SalesOrder
        from app.utils import generate_code

        order = WorkOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '工单不存在'}), 404

        data = request.get_json() if request.is_json else {}
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        last_so = SalesOrder.query.order_by(SalesOrder.id.desc()).first()
        so_no = generate_code('XS', last_so.id if last_so else 0)

        sales_order = SalesOrder(
            order_no=so_no,
            customer_id=order.customer_id,
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            customer_address=order.customer_address,
            order_date=datetime.now().date(),
            total_amount=data.get('total_amount', float(order.total_cost or 0)),
            total_quantity=data.get('total_quantity', 1),
            actual_amount=data.get('actual_amount', float(order.total_cost or 0)),
            paid_amount=data.get('paid_amount', 0),
            payment_method=data.get('payment_method'),
            delivery_method=data.get('delivery_method'),
            salesperson_id=user_id,
            salesperson_name=user_name,
            status=0,
            remark=f'从工单{order.wo_no}转来',
            created_by=user_id,
        )
        db.session.add(sales_order)
        db.session.flush()
        order.related_sales_id = sales_order.id

        add_wo_log(
            wo_id=id, action='转销售单',
            old_status=order.status, new_status=order.status,
            content=f'转销售单，销售单号：{so_no}',
            operator_id=user_id, operator_name=user_name,
        )

        db.session.commit()
        return jsonify({'code': 200, 'message': '转销售单成功',
                        'data': {'sales_order_id': sales_order.id, 'order_no': so_no}})
    except Exception as e:
        db.session.rollback()
        logger.error(f'转销售单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'转销售单失败: {str(e)}'}), 500


# ============================================
# 11. 上门送回
# ============================================

@bp.route('/api/workorders/<int:id>/return-visit', methods=['POST'])
@jwt_required()
def workorder_return_visit(id):
    """上门送回"""
    try:
        from models.workorder import WorkOrder
        order = WorkOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '工单不存在'}), 404

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        return_visit_time = data.get('return_visit_time')
        return_visit_result = data.get('return_visit_result')

        if return_visit_time:
            if isinstance(return_visit_time, str):
                order.return_visit_time = datetime.strptime(return_visit_time, '%Y-%m-%d %H:%M:%S')
            else:
                order.return_visit_time = return_visit_time
        if return_visit_result is not None:
            order.return_visit_result = return_visit_result

        add_wo_log(
            wo_id=id, action='上门送回',
            old_status=order.status, new_status=order.status,
            content=f'上门送回，时间：{return_visit_time}，结果：{return_visit_result or ""}',
            operator_id=user_id, operator_name=user_name,
        )

        db.session.commit()
        return jsonify({'code': 200, 'message': '上门送回记录成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'上门送回记录失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'上门送回记录失败: {str(e)}'}), 500


# ============================================
# 12. 客户验收
# ============================================

@bp.route('/api/workorders/<int:id>/acceptance', methods=['POST'])
@jwt_required()
def workorder_acceptance(id):
    """客户验收"""
    try:
        from models.workorder import WorkOrder
        order = WorkOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '工单不存在'}), 404

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        acceptance = data.get('customer_acceptance')
        sign = data.get('customer_acceptance_sign')

        if acceptance not in (1, 2):
            return jsonify({'code': 400, 'message': '验收结果必须是1(通过)或2(未通过)'}), 400

        order.customer_acceptance = acceptance
        order.customer_acceptance_time = datetime.now()
        if sign:
            order.customer_acceptance_sign = sign

        acceptance_text = '通过' if acceptance == 1 else '未通过'
        add_wo_log(
            wo_id=id, action='客户验收',
            old_status=order.status, new_status=order.status,
            content=f'客户验收{acceptance_text}',
            operator_id=user_id, operator_name=user_name,
        )

        db.session.commit()
        return jsonify({'code': 200, 'message': f'客户验收{acceptance_text}',
                        'data': {'customer_acceptance': acceptance}})
    except Exception as e:
        db.session.rollback()
        logger.error(f'客户验收失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'客户验收失败: {str(e)}'}), 500


# ============================================
# 13. 取消工单
# ============================================

@bp.route('/api/workorders/<int:id>/cancel', methods=['POST'])
@jwt_required()
def cancel_workorder_route(id):
    """取消工单"""
    try:
        from models.workorder import WorkOrder
        order = WorkOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '工单不存在'}), 404

        data = request.get_json() if request.is_json else {}
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()
        reason = data.get('reason', '')

        try:
            result = cancel_workorder(order, reason, user_id, user_name)
        except ValueError as e:
            return jsonify({'code': 400, 'message': str(e)}), 400

        db.session.commit()
        return jsonify({'code': 200, 'message': '工单已取消', 'data': result})
    except Exception as e:
        db.session.rollback()
        logger.error(f'取消工单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'取消工单失败: {str(e)}'}), 500
