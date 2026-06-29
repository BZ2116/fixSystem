"""商品管理 CRUD + 批量更新 + 导入导出。

迁移自 source-code/app.py 中 656-931 行（基础 CRUD）、11466-11550 行（导入导出）、
12044-12085 行（check_business_record 辅助）、12069-12230 行（批量更新）附近的
原始路由代码。保持行为完全一致：status=1 过滤、软删除（status=0）、
硬删除（批量，前置业务记录校验）、product_code/pinyin_code 自动生成、
Excel 白名单校验、库存关联写入、批量改分类/价格/库存预警/排序/启停等。

注意：debug_stock 路由（/api/debug/stock）属于调试端点，本蓝图不注册，留给
Task 29 "删除调试路由" 阶段处理。
"""
from datetime import datetime

from flask import Blueprint, Response, request
from flask_jwt_extended import jwt_required

from extensions import db
from app.utils import (
    export_to_excel,
    generate_code,
    generate_pinyin_code,
    read_excel_data,
    to_dict,
)

bp = Blueprint('product', __name__, url_prefix='/api/products')


# Excel 文件白名单（与原 app.py 行为一致）
ALLOWED_EXCEL_EXT = {'xlsx', 'xls', 'csv'}
ALLOWED_EXCEL_MIME = {
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/octet-stream',
    'text/csv',
}


def check_business_record(ids):
    """检查商品是否有业务记录（入库/出库/工单配件/采购明细/销售明细）。

    任何一个 Item 模型若未定义（对应的子域蓝图尚未迁移），就静默跳过；
    返回的列表只包含「有业务记录」的商品 id。
    """
    has_record_ids = []

    for module_path, model_name in (
        ('models.inventory.flow', 'InventoryInItem'),
        ('models.inventory.flow', 'InventoryOutItem'),
        ('models.workorder.order', 'WorkOrderPart'),
    ):
        try:
            import importlib
            mod = importlib.import_module(module_path)
            model = getattr(mod, model_name)
            rows = model.query.filter(
                model.product_id.in_(ids)
            ).with_entities(model.product_id).distinct().all()
            has_record_ids.extend([r[0] for r in rows])
        except (ImportError, AttributeError):
            continue

    for module_path, model_name in (
        ('models.purchase.order', 'PurchaseOrderItem'),
        ('models.sales.order', 'SalesOrderItem'),
    ):
        try:
            import importlib
            mod = importlib.import_module(module_path)
            model = getattr(mod, model_name)
            rows = model.query.filter(
                model.product_id.in_(ids)
            ).with_entities(model.product_id).distinct().all()
            has_record_ids.extend([r[0] for r in rows])
        except (ImportError, AttributeError):
            continue

    return list(set(has_record_ids))


# ============================================
# 商品 CRUD
# ============================================

@bp.route('', methods=['GET'])
@jwt_required()
def list_products():
    """获取商品列表。"""
    from models.product.info import ProductInfo
    from models.inventory.stock import InventoryStock

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '')
    category_id = request.args.get('category_id', type=int)

    query = ProductInfo.query.filter_by(status=1)

    if keyword:
        query = query.filter(
            db.or_(
                ProductInfo.product_name.contains(keyword),
                ProductInfo.pinyin_code.contains(keyword.upper()),
                ProductInfo.barcode.contains(keyword),
                ProductInfo.product_code.contains(keyword),
            )
        )

    if category_id:
        query = query.filter_by(category_id=category_id)

    total = query.count()
    products = query.order_by(ProductInfo.created_at.desc()).paginate(
        page=page, per_page=page_size, error_out=False
    )

    # 获取库存信息（从 InventoryStock 表）
    product_ids = [p.id for p in products.items]
    stocks = InventoryStock.query.filter(InventoryStock.product_id.in_(product_ids)).all()
    stock_map = {}
    for s in stocks:
        stock_map[int(s.product_id)] = s

    return {
        'code': 200,
        'data': {
            'list': [{
                'id': p.id,
                'product_code': p.product_code,
                'barcode': p.barcode,
                'product_name': p.product_name,
                'category_id': p.category_id,
                'category_name': p.category_name,
                'brand': p.brand,
                'specification': p.specification,
                'unit_name': p.unit_name or '个',
                'purchase_price': float(p.purchase_price) if p.purchase_price else 0.00,
                'sale_price': float(p.sale_price) if p.sale_price else 0.00,
                'member_price': float(p.member_price) if p.member_price else 0.00,
                'wholesale_price': float(p.wholesale_price) if p.wholesale_price else 0.00,
                'cost_price': float(p.cost_price) if p.cost_price else 0.00,
                'current_stock': float(stock_map.get(int(p.id)).available_quantity)
                    if stock_map.get(int(p.id)) and stock_map.get(int(p.id)).available_quantity else 0,
                'min_stock': p.min_stock,
                'is_serial': p.is_serial,
                'is_batch': p.is_batch,
                'is_assembly': p.is_assembly,
                'image_url': p.image_url,
                'created_at': p.created_at.strftime('%Y-%m-%d %H:%M:%S') if p.created_at else None,
            } for p in products.items],
            'total': total,
            'page': page,
            'page_size': page_size,
        },
    }, 200


@bp.route('/<int:pid>', methods=['GET'])
@jwt_required()
def get_product(pid):
    """获取商品详情。"""
    from models.product.info import ProductInfo, ProductUnit, ProductUnitRel
    from models.inventory.stock import InventoryStock

    product = ProductInfo.query.get(pid)
    if not product:
        return {'code': 404, 'message': '商品不存在'}, 404

    # 获取库存信息
    stock = InventoryStock.query.filter_by(product_id=pid).first()
    stock_info = None
    if stock:
        stock_info = {
            'quantity': float(stock.quantity) if stock.quantity else 0,
            'frozen_quantity': float(stock.frozen_quantity) if stock.frozen_quantity else 0,
            'available_quantity': float(stock.available_quantity) if stock.available_quantity else 0,
        }

    # 获取多单位信息
    unit_rels = ProductUnitRel.query.filter_by(product_id=pid).all()
    units = []
    for rel in unit_rels:
        unit = ProductUnit.query.get(rel.unit_id)
        if unit:
            units.append({
                'id': rel.id,
                'unit_id': rel.unit_id,
                'unit_name': unit.unit_name,
                'unit_code': unit.unit_code,
                'conversion_rate': float(rel.conversion_rate) if rel.conversion_rate else 1.0000,
                'is_default': rel.is_default,
            })

    result = to_dict(product)
    result['stock'] = stock_info
    result['units'] = units
    return {'code': 200, 'data': result}, 200


@bp.route('', methods=['POST'])
@jwt_required()
def create_product():
    """创建商品。"""
    from models.product.info import ProductInfo, ProductUnitRel
    from models.inventory.stock import InventoryStock

    data = request.get_json()

    last_product = ProductInfo.query.order_by(ProductInfo.id.desc()).first()
    product_code = generate_code('P', last_product.id if last_product else 0)

    # 处理 barcode：空字符串转为 None，避免唯一索引冲突
    barcode = data.get('barcode')
    if barcode is not None and str(barcode).strip() == '':
        barcode = None

    # 处理单位信息：从 units 中获取默认单位名称
    units = data.get('units', [])
    unit_name = data.get('unit_name', '')
    unit_id = data.get('unit_id')
    if units:
        for u in units:
            if u.get('is_default') == 1:
                unit_id = u.get('unit_id')
                unit_name = u.get('unit_name', '')
                break
        # 如果没有默认单位，取第一个
        if not unit_name and units:
            unit_id = units[0].get('unit_id')
            unit_name = units[0].get('unit_name', '')

    product = ProductInfo(
        product_code=product_code,
        barcode=barcode,
        product_name=data.get('product_name'),
        pinyin_code=generate_pinyin_code(data.get('product_name', '')),
        category_id=data.get('category_id'),
        category_name=data.get('category_name'),
        brand=data.get('brand'),
        specification=data.get('specification'),
        unit_id=unit_id,
        unit_name=unit_name,
        sub_unit_id=data.get('sub_unit_id'),
        sub_unit_rate=data.get('sub_unit_rate'),
        purchase_price=data.get('purchase_price', 0),
        sale_price=data.get('sale_price', 0),
        member_price=data.get('member_price', 0),
        wholesale_price=data.get('wholesale_price', 0),
        customer_price=data.get('customer_price', 0),
        cost_price=data.get('cost_price', 0),
        min_stock=data.get('min_stock', 0),
        max_stock=data.get('max_stock', 0),
        is_serial=data.get('is_serial', 0),
        is_batch=data.get('is_batch', 0),
        is_assembly=data.get('is_assembly', 0),
        is_gift=data.get('is_gift', 0),
        no_cost=data.get('no_cost', 0),
        no_stock=data.get('no_stock', 0),
        remark=data.get('remark'),
    )

    db.session.add(product)
    db.session.commit()

    # 创建库存记录
    stock = InventoryStock(
        product_id=product.id,
        product_code=product.product_code,
        product_name=product.product_name,
        quantity=0,
        frozen_quantity=0,
        available_quantity=0,
        cost_price=product.cost_price,
    )
    db.session.add(stock)

    # 处理多单位关联
    if units:
        for unit_data in units:
            unit_rel = ProductUnitRel(
                product_id=product.id,
                unit_id=unit_data.get('unit_id'),
                conversion_rate=unit_data.get('conversion_rate', 1.0000),
                is_default=unit_data.get('is_default', 0),
            )
            db.session.add(unit_rel)

    db.session.commit()

    return {
        'code': 200,
        'message': '创建成功',
        'data': {'id': product.id, 'product_code': product_code},
    }, 200


@bp.route('/<int:pid>', methods=['PUT'])
@jwt_required()
def update_product(pid):
    """更新商品。"""
    from models.product.info import ProductInfo, ProductUnitRel

    product = ProductInfo.query.get(pid)
    if not product:
        return {'code': 404, 'message': '商品不存在'}, 404

    data = request.get_json()

    for field in [
        'product_name', 'barcode', 'category_id', 'category_name', 'brand',
        'specification', 'unit_id', 'unit_name', 'sub_unit_id', 'sub_unit_rate',
        'purchase_price', 'sale_price', 'member_price', 'wholesale_price',
        'customer_price', 'cost_price', 'min_stock', 'max_stock',
        'is_serial', 'is_batch', 'is_assembly', 'is_gift', 'no_cost', 'no_stock', 'remark',
    ]:
        if field in data:
            setattr(product, field, data[field])

    if 'product_name' in data:
        product.pinyin_code = generate_pinyin_code(data['product_name'])

    # 处理多单位关联更新
    if 'units' in data:
        # 删除旧的单位关联
        ProductUnitRel.query.filter_by(product_id=pid).delete()

        # 添加新的单位关联
        for unit_data in data['units']:
            unit_rel = ProductUnitRel(
                product_id=pid,
                unit_id=unit_data.get('unit_id'),
                conversion_rate=unit_data.get('conversion_rate', 1.0000),
                is_default=unit_data.get('is_default', 0),
            )
            db.session.add(unit_rel)

    db.session.commit()
    return {'code': 200, 'message': '更新成功'}, 200


@bp.route('/<int:pid>', methods=['DELETE'])
@jwt_required()
def delete_product(pid):
    """软删除商品（status=0）。"""
    from models.product.info import ProductInfo

    product = ProductInfo.query.get(pid)
    if not product:
        return {'code': 404, 'message': '商品不存在'}, 404

    product.status = 0
    db.session.commit()
    return {'code': 200, 'message': '删除成功'}, 200


# ============================================
# 导入导出
# ============================================

@bp.route('/export', methods=['GET'])
@jwt_required()
def export_products():
    """导出商品 Excel。"""
    from models.product.info import ProductInfo

    products = ProductInfo.query.filter_by(status=1).all()

    rows = []
    for p in products:
        rows.append({
            '商品编码': p.product_code,
            '条形码': p.barcode,
            '商品名称': p.product_name,
            '分类': p.category_name,
            '品牌': p.brand,
            '规格': p.specification,
            '单位': p.unit_name,
            '采购价': float(p.purchase_price) if p.purchase_price else 0.00,
            '销售价': float(p.sale_price) if p.sale_price else 0.00,
            '会员价': float(p.member_price) if p.member_price else 0.00,
            '批发价': float(p.wholesale_price) if p.wholesale_price else 0.00,
            '成本价': float(p.cost_price) if p.cost_price else 0.00,
            '库存下限': p.min_stock,
            '库存上限': p.max_stock,
            '当前库存': p.current_stock,
            '是否序列号管理': '是' if p.is_serial else '否',
            '是否批次管理': '是' if p.is_batch else '否',
            '备注': p.remark,
        })

    headers = ['商品编码', '条形码', '商品名称', '分类', '品牌', '规格', '单位',
               '采购价', '销售价', '会员价', '批发价', '成本价',
               '库存下限', '库存上限', '当前库存',
               '是否序列号管理', '是否批次管理', '备注']

    excel_bytes = export_to_excel(rows, headers, sheet_name='数据')
    filename = f'商品列表_{datetime.now().strftime("%Y%m%d")}.xlsx'
    return Response(
        excel_bytes,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@bp.route('/import', methods=['POST'])
@jwt_required()
def import_products():
    """导入商品 Excel（带白名单校验 + 逐行错误收集）。"""
    from models.product.info import ProductInfo
    from models.inventory.stock import InventoryStock

    if 'file' not in request.files:
        return {'code': 400, 'message': '请选择文件'}, 400

    file = request.files['file']
    if file.filename == '':
        return {'code': 400, 'message': '请选择文件'}, 400

    # Excel 文件白名单
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXCEL_EXT:
        return {'code': 400, 'message': f'仅支持 xlsx/xls/csv 格式，当前: {ext}'}, 400
    if (file.mimetype or '').lower() not in ALLOWED_EXCEL_MIME:
        return {'code': 400, 'message': '文件 MIME 类型不符'}, 400

    try:
        rows, error = read_excel_data_with_err(file)
        if error:
            return {'code': 400, 'message': error}, 400

        success_count = 0
        error_count = 0
        errors = []

        for idx, row in enumerate(rows):
            try:
                product_name = row.get('商品名称')
                if not product_name or str(product_name).strip() == '':
                    error_count += 1
                    errors.append(f'第{idx + 2}行：商品名称不能为空')
                    continue

                last_product = ProductInfo.query.order_by(ProductInfo.id.desc()).first()
                product_code = generate_code('P', last_product.id if last_product else 0)

                def get_val(row_, key_):
                    v = row_.get(key_)
                    if v is None:
                        return None
                    s = str(v).strip()
                    return s if s else None

                def get_float(row_, key_, default=0.0):
                    v = row_.get(key_)
                    if v is None:
                        return default
                    try:
                        return float(v)
                    except Exception:
                        return default

                def get_int(row_, key_, default=0):
                    v = row_.get(key_)
                    if v is None:
                        return default
                    try:
                        return int(float(v))
                    except Exception:
                        return default

                is_serial = 1 if get_val(row, '是否序列号管理') == '是' else 0
                is_batch = 1 if get_val(row, '是否批次管理') == '是' else 0

                product = ProductInfo(
                    product_code=product_code,
                    barcode=get_val(row, '条形码'),
                    product_name=str(product_name).strip(),
                    pinyin_code=generate_pinyin_code(str(product_name)),
                    category_name=get_val(row, '分类'),
                    brand=get_val(row, '品牌'),
                    specification=get_val(row, '规格'),
                    unit_name=get_val(row, '单位'),
                    purchase_price=get_float(row, '采购价'),
                    sale_price=get_float(row, '销售价'),
                    member_price=get_float(row, '会员价'),
                    wholesale_price=get_float(row, '批发价'),
                    cost_price=get_float(row, '成本价'),
                    min_stock=get_int(row, '库存下限'),
                    max_stock=get_int(row, '库存上限'),
                    is_serial=is_serial,
                    is_batch=is_batch,
                    remark=get_val(row, '备注'),
                )

                db.session.add(product)
                db.session.flush()

                # 创建库存记录
                stock = InventoryStock(
                    product_id=product.id,
                    product_code=product.product_code,
                    product_name=product.product_name,
                    quantity=0,
                    frozen_quantity=0,
                    available_quantity=0,
                    cost_price=product.cost_price,
                )
                db.session.add(stock)

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


def read_excel_data_with_err(file):
    """封装 read_excel_data，统一返回 (rows, error_str)。

    原 app.py 用 (data, error) 元组风格，这里仅做薄包装。
    """
    try:
        rows = read_excel_data(file)
        return rows, None
    except Exception as e:
        return None, str(e)


# ============================================
# 批量更新
# ============================================

@bp.route('/batch-update-category', methods=['POST'])
@jwt_required()
def batch_update_category():
    """批量修改分类。"""
    from models.product.info import ProductInfo

    try:
        data = request.get_json()
        ids = data.get('ids', [])
        category_id = data.get('category_id')
        category_name = data.get('category_name', '')
        if not ids:
            return {'code': 400, 'message': '请选择要操作的商品'}, 400
        if not category_id:
            return {'code': 400, 'message': '请选择新分类'}, 400
        products = ProductInfo.query.filter(ProductInfo.id.in_(ids)).all()
        for product in products:
            product.category_id = category_id
            product.category_name = category_name
        db.session.commit()
        return {'code': 200, 'message': f'成功修改{len(products)}个商品的分类'}, 200
    except Exception:
        db.session.rollback()
        return {'code': 500, 'message': '批量修改分类失败，请稍后重试'}, 500


@bp.route('/batch-update-price', methods=['POST'])
@jwt_required()
def batch_update_price():
    """批量修改价格。"""
    from models.product.info import ProductInfo

    try:
        data = request.get_json()
        ids = data.get('ids', [])
        if not ids:
            return {'code': 400, 'message': '请选择要操作的商品'}, 400
        products = ProductInfo.query.filter(ProductInfo.id.in_(ids)).all()
        update_fields = {}
        for field in ['purchase_price', 'sale_price', 'cost_price', 'member_price',
                      'wholesale_price', 'customer_price']:
            if field in data and data[field] is not None:
                update_fields[field] = data[field]
        if not update_fields:
            return {'code': 400, 'message': '请至少填写一个价格字段'}, 400
        for product in products:
            for field, value in update_fields.items():
                setattr(product, field, value)
        db.session.commit()
        return {'code': 200, 'message': f'成功修改{len(products)}个商品的价格'}, 200
    except Exception:
        db.session.rollback()
        return {'code': 500, 'message': '批量修改价格失败，请稍后重试'}, 500


@bp.route('/batch-update-stock-warning', methods=['POST'])
@jwt_required()
def batch_update_stock_warning():
    """批量设置库存预警。"""
    from models.product.info import ProductInfo

    try:
        data = request.get_json()
        ids = data.get('ids', [])
        min_stock = data.get('min_stock')
        max_stock = data.get('max_stock')
        if not ids:
            return {'code': 400, 'message': '请选择要操作的商品'}, 400
        if min_stock is None:
            return {'code': 400, 'message': '请设置最低库存'}, 400
        products = ProductInfo.query.filter(ProductInfo.id.in_(ids)).all()
        for product in products:
            product.min_stock = min_stock
            if max_stock is not None:
                product.max_stock = max_stock
        db.session.commit()
        return {'code': 200, 'message': f'成功设置{len(products)}个商品的库存预警'}, 200
    except Exception:
        db.session.rollback()
        return {'code': 500, 'message': '批量设置库存预警失败，请稍后重试'}, 500


@bp.route('/batch-update-sort', methods=['POST'])
@jwt_required()
def batch_update_sort():
    """批量修改排序。"""
    from models.product.info import ProductInfo

    try:
        data = request.get_json()
        ids = data.get('ids', [])
        sort_order = data.get('sort_order')
        if not ids:
            return {'code': 400, 'message': '请选择要操作的商品'}, 400
        if sort_order is None:
            return {'code': 400, 'message': '请设置排序值'}, 400
        products = ProductInfo.query.filter(ProductInfo.id.in_(ids)).all()
        for product in products:
            product.sort_order = sort_order
        db.session.commit()
        return {'code': 200, 'message': f'成功修改{len(products)}个商品的排序'}, 200
    except Exception:
        db.session.rollback()
        return {'code': 500, 'message': '批量修改排序失败，请稍后重试'}, 500


@bp.route('/batch-disable', methods=['POST'])
@jwt_required()
def batch_disable():
    """批量禁用。"""
    from models.product.info import ProductInfo

    try:
        data = request.get_json()
        ids = data.get('ids', [])
        if not ids:
            return {'code': 400, 'message': '请选择要操作的商品'}, 400
        products = ProductInfo.query.filter(ProductInfo.id.in_(ids)).all()
        for product in products:
            product.status = 0
        db.session.commit()
        return {'code': 200, 'message': f'成功禁用{len(products)}个商品'}, 200
    except Exception:
        db.session.rollback()
        return {'code': 500, 'message': '批量禁用失败，请稍后重试'}, 500


@bp.route('/batch-enable', methods=['POST'])
@jwt_required()
def batch_enable():
    """批量启用。"""
    from models.product.info import ProductInfo

    try:
        data = request.get_json()
        ids = data.get('ids', [])
        if not ids:
            return {'code': 400, 'message': '请选择要操作的商品'}, 400
        products = ProductInfo.query.filter(ProductInfo.id.in_(ids)).all()
        for product in products:
            product.status = 1
        db.session.commit()
        return {'code': 200, 'message': f'成功启用{len(products)}个商品'}, 200
    except Exception:
        db.session.rollback()
        return {'code': 500, 'message': '批量启用失败，请稍后重试'}, 500


@bp.route('/batch-delete', methods=['POST'])
@jwt_required()
def batch_delete_products():
    """批量删除商品（硬删除，前置业务记录校验）。"""
    from models.product.info import ProductInfo

    try:
        data = request.get_json()
        ids = data.get('ids', [])
        if not ids:
            return {'code': 400, 'message': '请选择要删除的商品'}, 400
        has_record_ids = check_business_record(ids)
        if has_record_ids:
            record_products = ProductInfo.query.filter(
                ProductInfo.id.in_(has_record_ids)
            ).with_entities(ProductInfo.product_name).all()
            names = [p[0] for p in record_products[:3]]
            return {
                'code': 400,
                'message': '以下商品已存在业务记录，不允许删除：'
                           f'{"、".join(names)}{"等" if len(has_record_ids) > 3 else ""}',
            }, 400
        products = ProductInfo.query.filter(ProductInfo.id.in_(ids)).all()
        count = len(products)
        for product in products:
            db.session.delete(product)
        db.session.commit()
        return {'code': 200, 'message': f'成功删除{count}个商品'}, 200
    except Exception:
        db.session.rollback()
        return {'code': 500, 'message': '批量删除失败，请稍后重试'}, 500
