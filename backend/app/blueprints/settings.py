"""系统设置蓝图（工单类型 + 项目 + 打印模板 + 角色 + 权限 + 用户 + 系统日志）。

迁移自 source-code/app.py 中以下区段的原始路由代码：
- /api/settings/wo-types /projects /print-templates*  4534-4665 行附近
- /api/settings/roles + /roles/<id>/permissions      14631-14825 行附近
- /api/settings/permissions*                         14827-14922 行附近
- /api/settings/users + /users/<id>/{status,password,roles}  14924-15175 行附近
- /api/settings/init-permissions                     15178 行附近
- /api/settings/logs                                 15067, 15102 行附近

业务规则：
- 角色/权限：维护多对多关系（Role-Permission、User-Role）
- 密码：使用 bcrypt 加密，参考 auth 蓝图
- 状态：用户启用/禁用切换
- 系统日志：记录关键操作（用户/角色/权限变更），仅 GET + DELETE

跨子域依赖：
- SysUser / SysRole / SysPermission / SysLog  (models.system)
- WorkOrderType / Project                    (models.workorder)
- PrintTemplate                             (models.print_templates 或 models.print_template)

直接 import 当前蓝图用得到的本地 helper，其他跨子域模型按"函数内懒加载"惯例。
"""
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from werkzeug.security import generate_password_hash

from extensions import db
from app.utils import to_dict
from app.security import get_current_user_id

logger = logging.getLogger(__name__)

bp = Blueprint('settings', __name__)


# ============================================
# A) 工单类型 / 项目 / 打印模板
# ============================================

@bp.route('/api/settings/wo-types', methods=['GET'])
@jwt_required()
def get_wo_types():
    """获取工单类型列表"""
    from models.workorder import WoType
    types = WoType.query.filter_by(status=1).order_by(WoType.sort_order).all()
    return jsonify({
        'code': 200,
        'data': [to_dict(t) for t in types]
    })

@bp.route('/api/settings/projects', methods=['GET'])
@jwt_required()
def get_projects():
    """获取维修项目列表"""
    from models.workorder import Project
    projects = Project.query.filter_by(status=1).all()
    return jsonify({
        'code': 200,
        'data': [to_dict(p) for p in projects]
    })

# 打印模板管理
@bp.route('/api/settings/print-templates', methods=['GET'])
@jwt_required()
def get_print_templates():
    """获取打印模板列表"""
    from models.printer import PrintTemplate
    template_type = request.args.get('template_type', '')
    query = PrintTemplate.query.filter_by(status=1)
    if template_type:
        query = query.filter_by(template_type=template_type)
    templates = query.order_by(PrintTemplate.is_default.desc(), PrintTemplate.id).all()
    return jsonify({'code': 200, 'data': [to_dict(t) for t in templates]})

@bp.route('/api/settings/print-templates', methods=['POST'])
@jwt_required()
def create_print_template():
    """新增打印模板"""
    from models.printer import PrintTemplate
    data = request.get_json()
    template = PrintTemplate(
        template_name=data.get('template_name'),
        template_type=data.get('template_type'),
        description=data.get('description', ''),
        header_content=data.get('header_content', ''),
        body_content=data.get('body_content', ''),
        footer_content=data.get('footer_content', ''),
        style_content=data.get('style_content', ''),
        paper_size=data.get('paper_size', 'A4'),
        paper_width=data.get('paper_width', 210),
        paper_height=data.get('paper_height', 297),
        is_default=data.get('is_default', 0),
        status=1
    )
    if template.is_default:
        PrintTemplate.query.filter_by(template_type=template.template_type).update({'is_default': 0})
    db.session.add(template)
    db.session.commit()
    return jsonify({'code': 200, 'message': '创建成功', 'data': {'id': template.id}})

@bp.route('/api/settings/print-templates/<int:id>', methods=['PUT'])
@jwt_required()
def update_print_template(id):
    """更新打印模板"""
    from models.printer import PrintTemplate
    template = PrintTemplate.query.get(id)
    if not template:
        return jsonify({'code': 404, 'message': '模板不存在'}), 404
    data = request.get_json()
    for field in ['template_name', 'template_type', 'description', 'header_content', 'body_content', 'footer_content', 'style_content', 'paper_size', 'paper_width', 'paper_height']:
        if field in data:
            setattr(template, field, data[field])
    # 处理默认值：显式传入 is_default 时进行切换
    if 'is_default' in data:
        if data['is_default']:
            # 设为默认：先清除同类型所有模板的默认值，再设置当前模板
            PrintTemplate.query.filter_by(template_type=template.template_type).update({'is_default': 0})
            template.is_default = 1
        else:
            # 取消默认：仅清除当前模板的默认值
            template.is_default = 0
    db.session.commit()
    return jsonify({'code': 200, 'message': '更新成功'})

@bp.route('/api/settings/print-templates/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_print_template(id):
    """删除打印模板"""
    from models.printer import PrintTemplate
    template = PrintTemplate.query.get(id)
    if not template:
        return jsonify({'code': 404, 'message': '模板不存在'}), 404
    db.session.delete(template)
    db.session.commit()
    return jsonify({'code': 200, 'message': '删除成功'})

@bp.route('/api/settings/print-templates/init-defaults', methods=['POST'])
@jwt_required()
def init_default_print_templates():
    """初始化默认打印模板"""
    from models.printer import PrintTemplate
    # 先清空旧模板数据
    PrintTemplate.query.delete()
    db.session.flush()

    templates = [
        # === 工单管理 (work_order) ===
        {'template_name': '工单-标准A4', 'template_type': 'work_order', 'paper_size': 'A5', 'is_default': 1,
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>维修工单</h1><p>工单号：{{wo_no}} | 日期：{{created_at}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">客户信息</th></tr><tr><td>客户姓名：{{customer_name}}</td><td>联系电话：{{customer_phone}}</td><td>设备品牌：{{device_brand}}</td><td>设备型号：{{device_model}}</td></tr><tr><th colspan="4" style="background:#f0f0f0">故障描述</th></tr><tr><td colspan="4">{{fault_desc}}</td></tr><tr><th colspan="4" style="background:#f0f0f0">维修项目</th></tr><tr><td colspan="4">{{repair_items}}</td></tr><tr><th colspan="4" style="background:#f0f0f0">费用明细</th></tr><tr><td colspan="4">{{fee_detail}}</td></tr><tr><td colspan="2">合计金额：</td><td colspan="2" style="font-weight:bold">¥{{total_amount}}</td></tr></table>',
         'footer_content': '<div style="margin-top:40px;display:flex;justify-content:space-between"><div>客户签字：______________</div><div>工程师签字：______________</div><div>日期：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},
        {'template_name': '工单-简洁A5', 'template_type': 'work_order', 'paper_size': 'A5', 'paper_width': 148, 'paper_height': 210,
         'header_content': '<div style="text-align:center"><h2>维修工单</h2></div>',
         'body_content': '<p>工单号：{{wo_no}} | {{created_at}}</p><p>客户：{{customer_name}} | 电话：{{customer_phone}}</p><p>设备：{{device_brand}} {{device_model}}</p><hr><p>故障：{{fault_desc}}</p><p>维修：{{repair_items}}</p><hr><p style="font-weight:bold">合计：¥{{total_amount}}</p>',
         'footer_content': '<p>客户签字：______ 工程师：______</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:11px;padding:15px}'},
        {'template_name': '工单-详细带条码', 'template_type': 'work_order', 'paper_size': 'A5',
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>维修工单（详细）</h1><p>工单号：{{wo_no}}</p><div style="margin:10px 0">[条码区域: {{wo_no}}]</div><p>日期：{{created_at}} | 状态：{{status_name}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">客户信息</th></tr><tr><td>客户姓名：{{customer_name}}</td><td>联系电话：{{customer_phone}}</td><td>设备品牌：{{device_brand}}</td><td>设备型号：{{device_model}}</td></tr><tr><td>设备SN：{{device_sn}}</td><td>设备类型：{{device_type}}</td><td>工单类型：{{wo_type_name}}</td><td>优先级：{{priority_name}}</td></tr><tr><th colspan="4" style="background:#f0f0f0">故障描述</th></tr><tr><td colspan="4">{{fault_desc}}</td></tr><tr><th colspan="4" style="background:#f0f0f0">维修项目及配件</th></tr><tr><td colspan="4">{{repair_items}}</td></tr><tr><th colspan="4" style="background:#f0f0f0">费用明细</th></tr><tr><td colspan="4">{{fee_detail}}</td></tr><tr><td colspan="2">合计金额：</td><td colspan="2" style="font-weight:bold;font-size:16px">¥{{total_amount}}</td></tr><tr><td colspan="4">备注：{{remark}}</td></tr></table>',
         'footer_content': '<div style="margin-top:40px;display:flex;justify-content:space-between"><div>客户签字：______________</div><div>工程师签字：______________</div><div>日期：______________</div></div><p style="text-align:center;color:#999;font-size:10px;margin-top:20px">此单一式两联，客户联和存根联</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},

        # === 接件管理 (receive) ===
        {'template_name': '接件单-标准A4', 'template_type': 'receive', 'paper_size': 'A5', 'is_default': 1,
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>设备接件单</h1><p>接件单号：{{receive_no}} | 日期：{{created_at}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">客户信息</th></tr><tr><td>客户姓名：{{customer_name}}</td><td>联系电话：{{customer_phone}}</td><td colspan="2">地址：{{address}}</td></tr><tr><th colspan="4" style="background:#f0f0f0">设备信息</th></tr><tr><td>设备品牌：{{device_brand}}</td><td>设备型号：{{device_model}}</td><td>设备SN：{{device_sn}}</td><td>设备类型：{{device_type}}</td></tr><tr><th colspan="4" style="background:#f0f0f0">故障描述</th></tr><tr><td colspan="4">{{fault_desc}}</td></tr><tr><th colspan="4" style="background:#f0f0f0">外观检查</th></tr><tr><td colspan="4">{{appearance}}</td></tr><tr><td>附件：{{accessories}}</td><td colspan="3">预计费用：¥{{estimate_amount}}</td></tr></table>',
         'footer_content': '<div style="margin-top:40px;display:flex;justify-content:space-between"><div>客户签字：______________</div><div>接待人：______________</div><div>日期：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},
        {'template_name': '接件单-简洁版', 'template_type': 'receive', 'paper_size': 'A5', 'paper_width': 148, 'paper_height': 210,
         'header_content': '<h2 style="text-align:center">接件单</h2>',
         'body_content': '<p>单号：{{receive_no}} | {{created_at}}</p><p>客户：{{customer_name}} | {{customer_phone}}</p><p>设备：{{device_brand}} {{device_model}}</p><p>故障：{{fault_desc}}</p><p>预计费用：¥{{estimate_amount}}</p>',
         'footer_content': '<p>客户签字：______ 接待人：______</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:11px;padding:15px}'},
        {'template_name': '接件单-带照片', 'template_type': 'receive', 'paper_size': 'A5',
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>设备接件单（含照片）</h1><p>接件单号：{{receive_no}} | 日期：{{created_at}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="2" style="background:#f0f0f0">客户信息</th><th colspan="2" style="background:#f0f0f0">设备信息</th></tr><tr><td>客户：{{customer_name}}</td><td>电话：{{customer_phone}}</td><td>品牌：{{device_brand}}</td><td>型号：{{device_model}}</td></tr><tr><th colspan="4" style="background:#f0f0f0">故障描述</th></tr><tr><td colspan="4">{{fault_desc}}</td></tr><tr><th colspan="4" style="background:#f0f0f0">设备照片</th></tr><tr><td colspan="4" style="text-align:center;height:150px">[设备照片区域]</td></tr><tr><th colspan="4" style="background:#f0f0f0">外观及附件</th></tr><tr><td colspan="4">{{appearance}} | 附件：{{accessories}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px"><p>客户签字：______________ 接待人：______________</p></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},

        # === 派单管理 (dispatch) ===
        {'template_name': '派工单-标准A4', 'template_type': 'dispatch', 'paper_size': 'A5', 'is_default': 1,
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>派工单</h1><p>工单号：{{wo_no}} | 派单时间：{{dispatch_time}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th style="background:#f0f0f0" width="25%">客户信息</th><td>{{customer_name}} | {{customer_phone}}</td></tr><tr><th style="background:#f0f0f0">设备信息</th><td>{{device_brand}} {{device_model}} | SN:{{device_sn}}</td></tr><tr><th style="background:#f0f0f0">故障描述</th><td>{{fault_desc}}</td></tr><tr><th style="background:#f0f0f0">指派工程师</th><td>{{engineer_name}} | {{engineer_phone}}</td></tr><tr><th style="background:#f0f0f0">优先级</th><td>{{priority}}</td></tr><tr><th style="background:#f0f0f0">要求完成时间</th><td>{{deadline}}</td></tr><tr><th style="background:#f0f0f0">备注</th><td>{{remark}}</td></tr></table>',
         'footer_content': '<div style="margin-top:40px;display:flex;justify-content:space-between"><div>派单人：______________</div><div>工程师签字：______________</div><div>日期：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},
        {'template_name': '派工单-简洁版', 'template_type': 'dispatch', 'paper_size': 'A5', 'paper_width': 148, 'paper_height': 210,
         'header_content': '<h2 style="text-align:center">派工单</h2>',
         'body_content': '<p>工单号：{{wo_no}}</p><p>客户：{{customer_name}} | {{customer_phone}}</p><p>设备：{{device_brand}} {{device_model}}</p><p>工程师：{{engineer_name}} | {{engineer_phone}}</p><p>故障：{{fault_desc}}</p>',
         'footer_content': '<p>派单人：______ 工程师：______</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:11px;padding:15px}'},
        {'template_name': '派工单-详细版', 'template_type': 'dispatch', 'paper_size': 'A5',
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>派工单（详细）</h1><p>工单号：{{wo_no}} | 派单时间：{{dispatch_time}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">工单信息</th></tr><tr><td>工单号：{{wo_no}}</td><td>工单类型：{{wo_type}}</td><td>优先级：{{priority}}</td><td>截止时间：{{deadline}}</td></tr><tr><th colspan="4" style="background:#f0f0f0">客户信息</th></tr><tr><td>姓名：{{customer_name}}</td><td>电话：{{customer_phone}}</td><td>地址：{{address}}</td><td></td></tr><tr><th colspan="4" style="background:#f0f0f0">设备信息</th></tr><tr><td>品牌：{{device_brand}}</td><td>型号：{{device_model}}</td><td>SN：{{device_sn}}</td><td>类型：{{device_type}}</td></tr><tr><th colspan="4" style="background:#f0f0f0">故障描述</th></tr><tr><td colspan="4">{{fault_desc}}</td></tr><tr><th colspan="4" style="background:#f0f0f0">派工信息</th></tr><tr><td>工程师：{{engineer_name}}</td><td>电话：{{engineer_phone}}</td><td>派单人：{{dispatcher_name}}</td><td>派单方式：{{dispatch_type}}</td></tr><tr><th colspan="4" style="background:#f0f0f0">备注</th></tr><tr><td colspan="4">{{remark}}</td></tr></table>',
         'footer_content': '<div style="margin-top:40px;display:flex;justify-content:space-between"><div>派单人：______________</div><div>工程师签字：______________</div><div>日期：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},

        # === 报价管理 (quote) ===
        {'template_name': '报价单-标准A4', 'template_type': 'quote', 'paper_size': 'A5', 'is_default': 1,
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>维修报价单</h1><p>报价单号：{{quote_no}} | 日期：{{created_at}}</p><p>有效期：{{valid_days}}天</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">客户信息</th></tr><tr><td>客户姓名：{{customer_name}}</td><td>联系电话：{{customer_phone}}</td><td colspan="2">设备：{{device_brand}} {{device_model}}</td></tr><tr><th style="background:#f0f0f0">序号</th><th style="background:#f0f0f0">项目</th><th style="background:#f0f0f0">金额</th><th style="background:#f0f0f0">备注</th></tr>{{items}}<tr><td colspan="2" style="text-align:right;font-weight:bold">合计</td><td colspan="2" style="font-weight:bold">¥{{total_amount}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px"><p>报价说明：{{remark}}</p><p>客户签字：______________ 日期：______________</p></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},
        {'template_name': '报价单-简洁版', 'template_type': 'quote', 'paper_size': 'A5', 'paper_width': 148, 'paper_height': 210,
         'header_content': '<h2 style="text-align:center">报价单</h2>',
         'body_content': '<p>单号：{{quote_no}} | {{created_at}}</p><p>客户：{{customer_name}} | {{customer_phone}}</p><p>设备：{{device_brand}} {{device_model}}</p><hr><p>{{items}}</p><p style="font-weight:bold">合计：¥{{total_amount}}</p>',
         'footer_content': '<p>签字：______ 日期：______</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:11px;padding:15px}'},
        {'template_name': '报价单-详细带条款', 'template_type': 'quote', 'paper_size': 'A5',
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>维修报价单（正式）</h1><p>报价单号：{{quote_no}} | 报价日期：{{created_at}} | 有效期：{{valid_days}}天</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">客户信息</th></tr><tr><td>客户：{{customer_name}}</td><td>电话：{{customer_phone}}</td><td>设备：{{device_brand}} {{device_model}}</td><td>SN：{{device_sn}}</td></tr><tr><th style="background:#f0f0f0">序号</th><th style="background:#f0f0f0">维修项目</th><th style="background:#f0f0f0">单价</th><th style="background:#f0f0f0">小计</th></tr>{{items}}<tr><td colspan="2" style="text-align:right;font-weight:bold">合计</td><td colspan="2" style="font-weight:bold;font-size:16px">¥{{total_amount}}</td></tr></table><h3>服务条款</h3><ol><li>维修后保修{{warranty_days}}天</li><li>报价有效期内价格不变</li><li>如需额外配件将另行通知</li></ol>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>客户签字：______________</div><div>报价人：______________</div><div>日期：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},

        # === 销售管理 (sale) ===
        {'template_name': '销售单-标准A4', 'template_type': 'sale', 'paper_size': 'A5', 'is_default': 1,
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>销售单</h1><p>销售单号：{{sale_no}} | 日期：{{sale_date}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">客户信息</th></tr><tr><td>客户名称：{{customer_name}}</td><td>联系电话：{{customer_phone}}</td><td colspan="2">地址：{{address}}</td></tr><tr><th style="background:#f0f0f0">序号</th><th style="background:#f0f0f0">商品名称</th><th style="background:#f0f0f0">数量</th><th style="background:#f0f0f0">金额</th></tr>{{items}}<tr><td colspan="2" style="text-align:right;font-weight:bold">合计</td><td colspan="2" style="font-weight:bold">¥{{total_amount}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>客户签字：______________</div><div>经办人：______________</div><div>日期：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},
        {'template_name': '销售单-简洁版', 'template_type': 'sale', 'paper_size': 'A5', 'paper_width': 148, 'paper_height': 210,
         'header_content': '<h2 style="text-align:center">销售单</h2>',
         'body_content': '<p>单号：{{sale_no}} | {{sale_date}}</p><p>客户：{{customer_name}}</p><hr><p>{{items}}</p><p style="font-weight:bold">合计：¥{{total_amount}}</p>',
         'footer_content': '<p>签字：______</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:11px;padding:15px}'},
        {'template_name': '销售单-含税版', 'template_type': 'sale', 'paper_size': 'A5',
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>销售单（含税）</h1><p>销售单号：{{sale_no}} | 日期：{{sale_date}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">客户信息</th></tr><tr><td>客户：{{customer_name}}</td><td>电话：{{customer_phone}}</td><td>地址：{{address}}</td><td></td></tr><tr><th style="background:#f0f0f0">序号</th><th style="background:#f0f0f0">商品</th><th style="background:#f0f0f0">数量×单价</th><th style="background:#f0f0f0">金额</th></tr>{{items}}<tr><td colspan="2" style="text-align:right">小计</td><td colspan="2">¥{{subtotal}}</td></tr><tr><td colspan="2" style="text-align:right">税额</td><td colspan="2">¥{{tax_amount}}</td></tr><tr><td colspan="2" style="text-align:right;font-weight:bold">合计（含税）</td><td colspan="2" style="font-weight:bold;font-size:16px">¥{{total_amount}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>客户签字：______________</div><div>经办人：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},

        # === 采购管理 (purchase) ===
        {'template_name': '采购单-标准A4', 'template_type': 'purchase', 'paper_size': 'A5', 'is_default': 1,
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>采购单</h1><p>采购单号：{{purchase_no}} | 日期：{{purchase_date}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">供应商信息</th></tr><tr><td>供应商：{{supplier_name}}</td><td>联系人：{{contact_name}}</td><td>电话：{{phone}}</td><td></td></tr><tr><th style="background:#f0f0f0">序号</th><th style="background:#f0f0f0">商品名称</th><th style="background:#f0f0f0">数量</th><th style="background:#f0f0f0">金额</th></tr>{{items}}<tr><td colspan="2" style="text-align:right;font-weight:bold">合计</td><td colspan="2" style="font-weight:bold">¥{{total_amount}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>采购人：______________</div><div>审批人：______________</div><div>日期：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},
        {'template_name': '采购单-简洁版', 'template_type': 'purchase', 'paper_size': 'A5', 'paper_width': 148, 'paper_height': 210,
         'header_content': '<h2 style="text-align:center">采购单</h2>',
         'body_content': '<p>单号：{{purchase_no}} | {{purchase_date}}</p><p>供应商：{{supplier_name}}</p><hr><p>{{items}}</p><p style="font-weight:bold">合计：¥{{total_amount}}</p>',
         'footer_content': '<p>采购人：______ 审批人：______</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:11px;padding:15px}'},
        {'template_name': '采购单-详细版', 'template_type': 'purchase', 'paper_size': 'A5',
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>采购单（详细）</h1><p>采购单号：{{purchase_no}} | 日期：{{purchase_date}} | 交货日期：{{delivery_date}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">供应商信息</th></tr><tr><td>供应商：{{supplier_name}}</td><td>联系人：{{contact_name}}</td><td>电话：{{phone}}</td><td>地址：{{address}}</td></tr><tr><th style="background:#f0f0f0">序号</th><th style="background:#f0f0f0">商品</th><th style="background:#f0f0f0">规格</th><th style="background:#f0f0f0">数量×单价</th></tr>{{items}}<tr><td colspan="3" style="text-align:right;font-weight:bold">合计</td><td style="font-weight:bold">¥{{total_amount}}</td></tr><tr><td colspan="4">备注：{{remark}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>采购人：______________</div><div>审批人：______________</div><div>日期：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},

        # === 采购退货 (return_purchase) ===
        {'template_name': '采购退货单-标准A4', 'template_type': 'return_purchase', 'paper_size': 'A5', 'is_default': 1,
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>采购退货单</h1><p>退货单号：{{return_no}} | 日期：{{return_date}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">供应商信息</th></tr><tr><td>供应商：{{supplier_name}}</td><td>联系人：{{contact_name}}</td><td>电话：{{phone}}</td><td></td></tr><tr><th style="background:#f0f0f0">序号</th><th style="background:#f0f0f0">商品名称</th><th style="background:#f0f0f0">退货数量</th><th style="background:#f0f0f0">退货金额</th></tr>{{items}}<tr><td colspan="2" style="text-align:right;font-weight:bold">合计</td><td colspan="2" style="font-weight:bold">¥{{total_amount}}</td></tr><tr><td colspan="4">退货原因：{{reason}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>经办人：______________</div><div>审批人：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},
        {'template_name': '采购退货单-简洁版', 'template_type': 'return_purchase', 'paper_size': 'A5', 'paper_width': 148, 'paper_height': 210,
         'header_content': '<h2 style="text-align:center">采购退货单</h2>',
         'body_content': '<p>单号：{{return_no}} | {{return_date}}</p><p>供应商：{{supplier_name}}</p><hr><p>{{items}}</p><p>合计：¥{{total_amount}}</p><p>原因：{{reason}}</p>',
         'footer_content': '<p>经办人：______</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:11px;padding:15px}'},
        {'template_name': '采购退货单-详细版', 'template_type': 'return_purchase', 'paper_size': 'A5',
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>采购退货单（详细）</h1><p>退货单号：{{return_no}} | 日期：{{return_date}} | 原采购单号：{{original_no}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">供应商信息</th></tr><tr><td>供应商：{{supplier_name}}</td><td>联系人：{{contact_name}}</td><td>电话：{{phone}}</td><td>地址：{{address}}</td></tr><tr><th style="background:#f0f0f0">序号</th><th style="background:#f0f0f0">商品</th><th style="background:#f0f0f0">规格</th><th style="background:#f0f0f0">退货数量×单价</th></tr>{{items}}<tr><td colspan="3" style="text-align:right;font-weight:bold">合计</td><td style="font-weight:bold">¥{{total_amount}}</td></tr><tr><td colspan="4">退货原因：{{reason}}</td></tr><tr><td colspan="4">备注：{{remark}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>经办人：______________</div><div>审批人：______________</div><div>日期：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},

        # === 销售退货 (return_sale) ===
        {'template_name': '销售退货单-标准A4', 'template_type': 'return_sale', 'paper_size': 'A5', 'is_default': 1,
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>销售退货单</h1><p>退货单号：{{return_no}} | 日期：{{return_date}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">客户信息</th></tr><tr><td>客户：{{customer_name}}</td><td>电话：{{customer_phone}}</td><td colspan="2">地址：{{address}}</td></tr><tr><th style="background:#f0f0f0">序号</th><th style="background:#f0f0f0">商品名称</th><th style="background:#f0f0f0">退货数量</th><th style="background:#f0f0f0">退货金额</th></tr>{{items}}<tr><td colspan="2" style="text-align:right;font-weight:bold">合计</td><td colspan="2" style="font-weight:bold">¥{{total_amount}}</td></tr><tr><td colspan="4">退货原因：{{reason}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>客户签字：______________</div><div>经办人：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},
        {'template_name': '销售退货单-简洁版', 'template_type': 'return_sale', 'paper_size': 'A5', 'paper_width': 148, 'paper_height': 210,
         'header_content': '<h2 style="text-align:center">销售退货单</h2>',
         'body_content': '<p>单号：{{return_no}} | {{return_date}}</p><p>客户：{{customer_name}}</p><hr><p>{{items}}</p><p>合计：¥{{total_amount}}</p><p>原因：{{reason}}</p>',
         'footer_content': '<p>签字：______</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:11px;padding:15px}'},
        {'template_name': '销售退货单-详细版', 'template_type': 'return_sale', 'paper_size': 'A5',
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>销售退货单（详细）</h1><p>退货单号：{{return_no}} | 日期：{{return_date}} | 原销售单号：{{original_no}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">客户信息</th></tr><tr><td>客户：{{customer_name}}</td><td>电话：{{customer_phone}}</td><td>地址：{{address}}</td><td></td></tr><tr><th style="background:#f0f0f0">序号</th><th style="background:#f0f0f0">商品</th><th style="background:#f0f0f0">规格</th><th style="background:#f0f0f0">退货数量×单价</th></tr>{{items}}<tr><td colspan="3" style="text-align:right;font-weight:bold">合计</td><td style="font-weight:bold">¥{{total_amount}}</td></tr><tr><td colspan="4">退货原因：{{reason}}</td></tr><tr><td colspan="4">备注：{{remark}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>客户签字：______________</div><div>经办人：______________</div><div>日期：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},

        # === 入库管理 (inventory_in) ===
        {'template_name': '入库单-标准A4', 'template_type': 'inventory_in', 'paper_size': 'A5', 'is_default': 1,
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>入库单</h1><p>入库单号：{{in_no}} | 日期：{{in_date}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">入库信息</th></tr><tr><td>仓库：{{warehouse_name}}</td><td>入库类型：{{in_type}}</td><td>经办人：{{operator}}</td><td>关联单号：{{related_no}}</td></tr><tr><th style="background:#f0f0f0">序号</th><th style="background:#f0f0f0">商品名称</th><th style="background:#f0f0f0">数量</th><th style="background:#f0f0f0">金额</th></tr>{{items}}<tr><td colspan="2" style="text-align:right;font-weight:bold">合计</td><td colspan="2" style="font-weight:bold">¥{{total_amount}}</td></tr><tr><td colspan="4">备注：{{remark}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>制单人：______________</div><div>审核人：______________</div><div>入库人：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},
        {'template_name': '入库单-简洁版', 'template_type': 'inventory_in', 'paper_size': 'A5', 'paper_width': 148, 'paper_height': 210,
         'header_content': '<h2 style="text-align:center">入库单</h2>',
         'body_content': '<p>单号：{{in_no}} | {{in_date}}</p><p>仓库：{{warehouse_name}} | 类型：{{in_type}}</p><hr><p>{{items}}</p><p>合计：¥{{total_amount}}</p>',
         'footer_content': '<p>制单人：______ 入库人：______</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:11px;padding:15px}'},
        {'template_name': '入库单-详细版', 'template_type': 'inventory_in', 'paper_size': 'A5',
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>入库单（详细）</h1><p>入库单号：{{in_no}} | 日期：{{in_date}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">入库信息</th></tr><tr><td>仓库：{{warehouse_name}}</td><td>入库类型：{{in_type}}</td><td>经办人：{{operator}}</td><td>关联单号：{{related_no}}</td></tr><tr><th style="background:#f0f0f0">序号</th><th style="background:#f0f0f0">商品编码</th><th style="background:#f0f0f0">商品名称</th><th style="background:#f0f0f0">规格</th><th style="background:#f0f0f0">数量</th><th style="background:#f0f0f0">单价</th><th style="background:#f0f0f0">金额</th></tr>{{items}}<tr><td colspan="6" style="text-align:right;font-weight:bold">合计</td><td style="font-weight:bold">¥{{total_amount}}</td></tr><tr><td colspan="7">备注：{{remark}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>制单人：______________</div><div>审核人：______________</div><div>入库人：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},

        # === 出库管理 (inventory_out) ===
        {'template_name': '出库单-标准A4', 'template_type': 'inventory_out', 'paper_size': 'A5', 'is_default': 1,
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>出库单</h1><p>出库单号：{{out_no}} | 日期：{{out_date}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">出库信息</th></tr><tr><td>仓库：{{warehouse_name}}</td><td>出库类型：{{out_type}}</td><td>经办人：{{operator}}</td><td>关联单号：{{related_no}}</td></tr><tr><th style="background:#f0f0f0">序号</th><th style="background:#f0f0f0">商品名称</th><th style="background:#f0f0f0">数量</th><th style="background:#f0f0f0">金额</th></tr>{{items}}<tr><td colspan="2" style="text-align:right;font-weight:bold">合计</td><td colspan="2" style="font-weight:bold">¥{{total_amount}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>制单人：______________</div><div>审核人：______________</div><div>领用人：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},
        {'template_name': '出库单-简洁版', 'template_type': 'inventory_out', 'paper_size': 'A5', 'paper_width': 148, 'paper_height': 210,
         'header_content': '<h2 style="text-align:center">出库单</h2>',
         'body_content': '<p>单号：{{out_no}} | {{out_date}}</p><p>仓库：{{warehouse_name}} | 类型：{{out_type}}</p><hr><p>{{items}}</p><p>合计：¥{{total_amount}}</p>',
         'footer_content': '<p>制单人：______ 领用人：______</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:11px;padding:15px}'},
        {'template_name': '出库单-详细版', 'template_type': 'inventory_out', 'paper_size': 'A5',
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>出库单（详细）</h1><p>出库单号：{{out_no}} | 日期：{{out_date}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">出库信息</th></tr><tr><td>仓库：{{warehouse_name}}</td><td>出库类型：{{out_type}}</td><td>经办人：{{operator}}</td><td>关联单号：{{related_no}}</td></tr><tr><th style="background:#f0f0f0">序号</th><th style="background:#f0f0f0">商品编码</th><th style="background:#f0f0f0">商品名称</th><th style="background:#f0f0f0">规格</th><th style="background:#f0f0f0">数量</th><th style="background:#f0f0f0">单价</th><th style="background:#f0f0f0">金额</th></tr>{{items}}<tr><td colspan="6" style="text-align:right;font-weight:bold">合计</td><td style="font-weight:bold">¥{{total_amount}}</td></tr><tr><td colspan="7">备注：{{remark}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>制单人：______________</div><div>审核人：______________</div><div>领用人：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},

        # === 盘点管理 (inventory_check) ===
        {'template_name': '盘点单-标准A4', 'template_type': 'inventory_check', 'paper_size': 'A5', 'is_default': 1,
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>库存盘点单</h1><p>盘点单号：{{check_no}} | 日期：{{check_date}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">盘点信息</th></tr><tr><td>仓库：{{warehouse_name}}</td><td>货架：{{shelf_name}}</td><td>盘点人：{{operator}}</td><td>状态：{{status}}</td></tr><tr><th style="background:#f0f0f0">商品编码</th><th style="background:#f0f0f0">商品名称</th><th style="background:#f0f0f0">账面数量</th><th style="background:#f0f0f0">实盘数量</th><th style="background:#f0f0f0">差异</th></tr>{{items}}<tr><td colspan="4" style="text-align:right;font-weight:bold">盘盈/盘亏合计</td><td style="font-weight:bold">¥{{diff_amount}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>盘点人：______________</div><div>审核人：______________</div><div>日期：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},
        {'template_name': '盘点单-简洁版', 'template_type': 'inventory_check', 'paper_size': 'A5', 'paper_width': 148, 'paper_height': 210,
         'header_content': '<h2 style="text-align:center">盘点单</h2>',
         'body_content': '<p>单号：{{check_no}} | {{check_date}}</p><p>仓库：{{warehouse_name}}</p><hr><p>{{items}}</p><p>差异金额：¥{{diff_amount}}</p>',
         'footer_content': '<p>盘点人：______ 审核人：______</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:11px;padding:15px}'},
        {'template_name': '盘点差异报表', 'template_type': 'inventory_check', 'paper_size': 'A5',
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>盘点差异报表</h1><p>盘点单号：{{check_no}} | 日期：{{check_date}} | 仓库：{{warehouse_name}}</p></div>',
         'body_content': '<h3>盘盈明细</h3><table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th>商品编码</th><th>商品名称</th><th>账面</th><th>实盘</th><th>差异</th><th>差异金额</th></tr>{{profit_items}}</table><h3>盘亏明细</h3><table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th>商品编码</th><th>商品名称</th><th>账面</th><th>实盘</th><th>差异</th><th>差异金额</th></tr>{{loss_items}}</table><p style="font-weight:bold">盘盈合计：¥{{profit_amount}} | 盘亏合计：¥{{loss_amount}} | 净差异：¥{{net_amount}}</p>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>盘点人：______________</div><div>审核人：______________</div><div>日期：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},

        # === 调拨管理 (transfer) ===
        {'template_name': '调拨单-标准A4', 'template_type': 'transfer', 'paper_size': 'A5', 'is_default': 1,
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>库存调拨单</h1><p>调拨单号：{{transfer_no}} | 日期：{{transfer_date}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">调拨信息</th></tr><tr><td>调出仓库：{{from_warehouse}}</td><td>调入仓库：{{to_warehouse}}</td><td>经办人：{{operator}}</td><td>状态：{{status}}</td></tr><tr><th style="background:#f0f0f0">序号</th><th style="background:#f0f0f0">商品名称</th><th style="background:#f0f0f0">数量</th><th style="background:#f0f0f0">金额</th></tr>{{items}}<tr><td colspan="2" style="text-align:right;font-weight:bold">合计</td><td colspan="2" style="font-weight:bold">¥{{total_amount}}</td></tr><tr><td colspan="4">调拨原因：{{reason}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>调出方签字：______________</div><div>调入方签字：______________</div><div>审批人：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},
        {'template_name': '调拨单-简洁版', 'template_type': 'transfer', 'paper_size': 'A5', 'paper_width': 148, 'paper_height': 210,
         'header_content': '<h2 style="text-align:center">调拨单</h2>',
         'body_content': '<p>单号：{{transfer_no}} | {{transfer_date}}</p><p>{{from_warehouse}} → {{to_warehouse}}</p><hr><p>{{items}}</p><p>合计：¥{{total_amount}}</p>',
         'footer_content': '<p>调出方：______ 调入方：______</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:11px;padding:15px}'},
        {'template_name': '调拨单-详细版', 'template_type': 'transfer', 'paper_size': 'A5',
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>库存调拨单（详细）</h1><p>调拨单号：{{transfer_no}} | 日期：{{transfer_date}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="4" style="background:#f0f0f0">调拨信息</th></tr><tr><td>调出仓库：{{from_warehouse}}</td><td>调入仓库：{{to_warehouse}}</td><td>经办人：{{operator}}</td><td>状态：{{status}}</td></tr><tr><th style="background:#f0f0f0">序号</th><th style="background:#f0f0f0">商品编码</th><th style="background:#f0f0f0">商品名称</th><th style="background:#f0f0f0">规格</th><th style="background:#f0f0f0">数量</th><th style="background:#f0f0f0">单价</th><th style="background:#f0f0f0">金额</th></tr>{{items}}<tr><td colspan="6" style="text-align:right;font-weight:bold">合计</td><td style="font-weight:bold">¥{{total_amount}}</td></tr><tr><td colspan="7">调拨原因：{{reason}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>调出方签字：______________</div><div>调入方签字：______________</div><div>审批人：______________</div><div>日期：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},

        # === 应收管理 (receivable) ===
        {'template_name': '应收对账单-标准A4', 'template_type': 'receivable', 'paper_size': 'A5', 'is_default': 1,
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>应收对账单</h1><p>客户：{{customer_name}} | 日期：{{created_at}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th style="background:#f0f0f0">单号</th><th style="background:#f0f0f0">日期</th><th style="background:#f0f0f0">摘要</th><th style="background:#f0f0f0">应收金额</th><th style="background:#f0f0f0">已收金额</th><th style="background:#f0f0f0">未收金额</th></tr>{{items}}<tr><td colspan="3" style="text-align:right;font-weight:bold">合计</td><td style="font-weight:bold">¥{{total_amount}}</td><td style="font-weight:bold">¥{{received_amount}}</td><td style="font-weight:bold">¥{{unpaid_amount}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>制单人：______________</div><div>客户确认：______________</div><div>日期：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},
        {'template_name': '应收对账单-简洁版', 'template_type': 'receivable', 'paper_size': 'A5', 'paper_width': 148, 'paper_height': 210,
         'header_content': '<h2 style="text-align:center">应收对账单</h2>',
         'body_content': '<p>客户：{{customer_name}} | {{created_at}}</p><hr><p>{{items}}</p><p>应收合计：¥{{total_amount}} | 已收：¥{{received_amount}} | 未收：¥{{unpaid_amount}}</p>',
         'footer_content': '<p>确认签字：______</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:11px;padding:15px}'},
        {'template_name': '应收对账单-含逾期', 'template_type': 'receivable', 'paper_size': 'A5',
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>应收对账单（含逾期）</h1><p>客户：{{customer_name}} | 日期：{{created_at}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th style="background:#f0f0f0">单号</th><th style="background:#f0f0f0">日期</th><th style="background:#f0f0f0">摘要</th><th style="background:#f0f0f0">应收金额</th><th style="background:#f0f0f0">已收</th><th style="background:#f0f0f0">未收</th><th style="background:#f0f0f0">逾期天数</th></tr>{{items}}<tr><td colspan="3" style="text-align:right;font-weight:bold">合计</td><td style="font-weight:bold">¥{{total_amount}}</td><td style="font-weight:bold">¥{{received_amount}}</td><td style="font-weight:bold;color:red">¥{{unpaid_amount}}</td><td></td></tr></table><p style="color:red;font-weight:bold">逾期总金额：¥{{overdue_amount}}</p>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>制单人：______________</div><div>客户确认：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},

        # === 应付管理 (payable) ===
        {'template_name': '应付对账单-标准A4', 'template_type': 'payable', 'paper_size': 'A5', 'is_default': 1,
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>应付对账单</h1><p>供应商：{{supplier_name}} | 日期：{{created_at}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th style="background:#f0f0f0">单号</th><th style="background:#f0f0f0">日期</th><th style="background:#f0f0f0">摘要</th><th style="background:#f0f0f0">应付金额</th><th style="background:#f0f0f0">已付金额</th><th style="background:#f0f0f0">未付金额</th></tr>{{items}}<tr><td colspan="3" style="text-align:right;font-weight:bold">合计</td><td style="font-weight:bold">¥{{total_amount}}</td><td style="font-weight:bold">¥{{paid_amount}}</td><td style="font-weight:bold">¥{{unpaid_amount}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>制单人：______________</div><div>供应商确认：______________</div><div>日期：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},
        {'template_name': '应付对账单-简洁版', 'template_type': 'payable', 'paper_size': 'A5', 'paper_width': 148, 'paper_height': 210,
         'header_content': '<h2 style="text-align:center">应付对账单</h2>',
         'body_content': '<p>供应商：{{supplier_name}} | {{created_at}}</p><hr><p>{{items}}</p><p>应付合计：¥{{total_amount}} | 已付：¥{{paid_amount}} | 未付：¥{{unpaid_amount}}</p>',
         'footer_content': '<p>确认签字：______</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:11px;padding:15px}'},
        {'template_name': '应付对账单-含逾期', 'template_type': 'payable', 'paper_size': 'A5',
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>应付对账单（含逾期）</h1><p>供应商：{{supplier_name}} | 日期：{{created_at}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th style="background:#f0f0f0">单号</th><th style="background:#f0f0f0">日期</th><th style="background:#f0f0f0">摘要</th><th style="background:#f0f0f0">应付金额</th><th style="background:#f0f0f0">已付</th><th style="background:#f0f0f0">未付</th><th style="background:#f0f0f0">逾期天数</th></tr>{{items}}<tr><td colspan="3" style="text-align:right;font-weight:bold">合计</td><td style="font-weight:bold">¥{{total_amount}}</td><td style="font-weight:bold">¥{{paid_amount}}</td><td style="font-weight:bold;color:red">¥{{unpaid_amount}}</td><td></td></tr></table><p style="color:red;font-weight:bold">逾期总金额：¥{{overdue_amount}}</p>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>制单人：______________</div><div>供应商确认：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},

        # === 收款管理 (receipt) ===
        {'template_name': '收款凭证-标准A4', 'template_type': 'receipt', 'paper_size': 'A5', 'is_default': 1,
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>收款凭证</h1><p>凭证号：{{receipt_no}} | 日期：{{receipt_date}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th style="background:#f0f0f0">客户名称</th><td>{{customer_name}}</td><th style="background:#f0f0f0">收款金额</th><td style="font-weight:bold;font-size:16px">¥{{amount}}</td></tr><tr><th style="background:#f0f0f0">收款方式</th><td>{{payment_method}}</td><th style="background:#f0f0f0">收款账户</th><td>{{account_name}}</td></tr><tr><th style="background:#f0f0f0">关联单号</th><td colspan="3">{{related_no}}</td></tr><tr><th style="background:#f0f0f0">经办人</th><td>{{operator}}</td><th style="background:#f0f0f0">备注</th><td>{{remark}}</td></tr></table>',
         'footer_content': '<div style="margin-top:50px;display:flex;justify-content:space-between"><div>收款人签字：______________</div><div>客户确认签字：______________</div><div>日期：______________</div></div><p style="text-align:center;color:#999;font-size:10px">此凭证一式两联</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},
        {'template_name': '收款凭证-简洁版', 'template_type': 'receipt', 'paper_size': 'A5', 'paper_width': 148, 'paper_height': 210,
         'header_content': '<h2 style="text-align:center">收款凭证</h2>',
         'body_content': '<p>凭证号：{{receipt_no}} | {{receipt_date}}</p><p>客户：{{customer_name}}</p><p style="font-size:18px;font-weight:bold">收款金额：¥{{amount}}</p><p>方式：{{payment_method}} | 账户：{{account_name}}</p>',
         'footer_content': '<p>收款人：______ 客户：______</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:11px;padding:15px}'},
        {'template_name': '收款凭证-正式版', 'template_type': 'receipt', 'paper_size': 'A5',
         'header_content': '<div style="text-align:center;border-bottom:3px double #333;padding-bottom:15px"><h1 style="letter-spacing:10px">收  款  凭  证</h1><p>凭证号：{{receipt_no}} | 日期：{{receipt_date}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="8"><tr><td style="width:25%;background:#f5f5f5">今收到</td><td colspan="3">{{customer_name}}</td></tr><tr><td style="background:#f5f5f0">收款金额</td><td colspan="3" style="font-weight:bold;font-size:18px">人民币（大写）：{{amount_cn}}  ¥{{amount}}</td></tr><tr><td style="background:#f5f5f0">收款方式</td><td>{{payment_method}}</td><td style="background:#f5f5f0">收款账户</td><td>{{account_name}}</td></tr><tr><td style="background:#f5f5f0">关联单号</td><td>{{related_no}}</td><td style="background:#f5f5f0">经办人</td><td>{{operator}}</td></tr><tr><td style="background:#f5f5f0">备注</td><td colspan="3">{{remark}}</td></tr></table>',
         'footer_content': '<div style="margin-top:60px;display:flex;justify-content:space-between"><div>收款单位（章）：______________</div><div>客户确认（章）：______________</div></div><p style="text-align:center;color:#999;font-size:10px;margin-top:10px">此凭证一式两联，收款联和客户联</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:14px;padding:30px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:8px}'},

        # === 付款管理 (payment) ===
        {'template_name': '付款凭证-标准A4', 'template_type': 'payment', 'paper_size': 'A5', 'is_default': 1,
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>付款凭证</h1><p>凭证号：{{payment_no}} | 日期：{{payment_date}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th style="background:#f0f0f0">供应商名称</th><td>{{supplier_name}}</td><th style="background:#f0f0f0">付款金额</th><td style="font-weight:bold;font-size:16px">¥{{amount}}</td></tr><tr><th style="background:#f0f0f0">付款方式</th><td>{{payment_method}}</td><th style="background:#f0f0f0">付款账户</th><td>{{account_name}}</td></tr><tr><th style="background:#f0f0f0">关联单号</th><td colspan="3">{{related_no}}</td></tr><tr><th style="background:#f0f0f0">经办人</th><td>{{operator}}</td><th style="background:#f0f0f0">备注</th><td>{{remark}}</td></tr></table>',
         'footer_content': '<div style="margin-top:50px;display:flex;justify-content:space-between"><div>付款人签字：______________</div><div>审批人签字：______________</div><div>日期：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},
        {'template_name': '付款凭证-简洁版', 'template_type': 'payment', 'paper_size': 'A5', 'paper_width': 148, 'paper_height': 210,
         'header_content': '<h2 style="text-align:center">付款凭证</h2>',
         'body_content': '<p>凭证号：{{payment_no}} | {{payment_date}}</p><p>供应商：{{supplier_name}}</p><p style="font-size:18px;font-weight:bold">付款金额：¥{{amount}}</p><p>方式：{{payment_method}} | 账户：{{account_name}}</p>',
         'footer_content': '<p>付款人：______ 审批人：______</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:11px;padding:15px}'},
        {'template_name': '付款凭证-正式版', 'template_type': 'payment', 'paper_size': 'A5',
         'header_content': '<div style="text-align:center;border-bottom:3px double #333;padding-bottom:15px"><h1 style="letter-spacing:10px">付  款  凭  证</h1><p>凭证号：{{payment_no}} | 日期：{{payment_date}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="8"><tr><td style="width:25%;background:#f5f5f5">今付给</td><td colspan="3">{{supplier_name}}</td></tr><tr><td style="background:#f5f5f0">付款金额</td><td colspan="3" style="font-weight:bold;font-size:18px">人民币（大写）：{{amount_cn}}  ¥{{amount}}</td></tr><tr><td style="background:#f5f5f0">付款方式</td><td>{{payment_method}}</td><td style="background:#f5f5f0">付款账户</td><td>{{account_name}}</td></tr><tr><td style="background:#f5f5f0">关联单号</td><td>{{related_no}}</td><td style="background:#f5f5f0">经办人</td><td>{{operator}}</td></tr><tr><td style="background:#f5f5f0">备注</td><td colspan="3">{{remark}}</td></tr></table>',
         'footer_content': '<div style="margin-top:60px;display:flex;justify-content:space-between"><div>付款单位（章）：______________</div><div>审批人（章）：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:14px;padding:30px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:8px}'},

        # === 工资发放 (salary) ===
        {'template_name': '工资条-标准A4', 'template_type': 'salary', 'paper_size': 'A4', 'is_default': 1,
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>工资条</h1><p>月份：{{salary_month}} | 部门：{{department}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><th colspan="2" style="background:#f0f0f0">姓名：{{employee_name}}</th><th style="background:#f0f0f0">岗位：{{position}}</th><th style="background:#f0f0f0">工号：{{employee_no}}</th></tr><tr><th style="background:#f0f0f0">基本工资</th><td>{{base_salary}}</td><th style="background:#f0f0f0">绩效工资</th><td>{{performance_salary}}</td></tr><tr><th style="background:#f0f0f0">提成</th><td>{{commission}}</td><th style="background:#f0f0f0">补贴</th><td>{{allowance}}</td></tr><tr><th style="background:#f0f0f0">加班费</th><td>{{overtime_pay}}</td><th style="background:#f0f0f0">奖金</th><td>{{bonus}}</td></tr><tr><th style="background:#f0f0f0">应发合计</th><td colspan="3" style="font-weight:bold">¥{{gross_salary}}</td></tr><tr><th style="background:#f0f0f0">社保</th><td>{{social_insurance}}</td><th style="background:#f0f0f0">公积金</th><td>{{housing_fund}}</td></tr><tr><th style="background:#f0f0f0">个税</th><td>{{tax}}</td><th style="background:#f0f0f0">其他扣款</th><td>{{other_deductions}}</td></tr><tr><th style="background:#f0f0f0">实发工资</th><td colspan="3" style="font-weight:bold;font-size:16px">¥{{net_salary}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>员工签字：______________</div><div>发放人：______________</div><div>日期：______________</div></div>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},
        {'template_name': '工资条-简洁版', 'template_type': 'salary', 'paper_size': 'A5', 'paper_width': 148, 'paper_height': 210,
         'header_content': '<h2 style="text-align:center">工资条</h2>',
         'body_content': '<p>{{salary_month}} | {{employee_name}} | {{department}}</p><hr><p>基本工资：{{base_salary}} | 绩效：{{performance_salary}}</p><p>提成：{{commission}} | 补贴：{{allowance}}</p><p>应发：¥{{gross_salary}}</p><p>社保：{{social_insurance}} | 个税：{{tax}}</p><p style="font-weight:bold;font-size:16px">实发：¥{{net_salary}}</p>',
         'footer_content': '<p>员工签字：______</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:11px;padding:15px}'},
        {'template_name': '工资条-保密版', 'template_type': 'salary', 'paper_size': 'A4',
         'header_content': '<div style="text-align:center;border-bottom:2px solid #333;padding-bottom:10px"><h1>工资条（保密）</h1><p style="color:red">⚠ 本文件包含机密信息，请妥善保管</p><p>月份：{{salary_month}}</p></div>',
         'body_content': '<table width="100%" border="1" cellspacing="0" cellpadding="5"><tr><td style="background:#f0f0f0">姓名</td><td>{{employee_name}}</td><td style="background:#f0f0f0">部门</td><td>{{department}}</td><td style="background:#f0f0f0">岗位</td><td>{{position}}</td></tr><tr><td style="background:#f0f0f0">基本工资</td><td>{{base_salary}}</td><td style="background:#f0f0f0">绩效</td><td>{{performance_salary}}</td><td style="background:#f0f0f0">提成</td><td>{{commission}}</td></tr><tr><td style="background:#f0f0f0">补贴</td><td>{{allowance}}</td><td style="background:#f0f0f0">加班费</td><td>{{overtime_pay}}</td><td style="background:#f0f0f0">奖金</td><td>{{bonus}}</td></tr><tr style="background:#e8f5e9"><td style="font-weight:bold">应发合计</td><td colspan="5" style="font-weight:bold">¥{{gross_salary}}</td></tr><tr><td style="background:#f0f0f0">社保</td><td>{{social_insurance}}</td><td style="background:#f0f0f0">公积金</td><td>{{housing_fund}}</td><td style="background:#f0f0f0">个税</td><td>{{tax}}</td></tr><tr><td style="background:#f0f0f0">其他扣款</td><td colspan="5">{{other_deductions}}</td></tr><tr style="background:#fff3e0"><td style="font-weight:bold;font-size:14px">实发工资</td><td colspan="5" style="font-weight:bold;font-size:16px">¥{{net_salary}}</td></tr></table>',
         'footer_content': '<div style="margin-top:30px;display:flex;justify-content:space-between"><div>员工签字：______________</div><div>发放人：______________</div><div>日期：______________</div></div><p style="text-align:center;color:#999;font-size:10px">本工资条为机密文件，严禁外传</p>',
         'style_content': 'body{font-family:SimSun,serif;font-size:12px;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;padding:5px}th{background:#f5f5f5}'},

        # === 设备标签 (device_label) ===
        # 模板1 - 设备标签-标准版 (60x40mm)，每页21个（3列x7行）
        {'template_name': '设备标签-标准版', 'template_type': 'device_label', 'paper_size': 'A4', 'is_default': 1,
         'header_content': '',
         'body_content': '''<div class="label-grid">
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{device_brand}} {{device_model}}</div><div class="info">SN:{{device_sn}}</div><div class="date">{{receive_date}}</div></div>
</div>''',
         'footer_content': '',
         'style_content': 'body{font-family:"Microsoft YaHei",sans-serif;margin:0;padding:0}.label-grid{display:flex;flex-wrap:wrap;width:210mm}.label{width:70mm;height:40mm;border:1px solid #ccc;box-sizing:border-box;padding:2mm;page-break-inside:avoid}.no{font-size:10px;font-weight:bold;border-bottom:1px dashed #999;padding-bottom:1mm;margin-bottom:1mm}.info{font-size:8px;line-height:1.3;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.date{font-size:7px;color:#666;margin-top:auto}'},        # 模板2 - 设备标签-小巧版 (40x30mm)，每页45个（5列x9行）
        {'template_name': '设备标签-小巧版', 'template_type': 'device_label', 'paper_size': 'A4',
         'header_content': '',
         'body_content': '''<div class="label-grid">
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{device_model}}</div><div class="date">{{receive_date}}</div></div>
</div>''',
         'footer_content': '',
         'style_content': 'body{font-family:"Microsoft YaHei",sans-serif;margin:0;padding:0}.label-grid{display:flex;flex-wrap:wrap;width:210mm}.label{width:42mm;height:30mm;border:1px solid #ccc;box-sizing:border-box;padding:1.5mm;page-break-inside:avoid}.no{font-size:8px;font-weight:bold;border-bottom:1px dashed #999;padding-bottom:0.5mm;margin-bottom:0.5mm}.info{font-size:7px;line-height:1.2;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.date{font-size:6px;color:#666;margin-top:auto}'},        # 模板3 - 设备标签-最小版 (30x20mm)，每页98个（7列x14行）
        {'template_name': '设备标签-最小版', 'template_type': 'device_label', 'paper_size': 'A4',
         'header_content': '',
         'body_content': '''<div class="label-grid">
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="date">{{receive_date}}</div></div>
</div>''',
         'footer_content': '',
         'style_content': 'body{font-family:"Microsoft YaHei",sans-serif;margin:0;padding:0}.label-grid{display:flex;flex-wrap:wrap;width:210mm}.label{width:30mm;height:20mm;border:1px solid #ccc;box-sizing:border-box;padding:1mm;page-break-inside:avoid}.no{font-size:7px;font-weight:bold}.date{font-size:6px;color:#666}'},
        # === 客户自带标签 (customer_label) ===
        # 模板1 - 客户标签-标准版 (60x40mm)，每页21个（3列x7行）
        {'template_name': '客户标签-标准版', 'template_type': 'customer_label', 'paper_size': 'A4', 'is_default': 1,
         'header_content': '',
         'body_content': '''<div class="label-grid">
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="badge">客户自带</div><div class="no">{{receive_no}}</div><div class="info">{{customer_name}} {{customer_phone}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
</div>''',
         'footer_content': '',
         'style_content': 'body{font-family:"Microsoft YaHei",sans-serif;margin:0;padding:0}.label-grid{display:flex;flex-wrap:wrap;width:210mm}.label{width:70mm;height:40mm;border:1px solid #409EFF;box-sizing:border-box;padding:2mm;page-break-inside:avoid}.badge{font-size:7px;background:#409EFF;color:#fff;padding:0.3mm 1.5mm;border-radius:1px;display:inline-block;margin-bottom:0.5mm}.no{font-size:10px;font-weight:bold;border-bottom:1px dashed #409EFF;padding-bottom:1mm;margin-bottom:1mm}.info{font-size:8px;line-height:1.3;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.date{font-size:7px;color:#666;margin-top:auto}'},        # 模板2 - 客户标签-小巧版 (40x30mm)，每页45个（5列x9行）
        {'template_name': '客户标签-小巧版', 'template_type': 'customer_label', 'paper_size': 'A4',
         'header_content': '',
         'body_content': '''<div class="label-grid">
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
<div class="label"><div class="no">{{receive_no}}</div><div class="info">{{customer_name}}</div><div class="info">{{item_name}}</div><div class="date">{{receive_date}}</div></div>
</div>''',
         'footer_content': '',
         'style_content': 'body{font-family:"Microsoft YaHei",sans-serif;margin:0;padding:0}.label-grid{display:flex;flex-wrap:wrap;width:210mm}.label{width:42mm;height:30mm;border:1px solid #409EFF;box-sizing:border-box;padding:1.5mm;page-break-inside:avoid}.no{font-size:8px;font-weight:bold;border-bottom:1px dashed #409EFF;padding-bottom:0.5mm;margin-bottom:0.5mm}.info{font-size:7px;line-height:1.2;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.date{font-size:6px;color:#666;margin-top:auto}'},        # 模板3 - 客户标签-最小版 (30x20mm)，每页98个（7列x14行）
        {'template_name': '客户标签-最小版', 'template_type': 'customer_label', 'paper_size': 'A4',
         'header_content': '',
         'body_content': '''<div class="label-grid">
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
<div class="label"><div class="badge">自带</div><div class="no">{{receive_no}}</div></div>
</div>''',
         'footer_content': '',
         'style_content': 'body{font-family:"Microsoft YaHei",sans-serif;margin:0;padding:0}.label-grid{display:flex;flex-wrap:wrap;width:210mm}.label{width:30mm;height:20mm;border:1px solid #409EFF;box-sizing:border-box;padding:1mm;page-break-inside:avoid}.badge{font-size:6px;background:#409EFF;color:#fff;padding:0.2mm 1mm;border-radius:1px;display:inline-block}.no{font-size:7px;font-weight:bold;margin-top:0.5mm}'},
        # === 商品条码标签 (product_barcode) ===
        # 模板1 - 商品条码-标准版 (60x40mm)，每页21个（3列x7行）
        {'template_name': '商品条码-标准版', 'template_type': 'product_barcode', 'paper_size': 'A4', 'is_default': 1,
         'header_content': '',
         'body_content': '''<div class="label-grid">
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||||||||||||</div><div class="code">{{barcode}}</div><div class="info">规格:{{specification}}</div><div class="price">¥{{sale_price}}</div></div>
</div>''',
         'footer_content': '',
         'style_content': 'body{font-family:"Microsoft YaHei",sans-serif;margin:0;padding:0}.label-grid{display:flex;flex-wrap:wrap;width:210mm}.label{width:70mm;height:40mm;border:1px solid #ccc;box-sizing:border-box;padding:2mm;page-break-inside:avoid}.name{font-size:9px;font-weight:bold;margin-bottom:1mm;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.barcode{font-size:14px;letter-spacing:1px;color:#000;text-align:center}.code{font-size:7px;text-align:center;margin-bottom:1mm;font-family:"Courier New",monospace}.info{font-size:7px;color:#666}.price{font-size:10px;color:#E6A23C;font-weight:bold;margin-top:1mm}'},        # 模板2 - 商品条码-小巧版 (40x30mm)，每页45个（5列x9行）
        {'template_name': '商品条码-小巧版', 'template_type': 'product_barcode', 'paper_size': 'A4',
         'header_content': '',
         'body_content': '''<div class="label-grid">
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="name">{{product_name}}</div><div class="barcode">||||||||||||||</div><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
</div>''',
         'footer_content': '',
         'style_content': 'body{font-family:"Microsoft YaHei",sans-serif;margin:0;padding:0}.label-grid{display:flex;flex-wrap:wrap;width:210mm}.label{width:42mm;height:30mm;border:1px solid #ccc;box-sizing:border-box;padding:1.5mm;page-break-inside:avoid}.name{font-size:7px;font-weight:bold;margin-bottom:0.5mm;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.barcode{font-size:12px;letter-spacing:0.5px;color:#000;text-align:center}.code{font-size:6px;text-align:center;margin-bottom:0.5mm;font-family:"Courier New",monospace}.price{font-size:9px;color:#E6A23C;font-weight:bold}'},        # 模板3 - 商品条码-最小版 (30x20mm)，每页98个（7列x14行）
        {'template_name': '商品条码-最小版', 'template_type': 'product_barcode', 'paper_size': 'A4',
         'header_content': '',
         'body_content': '''<div class="label-grid">
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
<div class="label"><div class="code">{{barcode}}</div><div class="price">¥{{sale_price}}</div></div>
</div>''',
         'footer_content': '',
         'style_content': 'body{font-family:"Microsoft YaHei",sans-serif;margin:0;padding:0}.label-grid{display:flex;flex-wrap:wrap;width:210mm}.label{width:30mm;height:20mm;border:1px solid #ccc;box-sizing:border-box;padding:1mm;page-break-inside:avoid}.code{font-size:7px;text-align:center;font-family:"Courier New",monospace}.price{font-size:8px;color:#E6A23C;font-weight:bold;text-align:center;margin-top:0.5mm}'},
    ]

    for t in templates:
        db.session.add(PrintTemplate(**t))

    db.session.commit()
    return jsonify({'code': 200, 'message': f'已初始化{len(templates)}个默认打印模板'})

# ============================================
# Helper: 构建权限树
# ============================================

def build_permission_tree(permissions):
    """将权限列表构建为树形结构"""
    perm_dict = {}
    for p in permissions:
        perm_dict[p.id] = {
            'id': p.id,
            'name': p.name,
            'code': p.code,
            'type': p.type,
            'parent_id': p.parent_id,
            'path': p.path,
            'icon': p.icon,
            'sort_order': p.sort_order,
            'status': p.status,
            'children': []
        }
    tree = []
    for p in permissions:
        if p.parent_id and p.parent_id in perm_dict:
            perm_dict[p.parent_id]['children'].append(perm_dict[p.id])
        else:
            tree.append(perm_dict[p.id])
    tree.sort(key=lambda x: x.get('sort_order', 0))
    return tree


# ============================================
# B) 角色管理
# ============================================

@bp.route('/api/settings/roles', methods=['GET'])
@jwt_required()
def get_roles():
    """获取角色列表（分页、搜索）"""
    from models.system import SysRole
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '')

    query = SysRole.query
    if keyword:
        query = query.filter(
            db.or_(
                SysRole.role_name.contains(keyword),
                SysRole.role_code.contains(keyword)
            )
        )
    query = query.order_by(SysRole.created_at.desc())
    total = query.count()
    roles = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        'code': 200,
        'data': {
            'list': [to_dict(r) for r in roles],
            'total': total,
            'page': page,
            'page_size': page_size
        }
    })

@bp.route('/api/settings/roles/all', methods=['GET'])
@jwt_required()
def get_all_roles():
    """获取所有启用角色（下拉选择用）"""
    from models.system import SysRole
    roles = SysRole.query.filter_by(status=1).order_by(SysRole.created_at).all()
    return jsonify({
        'code': 200,
        'data': [{'id': r.id, 'role_name': r.role_name, 'role_code': r.role_code} for r in roles]
    })

@bp.route('/api/settings/roles', methods=['POST'])
@jwt_required()
def create_role():
    """创建角色"""
    from models.system import SysRole
    data = request.get_json()
    role_name = data.get('role_name')
    role_code = data.get('role_code')
    description = data.get('description', '')
    permissions = data.get('permissions', [])

    if not role_name or not role_code:
        return jsonify({'code': 400, 'message': '角色名称和角色编码不能为空'}), 400

    existing = SysRole.query.filter_by(role_code=role_code).first()
    if existing:
        return jsonify({'code': 400, 'message': '角色编码已存在'}), 400

    role = SysRole(
        role_name=role_name,
        role_code=role_code,
        description=description,
        permissions=permissions
    )
    db.session.add(role)
    db.session.commit()
    return jsonify({'code': 200, 'message': '创建成功', 'data': to_dict(role)})

@bp.route('/api/settings/roles/<int:role_id>', methods=['PUT'])
@jwt_required()
def update_role(role_id):
    """更新角色"""
    from models.system import SysRole
    role = SysRole.query.get(role_id)
    if not role:
        return jsonify({'code': 404, 'message': '角色不存在'}), 404

    data = request.get_json()
    if 'role_name' in data:
        role.role_name = data['role_name']
    if 'description' in data:
        role.description = data['description']
    if 'status' in data:
        role.status = data['status']
    if 'permissions' in data:
        role.permissions = data['permissions']
    if 'data_scope' in data:
        # 数据权限通过permissions JSON字段中的data_scope处理
        perms = role.permissions if role.permissions else []
        if isinstance(perms, list):
            # 将data_scope存入permissions的额外信息中
            # permissions保持为权限code列表，data_scope单独存储
            pass
        # 将data_scope作为角色额外属性存储在permissions中
        # 格式：permissions为列表时保持不变，data_scope通过单独字段传递
        # 由于不能修改模型，将data_scope嵌入permissions JSON
        current_perms = role.permissions
        if isinstance(current_perms, dict):
            current_perms['data_scope'] = data['data_scope']
        elif isinstance(current_perms, list):
            # 转为dict格式存储，包含codes和data_scope
            role.permissions = {'codes': current_perms, 'data_scope': data['data_scope']}

    role.updated_at = datetime.now()
    db.session.commit()
    return jsonify({'code': 200, 'message': '更新成功', 'data': to_dict(role)})

@bp.route('/api/settings/roles/<int:role_id>', methods=['DELETE'])
@jwt_required()
def delete_role(role_id):
    """删除角色（不能删除admin角色）"""
    from models.system import SysRole, SysUser
    role = SysRole.query.get(role_id)
    if not role:
        return jsonify({'code': 404, 'message': '角色不存在'}), 404

    if role.role_code == 'admin':
        return jsonify({'code': 400, 'message': '不能删除超级管理员角色'}), 400

    # 检查是否有用户使用该角色
    user_count = SysUser.query.filter_by(role_id=role_id).count()
    if user_count > 0:
        return jsonify({'code': 400, 'message': f'该角色下有{user_count}个用户，不能删除'}), 400

    db.session.delete(role)
    db.session.commit()
    return jsonify({'code': 200, 'message': '删除成功'})

@bp.route('/api/settings/roles/<int:role_id>/permissions', methods=['GET'])
@jwt_required()
def get_role_permissions(role_id):
    """获取角色权限（返回权限树）"""
    from models.system import SysRole, SysPermission
    role = SysRole.query.get(role_id)
    if not role:
        return jsonify({'code': 404, 'message': '角色不存在'}), 404

    # 获取角色已有的权限code列表
    role_perms = role.permissions if role.permissions else []
    if isinstance(role_perms, dict):
        role_perms = role_perms.get('codes', [])

    # 获取所有权限，构建树形结构，并标记角色已有的权限
    all_perms = SysPermission.query.filter_by(status=1).order_by(SysPermission.sort_order).all()
    perm_tree = build_permission_tree(all_perms)

    # 标记已选中的权限
    def mark_selected(nodes):
        for node in nodes:
            node['checked'] = node.get('code', '') in role_perms
            if node.get('children'):
                mark_selected(node['children'])
    mark_selected(perm_tree)

    return jsonify({
        'code': 200,
        'data': {
            'role': to_dict(role),
            'permission_tree': perm_tree,
            'selected_codes': role_perms
        }
    })

@bp.route('/api/settings/roles/<int:role_id>/permissions', methods=['POST'])
@jwt_required()
def set_role_permissions(role_id):
    """配置角色权限（接收permission_ids列表）"""
    from models.system import SysRole, SysPermission
    role = SysRole.query.get(role_id)
    if not role:
        return jsonify({'code': 404, 'message': '角色不存在'}), 404

    data = request.get_json()
    permission_ids = data.get('permission_ids', [])

    # 根据permission_ids查询对应的权限code
    if permission_ids:
        perms = SysPermission.query.filter(SysPermission.id.in_(permission_ids)).all()
        perm_codes = [p.code for p in perms]
    else:
        perm_codes = []

    # 保留data_scope（如果之前有的话）
    existing_perms = role.permissions
    data_scope = None
    if isinstance(existing_perms, dict):
        data_scope = existing_perms.get('data_scope')

    if data_scope:
        role.permissions = {'codes': perm_codes, 'data_scope': data_scope}
    else:
        role.permissions = perm_codes

    role.updated_at = datetime.now()
    db.session.commit()
    return jsonify({'code': 200, 'message': '权限配置成功'})


# ============================================
# C) 权限管理
# ============================================

@bp.route('/api/settings/permissions', methods=['GET'])
@jwt_required()
def get_permissions():
    """获取权限列表（树形结构）"""
    from models.system import SysPermission
    all_perms = SysPermission.query.order_by(SysPermission.sort_order).all()
    perm_tree = build_permission_tree(all_perms)
    return jsonify({'code': 200, 'data': perm_tree})

@bp.route('/api/settings/permissions/menus', methods=['GET'])
@jwt_required()
def get_menu_permissions():
    """获取菜单权限树（type=1）"""
    from models.system import SysPermission
    menu_perms = SysPermission.query.filter_by(type=1, status=1).order_by(SysPermission.sort_order).all()
    menu_tree = build_permission_tree(menu_perms)
    return jsonify({'code': 200, 'data': menu_tree})

@bp.route('/api/settings/permissions', methods=['POST'])
@jwt_required()
def create_permission():
    """创建权限"""
    from models.system import SysPermission
    data = request.get_json()
    name = data.get('name')
    code = data.get('code')
    perm_type = data.get('type', 1)
    parent_id = data.get('parent_id', 0)
    path = data.get('path', '')
    icon = data.get('icon', '')
    sort_order = data.get('sort_order', 0)

    if not name or not code:
        return jsonify({'code': 400, 'message': '权限名称和权限编码不能为空'}), 400

    existing = SysPermission.query.filter_by(code=code).first()
    if existing:
        return jsonify({'code': 400, 'message': '权限编码已存在'}), 400

    perm = SysPermission(
        name=name,
        code=code,
        type=perm_type,
        parent_id=parent_id,
        path=path,
        icon=icon,
        sort_order=sort_order
    )
    db.session.add(perm)
    db.session.commit()
    return jsonify({'code': 200, 'message': '创建成功', 'data': to_dict(perm)})

@bp.route('/api/settings/permissions/<int:perm_id>', methods=['PUT'])
@jwt_required()
def update_permission(perm_id):
    """更新权限"""
    from models.system import SysPermission
    perm = SysPermission.query.get(perm_id)
    if not perm:
        return jsonify({'code': 404, 'message': '权限不存在'}), 404

    data = request.get_json()
    if 'name' in data:
        perm.name = data['name']
    if 'type' in data:
        perm.type = data['type']
    if 'parent_id' in data:
        perm.parent_id = data['parent_id']
    if 'path' in data:
        perm.path = data['path']
    if 'icon' in data:
        perm.icon = data['icon']
    if 'sort_order' in data:
        perm.sort_order = data['sort_order']
    if 'status' in data:
        perm.status = data['status']

    db.session.commit()
    return jsonify({'code': 200, 'message': '更新成功', 'data': to_dict(perm)})

@bp.route('/api/settings/permissions/<int:perm_id>', methods=['DELETE'])
@jwt_required()
def delete_permission(perm_id):
    """删除权限"""
    from models.system import SysPermission
    perm = SysPermission.query.get(perm_id)
    if not perm:
        return jsonify({'code': 404, 'message': '权限不存在'}), 404

    # 检查是否有子权限
    children = SysPermission.query.filter_by(parent_id=perm_id).count()
    if children > 0:
        return jsonify({'code': 400, 'message': '该权限下有子权限，不能删除'}), 400

    db.session.delete(perm)
    db.session.commit()
    return jsonify({'code': 200, 'message': '删除成功'})



# ============================================
# D) 用户管理
# ============================================

@bp.route('/api/settings/users', methods=['GET'])
@jwt_required()
def get_settings_users():
    """获取用户列表（分页、搜索keyword、status筛选）"""
    from models.system import SysUser, SysRole
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '')
    status = request.args.get('status', type=int)

    query = SysUser.query.filter_by(is_deleted=0)
    if keyword:
        query = query.filter(
            db.or_(
                SysUser.username.contains(keyword),
                SysUser.real_name.contains(keyword),
                SysUser.phone.contains(keyword),
                SysUser.email.contains(keyword)
            )
        )
    if status is not None:
        query = query.filter_by(status=status)

    query = query.order_by(SysUser.created_at.desc())
    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()

    # 附加角色名称
    user_list = []
    for u in users:
        item = to_dict(u, exclude=['password'])
        if u.role_id:
            role = SysRole.query.get(u.role_id)
            item['role_name'] = role.role_name if role else ''
            item['role_code'] = role.role_code if role else ''
        else:
            item['role_name'] = ''
            item['role_code'] = ''
        user_list.append(item)

    return jsonify({
        'code': 200,
        'data': {
            'list': user_list,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    })

@bp.route('/api/settings/users', methods=['POST'])
@jwt_required()
def create_user():
    """创建用户"""
    from models.system import SysUser
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    real_name = data.get('real_name', '')
    phone = data.get('phone', '')
    email = data.get('email', '')
    role_id = data.get('role_id')
    department = data.get('department', '')
    position = data.get('position', '')

    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400

    existing = SysUser.query.filter_by(username=username).first()
    if existing:
        return jsonify({'code': 400, 'message': '用户名已存在'}), 400

    user = SysUser(
        username=username,
        password=generate_password_hash(password),
        real_name=real_name,
        phone=phone,
        email=email,
        role_id=role_id,
        department=department,
        position=position,
        base_salary=data.get('base_salary', 0),
        status=1,
        created_by=get_current_user_id()
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'code': 200, 'message': '创建成功', 'data': to_dict(user, exclude=['password'])})

@bp.route('/api/settings/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """更新用户"""
    from models.system import SysUser
    user = SysUser.query.get(user_id)
    if not user or user.is_deleted:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404

    data = request.get_json()
    if 'real_name' in data:
        user.real_name = data['real_name']
    if 'phone' in data:
        user.phone = data['phone']
    if 'email' in data:
        user.email = data['email']
    if 'department' in data:
        user.department = data['department']
    if 'position' in data:
        user.position = data['position']
    if 'avatar' in data:
        user.avatar = data['avatar']
    if 'base_salary' in data:
        user.base_salary = data['base_salary']
    if 'role_id' in data:
        user.role_id = data['role_id']
    if 'status' in data:
        user.status = data['status']

    user.updated_at = datetime.now()
    db.session.commit()
    return jsonify({'code': 200, 'message': '更新成功', 'data': to_dict(user, exclude=['password'])})

@bp.route('/api/settings/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """删除用户（不能删除自己、不能删除admin）"""
    from models.system import SysUser
    current_user_id = get_current_user_id()

    if current_user_id == user_id:
        return jsonify({'code': 400, 'message': '不能删除自己'}), 400

    user = SysUser.query.get(user_id)
    if not user or user.is_deleted:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404

    if user.username == 'admin':
        return jsonify({'code': 400, 'message': '不能删除管理员账号'}), 400

    # 软删除
    user.is_deleted = 1
    user.status = 0
    user.updated_at = datetime.now()
    db.session.commit()
    return jsonify({'code': 200, 'message': '删除成功'})

@bp.route('/api/settings/users/<int:user_id>/status', methods=['PUT'])
@jwt_required()
def toggle_user_status(user_id):
    """启用/禁用用户"""
    from models.system import SysUser
    current_user_id = get_current_user_id()

    if current_user_id == user_id:
        return jsonify({'code': 400, 'message': '不能禁用自己'}), 400

    user = SysUser.query.get(user_id)
    if not user or user.is_deleted:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404

    if user.username == 'admin':
        return jsonify({'code': 400, 'message': '不能禁用管理员账号'}), 400

    data = request.get_json()
    user.status = data.get('status', 0)
    user.updated_at = datetime.now()
    db.session.commit()
    return jsonify({'code': 200, 'message': '状态更新成功'})

@bp.route('/api/settings/users/<int:user_id>/password', methods=['PUT'])
@jwt_required()
def reset_user_password(user_id):
    """重置密码"""
    from models.system import SysUser
    user = SysUser.query.get(user_id)
    if not user or user.is_deleted:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404

    data = request.get_json()
    new_password = data.get('password')
    if not new_password:
        return jsonify({'code': 400, 'message': '新密码不能为空'}), 400

    if len(new_password) < 6:
        return jsonify({'code': 400, 'message': '密码长度不能少于6位'}), 400

    user.password = generate_password_hash(new_password)
    user.updated_at = datetime.now()
    db.session.commit()
    return jsonify({'code': 200, 'message': '密码重置成功'})

@bp.route('/api/settings/users/<int:user_id>/roles', methods=['PUT'])
@jwt_required()
def assign_user_role(user_id):
    """分配角色（接收role_id）"""
    from models.system import SysUser, SysRole
    user = SysUser.query.get(user_id)
    if not user or user.is_deleted:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404

    data = request.get_json()
    role_id = data.get('role_id')

    if role_id:
        role = SysRole.query.get(role_id)
        if not role:
            return jsonify({'code': 400, 'message': '角色不存在'}), 400

    user.role_id = role_id
    user.updated_at = datetime.now()
    db.session.commit()
    return jsonify({'code': 200, 'message': '角色分配成功'})



# ============================================
# E) 系统日志
# ============================================

@bp.route('/api/settings/logs', methods=['GET'])
@jwt_required()
def get_operation_logs():
    """获取操作日志列表"""
    from models.system import OperationLog
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    user_id = request.args.get('user_id', type=int)
    action = request.args.get('action', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = OperationLog.query

    if user_id:
        query = query.filter_by(user_id=user_id)
    if action:
        query = query.filter(OperationLog.action.contains(action))
    if start_date:
        query = query.filter(OperationLog.created_at >= start_date)
    if end_date:
        query = query.filter(OperationLog.created_at <= end_date + ' 23:59:59')

    total = query.count()
    logs = query.order_by(OperationLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        'code': 200,
        'data': {
            'list': [to_dict(l) for l in logs],
            'total': total,
            'page': page,
            'page_size': page_size
        }
    })

@bp.route('/api/settings/logs', methods=['DELETE'])
@jwt_required()
def clear_operation_logs():
    """清空操作日志"""
    from models.system import OperationLog
    OperationLog.query.delete()
    db.session.commit()
    return jsonify({'code': 200, 'message': '清空成功'})

# ============================================
# F) 权限初始化
# ============================================

@bp.route('/api/settings/init-permissions', methods=['POST'])
@jwt_required()
def init_permissions():
    """初始化系统权限数据（菜单+按钮权限种子数据）"""
    from models.system import SysPermission
    try:
        # 菜单权限定义（parent_id=0）
        menu_permissions = [
            {'name': '首页', 'code': 'dashboard', 'path': '/dashboard', 'icon': 'dashboard', 'sort_order': 1},
            {'name': '工单管理', 'code': 'workorder', 'path': '/workorder', 'icon': 'workorder', 'sort_order': 2},
            {'name': '接件管理', 'code': 'receive', 'path': '/receive', 'icon': 'receive', 'sort_order': 3},
            {'name': '派单管理', 'code': 'dispatch', 'path': '/dispatch', 'icon': 'dispatch', 'sort_order': 4},
            {'name': '报价管理', 'code': 'quote', 'path': '/quote', 'icon': 'quote', 'sort_order': 5},
            {'name': '设备管理', 'code': 'device', 'path': '/device', 'icon': 'device', 'sort_order': 6},
            {'name': '商品管理', 'code': 'product', 'path': '/product', 'icon': 'product', 'sort_order': 7},
            {'name': '销售管理', 'code': 'sales', 'path': '/sales', 'icon': 'sales', 'sort_order': 8},
            {'name': '采购管理', 'code': 'purchase', 'path': '/purchase', 'icon': 'purchase', 'sort_order': 9},
            {'name': '采购预订', 'code': 'preorder', 'path': '/preorder', 'icon': 'preorder', 'sort_order': 10},
            {'name': '销售预订', 'code': 'preorder-sale', 'path': '/preorder-sale', 'icon': 'preorder-sale', 'sort_order': 11},
            {'name': '采购退货', 'code': 'purchase-return', 'path': '/purchase-return', 'icon': 'purchase-return', 'sort_order': 12},
            {'name': '销售退货', 'code': 'sales-return', 'path': '/sales-return', 'icon': 'sales-return', 'sort_order': 13},
            {'name': '库存查询', 'code': 'inventory', 'path': '/inventory', 'icon': 'inventory', 'sort_order': 14},
            {'name': '入库管理', 'code': 'inventory-in', 'path': '/inventory-in', 'icon': 'inventory-in', 'sort_order': 15},
            {'name': '出库管理', 'code': 'inventory-out', 'path': '/inventory-out', 'icon': 'inventory-out', 'sort_order': 16},
            {'name': '库存盘点', 'code': 'inventory-check', 'path': '/inventory-check', 'icon': 'inventory-check', 'sort_order': 17},
            {'name': '客户管理', 'code': 'customer', 'path': '/customer', 'icon': 'customer', 'sort_order': 18},
            {'name': '供应商管理', 'code': 'supplier', 'path': '/supplier', 'icon': 'supplier', 'sort_order': 19},
            {'name': '应收管理', 'code': 'finance-receivable', 'path': '/finance-receivable', 'icon': 'finance-receivable', 'sort_order': 20},
            {'name': '应付管理', 'code': 'finance-payable', 'path': '/finance-payable', 'icon': 'finance-payable', 'sort_order': 21},
            {'name': '账户管理', 'code': 'finance-account', 'path': '/finance-account', 'icon': 'finance-account', 'sort_order': 22},
            {'name': '收款管理', 'code': 'finance-receipt', 'path': '/finance-receipt', 'icon': 'finance-receipt', 'sort_order': 23},
            {'name': '付款管理', 'code': 'finance-payment', 'path': '/finance-payment', 'icon': 'finance-payment', 'sort_order': 24},
            {'name': '发票管理', 'code': 'invoice', 'path': '/invoice', 'icon': 'invoice', 'sort_order': 25},
            {'name': '用户管理', 'code': 'settings-users', 'path': '/settings/users', 'icon': 'settings-users', 'sort_order': 26},
            {'name': '角色管理', 'code': 'settings-roles', 'path': '/settings/roles', 'icon': 'settings-roles', 'sort_order': 27},
            {'name': '操作日志', 'code': 'settings-log', 'path': '/settings/log', 'icon': 'settings-log', 'sort_order': 28},
            {'name': '商品分类', 'code': 'settings-category', 'path': '/settings/category', 'icon': 'settings-category', 'sort_order': 29},
            {'name': '计量单位', 'code': 'settings-unit', 'path': '/settings/unit', 'icon': 'settings-unit', 'sort_order': 30},
            {'name': '打印模版', 'code': 'settings-print', 'path': '/settings/print', 'icon': 'settings-print', 'sort_order': 31},
        ]

        # 按钮权限定义
        button_actions = ['view', 'add', 'edit', 'delete', 'export', 'print']
        button_names = {
            'view': '查看', 'add': '新增', 'edit': '编辑',
            'delete': '删除', 'export': '导出', 'print': '打印'
        }

        # 创建菜单权限
        menu_id_map = {}
        for menu in menu_permissions:
            existing = SysPermission.query.filter_by(code=menu['code'], type=1).first()
            if not existing:
                perm = SysPermission(
                    name=menu['name'],
                    code=menu['code'],
                    type=1,
                    parent_id=0,
                    path=menu['path'],
                    icon=menu['icon'],
                    sort_order=menu['sort_order'],
                    status=1
                )
                db.session.add(perm)
                db.session.flush()  # 获取id
                menu_id_map[menu['code']] = perm.id
            else:
                menu_id_map[menu['code']] = existing.id

        # 创建按钮权限（每个菜单下挂载）
        btn_count = 0
        for menu_code, parent_id in menu_id_map.items():
            for action in button_actions:
                btn_code = f'{menu_code}:{action}'
                existing = SysPermission.query.filter_by(code=btn_code, type=2).first()
                if not existing:
                    perm = SysPermission(
                        name=f'{menu_code} - {button_names[action]}',
                        code=btn_code,
                        type=2,
                        parent_id=parent_id,
                        sort_order=button_actions.index(action) + 1,
                        status=1
                    )
                    db.session.add(perm)
                    btn_count += 1

        db.session.commit()
        return jsonify({
            'code': 200,
            'message': f'权限初始化成功，共{len(menu_permissions)}个菜单权限，新增{btn_count}个按钮权限'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'权限初始化失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'权限初始化失败: {str(e)}'}), 500



