"""工单管理蓝图（CRUD + Logs + Parts + Export）。

迁移自 source-code/app.py 中以下区段的原始路由代码：
- /api/workorders  CRUD + 列表 + 详情 + 二级分类   1334-2010 行附近
- /api/workorders/<id>/logs      操作日志           3111-3139 行附近
- /api/workorders/auto-dispatch  自动派单推荐       3141-3162 行附近
- /api/workorders/<wo_id>/parts  配件CRUD           3165-3307 行附近
- /api/workorders/batch-delete   批量删除           12265-12286 行附近
- /api/workorders/export         导出Excel          14290-14356 行附近

13 个状态机路由（status/dispatch/accept/allocate-parts/finish/settle/
to-quote/quote/to-purchase/to-sales/return-visit/acceptance/cancel）
已拆到 workorder_actions.py。

业务逻辑已抽到 backend/app/services/workorder_service.py，
路由层只做参数校验、状态检查、事务包装（commit/rollback）。
"""
import io
import json
import logging
from datetime import datetime

import openpyxl
from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from app.utils import generate_code, to_dict
from app.services.workorder_service import (
    add_wo_log,
    _generate_wo_no,
)

logger = logging.getLogger(__name__)

bp = Blueprint('workorder', __name__)


# ============================================
# 常量（与原 app.py 1188-1259 行一致）
# ============================================

WO_STATUS_MAP = {
    0: '待派单',
    1: '待接单',
    2: '待备件',
    3: '待上门',
    4: '处理中',
    5: '待结算',
    6: '已完成',
    7: '已取消',
}

WO_TYPE_MAP = {
    'maintenance': '维护服务',
    'inspection': '检测服务',
    'delivery': '送货服务',
    'installation': '安装服务',
    'repair': '维修服务',
    'purchase': '产品代购',
    'survey': '现场勘察',
}

WO_SUB_TYPE_MAP = {
    # 维修服务二级分类
    'repair_monitor': '监控维修',
    'repair_network': '网络维修',
    'repair_printer': '打印维修',
    'repair_computer': '电脑维修',
    'repair_other': '其他办公设备维修',
    # 维护服务二级分类
    'maintenance_monitor': '监控维护',
    'maintenance_network': '网络维护',
    'maintenance_printer': '打印维护',
    'maintenance_computer': '电脑维护',
    'maintenance_other': '其他办公设备维护',
    # 检测服务二级分类
    'inspection_monitor': '监控检测',
    'inspection_network': '网络检测',
    'inspection_printer': '打印检测',
    'inspection_computer': '电脑检测',
    'inspection_other': '其他办公设备检测',
    # 安装服务二级分类
    'installation_monitor': '监控安装',
    'installation_network': '网络安装',
    'installation_printer': '打印安装',
    'installation_computer': '电脑安装',
    'installation_other': '其他办公设备安装',
}

WO_STATUS_TRANSITIONS = {
    0: [1, 7],
    1: [2, 3, 7],
    2: [3, 7],
    3: [4, 7],
    4: [5, 7],
    5: [6],
    6: [],
    7: [],
}


# ============================================
# 工具函数
# ============================================

def _get_current_user_name():
    """获取当前登录用户姓名。迁移期兼容（app.py 174 行）。"""
    from models.system import SysUser
    user_id = get_jwt_identity()
    user = SysUser.query.get(user_id)
    if user:
        return user.real_name or user.username
    return ''


def _auto_dispatch_engineer(wo_type, required_skills=None):
    """自动派单：根据工单类型匹配最优工程师。迁移自 app.py 1261-1318 行。"""
    from models.dispatch import StaffStatus

    skill_keywords = {
        'repair': ['维修', 'repair', '打印机', 'printer', '电脑', 'computer',
                   '笔记本', '硬件', '监控', '摄像头', 'camera', 'NVR', 'DVR',
                   '海康', '大华', '网络', 'network', '宽带', '路由', '交换机',
                   'WiFi', '布线'],
        'maintenance': ['维护', 'maintenance', '保养', '打印机', 'printer', '电脑',
                        'computer', '监控', '摄像头', 'camera', '网络', 'network',
                        '宽带', '路由'],
        'inspection': ['检测', 'inspection', '打印机', 'printer', '电脑', 'computer',
                       '监控', '摄像头', 'camera', '网络', 'network'],
        'installation': ['安装', 'installation', '监控', '摄像头', 'camera', '网络',
                         'network', '打印机', 'printer', '电脑', 'computer'],
        'delivery': ['配送', '送货', 'delivery'],
        'purchase': ['代购', '采购', 'purchase'],
        'survey': ['勘察', 'survey', '现场'],
    }
    keywords = skill_keywords.get(wo_type, [])
    if required_skills:
        keywords.extend(required_skills if isinstance(required_skills, list)
                        else [required_skills])

    engineers = StaffStatus.query.filter_by(online_status=1).all()
    matched = []
    for eng in engineers:
        if not keywords:
            matched.append(eng)
            continue
        eng_skills = (eng.skills or '').lower()
        for kw in keywords:
            if kw.lower() in eng_skills:
                matched.append(eng)
                break

    available = [e for e in matched if e.today_count < e.max_daily]
    available.sort(key=lambda x: (-float(x.rating or 0), x.today_count or 0))

    result = []
    for eng in available[:5]:
        result.append({
            'staff_id': eng.staff_id,
            'staff_name': eng.staff_name,
            'skills': eng.skills,
            'rating': float(eng.rating or 0),
            'today_count': eng.today_count or 0,
            'max_daily': eng.max_daily or 10,
            'location': eng.location,
        })
    return result


# ============================================
# 1. CRUD
# ============================================

@bp.route('/api/workorders', methods=['GET'])
@jwt_required()
def get_workorders():
    """获取工单列表 - 支持多条件筛选和分页"""
    try:
        from models.workorder import WorkOrder
        from models.system import SysUser, SysRole

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', '')
        wo_type = request.args.get('wo_type', '')
        status = request.args.get('status', type=int)
        assigned_user_id = request.args.get('assigned_user_id', type=int)
        customer_id = request.args.get('customer_id', type=int)
        date_start = request.args.get('date_start', '')
        date_end = request.args.get('date_end', '')
        min_amount = request.args.get('min_amount', type=float)
        max_amount = request.args.get('max_amount', type=float)

        query = WorkOrder.query

        # 权限：工程师仅查看个人工单
        user_id = get_jwt_identity()
        current_user = SysUser.query.get(user_id)
        if current_user and current_user.role_id:
            role = SysRole.query.get(current_user.role_id)
            if role and 'engineer' in (role.role_code or '').lower():
                query = query.filter(WorkOrder.assigned_user_id == user_id)

        if keyword:
            query = query.filter(
                db.or_(
                    WorkOrder.wo_no.contains(keyword),
                    WorkOrder.customer_name.contains(keyword),
                    WorkOrder.customer_phone.contains(keyword),
                    WorkOrder.customer_company.contains(keyword),
                    WorkOrder.device_sn.contains(keyword),
                    WorkOrder.device_model.contains(keyword),
                    WorkOrder.fault_desc.contains(keyword),
                )
            )
        if wo_type:
            query = query.filter_by(wo_type=wo_type)
        if status is not None:
            query = query.filter_by(status=status)
        if assigned_user_id:
            query = query.filter_by(assigned_user_id=assigned_user_id)
        if customer_id:
            query = query.filter_by(customer_id=customer_id)
        if date_start:
            query = query.filter(WorkOrder.created_at >= date_start)
        if date_end:
            query = query.filter(WorkOrder.created_at <= date_end + ' 23:59:59')
        if min_amount is not None:
            query = query.filter(WorkOrder.total_cost >= min_amount)
        if max_amount is not None:
            query = query.filter(WorkOrder.total_cost <= max_amount)

        total = query.count()
        orders = query.order_by(WorkOrder.created_at.desc()).paginate(
            page=page, per_page=page_size, error_out=False)

        return jsonify({
            'code': 200,
            'data': {
                'list': [{
                    'id': o.id,
                    'wo_no': o.wo_no,
                    'wo_type': o.wo_type,
                    'wo_type_text': WO_TYPE_MAP.get(o.wo_type, o.wo_type or '未知'),
                    'wo_sub_type': o.wo_sub_type,
                    'sub_type_name': WO_SUB_TYPE_MAP.get(o.wo_sub_type, '') if o.wo_sub_type else '',
                    'customer_name': o.customer_name,
                    'customer_phone': o.customer_phone,
                    'customer_company': o.customer_company,
                    'device_type': o.device_type,
                    'device_brand': o.device_brand,
                    'device_model': o.device_model,
                    'fault_desc': o.fault_desc,
                    'status': o.status,
                    'status_text': WO_STATUS_MAP.get(o.status, '未知'),
                    'priority': o.priority,
                    'assigned_user_id': o.assigned_user_id,
                    'assigned_user_name': o.assigned_user_name,
                    'labor_cost': float(o.labor_cost) if o.labor_cost else 0.00,
                    'parts_cost': float(o.parts_cost) if o.parts_cost else 0.00,
                    'total_cost': float(o.total_cost) if o.total_cost else 0.00,
                    'settlement_status': o.settlement_status,
                    'customer_address': o.customer_address,
                    'order_source': '',
                    'service_type': '',
                    'created_at': o.created_at.strftime('%Y-%m-%d %H:%M:%S') if o.created_at else None,
                } for o in orders.items],
                'total': total,
                'page': page,
                'page_size': page_size,
            }
        })
    except Exception as e:
        logger.error(f'获取工单列表失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取工单列表失败: {str(e)}'}), 500


@bp.route('/api/workorders/<int:id>', methods=['GET'])
@jwt_required()
def get_workorder(id):
    """获取工单详情 - 包含配件明细和操作日志"""
    try:
        from models.workorder import (
            WorkOrder, WorkOrderPart, WorkOrderLog, WorkOrderQuoteItem,
            WorkOrderExtend, WoCustomerPart, WoDynamicField, WoSubType,
        )

        order = WorkOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '工单不存在'}), 404

        parts = WorkOrderPart.query.filter_by(wo_id=id).all()
        logs = WorkOrderLog.query.filter_by(wo_id=id).order_by(WorkOrderLog.created_at.desc()).all()
        quote_items = WorkOrderQuoteItem.query.filter_by(work_order_id=id).all()
        extend = WorkOrderExtend.query.filter_by(wo_id=id).first()

        result = to_dict(order)
        result['status_text'] = WO_STATUS_MAP.get(order.status, '未知')
        result['wo_type_text'] = WO_TYPE_MAP.get(order.wo_type, order.wo_type or '未知')
        result['sub_type_name'] = WO_SUB_TYPE_MAP.get(order.wo_sub_type, '') if order.wo_sub_type else ''
        result['reception_user_id'] = order.receiver_id
        result['reception_user_name'] = order.receiver_name
        result['expected_finish_time'] = order.estimated_time.strftime('%Y-%m-%d %H:%M:%S') if order.estimated_time else ''
        result['parts'] = [to_dict(p) for p in parts]
        result['logs'] = [to_dict(l) for l in logs]
        result['quote_items'] = [to_dict(i) for i in quote_items]

        customer_parts = WoCustomerPart.query.filter_by(wo_id=id).all()
        result['customer_parts'] = [to_dict(cp) for cp in customer_parts]

        result['order_source'] = extend.order_source if extend else ''
        result['service_type'] = extend.service_type if extend else ''

        dynamic_fields = WoDynamicField.query.filter_by(wo_id=id).all()
        result['dynamic_fields'] = [{
            'id': df.id, 'field_key': df.field_key,
            'field_value': df.field_value, 'field_label': df.field_label,
        } for df in dynamic_fields]

        if result.get('delivery_products'):
            try:
                result['delivery_products'] = json.loads(result['delivery_products'])
            except Exception:
                result['delivery_products'] = []
        else:
            result['delivery_products'] = []

        if order.wo_type:
            sub_types = WoSubType.query.filter_by(parent_type=order.wo_type, status=1).order_by(WoSubType.sort_order).all()
            result['sub_types'] = [{
                'sub_type_code': s.sub_type_code,
                'sub_type_name': s.sub_type_name,
                'device_category': s.device_category,
            } for s in sub_types]
        else:
            result['sub_types'] = []

        return jsonify({'code': 200, 'data': result})
    except Exception as e:
        logger.error(f'获取工单详情失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取工单详情失败: {str(e)}'}), 500


@bp.route('/api/workorders/init-subtypes', methods=['POST'])
@jwt_required()
def init_wo_subtypes():
    """初始化工单二级分类数据"""
    from models.workorder import WoSubType

    subtypes = [
        # 维修服务
        {'parent_type': 'repair', 'sub_type_code': 'repair_monitor', 'sub_type_name': '监控维修', 'device_category': 'monitor', 'sort_order': 1},
        {'parent_type': 'repair', 'sub_type_code': 'repair_network', 'sub_type_name': '网络维修', 'device_category': 'network', 'sort_order': 2},
        {'parent_type': 'repair', 'sub_type_code': 'repair_printer', 'sub_type_name': '打印维修', 'device_category': 'printer', 'sort_order': 3},
        {'parent_type': 'repair', 'sub_type_code': 'repair_computer', 'sub_type_name': '电脑维修', 'device_category': 'computer', 'sort_order': 4},
        {'parent_type': 'repair', 'sub_type_code': 'repair_other', 'sub_type_name': '其他办公设备维修', 'device_category': 'other', 'sort_order': 5},
        # 维护服务
        {'parent_type': 'maintenance', 'sub_type_code': 'maintenance_monitor', 'sub_type_name': '监控维护', 'device_category': 'monitor', 'sort_order': 1},
        {'parent_type': 'maintenance', 'sub_type_code': 'maintenance_network', 'sub_type_name': '网络维护', 'device_category': 'network', 'sort_order': 2},
        {'parent_type': 'maintenance', 'sub_type_code': 'maintenance_printer', 'sub_type_name': '打印维护', 'device_category': 'printer', 'sort_order': 3},
        {'parent_type': 'maintenance', 'sub_type_code': 'maintenance_computer', 'sub_type_name': '电脑维护', 'device_category': 'computer', 'sort_order': 4},
        {'parent_type': 'maintenance', 'sub_type_code': 'maintenance_other', 'sub_type_name': '其他办公设备维护', 'device_category': 'other', 'sort_order': 5},
        # 检测服务
        {'parent_type': 'inspection', 'sub_type_code': 'inspection_monitor', 'sub_type_name': '监控检测', 'device_category': 'monitor', 'sort_order': 1},
        {'parent_type': 'inspection', 'sub_type_code': 'inspection_network', 'sub_type_name': '网络检测', 'device_category': 'network', 'sort_order': 2},
        {'parent_type': 'inspection', 'sub_type_code': 'inspection_printer', 'sub_type_name': '打印检测', 'device_category': 'printer', 'sort_order': 3},
        {'parent_type': 'inspection', 'sub_type_code': 'inspection_computer', 'sub_type_name': '电脑检测', 'device_category': 'computer', 'sort_order': 4},
        {'parent_type': 'inspection', 'sub_type_code': 'inspection_other', 'sub_type_name': '其他办公设备检测', 'device_category': 'other', 'sort_order': 5},
        # 安装服务
        {'parent_type': 'installation', 'sub_type_code': 'installation_monitor', 'sub_type_name': '监控安装', 'device_category': 'monitor', 'sort_order': 1},
        {'parent_type': 'installation', 'sub_type_code': 'installation_network', 'sub_type_name': '网络安装', 'device_category': 'network', 'sort_order': 2},
        {'parent_type': 'installation', 'sub_type_code': 'installation_printer', 'sub_type_name': '打印安装', 'device_category': 'printer', 'sort_order': 3},
        {'parent_type': 'installation', 'sub_type_code': 'installation_computer', 'sub_type_name': '电脑安装', 'device_category': 'computer', 'sort_order': 4},
        {'parent_type': 'installation', 'sub_type_code': 'installation_other', 'sub_type_name': '其他办公设备安装', 'device_category': 'other', 'sort_order': 5},
    ]

    count = 0
    for st in subtypes:
        existing = WoSubType.query.filter_by(sub_type_code=st['sub_type_code']).first()
        if not existing:
            db.session.add(WoSubType(**st))
            count += 1
    db.session.commit()
    return jsonify({'code': 200, 'message': f'初始化完成，新增 {count} 条二级分类'})


@bp.route('/api/workorders/subtypes', methods=['GET'])
@jwt_required()
def get_wo_subtypes():
    """获取工单二级分类列表"""
    from models.workorder import WoSubType
    parent_type = request.args.get('parent_type', '')
    query = WoSubType.query.filter_by(status=1)
    if parent_type:
        query = query.filter_by(parent_type=parent_type)
    subtypes = query.order_by(WoSubType.sort_order).all()
    return jsonify({
        'code': 200,
        'data': [{
            'id': s.id, 'parent_type': s.parent_type,
            'sub_type_code': s.sub_type_code, 'sub_type_name': s.sub_type_name,
            'device_category': s.device_category,
        } for s in subtypes]
    })


@bp.route('/api/workorders', methods=['POST'])
@jwt_required()
def create_workorder():
    """创建工单 - 根据wo_type接收不同字段，自动生成工单号"""
    try:
        from models.workorder import WorkOrder, WorkOrderExtend, WoDynamicField, WoCustomerPart
        from models.receive import ReceiveOrder

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        # 统一类型转换
        _int_fields = ['priority', 'customer_id', 'receiver_id', 'assigned_user_id',
                       'need_bring_back', 'auto_dispatch', 'device_need_door',
                       'net_need_device', 'goods_quantity', 'goods_need_install',
                       'goods_floor', 'monitor_need_record', 'record_days',
                       'camera_count', 'purchase_qty', 'print_count',
                       'test_result', 'customer_acceptance', 'settlement_status']
        _float_fields = ['labor_hours', 'labor_unit_price', 'service_fee',
                         'estimated_cost', 'purchase_price',
                         'labor_cost', 'parts_cost', 'material_cost',
                         'transport_cost', 'total_cost']
        for f in _int_fields:
            if f in data and data[f] is not None and data[f] != '':
                try:
                    data[f] = int(data[f])
                except (ValueError, TypeError):
                    if f == 'priority':
                        data[f] = 0
                    elif f in ('need_bring_back', 'auto_dispatch', 'device_need_door',
                               'net_need_device', 'goods_need_install', 'monitor_need_record'):
                        data[f] = 0
                    else:
                        data[f] = None
        for f in _float_fields:
            if f in data and data[f] is not None and data[f] != '':
                try:
                    data[f] = float(data[f])
                except (ValueError, TypeError):
                    data[f] = 0

        wo_no = _generate_wo_no()

        order = WorkOrder(
            wo_no=wo_no,
            wo_type=data.get('wo_type'),
            wo_sub_type=data.get('wo_sub_type'),
            customer_id=data.get('customer_id'),
            customer_name=data.get('customer_name'),
            customer_phone=data.get('customer_phone'),
            customer_address=data.get('customer_address'),
            device_type=data.get('device_type'),
            device_brand=data.get('device_brand'),
            device_model=data.get('device_model'),
            device_sn=data.get('device_sn'),
            device_imei=data.get('device_imei'),
            device_password=data.get('device_password'),
            device_need_door=data.get('device_need_door', 0),
            net_type=data.get('net_type'),
            net_operator=data.get('net_operator'),
            net_need_device=data.get('net_need_device', 0),
            goods_type=data.get('goods_type'),
            goods_quantity=data.get('goods_quantity', 1),
            goods_need_install=data.get('goods_need_install', 0),
            goods_floor_type=data.get('goods_floor_type'),
            goods_floor=data.get('goods_floor', 1),
            monitor_brand=data.get('monitor_brand'),
            camera_count=data.get('camera_count', 0),
            camera_location=data.get('camera_location'),
            monitor_need_record=data.get('monitor_need_record', 0),
            record_days=data.get('record_days', 7),
            fault_desc=data.get('fault_desc'),
            appearance_desc=data.get('appearance_desc'),
            accessories=data.get('accessories'),
            remark=data.get('remark'),
            priority=data.get('priority', 0),
            customer_company=data.get('customer_company'),
            customer_office=data.get('customer_office'),
            receiver_id=data.get('receiver_id'),
            receiver_name=data.get('receiver_name'),
            need_bring_back=data.get('need_bring_back', 0),
            auto_dispatch=data.get('auto_dispatch', 0),
            dispatch_rule=data.get('dispatch_rule'),
            labor_hours=data.get('labor_hours'),
            labor_unit_price=data.get('labor_unit_price'),
            service_fee=data.get('service_fee', 0),
            delivery_address=data.get('delivery_address'),
            install_position=data.get('install_position'),
            install_material=data.get('install_material'),
            acceptance_standard=data.get('acceptance_standard'),
            customer_confirm_items=data.get('customer_confirm_items'),
            survey_address=data.get('survey_address'),
            site_environment=data.get('site_environment'),
            device_status_desc=data.get('device_status_desc'),
            problem_summary=data.get('problem_summary'),
            construction_plan=data.get('construction_plan'),
            required_parts=json.dumps(data.get('required_parts')) if isinstance(data.get('required_parts'), (list, dict)) else data.get('required_parts'),
            estimated_duration=data.get('estimated_duration'),
            estimated_cost=data.get('estimated_cost'),
            customer_device_model=data.get('customer_device_model'),
            device_source=data.get('device_source'),
            install_requirement=data.get('install_requirement'),
            consumable_usage=data.get('consumable_usage'),
            purchase_product=data.get('purchase_product'),
            purchase_brand=data.get('purchase_brand'),
            purchase_spec=data.get('purchase_spec'),
            purchase_qty=data.get('purchase_qty'),
            customer_demand=data.get('customer_demand'),
            expected_arrival_date=data.get('expected_arrival_date'),
            purchase_price=data.get('purchase_price'),
            net_topology=data.get('net_topology'),
            fault_location=data.get('fault_location'),
            net_ip=data.get('net_ip'),
            device_port=data.get('device_port'),
            line_type=data.get('line_type'),
            test_items=data.get('test_items'),
            net_speed_data=data.get('net_speed_data'),
            maintenance_cycle=data.get('maintenance_cycle'),
            restart_record=data.get('restart_record'),
            debug_content=data.get('debug_content'),
            device_config=data.get('device_config'),
            os_version=data.get('os_version'),
            error_code=data.get('error_code'),
            repair_part=data.get('repair_part'),
            maintenance_items=data.get('maintenance_items'),
            replaced_parts=json.dumps(data.get('replaced_parts')) if isinstance(data.get('replaced_parts'), (list, dict)) else data.get('replaced_parts'),
            retest_result=data.get('retest_result'),
            channel_no=data.get('channel_no'),
            nvr_model=data.get('nvr_model'),
            disk_capacity=data.get('disk_capacity'),
            recording_status=data.get('recording_status'),
            screen_fault=data.get('screen_fault'),
            infrared_status=data.get('infrared_status'),
            power_status=data.get('power_status'),
            line_inspection=data.get('line_inspection'),
            point_debug_record=data.get('point_debug_record'),
            install_points=data.get('install_points'),
            camera_model=data.get('camera_model'),
            storage_config=data.get('storage_config'),
            cable_length=data.get('cable_length'),
            consumable_qty=data.get('consumable_qty'),
            debug_result=data.get('debug_result'),
            picture_clarity=data.get('picture_clarity'),
            recording_settings=data.get('recording_settings'),
            delivery_products=json.dumps(data.get('delivery_products')) if data.get('delivery_products') else None,
            repair_camera_count=data.get('repair_camera_count', 0),
            status=0,
            status_name='待派单',
            created_by=user_id,
        )
        db.session.add(order)
        db.session.flush()

        if data.get('order_source') or data.get('service_type'):
            extend = WorkOrderExtend(
                wo_id=order.id,
                order_source=data.get('order_source'),
                service_type=data.get('service_type'),
            )
            db.session.add(extend)

        for df in data.get('dynamic_fields', []):
            db.session.add(WoDynamicField(
                wo_id=order.id,
                field_key=df.get('field_key'),
                field_value=str(df.get('field_value', '')),
                field_label=df.get('field_label', ''),
            ))

        for cp in data.get('parts', []):
            db.session.add(WoCustomerPart(
                wo_id=order.id,
                product_id=cp.get('product_id'),
                product_name=cp.get('product_name') or cp.get('part_name', ''),
                specification=cp.get('specification', ''),
                quantity=cp.get('quantity', 1),
                unit_price=cp.get('unit_price', 0),
                remark=cp.get('remark', '客户需求配件'),
            ))

        # need_bring_back=1 自动创建接件单
        if data.get('need_bring_back') == 1:
            try:
                last_ro = ReceiveOrder.query.order_by(ReceiveOrder.id.desc()).first()
                ro_no = generate_code('RO', last_ro.id if last_ro else 0)
                receive_order = ReceiveOrder(
                    receive_no=ro_no,
                    customer_id=data.get('customer_id'),
                    customer_name=data.get('customer_name'),
                    customer_phone=data.get('customer_phone'),
                    receive_type=1,
                    receiver_id=user_id,
                    receiver_name=user_name,
                    remark=f'工单{wo_no}自动创建接件单',
                    created_by=user_id,
                )
                db.session.add(receive_order)
                db.session.flush()
                order.receive_order_id = receive_order.id
            except Exception as e:
                logger.warning(f'自动创建接件单失败: {str(e)}')

        add_wo_log(
            wo_id=order.id,
            action='创建工单',
            old_status=None, new_status=0,
            content=f'创建工单，工单号：{wo_no}，类型：{WO_TYPE_MAP.get(data.get("wo_type", ""), data.get("wo_type", ""))}',
            operator_id=user_id,
            operator_name=user_name,
        )

        db.session.commit()
        return jsonify({'code': 200, 'message': '创建成功', 'data': {'id': order.id, 'wo_no': wo_no}})
    except Exception as e:
        db.session.rollback()
        logger.error(f'创建工单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'创建工单失败: {str(e)}'}), 500


@bp.route('/api/workorders/<int:id>', methods=['PUT'])
@jwt_required()
def update_workorder(id):
    """更新工单"""
    try:
        from models.workorder import WorkOrder, WorkOrderExtend, WoDynamicField

        order = WorkOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '工单不存在'}), 404

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        _int_fields = ['priority', 'customer_id', 'receiver_id', 'assigned_user_id',
                       'need_bring_back', 'auto_dispatch', 'device_need_door',
                       'net_need_device', 'goods_quantity', 'goods_need_install',
                       'goods_floor', 'monitor_need_record', 'record_days',
                       'camera_count', 'purchase_qty', 'print_count',
                       'test_result', 'customer_acceptance', 'settlement_status']
        _float_fields = ['labor_hours', 'labor_unit_price', 'service_fee',
                         'estimated_cost', 'purchase_price',
                         'labor_cost', 'parts_cost', 'material_cost',
                         'transport_cost', 'total_cost']
        for f in _int_fields:
            if f in data and data[f] is not None and data[f] != '':
                try:
                    data[f] = int(data[f])
                except (ValueError, TypeError):
                    data[f] = 0 if f == 'priority' else None
        for f in _float_fields:
            if f in data and data[f] is not None and data[f] != '':
                try:
                    data[f] = float(data[f])
                except (ValueError, TypeError):
                    data[f] = 0

        updatable_fields = [
            'wo_type', 'wo_sub_type', 'customer_id', 'customer_name', 'customer_phone',
            'customer_address', 'customer_company', 'customer_office',
            'device_type', 'device_brand', 'device_model', 'device_sn',
            'device_imei', 'device_password', 'device_need_door',
            'net_type', 'net_operator', 'net_need_device',
            'goods_type', 'goods_quantity', 'goods_need_install', 'goods_floor_type', 'goods_floor',
            'monitor_brand', 'camera_count', 'camera_location', 'monitor_need_record', 'record_days',
            'fault_desc', 'appearance_desc', 'accessories', 'remark', 'priority',
            'receiver_id', 'receiver_name', 'auto_dispatch', 'dispatch_rule',
            'labor_hours', 'labor_unit_price', 'service_fee',
            'delivery_address', 'install_position', 'arrival_time',
            'install_material', 'acceptance_standard', 'customer_confirm_items',
            'survey_address', 'site_environment', 'device_status_desc',
            'problem_summary', 'construction_plan', 'required_parts',
            'estimated_duration', 'estimated_cost',
            'customer_device_model', 'device_source', 'install_requirement',
            'consumable_usage', 'purchase_product', 'purchase_brand', 'purchase_spec',
            'purchase_qty', 'customer_demand', 'expected_arrival_date', 'purchase_price',
            'net_topology', 'fault_location', 'net_ip', 'device_port', 'line_type',
            'test_items', 'net_speed_data', 'maintenance_cycle', 'restart_record', 'debug_content',
            'device_config', 'os_version', 'error_code', 'repair_part',
            'maintenance_items', 'replaced_parts', 'retest_result',
            'channel_no', 'nvr_model', 'disk_capacity', 'recording_status',
            'screen_fault', 'infrared_status', 'power_status',
            'line_inspection', 'point_debug_record',
            'install_points', 'camera_model', 'storage_config', 'cable_length',
            'consumable_qty', 'debug_result', 'picture_clarity', 'recording_settings',
            'labor_cost', 'parts_cost', 'material_cost', 'transport_cost', 'total_cost',
            'assigned_user_id', 'assigned_user_name',
            'delivery_products', 'repair_camera_count',
            'estimated_time',
        ]
        field_mapping = {
            'reception_user_id': 'receiver_id',
            'reception_user_name': 'receiver_name',
            'expected_finish_time': 'estimated_time',
        }

        for field in updatable_fields:
            if field in data:
                value = data[field]
                if field in ('required_parts', 'replaced_parts', 'finish_photos') and isinstance(value, (list, dict)):
                    value = json.dumps(value, ensure_ascii=False)
                if field == 'delivery_products' and isinstance(value, (list, dict)):
                    value = json.dumps(value, ensure_ascii=False)
                setattr(order, field, value)

        for frontend_field, backend_field in field_mapping.items():
            if frontend_field in data:
                value = data[frontend_field]
                if backend_field == 'estimated_time' and value:
                    try:
                        if isinstance(value, str):
                            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    except Exception:
                        pass
                setattr(order, backend_field, value)

        dynamic_fields = data.get('dynamic_fields', [])
        if dynamic_fields:
            WoDynamicField.query.filter_by(wo_id=id).delete()
            for df in dynamic_fields:
                db.session.add(WoDynamicField(
                    wo_id=id,
                    field_key=df.get('field_key'),
                    field_value=str(df.get('field_value', '')),
                    field_label=df.get('field_label', ''),
                ))

        if 'order_source' in data or 'service_type' in data:
            extend = WorkOrderExtend.query.filter_by(wo_id=id).first()
            if extend:
                if 'order_source' in data:
                    extend.order_source = data.get('order_source')
                if 'service_type' in data:
                    extend.service_type = data.get('service_type')
            else:
                db.session.add(WorkOrderExtend(
                    wo_id=id,
                    order_source=data.get('order_source'),
                    service_type=data.get('service_type'),
                ))

        add_wo_log(
            wo_id=id, action='更新工单',
            old_status=order.status, new_status=order.status,
            content='更新工单信息',
            operator_id=user_id, operator_name=user_name,
        )

        db.session.commit()
        return jsonify({'code': 200, 'message': '更新成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新工单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'更新工单失败: {str(e)}'}), 500


@bp.route('/api/workorders/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_workorder(id):
    """删除工单 - 只有状态为待派单(0)或已取消(7)的工单才能删除"""
    try:
        from models.workorder import (
            WorkOrder, WorkOrderPart, WorkOrderQuoteItem, WorkOrderLog,
            WorkOrderExtend, WoCustomerPart,
        )
        order = WorkOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '工单不存在'}), 404
        if order.status not in (0, 7):
            return jsonify({'code': 400, 'message': f'当前状态为【{WO_STATUS_MAP.get(order.status, "未知")}】，只有待派单或已取消的工单才能删除'}), 400

        WorkOrderPart.query.filter_by(wo_id=id).delete()
        WorkOrderQuoteItem.query.filter_by(work_order_id=id).delete()
        WorkOrderLog.query.filter_by(wo_id=id).delete()
        WorkOrderExtend.query.filter_by(wo_id=id).delete()
        WoCustomerPart.query.filter_by(wo_id=id).delete()
        db.session.delete(order)
        db.session.commit()
        return jsonify({'code': 200, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除工单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'删除工单失败: {str(e)}'}), 500



# ============================================
# 2. 日志
# ============================================

@bp.route('/api/workorders/<int:id>/logs', methods=['GET'])
@jwt_required()
def get_workorder_logs(id):
    """获取工单操作日志"""
    try:
        from models.workorder import WorkOrder, WorkOrderLog
        order = WorkOrder.query.get(id)
        if not order:
            return jsonify({'code': 404, 'message': '工单不存在'}), 404

        logs = WorkOrderLog.query.filter_by(wo_id=id).order_by(WorkOrderLog.created_at.desc()).all()
        return jsonify({
            'code': 200,
            'data': [{
                'id': l.id, 'action': l.action,
                'old_status': l.old_status,
                'old_status_text': WO_STATUS_MAP.get(l.old_status, '') if l.old_status is not None else '',
                'new_status': l.new_status,
                'new_status_text': WO_STATUS_MAP.get(l.new_status, '') if l.new_status is not None else '',
                'content': l.content,
                'operator_id': l.operator_id,
                'operator_name': l.operator_name,
                'created_at': l.created_at.strftime('%Y-%m-%d %H:%M:%S') if l.created_at else None,
            } for l in logs]
        })
    except Exception as e:
        logger.error(f'获取操作日志失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取操作日志失败: {str(e)}'}), 500


@bp.route('/api/workorders/auto-dispatch', methods=['GET'])
@jwt_required()
def get_auto_dispatch_recommendation():
    """获取自动派单推荐 - 根据工单类型匹配工程师"""
    try:
        wo_type = request.args.get('wo_type', '')
        if not wo_type:
            return jsonify({'code': 400, 'message': '请提供工单类型(wo_type)'}), 400

        recommendations = _auto_dispatch_engineer(wo_type)
        return jsonify({
            'code': 200,
            'data': {
                'wo_type': wo_type,
                'wo_type_text': WO_TYPE_MAP.get(wo_type, wo_type),
                'recommendations': recommendations,
            }
        })
    except Exception as e:
        logger.error(f'获取自动派单推荐失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取自动派单推荐失败: {str(e)}'}), 500


# ============================================
# 3. 配件管理
# ============================================

@bp.route('/api/workorders/<int:wo_id>/parts', methods=['GET'])
@jwt_required()
def get_workorder_parts(wo_id):
    """获取工单配件列表"""
    try:
        from models.workorder import WorkOrderPart
        parts = WorkOrderPart.query.filter_by(wo_id=wo_id).all()
        return jsonify({
            'code': 200,
            'data': [{
                'id': p.id, 'product_id': p.product_id,
                'product_name': p.product_name, 'product_code': p.product_code,
                'specification': p.specification,
                'quantity': float(p.quantity) if p.quantity else 0,
                'used_quantity': float(p.used_quantity) if p.used_quantity else 0,
                'unit_price': float(p.unit_price) if p.unit_price else 0,
                'total_price': float(p.total_price) if p.total_price else 0,
                'cost_price': float(p.cost_price) if p.cost_price else 0,
                'is_own': p.is_own, 'status': p.status, 'remark': p.remark,
                'created_at': p.created_at.strftime('%Y-%m-%d %H:%M:%S') if p.created_at else None,
            } for p in parts]
        })
    except Exception as e:
        logger.error(f'获取工单配件列表失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取工单配件列表失败: {str(e)}'}), 500


@bp.route('/api/workorders/<int:wo_id>/parts', methods=['POST'])
@jwt_required()
def add_workorder_part(wo_id):
    """添加工单配件"""
    try:
        from models.workorder import WorkOrder, WorkOrderPart
        order = WorkOrder.query.get(wo_id)
        if not order:
            return jsonify({'code': 404, 'message': '工单不存在'}), 404

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        part = WorkOrderPart(
            wo_id=wo_id,
            product_id=data.get('product_id'),
            product_name=data.get('product_name'),
            product_code=data.get('product_code'),
            quantity=data.get('quantity', 1),
            unit_price=data.get('unit_price', 0),
            total_price=float(data.get('quantity', 1)) * float(data.get('unit_price', 0)),
            cost_price=data.get('cost_price', 0),
            is_own=data.get('is_own', 1),
            status=0,
            remark=data.get('remark'),
        )
        db.session.add(part)
        db.session.flush()

        add_wo_log(
            wo_id=wo_id, action='添加配件',
            old_status=order.status, new_status=order.status,
            content=f'添加配件：{data.get("product_name", "")} x {data.get("quantity", 1)}',
            operator_id=user_id, operator_name=user_name,
        )

        db.session.commit()
        return jsonify({'code': 200, 'message': '添加成功', 'data': {'id': part.id}})
    except Exception as e:
        db.session.rollback()
        logger.error(f'添加工单配件失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'添加工单配件失败: {str(e)}'}), 500


@bp.route('/api/workorders/<int:wo_id>/parts/<int:part_id>', methods=['PUT'])
@jwt_required()
def update_workorder_part(wo_id, part_id):
    """更新工单配件"""
    try:
        from models.workorder import WorkOrderPart
        part = WorkOrderPart.query.get(part_id)
        if not part or part.wo_id != wo_id:
            return jsonify({'code': 404, 'message': '配件不存在'}), 404

        data = request.get_json()
        user_id = get_jwt_identity()
        user_name = _get_current_user_name()

        for field in ['quantity', 'unit_price', 'is_own', 'status', 'remark',
                      'product_name', 'product_code', 'cost_price']:
            if field in data:
                setattr(part, field, data[field])

        if 'quantity' in data or 'unit_price' in data:
            part.total_price = float(part.quantity or 0) * float(part.unit_price or 0)

        add_wo_log(
            wo_id=wo_id, action='更新配件',
            old_status=None, new_status=None,
            content=f'更新配件ID:{part_id}',
            operator_id=user_id, operator_name=user_name,
        )

        db.session.commit()
        return jsonify({'code': 200, 'message': '更新成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新工单配件失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'更新工单配件失败: {str(e)}'}), 500


@bp.route('/api/workorders/<int:wo_id>/parts/<int:part_id>', methods=['DELETE'])
@jwt_required()
def delete_workorder_part(wo_id, part_id):
    """删除工单配件"""
    try:
        from models.workorder import WorkOrderPart
        part = WorkOrderPart.query.get(part_id)
        if not part or part.wo_id != wo_id:
            return jsonify({'code': 404, 'message': '配件不存在'}), 404

        part_name = part.product_name or ''
        db.session.delete(part)

        user_id = get_jwt_identity()
        add_wo_log(
            wo_id=wo_id, action='删除配件',
            old_status=None, new_status=None,
            content=f'删除配件：{part_name}',
            operator_id=user_id, operator_name=user_name,
        )

        db.session.commit()
        return jsonify({'code': 200, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除工单配件失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'删除工单配件失败: {str(e)}'}), 500


# ============================================
# 4. 批量删除
# ============================================

@bp.route('/api/workorders/batch-delete', methods=['POST'])
@jwt_required()
def batch_delete_workorders():
    """批量删除工单"""
    try:
        from models.workorder import WorkOrder
        data = request.get_json()
        ids = data.get('ids', [])
        if not ids:
            return jsonify({'code': 400, 'message': '请选择要删除的工单'}), 400
        completed = WorkOrder.query.filter(WorkOrder.id.in_(ids), WorkOrder.status == 6).all()
        if completed:
            return jsonify({'code': 400, 'message': '选中的工单中包含已完成的工单，无法删除'}), 400
        workorders = WorkOrder.query.filter(WorkOrder.id.in_(ids)).all()
        count = len(workorders)
        for wo in workorders:
            db.session.delete(wo)
        db.session.commit()
        return jsonify({'code': 200, 'message': f'成功删除{count}个工单'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': '批量删除工单失败，请稍后重试'}), 500


# ============================================
# 5. 导出
# ============================================

@bp.route('/api/workorders/export', methods=['GET'])
@jwt_required()
def export_workorders():
    """导出工单Excel"""
    try:
        from models.workorder import WorkOrder
        keyword = request.args.get('keyword', '')
        status = request.args.get('status', type=int)
        wo_type = request.args.get('wo_type', '')
        date_start = request.args.get('date_start', '')
        date_end = request.args.get('date_end', '')

        query = WorkOrder.query
        if keyword:
            query = query.filter(db.or_(
                WorkOrder.wo_no.contains(keyword),
                WorkOrder.customer_name.contains(keyword),
                WorkOrder.customer_phone.contains(keyword),
                WorkOrder.customer_company.contains(keyword),
            ))
        if status is not None:
            query = query.filter(WorkOrder.status == status)
        if wo_type:
            query = query.filter(WorkOrder.wo_type == wo_type)
        if date_start:
            query = query.filter(WorkOrder.created_at >= date_start)
        if date_end:
            query = query.filter(WorkOrder.created_at <= date_end + ' 23:59:59')

        orders = query.order_by(WorkOrder.created_at.desc()).all()
        data = []
        for o in orders:
            data.append({
                '工单号': o.wo_no,
                '工单类型': WO_TYPE_MAP.get(o.wo_type, o.wo_type or ''),
                '客户名称': o.customer_name,
                '客户单位': o.customer_company or '',
                '客户电话': o.customer_phone,
                '设备类型': o.device_type or '',
                '设备品牌': o.device_brand or '',
                '设备型号': o.device_model or '',
                '故障描述': o.fault_desc or '',
                '人工费': float(o.labor_cost or 0),
                '配件费': float(o.parts_cost or 0),
                '材料费': float(o.material_cost or 0),
                '总费用': float(o.total_cost or 0),
                '状态': WO_STATUS_MAP.get(o.status, str(o.status)),
                '指派工程师': o.assigned_user_name or '',
                '创建时间': o.created_at.strftime('%Y-%m-%d %H:%M') if o.created_at else '',
            })

        output = io.BytesIO()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = '工单列表'
        headers = ['工单号', '工单类型', '客户名称', '客户单位', '客户电话',
                   '设备类型', '设备品牌', '设备型号', '故障描述',
                   '人工费', '配件费', '材料费', '总费用', '状态',
                   '指派工程师', '创建时间']
        ws.append(headers)
        for row in data:
            ws.append(list(row.values()))
        wb.save(output)
        output.seek(0)

        return send_file(
            output, as_attachment=True,
            download_name=f'工单列表_{datetime.now().strftime("%Y%m%d")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
    except Exception as e:
        logger.error(f'导出工单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'导出工单失败: {str(e)}'}), 500
