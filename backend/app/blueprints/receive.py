"""接件单管理蓝图（CRUD + 配件/照片/签收 + 日志 + 导出）。

迁移自 source-code/app.py 中以下区段的原始路由代码：
- /api/receiveorders                  CRUD + 列表 + 详情        3313-3540 行附近
- /api/receiveorders/<id>/logs        操作日志                   7112-7126 行附近
- /api/receiveorders/<id>/accessories 配件 CRUD                  11642-11689 行附近
- /api/receiveorders/<id>/photos      照片 GET/POST              11691-11731 行附近
- /api/receiveorders/<id>/sign        客户签字                   11732-11734 行附近
- /api/receiveorders/export           导出 Excel                 14453-14555 行附近

14 个状态机路由（detect/quote/confirm/allocate/finish/test/notify/settle/
complete/external-send/external-quote/customer-quote/external-confirm/
external-return/external-retest/cancel）
已拆到 receive_actions.py。

业务逻辑已抽到 backend/app/services/receive_service.py，
路由层只做参数校验、状态检查、事务包装（commit/rollback）。
"""
import io
import json
import logging
import os
import uuid as _uuid
from datetime import datetime

import openpyxl
from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from app.utils import generate_code, to_dict

logger = logging.getLogger(__name__)

bp = Blueprint('receive', __name__)


# ============================================
# 常量
# ============================================

RO_STATUS_MAP = {
    0: '已登记',
    1: '检测中',
    2: '待报价',
    3: '待客户确认',
    4: '待领料/采购',
    5: '维修中',
    6: '待测试',
    7: '待取件',
    8: '待结算',
    9: '已完成',
    10: '送修外店',
    11: '外店已报价',
    12: '待外店维修',
    13: '外店维修中',
    14: '外店取回待测试',
    15: '已取消',
}


# ============================================
# 工具函数
# ============================================

def _get_current_user_name():
    """获取当前登录用户姓名。迁移期兼容。"""
    from models.system import SysUser
    user_id = get_jwt_identity()
    user = SysUser.query.get(user_id)
    if user:
        return user.real_name or user.username
    return ''


# ============================================
# 1. CRUD
# ============================================

@bp.route('/api/receiveorders', methods=['GET'])
@jwt_required()
def get_receiveorders():
    """获取接件单列表"""
    try:
        from models.receive import ReceiveOrder, ReceiveOrderDevice

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', '')
        status = request.args.get('status', type=int)
        receive_type = request.args.get('receive_type', type=int)

        query = ReceiveOrder.query

        if keyword:
            query = query.filter(
                db.or_(
                    ReceiveOrder.receive_no.contains(keyword),
                    ReceiveOrder.customer_name.contains(keyword),
                    ReceiveOrder.customer_phone.contains(keyword),
                )
            )
        if status is not None:
            query = query.filter_by(status=status)
        if receive_type is not None:
            query = query.filter_by(receive_type=receive_type)

        total = query.count()
        orders = query.order_by(ReceiveOrder.created_at.desc()).paginate(
            page=page, per_page=page_size, error_out=False
        )

        result_list = []
        for order in orders.items:
            order_dict = to_dict(order)
            devices = ReceiveOrderDevice.query.filter_by(receive_order_id=order.id).all()
            order_dict['devices'] = [to_dict(d) for d in devices]
            if devices:
                order_dict['device_type'] = devices[0].device_type
                order_dict['device_brand'] = devices[0].device_brand
                order_dict['device_model'] = devices[0].device_model
                order_dict['device_sn'] = devices[0].device_sn
                order_dict['fault_desc'] = devices[0].fault_desc
            else:
                order_dict['device_type'] = ''
                order_dict['device_brand'] = ''
                order_dict['device_model'] = ''
                order_dict['device_sn'] = ''
                order_dict['fault_desc'] = ''
            order_dict['reception_user_name'] = order.receiver_name or ''
            order_dict['engineer_user_name'] = order.engineer_name or ''
            order_dict['status_text'] = RO_STATUS_MAP.get(order.status, '未知')
            result_list.append(order_dict)

        return jsonify({
            'code': 200,
            'data': {
                'list': result_list,
                'total': total,
                'page': page,
                'page_size': page_size,
            }
        })
    except Exception as e:
        logger.error(f'获取接件单列表失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取接件单列表失败: {str(e)}'}), 500


@bp.route('/api/receiveorders/<int:id>', methods=['GET'])
@jwt_required()
def get_receiveorder(id):
    """获取接件单详情"""
    try:
        from models.receive import (
            ReceiveOrder, ReceiveOrderDevice, ReceiveOrderPart,
        )
        from models.quote.order import QuoteOrder, QuoteOrderItem

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        devices = ReceiveOrderDevice.query.filter_by(receive_order_id=id).all()
        parts = ReceiveOrderPart.query.filter_by(receive_order_id=id).all()

        result = to_dict(order)
        result['status_text'] = RO_STATUS_MAP.get(order.status, '未知')
        result['devices'] = [to_dict(d) for d in devices]
        result['parts'] = [to_dict(p) for p in parts]

        quote_order = QuoteOrder.query.filter_by(
            related_type='receive_order', related_id=id
        ).first()
        if quote_order:
            quote_items = QuoteOrderItem.query.filter_by(quote_id=quote_order.id).all()
            result['quote_items'] = [to_dict(item) for item in quote_items]
        else:
            result['quote_items'] = []

        return jsonify({'code': 200, 'data': result})
    except Exception as e:
        logger.error(f'获取接件单详情失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取接件单详情失败: {str(e)}'}), 500


@bp.route('/api/receiveorders', methods=['POST'])
@jwt_required()
def create_receiveorder():
    """创建接件单"""
    try:
        from models.receive import ReceiveOrder, ReceiveOrderDevice, ReceiveOrderPart
        from app import ReceiveOrderLog
        from models.system import SysUser

        data = request.get_json()
        logger.debug(f'创建接件单 - 接收数据: {data}')

        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        last_order = ReceiveOrder.query.order_by(ReceiveOrder.id.desc()).first()
        receive_no = generate_code('RO', last_order.id if last_order else 0)

        reception_user_id = data.get('reception_user_id')
        engineer_user_id = data.get('engineer_user_id')

        reception_user_name = user_name
        engineer_user_name = ''

        if reception_user_id:
            reception_user = SysUser.query.get(reception_user_id)
            if reception_user:
                reception_user_name = reception_user.real_name or reception_user.username

        if engineer_user_id:
            engineer_user = SysUser.query.get(engineer_user_id)
            if engineer_user:
                engineer_user_name = engineer_user.real_name or engineer_user.username

        order = ReceiveOrder(
            receive_no=receive_no,
            customer_id=data.get('customer_id'),
            customer_name=data.get('customer_name'),
            customer_phone=data.get('customer_phone'),
            receive_type=data.get('receive_type', 1),
            external_shop_id=data.get('external_shop_id'),
            external_shop_name=data.get('external_shop_name'),
            remark=data.get('remark'),
            created_by=user_id,
            receiver_id=reception_user_id or user_id,
            receiver_name=reception_user_name,
            engineer_id=engineer_user_id,
            engineer_name=engineer_user_name,
        )

        db.session.add(order)
        db.session.flush()

        devices = data.get('devices', [])
        for device_data in devices:
            device_brand = (
                device_data.get('device_brand') or device_data.get('brand') or ''
            )
            device_model = (
                device_data.get('device_model') or device_data.get('model') or ''
            )
            device_sn = (
                device_data.get('device_sn') or device_data.get('serial_number') or ''
            )
            device = ReceiveOrderDevice(
                receive_order_id=order.id,
                device_type=device_data.get('device_type'),
                device_brand=device_brand,
                device_model=device_model,
                device_sn=device_sn,
                device_imei=device_data.get('device_imei'),
                fault_desc=device_data.get('fault_desc'),
                appearance_desc=device_data.get('appearance_desc'),
                accessories=device_data.get('accessories'),
                device_name=device_data.get('device_name'),
                cpu=device_data.get('cpu'),
                memory=device_data.get('memory'),
                disk=device_data.get('disk'),
                os=device_data.get('os'),
                os_version=device_data.get('os_version'),
                toner_model=device_data.get('toner_model'),
                drum_model=device_data.get('drum_model'),
                ip_address=device_data.get('ip_address'),
                port=device_data.get('port'),
                camera_count=device_data.get('camera_count'),
                monitor_brand=device_data.get('monitor_brand'),
                firmware_version=device_data.get('firmware_version'),
                port_count=device_data.get('port_count'),
            )
            db.session.add(device)

            device_parts = device_data.get('parts', [])
            for part in device_parts:
                part_status = part.get('status', 0)
                p = ReceiveOrderPart(
                    receive_order_id=order.id,
                    product_name=part.get('name') or part.get('product_name', ''),
                    specification=part.get('specification', ''),
                    unit_name=part.get('unit', '个'),
                    quantity=int(part.get('quantity', 1)) if part.get('quantity') else 1,
                    status=int(part_status) if str(part_status).isdigit() else 0,
                    remark=str(part.get('remark', '')),
                    source=1,
                )
                db.session.add(p)

        db.session.commit()

        log = ReceiveOrderLog(
            receive_order_id=order.id,
            action='创建接件单',
            old_status=None,
            new_status=0,
            content=f'创建接件单 {receive_no}，客户：{order.customer_name}',
            operator_id=user_id,
            operator_name=user_name,
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'code': 200, 'message': '创建成功', 'data': {
            'id': order.id, 'receive_no': receive_no,
        }})
    except Exception as e:
        db.session.rollback()
        logger.error(f'创建接件单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'创建接件单失败: {str(e)}'}), 500


@bp.route('/api/receiveorders/<int:id>', methods=['PUT'])
@jwt_required()
def update_receiveorder(id):
    """更新接件单（含设备、配件、员工信息）"""
    try:
        from models.receive import (
            ReceiveOrder, ReceiveOrderDevice, ReceiveOrderPart,
        )
        from models.system import SysUser

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        data = request.get_json()

        for field in ['customer_id', 'customer_name', 'customer_phone',
                      'receive_type', 'external_shop_id', 'external_shop_name', 'remark']:
            if field in data:
                setattr(order, field, data[field])

        if 'reception_user_id' in data:
            reception_user_id = data.get('reception_user_id')
            order.receiver_id = reception_user_id
            if reception_user_id:
                reception_user = SysUser.query.get(reception_user_id)
                if reception_user:
                    order.receiver_name = reception_user.real_name or reception_user.username

        if 'engineer_user_id' in data:
            engineer_user_id = data.get('engineer_user_id')
            order.engineer_id = engineer_user_id
            if engineer_user_id:
                engineer_user = SysUser.query.get(engineer_user_id)
                if engineer_user:
                    order.engineer_name = engineer_user.real_name or engineer_user.username

        if 'devices' in data and isinstance(data['devices'], list):
            ReceiveOrderDevice.query.filter_by(receive_order_id=id).delete()
            for dev in data['devices']:
                device = ReceiveOrderDevice(
                    receive_order_id=id,
                    device_type=dev.get('device_type', ''),
                    device_brand=dev.get('brand') or dev.get('device_brand', ''),
                    device_model=dev.get('model') or dev.get('device_model', ''),
                    device_sn=dev.get('serial_number') or dev.get('device_sn', ''),
                    device_name=dev.get('device_name', ''),
                    fault_desc=dev.get('fault_desc', ''),
                    appearance_desc=dev.get('appearance_desc', ''),
                    cpu=dev.get('cpu', ''),
                    memory=dev.get('memory', ''),
                    disk=dev.get('hard_disk') or dev.get('disk', ''),
                    os=dev.get('os', ''),
                    os_version=dev.get('os_version', ''),
                    toner_model=dev.get('toner_model', ''),
                    drum_model=dev.get('cartridge_model') or dev.get('drum_model', ''),
                    monitor_brand=dev.get('monitor_brand', ''),
                    camera_count=dev.get('camera_count', 0),
                    port_count=dev.get('port_count', 0),
                    ip_address=dev.get('ip_address', ''),
                    firmware_version=dev.get('firmware_version', ''),
                    accessories=dev.get('accessories', ''),
                )
                db.session.add(device)
            db.session.flush()

        if 'parts' in data and isinstance(data['parts'], list):
            ReceiveOrderPart.query.filter_by(receive_order_id=id).delete()
            for part in data['parts']:
                p = ReceiveOrderPart(
                    receive_order_id=id,
                    product_name=part.get('name') or part.get('product_name', ''),
                    specification=part.get('specification', ''),
                    unit_name=part.get('unit', ''),
                    quantity=part.get('quantity', 1),
                    unit_price=part.get('unit_price', 0),
                    total_price=(part.get('quantity', 1) or 1) * (part.get('unit_price', 0) or 0),
                    status=part.get('status', '完好'),
                    remark=part.get('remark', ''),
                    source='自带',
                )
                db.session.add(p)

        db.session.commit()
        return jsonify({'code': 200, 'message': '更新成功', 'data': to_dict(order)})
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新接件单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'更新接件单失败: {str(e)}'}), 500


@bp.route('/api/receiveorders/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_receiveorder(id):
    """删除接件单 - 只有状态为已登记(0)或已取消(15)的接件单才能删除"""
    try:
        from models.receive import (
            ReceiveOrder, ReceiveOrderDevice, ReceiveOrderPart, ReceiveOrderLog,
        )

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        if order.status not in (0, 15):
            return jsonify({
                'code': 400,
                'message': f'当前状态为【{RO_STATUS_MAP.get(order.status, "未知")}】，只有已登记或已取消的接件单才能删除',
            }), 400

        ReceiveOrderDevice.query.filter_by(receive_order_id=id).delete()
        ReceiveOrderPart.query.filter_by(receive_order_id=id).delete()
        ReceiveOrderLog.query.filter_by(receive_order_id=id).delete()

        db.session.delete(order)
        db.session.commit()
        return jsonify({'code': 200, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除接件单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'删除接件单失败: {str(e)}'}), 500


# ============================================
# 2. 操作日志
# ============================================

@bp.route('/api/receiveorders/<int:id>/logs', methods=['GET'])
@jwt_required()
def get_receiveorder_logs(id):
    """获取接件单操作日志"""
    try:
        from models.receive import ReceiveOrder, ReceiveOrderLog

        order = ReceiveOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '接件单不存在'}), 404

        logs = ReceiveOrderLog.query.filter_by(receive_order_id=id).order_by(
            ReceiveOrderLog.created_at.desc()
        ).limit(50).all()

        return jsonify({'code': 200, 'data': [to_dict(l) for l in logs]})
    except Exception as e:
        logger.error(f'获取接件单日志失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取接件单日志失败: {str(e)}'}), 500


# ============================================
# 3. 配件 CRUD
# ============================================

@bp.route('/api/receiveorders/<int:receive_id>/accessories', methods=['GET'])
@jwt_required()
def get_accessories(receive_id):
    """获取接件单配件列表"""
    try:
        from models.receive import DeviceAccessory

        accessories = DeviceAccessory.query.filter_by(receive_order_id=receive_id).all()
        return jsonify({'code': 200, 'data': [to_dict(a) for a in accessories]})
    except Exception as e:
        logger.error(f'获取配件列表失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取配件列表失败: {str(e)}'}), 500


@bp.route('/api/receiveorders/<int:receive_id>/accessories', methods=['POST'])
@jwt_required()
def add_accessory(receive_id):
    """添加配件"""
    try:
        from models.receive import DeviceAccessory

        data = request.get_json()
        accessory = DeviceAccessory(
            receive_order_id=receive_id,
            accessory_name=data.get('accessory_name'),
            quantity=data.get('quantity', 1),
            status=data.get('status', '完好'),
            remark=data.get('remark'),
        )
        db.session.add(accessory)
        db.session.commit()
        return jsonify({'code': 200, 'message': '添加成功', 'data': to_dict(accessory)})
    except Exception as e:
        db.session.rollback()
        logger.error(f'添加配件失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'添加配件失败: {str(e)}'}), 500


@bp.route('/api/receiveorders/accessories/<int:accessory_id>', methods=['PUT'])
@jwt_required()
def update_accessory(accessory_id):
    """更新配件"""
    try:
        from models.receive import DeviceAccessory

        accessory = DeviceAccessory.query.get_or_404(accessory_id)
        data = request.get_json()
        if 'accessory_name' in data:
            accessory.accessory_name = data['accessory_name']
        if 'quantity' in data:
            accessory.quantity = data['quantity']
        if 'status' in data:
            accessory.status = data['status']
        if 'remark' in data:
            accessory.remark = data['remark']
        db.session.commit()
        return jsonify({'code': 200, 'message': '更新成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新配件失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'更新配件失败: {str(e)}'}), 500


@bp.route('/api/receiveorders/accessories/<int:accessory_id>', methods=['DELETE'])
@jwt_required()
def delete_accessory(accessory_id):
    """删除配件"""
    try:
        from models.receive import DeviceAccessory

        accessory = DeviceAccessory.query.get_or_404(accessory_id)
        db.session.delete(accessory)
        db.session.commit()
        return jsonify({'code': 200, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除配件失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'删除配件失败: {str(e)}'}), 500


# ============================================
# 4. 接件照片
# ============================================

@bp.route('/api/receiveorders/<int:receive_id>/photos', methods=['GET'])
@jwt_required()
def get_photos(receive_id):
    """获取接件单照片列表"""
    try:
        from models.receive import DevicePhoto

        photos = DevicePhoto.query.filter_by(receive_order_id=receive_id).all()
        return jsonify({'code': 200, 'data': [to_dict(p) for p in photos]})
    except Exception as e:
        logger.error(f'获取照片列表失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取照片列表失败: {str(e)}'}), 500


@bp.route('/api/receiveorders/<int:receive_id>/photos', methods=['POST'])
@jwt_required()
def upload_photo(receive_id):
    """上传接件照片（带白名单校验）"""
    try:
        from models.receive import DevicePhoto

        photo_type = request.form.get('photo_type', '整体照')
        remark = request.form.get('remark', '')
        file = request.files.get('file')
        if not file:
            return jsonify({'code': 400, 'message': '请选择文件'}), 400

        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in {'png', 'jpg', 'jpeg', 'gif'}:
            return jsonify({'code': 400, 'message': f'不支持的图片格式: {ext}'}), 400
        if (file.mimetype or '').lower() not in {'image/png', 'image/jpeg', 'image/gif'}:
            return jsonify({'code': 400, 'message': '文件 MIME 类型不符'}), 400

        safe_name = f'{_uuid.uuid4().hex}.{ext}'
        upload_dir = os.path.join('uploads', 'receive_photos', str(receive_id))
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, safe_name)
        file.save(filepath)
        photo_url = f"/uploads/receive_photos/{receive_id}/{safe_name}"

        photo = DevicePhoto(
            receive_order_id=receive_id,
            photo_type=photo_type,
            photo_url=photo_url,
            remark=remark,
        )
        db.session.add(photo)
        db.session.commit()
        return jsonify({'code': 200, 'message': '上传成功', 'data': to_dict(photo)})
    except Exception as e:
        db.session.rollback()
        logger.error(f'上传照片失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'上传照片失败: {str(e)}'}), 500


# ============================================
# 5. 接件签字
# ============================================

@bp.route('/api/receiveorders/<int:receive_id>/sign', methods=['POST'])
@jwt_required()
def customer_sign(receive_id):
    """客户签字"""
    try:
        from models.receive import ReceiveOrder

        order = ReceiveOrder.query.get_or_404(receive_id)
        data = request.get_json()
        order.customer_sign = data.get('sign_url')
        order.sign_time = datetime.now()
        db.session.commit()
        return jsonify({'code': 200, 'message': '签字成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'客户签字失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'客户签字失败: {str(e)}'}), 500


# ============================================
# 6. 导出 Excel
# ============================================

@bp.route('/api/receiveorders/export', methods=['GET'])
@jwt_required()
def export_receive_orders():
    """导出接件单"""
    try:
        from models.receive import ReceiveOrder

        keyword = request.args.get('keyword', '')
        status = request.args.get('status', type=int)
        date_start = request.args.get('date_start', '')
        date_end = request.args.get('date_end', '')

        query = ReceiveOrder.query
        if keyword:
            query = query.filter(db.or_(
                ReceiveOrder.receive_no.contains(keyword),
                ReceiveOrder.customer_name.contains(keyword),
                ReceiveOrder.customer_phone.contains(keyword),
            ))
        if status is not None:
            query = query.filter(ReceiveOrder.status == status)
        if date_start:
            query = query.filter(ReceiveOrder.created_at >= date_start)
        if date_end:
            query = query.filter(ReceiveOrder.created_at <= date_end + ' 23:59:59')

        orders = query.order_by(ReceiveOrder.created_at.desc()).all()

        ro_status_map = {
            0: '待检测', 1: '检测中', 2: '待报价', 3: '待确认', 4: '维修中',
            5: '外送修', 6: '待测试', 7: '待取件', 8: '已完成', 9: '已取消',
        }
        ro_type_map = {1: '本店修', 2: '外送修'}

        data = []
        for o in orders:
            data.append({
                '接件单号': o.receive_no,
                '客户名称': o.customer_name or '',
                '客户电话': o.customer_phone or '',
                '接件类型': ro_type_map.get(o.receive_type, '本店修'),
                '状态': ro_status_map.get(o.status, str(o.status)),
                '总金额': float(o.total_amount or 0),
                '已付金额': float(o.paid_amount or 0),
                '接待人': o.receiver_name or '',
                '工程师': o.engineer_name or '',
                '外送供应商': o.external_shop_name or '',
                '报价人工费': float(o.quote_labor_cost or 0),
                '报价材料费': float(o.quote_material_cost or 0),
                '报价其他费': float(o.quote_other_cost or 0),
                '报价总计': float(o.quote_total or 0),
                '检测结果': o.detect_result or '',
                '故障原因': o.detect_fault_reason or '',
                '维修方案': o.detect_repair_plan or '',
                '完工报告': o.finish_report or '',
                '测试结果': '通过' if o.test_result == 1 else ('未通过' if o.test_result == 2 else '待测试'),
                '备注': o.remark or '',
                '创建时间': o.created_at.strftime('%Y-%m-%d %H:%M') if o.created_at else '',
            })

        output = io.BytesIO()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = '接件单列表'
        headers = ['接件单号', '客户名称', '客户电话', '接件类型', '状态', '总金额',
                   '已付金额', '接待人', '工程师', '外送供应商', '报价人工费',
                   '报价材料费', '报价其他费', '报价总计', '检测结果', '故障原因',
                   '维修方案', '完工报告', '测试结果', '备注', '创建时间']
        ws.append(headers)
        for row in data:
            ws.append(list(row.values()))
        wb.save(output)
        output.seek(0)

        return send_file(
            output, as_attachment=True,
            download_name=f'接件单列表_{datetime.now().strftime("%Y%m%d")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
    except Exception as e:
        logger.error(f'导出接件单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'导出接件单失败: {str(e)}'}), 500