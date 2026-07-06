"""供应商管理 CRUD + 导入导出 + 批量删除。

迁移自 source-code/app.py 中 530-654 行、11341-11410 行附近、12246-12265 行附近的
原始路由代码。保持行为完全一致：状态过滤、软删除（status=0）、
硬删除（批量）、supplier_code/pinyin_code 自动生成、Excel 白名单校验等。
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

bp = Blueprint('supplier', __name__, url_prefix='/api/suppliers')


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
@permission('supplier:view')
def list_suppliers():
    """获取供应商列表（仅 status=1，按 created_at desc 排序）。"""
    from models.supplier import BaseSupplier

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '')
    is_repair_partner = request.args.get('is_repair_partner', type=int)

    query = BaseSupplier.query.filter_by(status=1)

    if keyword:
        query = query.filter(
            db.or_(
                BaseSupplier.supplier_name.contains(keyword),
                BaseSupplier.pinyin_code.contains(keyword.upper()),
                BaseSupplier.phone.contains(keyword),
                BaseSupplier.supplier_code.contains(keyword),
            )
        )

    if is_repair_partner is not None:
        query = query.filter_by(is_repair_partner=is_repair_partner)

    total = query.count()
    suppliers = query.order_by(BaseSupplier.created_at.desc()).paginate(
        page=page, per_page=page_size, error_out=False
    )

    return {
        'code': 200,
        'data': {
            'list': [{
                'id': s.id,
                'supplier_code': s.supplier_code,
                'supplier_name': s.supplier_name,
                'contact_name': s.contact_name,
                'phone': s.phone,
                'is_repair_partner': s.is_repair_partner,
                'total_purchase_amount': float(s.total_purchase_amount) if s.total_purchase_amount else 0.00,
                'total_repair_amount': float(s.total_repair_amount) if s.total_repair_amount else 0.00,
                'created_at': s.created_at.strftime('%Y-%m-%d %H:%M:%S') if s.created_at else None,
            } for s in suppliers.items],
            'total': total,
            'page': page,
            'page_size': page_size,
        }
    }, 200


@bp.route('/<int:sid>', methods=['GET'])
@jwt_required()
@permission('supplier:view')
def get_supplier(sid):
    """获取供应商详情。"""
    from models.supplier import BaseSupplier
    from app.utils import to_dict

    supplier = BaseSupplier.query.get(sid)
    if not supplier:
        return {'code': 404, 'message': '供应商不存在'}, 404

    return {'code': 200, 'data': to_dict(supplier)}, 200


@bp.route('', methods=['POST'])
@jwt_required()
@permission('supplier:add')
def create_supplier():
    """创建供应商（自动生成 supplier_code 和 pinyin_code）。"""
    from models.supplier import BaseSupplier

    data = request.get_json()

    last_supplier = BaseSupplier.query.order_by(BaseSupplier.id.desc()).first()
    supplier_code = generate_code('S', last_supplier.id if last_supplier else 0)

    supplier = BaseSupplier(
        supplier_code=supplier_code,
        supplier_name=data.get('supplier_name'),
        pinyin_code=generate_pinyin_code(data.get('supplier_name', '')),
        contact_name=data.get('contact_name'),
        phone=data.get('phone'),
        email=data.get('email'),
        address=data.get('address'),
        tax_number=data.get('tax_number'),
        bank_name=data.get('bank_name'),
        bank_account=data.get('bank_account'),
        is_repair_partner=data.get('is_repair_partner', 0),
        repair_types=data.get('repair_types'),
        remark=data.get('remark'),
    )

    db.session.add(supplier)
    db.session.commit()

    return {
        'code': 200,
        'message': '创建成功',
        'data': {'id': supplier.id, 'supplier_code': supplier_code},
    }, 200


@bp.route('/<int:sid>', methods=['PUT'])
@jwt_required()
@permission('supplier:edit')
def update_supplier(sid):
    """更新供应商。"""
    from models.supplier import BaseSupplier

    supplier = BaseSupplier.query.get(sid)
    if not supplier:
        return {'code': 404, 'message': '供应商不存在'}, 404

    data = request.get_json()

    for field in ['supplier_name', 'contact_name', 'phone', 'email', 'address',
                  'tax_number', 'bank_name', 'bank_account', 'is_repair_partner',
                  'repair_types', 'remark']:
        if field in data:
            setattr(supplier, field, data[field])

    if 'supplier_name' in data:
        supplier.pinyin_code = generate_pinyin_code(data['supplier_name'])

    db.session.commit()
    return {'code': 200, 'message': '更新成功'}, 200


@bp.route('/<int:sid>', methods=['DELETE'])
@jwt_required()
@permission('supplier:delete')
def delete_supplier(sid):
    """软删除供应商（status=0）。"""
    from models.supplier import BaseSupplier

    supplier = BaseSupplier.query.get(sid)
    if not supplier:
        return {'code': 404, 'message': '供应商不存在'}, 404

    supplier.status = 0
    db.session.commit()
    return {'code': 200, 'message': '删除成功'}, 200


@bp.route('/export', methods=['GET'])
@jwt_required()
@permission('supplier:view')
def export_suppliers():
    """导出供应商 Excel。"""
    from models.supplier import BaseSupplier

    suppliers = BaseSupplier.query.filter_by(status=1).all()

    data = []
    for s in suppliers:
        data.append({
            '供应商编码': s.supplier_code,
            '供应商名称': s.supplier_name,
            '联系人': s.contact_name,
            '电话': s.phone,
            '邮箱': s.email,
            '地址': s.address,
            '税号': s.tax_number,
            '开户行': s.bank_name,
            '银行账号': s.bank_account,
            '是否维修合作方': '是' if s.is_repair_partner else '否',
            '备注': s.remark,
        })

    headers = ['供应商编码', '供应商名称', '联系人', '电话', '邮箱', '地址',
               '税号', '开户行', '银行账号', '是否维修合作方', '备注']

    excel_bytes = export_to_excel(data, headers, sheet_name='数据')
    filename = f'供应商列表_{datetime.now().strftime("%Y%m%d")}.xlsx'
    return Response(
        excel_bytes,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@bp.route('/import', methods=['POST'])
@jwt_required()
@permission('supplier:add')
def import_suppliers():
    """导入供应商 Excel（带白名单校验 + 逐行错误收集）。"""
    from models.supplier import BaseSupplier

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
                supplier_name = row.get('供应商名称')
                if not supplier_name or str(supplier_name).strip() == '':
                    error_count += 1
                    errors.append(f'第{idx + 2}行：供应商名称不能为空')
                    continue

                last_supplier = BaseSupplier.query.order_by(BaseSupplier.id.desc()).first()
                supplier_code = generate_code('S', last_supplier.id if last_supplier else 0)

                def _get_val(row_, key_):
                    v = row_.get(key_)
                    if v is None:
                        return None
                    s = str(v).strip()
                    return s if s else None

                is_repair = 1 if _get_val(row, '是否维修合作方') == '是' else 0

                supplier = BaseSupplier(
                    supplier_code=supplier_code,
                    supplier_name=str(supplier_name).strip(),
                    pinyin_code=generate_pinyin_code(str(supplier_name)),
                    contact_name=_get_val(row, '联系人'),
                    phone=_get_val(row, '电话'),
                    email=_get_val(row, '邮箱'),
                    address=_get_val(row, '地址'),
                    tax_number=_get_val(row, '税号'),
                    bank_name=_get_val(row, '开户行'),
                    bank_account=_get_val(row, '银行账号'),
                    is_repair_partner=is_repair,
                    remark=_get_val(row, '备注'),
                )

                db.session.add(supplier)
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
@permission('supplier:delete')
def batch_delete_suppliers():
    """批量删除供应商（硬删除，与单条软删除保持原行为差异）。"""
    from models.supplier import BaseSupplier

    try:
        data = request.get_json()
        ids = data.get('ids', [])
        if not ids:
            return {'code': 400, 'message': '请选择要删除的供应商'}, 400
        suppliers = BaseSupplier.query.filter(BaseSupplier.id.in_(ids)).all()
        count = len(suppliers)
        for supplier in suppliers:
            db.session.delete(supplier)
        db.session.commit()
        return {'code': 200, 'message': f'成功删除{count}个供应商'}, 200
    except Exception:
        db.session.rollback()
        return {'code': 500, 'message': '批量删除供应商失败，请稍后重试'}, 500