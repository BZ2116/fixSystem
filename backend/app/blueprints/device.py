"""设备管理：客户设备档案（DeviceArchive）+ 自有设备（OwnDevice）+ 维修历史。

迁移自 source-code/app.py 中 7477-7822 行附近的原始路由代码。
保持行为完全一致：
- 客户设备：状态过滤、软删除（status=0）、device_code 自动生成、
  字段名映射（brand/device_brand、model/device_model、serial_number/device_sn）
- 自有设备：硬删除、password 哈希化、列表/详情排除 password 字段
- 维修历史：通过 ReceiveOrderDevice 反查关联 WorkOrder，并按 device_sn 兜底匹配
"""
from werkzeug.security import generate_password_hash
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from extensions import db
from app.utils import generate_code, to_dict

bp = Blueprint('device', __name__, url_prefix='/api/devices')


# 设备类型映射（与原 app.py 行为一致）
DEVICE_TYPE_MAP = {
    'desktop': '台式机', 'laptop': '笔记本', 'server': '服务器',
    'printer': '打印机', 'network': '网络设备',
    'office_supplies': '办公文具', 'monitor': '监控设备', 'other': '其他'
}

# 工单状态映射（与原 app.py 行为一致；独立副本避免对未迁移的 workorder 蓝图产生依赖）
WO_STATUS_MAP = {
    0: '待派单', 1: '待接单', 2: '待备件', 3: '待上门',
    4: '处理中', 5: '待结算', 6: '已完成', 7: '已取消'
}


# ============================================
# 客户设备档案 CRUD（DeviceArchive）
# ============================================

@bp.route('', methods=['GET'])
@jwt_required()
def list_devices():
    """获取客户设备列表。"""
    from models.receive.order import DeviceArchive
    from models.customer import BaseCustomer

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '')
    customer_id = request.args.get('customer_id', type=int)

    query = DeviceArchive.query.filter_by(status=1)

    if keyword:
        query = query.filter(
            db.or_(
                DeviceArchive.device_code.contains(keyword),
                DeviceArchive.device_type.contains(keyword),
                DeviceArchive.device_brand.contains(keyword),
                DeviceArchive.device_model.contains(keyword),
                DeviceArchive.device_sn.contains(keyword),
                DeviceArchive.device_name.contains(keyword)
            )
        )

    if customer_id:
        query = query.filter_by(customer_id=customer_id)

    total = query.count()
    devices = query.order_by(DeviceArchive.created_at.desc()).paginate(
        page=page, per_page=page_size, error_out=False
    )

    # 获取所有相关的客户信息
    customer_ids = list(set(d.customer_id for d in devices.items if d.customer_id))
    customers = {}
    if customer_ids:
        customer_list = BaseCustomer.query.filter(BaseCustomer.id.in_(customer_ids)).all()
        customers = {c.id: c for c in customer_list}

    device_list = []
    for d in devices.items:
        item = to_dict(d)
        item['device_type_label'] = DEVICE_TYPE_MAP.get(d.device_type, d.device_type or '未知')
        item['brand'] = d.device_brand
        item['model'] = d.device_model
        item['serial_number'] = d.device_sn
        # 关联客户信息
        customer = customers.get(d.customer_id)
        if customer:
            item['customer_name'] = customer.customer_name
            item['contact_name'] = customer.contact_name
            item['phone'] = customer.phone
        else:
            item['customer_name'] = ''
            item['contact_name'] = ''
            item['phone'] = ''
        device_list.append(item)

    return jsonify({
        'code': 200,
        'data': {
            'list': device_list,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    })


@bp.route('/<int:device_id>', methods=['GET'])
@jwt_required()
def get_device(device_id):
    """获取设备详情。"""
    from models.receive.order import DeviceArchive
    from models.customer import BaseCustomer

    device = DeviceArchive.query.get(device_id)
    if not device:
        return jsonify({'code': 404, 'message': '设备不存在'}), 404

    data = to_dict(device)
    # 添加前端需要的字段映射
    data['brand'] = device.device_brand
    data['model'] = device.device_model
    data['serial_number'] = device.device_sn
    data['device_type_label'] = DEVICE_TYPE_MAP.get(device.device_type, device.device_type or '未知')
    # 关联客户信息
    if device.customer_id:
        customer = BaseCustomer.query.get(device.customer_id)
        if customer:
            data['customer_name'] = customer.customer_name
            data['contact_name'] = customer.contact_name
            data['phone'] = customer.phone

    return jsonify({'code': 200, 'data': data})


@bp.route('', methods=['POST'])
@jwt_required()
def create_device():
    """创建客户设备。"""
    from models.receive.order import DeviceArchive

    data = request.get_json()

    last_device = DeviceArchive.query.order_by(DeviceArchive.id.desc()).first()
    device_code = generate_code('DEV', last_device.id if last_device else 0)

    # 处理日期字段：空字符串转为 None
    def parse_date(val):
        if not val or str(val).strip() == '':
            return None
        return val

    device = DeviceArchive(
        device_code=device_code,
        customer_id=data.get('customer_id'),
        device_type=data.get('device_type'),
        device_name=data.get('device_name'),
        device_brand=data.get('brand') or data.get('device_brand'),
        device_model=data.get('model') or data.get('device_model'),
        device_sn=data.get('serial_number') or data.get('device_sn'),
        device_imei=data.get('device_imei'),
        device_password=data.get('device_password'),
        ip_address=data.get('ip_address'),
        port=data.get('port'),
        quantity=data.get('quantity', 1),
        cpu=data.get('cpu'),
        memory=data.get('memory'),
        disk=data.get('disk'),
        os=data.get('os'),
        os_version=data.get('os_version'),
        accessories=data.get('accessories'),
        account=data.get('account'),
        password=data.get('password'),
        password_remark=data.get('password_remark'),
        purchase_date=parse_date(data.get('purchase_date')),
        warranty_expire=parse_date(data.get('warranty_expire')),
        remark=data.get('remark')
    )

    db.session.add(device)
    db.session.commit()

    return jsonify({'code': 200, 'message': '创建成功',
                    'data': {'id': device.id, 'device_code': device_code}})


@bp.route('/<int:device_id>', methods=['PUT'])
@jwt_required()
def update_device(device_id):
    """更新客户设备。"""
    from models.receive.order import DeviceArchive

    device = DeviceArchive.query.get(device_id)
    if not device:
        return jsonify({'code': 404, 'message': '设备不存在'}), 404

    data = request.get_json()

    for field in ['customer_id', 'device_type', 'device_name',
                  'device_brand', 'brand', 'device_model', 'model',
                  'device_sn', 'serial_number', 'device_imei',
                  'device_password', 'ip_address', 'port', 'quantity',
                  'cpu', 'memory', 'disk', 'os', 'os_version', 'accessories',
                  'account', 'password', 'password_remark',
                  'purchase_date', 'warranty_expire', 'remark']:
        if field in data:
            val = data[field]
            # 字段名映射
            if field == 'brand':
                device.device_brand = val
            elif field == 'model':
                device.device_model = val
            elif field == 'serial_number':
                device.device_sn = val
            else:
                setattr(device, field, val)

    db.session.commit()
    return jsonify({'code': 200, 'message': '更新成功'})


@bp.route('/<int:device_id>', methods=['DELETE'])
@jwt_required()
def delete_device(device_id):
    """删除客户设备（软删除 status=0）。"""
    from models.receive.order import DeviceArchive

    device = DeviceArchive.query.get(device_id)
    if not device:
        return jsonify({'code': 404, 'message': '设备不存在'}), 404

    device.status = 0
    db.session.commit()
    return jsonify({'code': 200, 'message': '删除成功'})


# ============================================
# 自有设备 CRUD（OwnDevice）
# ============================================

@bp.route('/own', methods=['GET'])
@jwt_required()
def list_own_devices():
    """获取自有设备列表。"""
    from models.asset import OwnDevice

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '')
    status = request.args.get('status', type=int)

    query = OwnDevice.query

    if keyword:
        query = query.filter(
            db.or_(
                OwnDevice.asset_no.contains(keyword),
                OwnDevice.device_type.contains(keyword),
                OwnDevice.device_model.contains(keyword),
                OwnDevice.serial_number.contains(keyword),
                OwnDevice.location.contains(keyword)
            )
        )

    if status is not None:
        query = query.filter_by(status=status)

    total = query.count()
    devices = query.order_by(OwnDevice.created_at.desc()).paginate(
        page=page, per_page=page_size, error_out=False
    )

    return jsonify({
        'code': 200,
        'data': {
            'list': [to_dict(d, exclude=['password']) for d in devices.items],
            'total': total,
            'page': page,
            'page_size': page_size
        }
    })


@bp.route('/own/<int:device_id>', methods=['GET'])
@jwt_required()
def get_own_device(device_id):
    """获取自有设备详情。"""
    from models.asset import OwnDevice

    device = OwnDevice.query.get(device_id)
    if not device:
        return jsonify({'code': 404, 'message': '自有设备不存在'}), 404
    return jsonify({'code': 200, 'data': to_dict(device, exclude=['password'])})


@bp.route('/own', methods=['POST'])
@jwt_required()
def create_own_device():
    """创建自有设备（密码哈希化）。"""
    from models.asset import OwnDevice

    data = request.get_json()

    last_device = OwnDevice.query.order_by(OwnDevice.id.desc()).first()
    asset_no = generate_code('ASSET', last_device.id if last_device else 0)

    device = OwnDevice(
        asset_no=asset_no,
        device_type=data.get('device_type'),
        device_model=data.get('device_model'),
        serial_number=data.get('serial_number'),
        cpu=data.get('cpu'),
        memory=data.get('memory'),
        hard_disk=data.get('hard_disk'),
        system=data.get('system'),
        system_version=data.get('system_version'),
        accessories=data.get('accessories'),
        account=data.get('account'),
        password=generate_password_hash(data.get('password', '')) if data.get('password') else '',
        password_remark=data.get('password_remark'),
        purchase_date=data.get('purchase_date'),
        warranty_expire=data.get('warranty_expire'),
        location=data.get('location'),
        user_id=data.get('user_id'),
        cost=data.get('cost', 0),
        depreciation=data.get('depreciation', 0),
        remark=data.get('remark')
    )

    db.session.add(device)
    db.session.commit()

    return jsonify({'code': 200, 'message': '创建成功',
                    'data': {'id': device.id, 'asset_no': asset_no}})


@bp.route('/own/<int:device_id>', methods=['PUT'])
@jwt_required()
def update_own_device(device_id):
    """更新自有设备。"""
    from models.asset import OwnDevice

    device = OwnDevice.query.get(device_id)
    if not device:
        return jsonify({'code': 404, 'message': '自有设备不存在'}), 404

    data = request.get_json()

    for field in ['device_type', 'device_model', 'serial_number', 'cpu', 'memory',
                  'hard_disk', 'system', 'system_version', 'accessories', 'account',
                  'password_remark', 'purchase_date', 'warranty_expire', 'location',
                  'user_id', 'cost', 'depreciation', 'status', 'remark']:
        if field in data:
            setattr(device, field, data[field])

    if data.get('password'):
        device.password = generate_password_hash(data['password'])

    db.session.commit()
    return jsonify({'code': 200, 'message': '更新成功'})


@bp.route('/own/<int:device_id>', methods=['DELETE'])
@jwt_required()
def delete_own_device(device_id):
    """删除自有设备（硬删除）。"""
    from models.asset import OwnDevice

    device = OwnDevice.query.get(device_id)
    if not device:
        return jsonify({'code': 404, 'message': '自有设备不存在'}), 404

    db.session.delete(device)
    db.session.commit()
    return jsonify({'code': 200, 'message': '删除成功'})


# ============================================
# 设备维修历史
# ============================================

@bp.route('/<int:device_id>/repair-history', methods=['GET'])
@jwt_required()
def get_device_repair_history(device_id):
    """获取设备维修历史。

    通过 ReceiveOrderDevice 反查关联 WorkOrder，并按 device_sn 兜底匹配。
    """
    from models.receive.order import DeviceArchive, ReceiveOrderDevice
    from models.workorder.order import WorkOrder

    device = DeviceArchive.query.get(device_id)
    if not device:
        return jsonify({'code': 404, 'message': '设备不存在'}), 404

    # 通过接件单设备明细查找关联工单
    work_orders = WorkOrder.query.filter(
        WorkOrder.receive_order_id.in_(
            db.session.query(ReceiveOrderDevice.receive_order_id).filter(
                ReceiveOrderDevice.device_archive_id == device_id
            )
        )
    ).order_by(WorkOrder.created_at.desc()).limit(20).all()

    # 也通过设备 SN 直接匹配工单
    if device.device_sn:
        sn_orders = WorkOrder.query.filter(
            WorkOrder.device_sn == device.device_sn
        ).order_by(WorkOrder.created_at.desc()).limit(20).all()
        # 合并去重
        existing_ids = {wo.id for wo in work_orders}
        for wo in sn_orders:
            if wo.id not in existing_ids:
                work_orders.append(wo)

    return jsonify({
        'code': 200,
        'data': [{
            'id': wo.id,
            'wo_no': wo.wo_no,
            'fault_desc': wo.fault_desc,
            'status': wo.status,
            'status_text': WO_STATUS_MAP.get(wo.status, '未知'),
            'total_cost': float(wo.total_cost) if wo.total_cost else 0.00,
            'created_at': wo.created_at.strftime('%Y-%m-%d %H:%M:%S') if wo.created_at else None,
            'actual_time': wo.actual_time.strftime('%Y-%m-%d %H:%M:%S') if wo.actual_time else None
        } for wo in work_orders]
    })
