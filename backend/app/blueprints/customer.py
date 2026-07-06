"""客户管理 CRUD + 导入导出 + 批量删除。

迁移自 source-code/app.py 中 396-528 行、11201-11270 行附近、12227-12260 行附近的
原始路由代码。保持行为完全一致：状态过滤、软删除（status=0）、
硬删除（批量）、customer_code/pinyin_code 自动生成、Excel 白名单校验等。
"""
from datetime import datetime

from flask import Blueprint, Response, request
from flask_jwt_extended import jwt_required

from extensions import db
from app.security import permission
from app.utils import (
    export_to_excel,
    generate_code,
    generate_pinyin_code,
    read_excel_data,
)

bp = Blueprint('customer', __name__, url_prefix='/api/customers')


# Excel 文件白名单（与原 app.py 行为一致）
ALLOWED_EXCEL_EXT = {'xlsx', 'xls', 'csv'}
ALLOWED_EXCEL_MIME = {
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/octet-stream',
    'text/csv',
}


@bp.route('', methods=['GET'])
@jwt_required()
@permission('customer:view')
def list_customers():
    """获取客户列表（仅 status=1，按 created_at desc 排序）。"""
    from models.customer import BaseCustomer

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '')
    customer_type = request.args.get('customer_type', type=int)

    query = BaseCustomer.query.filter_by(status=1)

    if keyword:
        query = query.filter(
            db.or_(
                BaseCustomer.customer_name.contains(keyword),
                BaseCustomer.pinyin_code.contains(keyword.upper()),
                BaseCustomer.phone.contains(keyword),
                BaseCustomer.customer_code.contains(keyword),
            )
        )

    if customer_type:
        query = query.filter_by(customer_type=customer_type)

    total = query.count()
    customers = query.order_by(BaseCustomer.created_at.desc()).paginate(
        page=page, per_page=page_size, error_out=False
    )

    return {
        'code': 200,
        'data': {
            'list': [{
                'id': c.id,
                'customer_code': c.customer_code,
                'customer_name': c.customer_name,
                'customer_type': c.customer_type,
                'contact_name': c.contact_name,
                'phone': c.phone,
                'phone2': c.phone2,
                'address': c.address,
                'discount_rate': float(c.discount_rate) if c.discount_rate else 100.00,
                'total_sales_amount': float(c.total_sales_amount) if c.total_sales_amount else 0.00,
                'total_sales_count': c.total_sales_count,
                'created_at': c.created_at.strftime('%Y-%m-%d %H:%M:%S') if c.created_at else None,
            } for c in customers.items],
            'total': total,
            'page': page,
            'page_size': page_size,
        }
    }, 200


@bp.route('/<int:cid>', methods=['GET'])
@jwt_required()
@permission('customer:view')
def get_customer(cid):
    """获取客户详情。"""
    from models.customer import BaseCustomer
    from app.utils import to_dict

    customer = BaseCustomer.query.get(cid)
    if not customer:
        return {'code': 404, 'message': '客户不存在'}, 404

    return {'code': 200, 'data': to_dict(customer)}, 200


@bp.route('', methods=['POST'])
@jwt_required()
@permission('customer:add')
def create_customer():
    """创建客户（自动生成 customer_code 和 pinyin_code）。"""
    from models.customer import BaseCustomer

    data = request.get_json()

    last_customer = BaseCustomer.query.order_by(BaseCustomer.id.desc()).first()
    customer_code = generate_code('C', last_customer.id if last_customer else 0)

    customer = BaseCustomer(
        customer_code=customer_code,
        customer_name=data.get('customer_name'),
        customer_type=data.get('customer_type', 1),
        pinyin_code=generate_pinyin_code(data.get('customer_name', '')),
        contact_name=data.get('contact_name'),
        phone=data.get('phone'),
        phone2=data.get('phone2'),
        email=data.get('email'),
        address=data.get('address'),
        discount_rate=data.get('discount_rate', 100.00),
        credit_limit=data.get('credit_limit', 0.00),
        tax_number=data.get('tax_number'),
        bank_name=data.get('bank_name'),
        bank_account=data.get('bank_account'),
        remark=data.get('remark'),
    )

    db.session.add(customer)
    db.session.commit()

    return {
        'code': 200,
        'message': '创建成功',
        'data': {'id': customer.id, 'customer_code': customer_code},
    }, 200


@bp.route('/<int:cid>', methods=['PUT'])
@jwt_required()
@permission('customer:edit')
def update_customer(cid):
    """更新客户。"""
    from models.customer import BaseCustomer

    customer = BaseCustomer.query.get(cid)
    if not customer:
        return {'code': 404, 'message': '客户不存在'}, 404

    data = request.get_json()

    for field in ['customer_name', 'customer_type', 'contact_name', 'phone', 'phone2',
                  'email', 'address', 'discount_rate', 'credit_limit', 'tax_number',
                  'bank_name', 'bank_account', 'remark']:
        if field in data:
            setattr(customer, field, data[field])

    if 'customer_name' in data:
        customer.pinyin_code = generate_pinyin_code(data['customer_name'])

    db.session.commit()
    return {'code': 200, 'message': '更新成功'}, 200


@bp.route('/<int:cid>', methods=['DELETE'])
@jwt_required()
@permission('customer:delete')
def delete_customer(cid):
    """软删除客户（status=0）。"""
    from models.customer import BaseCustomer

    customer = BaseCustomer.query.get(cid)
    if not customer:
        return {'code': 404, 'message': '客户不存在'}, 404

    customer.status = 0
    db.session.commit()
    return {'code': 200, 'message': '删除成功'}, 200


@bp.route('/export', methods=['GET'])
@jwt_required()
@permission('customer:view')
def export_customers():
    """导出客户 Excel。"""
    from models.customer import BaseCustomer

    customers = BaseCustomer.query.filter_by(status=1).all()

    data = []
    for c in customers:
        data.append({
            '客户编码': c.customer_code,
            '客户名称': c.customer_name,
            '客户类型': '个人' if c.customer_type == 1 else '企业',
            '联系人': c.contact_name,
            '电话': c.phone,
            '电话2': c.phone2,
            '邮箱': c.email,
            '地址': c.address,
            '折扣率': float(c.discount_rate) if c.discount_rate else 100.00,
            '信用额度': float(c.credit_limit) if c.credit_limit else 0.00,
            '税号': c.tax_number,
            '开户行': c.bank_name,
            '银行账号': c.bank_account,
            '备注': c.remark,
        })

    headers = ['客户编码', '客户名称', '客户类型', '联系人', '电话', '电话2', '邮箱', '地址',
               '折扣率', '信用额度', '税号', '开户行', '银行账号', '备注']

    excel_bytes = export_to_excel(data, headers, sheet_name='数据')
    filename = f'客户列表_{datetime.now().strftime("%Y%m%d")}.xlsx'
    return Response(
        excel_bytes,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@bp.route('/import', methods=['POST'])
@jwt_required()
@permission('customer:add')
def import_customers():
    """导入客户 Excel（带白名单校验 + 逐行错误收集）。"""
    from models.customer import BaseCustomer

    if 'file' not in request.files:
        return {'code': 400, 'message': '请选择文件'}, 400

    file = request.files['file']
    if file.filename == '':
        return {'code': 400, 'message': '请选择文件'}, 400

    # Excel 文件白名单校验
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXCEL_EXT:
        return {'code': 400, 'message': f'仅支持 xlsx/xls/csv 格式，当前: {ext}'}, 400
    if (file.mimetype or '').lower() not in ALLOWED_EXCEL_MIME:
        return {'code': 400, 'message': '文件 MIME 类型不符'}, 400

    try:
        rows = read_excel_data(file)

        success_count = 0
        error_count = 0
        errors = []

        for idx, row in enumerate(rows):
            try:
                # 验证必填字段
                customer_name = row.get('客户名称')
                if not customer_name or str(customer_name).strip() == '':
                    error_count += 1
                    errors.append(f'第{idx + 2}行：客户名称不能为空')
                    continue

                last_customer = BaseCustomer.query.order_by(BaseCustomer.id.desc()).first()
                customer_code = generate_code('C', last_customer.id if last_customer else 0)

                def _get_val(row_, key_):
                    v = row_.get(key_)
                    if v is None:
                        return None
                    s = str(v).strip()
                    return s if s else None

                def _get_float(row_, key_, default=0.0):
                    v = row_.get(key_)
                    if v is None:
                        return default
                    try:
                        return float(v)
                    except Exception:
                        return default

                customer = BaseCustomer(
                    customer_code=customer_code,
                    customer_name=str(customer_name).strip(),
                    customer_type=1 if _get_val(row, '客户类型') == '个人' else 2,
                    pinyin_code=generate_pinyin_code(str(customer_name)),
                    contact_name=_get_val(row, '联系人'),
                    phone=_get_val(row, '电话'),
                    phone2=_get_val(row, '电话2'),
                    email=_get_val(row, '邮箱'),
                    address=_get_val(row, '地址'),
                    discount_rate=_get_float(row, '折扣率', 100.00),
                    credit_limit=_get_float(row, '信用额度', 0.00),
                    tax_number=_get_val(row, '税号'),
                    bank_name=_get_val(row, '开户行'),
                    bank_account=_get_val(row, '银行账号'),
                    remark=_get_val(row, '备注'),
                )

                db.session.add(customer)
                success_count += 1

            except Exception as e:
                error_count += 1
                errors.append(f'第{idx + 2}行：{str(e)}')

        db.session.commit()

        return {
            'code': 200,
            'message': f'导入完成，成功{success_count}条，失败{error_count}条',
            'data': {
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors[:10],
            },
        }, 200

    except Exception as e:
        return {'code': 500, 'message': f'导入失败：{str(e)}'}, 500


@bp.route('/batch-delete', methods=['POST'])
@jwt_required()
@permission('customer:delete')
def batch_delete_customers():
    """批量删除客户（硬删除，与单条软删除保持原行为差异）。"""
    from models.customer import BaseCustomer

    try:
        data = request.get_json()
        ids = data.get('ids', [])
        if not ids:
            return {'code': 400, 'message': '请选择要删除的客户'}, 400
        customers = BaseCustomer.query.filter(BaseCustomer.id.in_(ids)).all()
        count = len(customers)
        for customer in customers:
            db.session.delete(customer)
        db.session.commit()
        return {'code': 200, 'message': f'成功删除{count}个客户'}, 200
    except Exception:
        db.session.rollback()
        return {'code': 500, 'message': '批量删除客户失败，请稍后重试'}, 500