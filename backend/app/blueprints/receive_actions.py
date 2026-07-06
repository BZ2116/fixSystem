"""接件单状态机动作蓝图（拆分自 receive.py）。

包含 14 个状态机路由：
- /api/receiveorders/<id>/detect            工程师检测
- /api/receiveorders/<id>/quote             内店报价
- /api/receiveorders/<id>/confirm           客户确认/拒绝
- /api/receiveorders/<id>/allocate          领料/采购
- /api/receiveorders/<id>/finish            完工提交
- /api/receiveorders/<id>/test              设备测试
- /api/receiveorders/<id>/notify            通知取件
- /api/receiveorders/<id>/settle            完工结算
- /api/receiveorders/<id>/complete          取件完成
- /api/receiveorders/<id>/external-send     送修外店
- /api/receiveorders/<id>/external-quote    外店报价
- /api/receiveorders/<id>/customer-quote   给客户报价（外店流程）
- /api/receiveorders/<id>/external-confirm  确认送修
- /api/receiveorders/<id>/external-return   取回设备
- /api/receiveorders/<id>/external-retest   外店取回测试
- /api/receiveorders/<id>/cancel            取消接件单

业务逻辑放在 backend/app/services/receive_service.py。
本文件只做参数校验、状态检查、事务包装。
"""
import json
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from app.security import permission
from app.services.receive_service import (
    add_ro_log,
    allocate_receiveorder,
    cancel_receiveorder,
    complete_receiveorder,
    external_quote_flow,
    settle_receiveorder,
)
from app.blueprints.receive import (
    RO_STATUS_MAP,
    _get_current_user_name,
)

logger = logging.getLogger(__name__)

bp = Blueprint('receive_actions', __name__)


# ============================================
# 1. 检测
# ============================================

@bp.route('/api/receiveorders/<int:id>/detect', methods=['POST'])
@permission('receive:edit')
@jwt_required()
def detect_receiveorder(id):
    """工程师检测：已登记(0) -> 待报价(2) 或 送修外店(9)"""
    try:
        from models.receive import ReceiveOrder

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        if order.status not in [0]:
            return jsonify({
                'code': 400,
                'message': f'当前状态【{RO_STATUS_MAP.get(order.status, "未知")}】不允许执行检测操作',
            }), 400

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        old_status = order.status
        can_repair = data.get('can_repair', True)

        order.detect_result = data.get('detect_result', '')
        order.detect_fault_reason = data.get('detect_fault_reason', '')
        order.detect_repair_plan = data.get('detect_repair_plan', '')
        detect_parts = data.get('detect_parts')
        if detect_parts is not None:
            order.detect_parts = (
                json.dumps(detect_parts, ensure_ascii=False)
                if isinstance(detect_parts, (list, dict)) else str(detect_parts)
            )

        if data.get('engineer_id'):
            order.engineer_id = data['engineer_id']
            order.engineer_name = data.get('engineer_name', '')

        if can_repair:
            order.status = 2
            content = (
                f'检测完成，可维修。故障原因：{order.detect_fault_reason}，'
                f'维修方案：{order.detect_repair_plan}'
            )
        else:
            order.status = 9
            content = f'检测完成，本店无法维修。故障原因：{order.detect_fault_reason}'

        add_ro_log(
            ro_id=id, action='工程师检测',
            old_status=old_status, new_status=order.status,
            content=content,
            operator_id=user_id, operator_name=user_name,
        )
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '检测完成',
            'data': {'status': order.status, 'status_text': RO_STATUS_MAP.get(order.status, '未知')},
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'检测失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'检测失败: {str(e)}'}), 500


# ============================================
# 2. 内店报价
# ============================================

@bp.route('/api/receiveorders/<int:id>/quote', methods=['POST'])
@permission('receive:edit')
@jwt_required()
def quote_receiveorder(id):
    """内店报价：待报价(2) -> 待客户确认(3)"""
    try:
        from models.receive import ReceiveOrder

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        if order.status not in [2]:
            return jsonify({
                'code': 400,
                'message': f'当前状态【{RO_STATUS_MAP.get(order.status, "未知")}】不允许执行报价操作',
            }), 400

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        try:
            result = external_quote_flow(
                order, target='quote', items=data,
                user_id=user_id, user_name=user_name,
            )
        except ValueError as e:
            return jsonify({'code': 400, 'message': str(e)}), 400

        db.session.commit()
        return jsonify({
            'code': 200,
            'message': '报价成功',
            'data': {
                'status': result['status'],
                'status_text': RO_STATUS_MAP.get(result['status'], '未知'),
                'quote_total': result['quote_total'],
            },
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'报价失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'报价失败: {str(e)}'}), 500


# ============================================
# 3. 客户确认/拒绝
# ============================================

@bp.route('/api/receiveorders/<int:id>/confirm', methods=['POST'])
@permission('receive:edit')
@jwt_required()
def confirm_receiveorder(id):
    """客户确认/拒绝报价：待客户确认(3) -> 待领料(4) 或 客户拒绝报价(17)"""
    try:
        from models.receive import ReceiveOrder

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        if order.status not in [3]:
            return jsonify({
                'code': 400,
                'message': f'当前状态【{RO_STATUS_MAP.get(order.status, "未知")}】不允许执行确认操作',
            }), 400

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()
        confirmed = data.get('confirmed')

        old_status = order.status
        if confirmed == 1:
            order.quote_confirmed = 1
            order.quote_confirm_time = datetime.now()
            order.status = 4
            content = '客户已确认报价'
        elif confirmed == 2:
            order.quote_confirmed = 2
            order.quote_confirm_time = datetime.now()
            order.status = 17
            content = f'客户拒绝报价，原因：{data.get("reject_reason", "")}'
        else:
            return jsonify({
                'code': 400,
                'message': '参数错误，confirmed应为1(确认)或2(拒绝)',
            }), 400

        add_ro_log(
            ro_id=id, action='客户确认',
            old_status=old_status, new_status=order.status,
            content=content,
            operator_id=user_id, operator_name=user_name,
        )
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '操作成功',
            'data': {'status': order.status, 'status_text': RO_STATUS_MAP.get(order.status, '未知')},
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'确认报价失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'确认报价失败: {str(e)}'}), 500


# ============================================
# 4. 领料/采购
# ============================================

@bp.route('/api/receiveorders/<int:id>/allocate', methods=['POST'])
@permission('receive:edit')
@jwt_required()
def allocate_route(id):
    """领料/采购：待领料(4) -> 维修中(5)"""
    try:
        from models.receive import ReceiveOrder

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        if order.status not in [4]:
            return jsonify({
                'code': 400,
                'message': f'当前状态【{RO_STATUS_MAP.get(order.status, "未知")}】不允许执行领料操作',
            }), 400

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        try:
            result = allocate_receiveorder(order, data, user_id, user_name)
        except ValueError as e:
            return jsonify({'code': 400, 'message': str(e)}), 400

        db.session.commit()
        return jsonify({
            'code': 200,
            'message': '领料操作完成',
            'data': {
                'status': result['status'],
                'status_text': result['status_text'],
                'out_count': result['out_count'],
                'purchase_count': result['purchase_count'],
            },
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'领料失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'领料失败: {str(e)}'}), 500


# ============================================
# 5. 完工提交
# ============================================

@bp.route('/api/receiveorders/<int:id>/finish', methods=['POST'])
@permission('receive:edit')
@jwt_required()
def finish_receiveorder(id):
    """完工提交：维修中(5) -> 待测试(6)"""
    try:
        from models.receive import ReceiveOrder

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        if order.status not in [5]:
            return jsonify({
                'code': 400,
                'message': f'当前状态【{RO_STATUS_MAP.get(order.status, "未知")}】不允许提交完工',
            }), 400

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        old_status = order.status
        order.finish_report = data.get('finish_report', '')
        finish_photos = data.get('finish_photos')
        if finish_photos is not None:
            order.finish_photos = (
                json.dumps(finish_photos, ensure_ascii=False)
                if isinstance(finish_photos, (list, dict)) else str(finish_photos)
            )
        order.status = 6

        add_ro_log(
            ro_id=id, action='提交完工',
            old_status=old_status, new_status=6,
            content='工程师提交完工报告',
            operator_id=user_id, operator_name=user_name,
        )
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '完工提交成功',
            'data': {'status': order.status, 'status_text': RO_STATUS_MAP.get(order.status, '未知')},
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'完工提交失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'完工提交失败: {str(e)}'}), 500


# ============================================
# 6. 设备测试
# ============================================

@bp.route('/api/receiveorders/<int:id>/test', methods=['POST'])
@permission('receive:edit')
@jwt_required()
def test_receiveorder(id):
    """设备测试：待测试(6) -> 待取件(7) 或 维修中(5)"""
    try:
        from models.receive import ReceiveOrder

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        if order.status not in [6]:
            return jsonify({
                'code': 400,
                'message': f'当前状态【{RO_STATUS_MAP.get(order.status, "未知")}】不允许执行测试操作',
            }), 400

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        old_status = order.status
        test_result = data.get('test_result')
        test_remark = data.get('test_remark', '')

        order.test_result = test_result
        order.test_remark = test_remark

        if test_result == 1:
            order.status = 7
            content = '设备测试通过'
        elif test_result == 2:
            order.status = 5
            content = f'设备测试未通过，原因：{test_remark}，返回维修中'
        else:
            return jsonify({
                'code': 400,
                'message': '参数错误，test_result应为1(通过)或2(未通过)',
            }), 400

        add_ro_log(
            ro_id=id, action='设备测试',
            old_status=old_status, new_status=order.status,
            content=content,
            operator_id=user_id, operator_name=user_name,
        )
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '测试操作完成',
            'data': {'status': order.status, 'status_text': RO_STATUS_MAP.get(order.status, '未知')},
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'测试失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'测试失败: {str(e)}'}), 500


# ============================================
# 7. 通知取件
# ============================================

@bp.route('/api/receiveorders/<int:id>/notify', methods=['POST'])
@permission('receive:edit')
@jwt_required()
def notify_receiveorder(id):
    """通知取件：状态保持 7(待取件)"""
    try:
        from models.receive import ReceiveOrder

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        if order.status not in [7]:
            return jsonify({
                'code': 400,
                'message': f'当前状态【{RO_STATUS_MAP.get(order.status, "未知")}】不允许执行通知操作',
            }), 400

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        order.notify_time = datetime.now()
        order.notify_method = data.get('notify_method', '电话')

        add_ro_log(
            ro_id=id, action='通知取件',
            old_status=order.status, new_status=order.status,
            content=f'已通过【{order.notify_method}】通知客户取件',
            operator_id=user_id, operator_name=user_name,
        )
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '通知成功',
            'data': {'status': order.status, 'status_text': RO_STATUS_MAP.get(order.status, '未知')},
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'通知取件失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'通知取件失败: {str(e)}'}), 500


# ============================================
# 8. 完工结算（核心：原 app.py 6495 行）
# ============================================

@bp.route('/api/receiveorders/<int:id>/settle', methods=['POST'])
@permission('receive:edit', 'finance:view')
@jwt_required()
def settle_route(id):
    """完工结算：待取件(7) -> 待结算(8)"""
    try:
        from models.receive import ReceiveOrder

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        if order.status not in [7]:
            return jsonify({
                'code': 400,
                'message': f'当前状态【{RO_STATUS_MAP.get(order.status, "未知")}】不允许结算，需为待取件',
            }), 400

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        result = settle_receiveorder(order, data, user_id, user_name)
        db.session.commit()
        return jsonify({
            'code': 200,
            'message': '结算成功',
            'data': {
                'status': result['status'],
                'status_text': result['status_text'],
                'total_cost': result['total_cost'],
            },
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'接件单结算失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'结算失败: {str(e)}'}), 500


# ============================================
# 9. 取件完成
# ============================================

@bp.route('/api/receiveorders/<int:id>/complete', methods=['POST'])
@permission('receive:edit')
@jwt_required()
def complete_route(id):
    """取件完成：待结算(8) -> 已完成(9)"""
    try:
        from models.receive import ReceiveOrder

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        if order.status not in [8]:
            return jsonify({
                'code': 400,
                'message': f'当前状态【{RO_STATUS_MAP.get(order.status, "未知")}】不允许执行完成操作，需先结算',
            }), 400

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        result = complete_receiveorder(order, data, user_id, user_name)
        db.session.commit()
        return jsonify({
            'code': 200,
            'message': '取件完成',
            'data': {'status': result['status'], 'status_text': result['status_text']},
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'取件完成失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'取件完成失败: {str(e)}'}), 500


# ============================================
# 10. 送修外店
# ============================================

@bp.route('/api/receiveorders/<int:id>/external-send', methods=['POST'])
@permission('receive:edit')
@jwt_required()
def external_send_receiveorder(id):
    """送修外店：检测中(1) 或 检测后无法维修(9) -> 送修外店(9)"""
    try:
        from models.receive import ReceiveOrder

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        if order.status not in [1, 9]:
            return jsonify({
                'code': 400,
                'message': f'当前状态【{RO_STATUS_MAP.get(order.status, "未知")}】不允许执行送修外店操作',
            }), 400

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        old_status = order.status
        order.receive_type = 2
        order.external_shop_id = data.get('external_shop_id')
        order.external_shop_name = data.get('external_shop_name')
        order.external_repair_reason = data.get('external_repair_reason', '')
        order.external_send_date = datetime.now().date()
        order.status = 9

        add_ro_log(
            ro_id=id, action='送修外店',
            old_status=old_status, new_status=9,
            content=f'送修外店：{order.external_shop_name}，原因：{order.external_repair_reason}',
            operator_id=user_id, operator_name=user_name,
        )
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '已送修外店',
            'data': {'status': order.status, 'status_text': RO_STATUS_MAP.get(order.status, '未知')},
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'送修外店失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'送修外店失败: {str(e)}'}), 500


# ============================================
# 11. 外店报价
# ============================================

@bp.route('/api/receiveorders/<int:id>/external-quote', methods=['POST'])
@permission('receive:edit')
@jwt_required()
def external_quote_route(id):
    """外店报价：送修外店(9) -> 外店已报价(10)"""
    try:
        from models.receive import ReceiveOrder

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        if order.status not in [9]:
            return jsonify({
                'code': 400,
                'message': f'当前状态【{RO_STATUS_MAP.get(order.status, "未知")}】不允许执行外店报价操作',
            }), 400

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        try:
            result = external_quote_flow(
                order, target='external_quote', items=data,
                user_id=user_id, user_name=user_name,
            )
        except ValueError as e:
            return jsonify({'code': 400, 'message': str(e)}), 400

        db.session.commit()
        return jsonify({
            'code': 200,
            'message': '外店报价已录入',
            'data': {'status': result['status'], 'status_text': RO_STATUS_MAP.get(result['status'], '未知')},
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'外店报价失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'外店报价失败: {str(e)}'}), 500


# ============================================
# 12. 给客户报价（外店流程）
# ============================================

@bp.route('/api/receiveorders/<int:id>/customer-quote', methods=['POST'])
@permission('receive:edit')
@jwt_required()
def customer_quote_route(id):
    """给客户报价：外店已报价(10) -> 待客户确认(3)"""
    try:
        from models.receive import ReceiveOrder

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        if order.status not in [10]:
            return jsonify({
                'code': 400,
                'message': f'当前状态【{RO_STATUS_MAP.get(order.status, "未知")}】不允许执行客户报价操作',
            }), 400

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        try:
            result = external_quote_flow(
                order, target='customer_quote', items=data,
                user_id=user_id, user_name=user_name,
            )
        except ValueError as e:
            return jsonify({'code': 400, 'message': str(e)}), 400

        db.session.commit()
        return jsonify({
            'code': 200,
            'message': '客户报价已生成',
            'data': {
                'status': result['status'],
                'status_text': RO_STATUS_MAP.get(result['status'], '未知'),
                'quote_total': result['quote_total'],
            },
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'客户报价失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'客户报价失败: {str(e)}'}), 500


# ============================================
# 13. 确认送修
# ============================================

@bp.route('/api/receiveorders/<int:id>/external-confirm', methods=['POST'])
@permission('receive:edit')
@jwt_required()
def external_confirm_receiveorder(id):
    """确认送修：待外店维修(11) -> 外店维修中(12)"""
    try:
        from models.receive import ReceiveOrder

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        if order.status not in [11]:
            return jsonify({
                'code': 400,
                'message': f'当前状态【{RO_STATUS_MAP.get(order.status, "未知")}】不允许执行确认送修操作',
            }), 400

        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        old_status = order.status
        order.status = 12

        add_ro_log(
            ro_id=id, action='确认送修',
            old_status=old_status, new_status=12,
            content=f'确认送修外店：{order.external_shop_name}，设备已送出',
            operator_id=user_id, operator_name=user_name,
        )
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '已确认送修',
            'data': {'status': order.status, 'status_text': RO_STATUS_MAP.get(order.status, '未知')},
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'确认送修失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'确认送修失败: {str(e)}'}), 500


# ============================================
# 14. 取回设备
# ============================================

@bp.route('/api/receiveorders/<int:id>/external-return', methods=['POST'])
@permission('receive:edit')
@jwt_required()
def external_return_receiveorder(id):
    """取回设备：外店维修中(12) -> 外店取回待测试(13)"""
    try:
        from models.receive import ReceiveOrder

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        if order.status not in [12]:
            return jsonify({
                'code': 400,
                'message': f'当前状态【{RO_STATUS_MAP.get(order.status, "未知")}】不允许执行取回操作',
            }), 400

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        old_status = order.status
        return_date = data.get('external_return_date')
        if return_date:
            order.external_return_date = (
                datetime.strptime(return_date, '%Y-%m-%d').date()
                if isinstance(return_date, str) else return_date
            )
        else:
            order.external_return_date = datetime.now().date()

        order.external_round = (order.external_round or 1) + 1
        order.status = 13

        history = []
        if order.external_history:
            try:
                history = json.loads(order.external_history)
            except (json.JSONDecodeError, TypeError):
                history = []
        history.append({
            'round': order.external_round,
            'shop_name': order.external_shop_name,
            'send_date': str(order.external_send_date) if order.external_send_date else '',
            'return_date': str(order.external_return_date),
            'quote': float(order.external_quote or 0),
            'operator': user_name,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })
        order.external_history = json.dumps(history, ensure_ascii=False)

        add_ro_log(
            ro_id=id, action='取回设备',
            old_status=old_status, new_status=13,
            content=f'从外店取回设备，第{order.external_round}次往返，待测试',
            operator_id=user_id, operator_name=user_name,
        )
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '设备已取回',
            'data': {
                'status': order.status,
                'status_text': RO_STATUS_MAP.get(order.status, '未知'),
                'external_round': order.external_round,
            },
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'取回设备失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'取回设备失败: {str(e)}'}), 500


# ============================================
# 15. 外店取回测试
# ============================================

@bp.route('/api/receiveorders/<int:id>/external-retest', methods=['POST'])
@permission('receive:edit')
@jwt_required()
def external_retest_receiveorder(id):
    """外店取回测试：外店取回待测试(13) -> 待取件(7) 或 送修外店(9)"""
    try:
        from models.receive import ReceiveOrder

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        if order.status not in [13]:
            return jsonify({
                'code': 400,
                'message': f'当前状态【{RO_STATUS_MAP.get(order.status, "未知")}】不允许执行测试操作',
            }), 400

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        old_status = order.status
        test_result = data.get('test_result')
        test_remark = data.get('test_remark', '')

        order.test_result = test_result
        order.test_remark = test_remark

        if test_result == 1:
            order.status = 7
            content = '外店取回后测试通过'
        elif test_result == 2:
            order.status = 9
            content = f'外店取回后测试未通过，原因：{test_remark}，需再次送修外店'
        else:
            return jsonify({
                'code': 400,
                'message': '参数错误，test_result应为1(通过)或2(未通过)',
            }), 400

        add_ro_log(
            ro_id=id, action='外店取回后测试',
            old_status=old_status, new_status=order.status,
            content=content,
            operator_id=user_id, operator_name=user_name,
        )
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '测试操作完成',
            'data': {'status': order.status, 'status_text': RO_STATUS_MAP.get(order.status, '未知')},
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'外店取回测试失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'外店取回测试失败: {str(e)}'}), 500


# ============================================
# 16. 取消接件单
# ============================================

@bp.route('/api/receiveorders/<int:id>/cancel', methods=['POST'])
@permission('receive:delete')
@jwt_required()
def cancel_route(id):
    """取消接件单：任意状态 -> 已取消(14)（除已完成 8 和已取消 14）"""
    try:
        from models.receive import ReceiveOrder

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        data = request.get_json() or {}
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()
        cancel_reason = data.get('cancel_reason', '')

        try:
            result = cancel_receiveorder(order, cancel_reason, user_id, user_name)
        except ValueError as e:
            return jsonify({'code': 400, 'message': str(e)}), 400

        db.session.commit()
        return jsonify({
            'code': 200,
            'message': '接件单已取消',
            'data': {'status': result['status'], 'status_text': result['status_text']},
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'取消接件单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'取消接件单失败: {str(e)}'}), 500