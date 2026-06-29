"""对账管理蓝图（客户/供应商/账户 3 类对账单，每类含单条 + 列表 2 个端点）。

迁移自 source-code/app.py 中以下区段的原始路由代码：
- /api/reconciliation/customer, /customers     16804, 16917
- /api/reconciliation/supplier, /suppliers     16986, 17099
- /api/reconciliation/account, /accounts       17168, 17277

业务规则：
- 客户对账：按客户聚合销售单/应收/收款，计算期初/本期销售/本期回款/期末余额
- 供应商对账：按供应商聚合采购单/应付/付款，同样 4 项指标
- 账户对账：按账户聚合流水/余额变动，含期初/本期收/本期支/期末

跨子域依赖：
- BaseCustomer / BaseSupplier           (models.customer / models.supplier)
- SalesOrder / SalesReceipt / SalesReturn  (models.sales.*)
- PurchaseOrder / PurchaseReturn         (models.purchase.*)
- FinanceAccount / FinanceRecord / FinanceReceivable / FinancePayable  (models.finance.account)
- SysUser                               (models.system)

直接 import 当前蓝图用得到的本地 helper，其他跨子域模型按"函数内懒加载"惯例。
"""
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from extensions import db
from app.utils import to_dict
from app.security import get_current_user_id

logger = logging.getLogger(__name__)

bp = Blueprint('reconciliation', __name__)


# 关联类型文字映射（与原 app.py 16781 行 RELATED_TYPE_MAP 行为一致；独立副本避免对未迁移的常量产生依赖）
RELATED_TYPE_MAP = {
    'sale': '销售单',
    'purchase': '采购单',
    'work_order': '工单',
    'return_sale': '销售退货',
    'return_purchase': '采购退货',
    'receivable': '应收收款',
    'payable': '应付付款',
    'transfer': '转账',
    'adjust': '调整',
    'salary': '工资发放',
    'expense': '费用'
}

# 状态文字映射（与原 app.py 16796 行 STATUS_MAP 行为一致）
STATUS_MAP = {
    0: '待处理',
    1: '部分处理',
    2: '已结清',
    3: '已取消'
}


@bp.route('/api/reconciliation/customer', methods=['GET'])
@jwt_required()
def get_customer_reconciliation():
    """客户对账单"""
    from models.customer import BaseCustomer
    from models.finance.account import FinanceReceivable, FinanceRecord

    try:
        customer_id = request.args.get('customer_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not customer_id:
            return jsonify({'code': 400, 'message': '客户ID不能为空'}), 400

        # 获取客户信息
        customer = BaseCustomer.query.get(customer_id)
        if not customer:
            return jsonify({'code': 404, 'message': '客户不存在'}), 404

        customer_info = {
            'id': customer.id,
            'name': customer.customer_name,
            'contact': customer.contact_name,
            'phone': customer.phone
        }

        # 构建应收账款查询
        receivable_query = FinanceReceivable.query.filter(
            FinanceReceivable.customer_id == customer_id
        )

        if start_date:
            receivable_query = receivable_query.filter(FinanceReceivable.created_at >= start_date)
        if end_date:
            receivable_query = receivable_query.filter(FinanceReceivable.created_at <= end_date + ' 23:59:59')

        receivables = receivable_query.order_by(FinanceReceivable.created_at.desc()).all()

        # 计算汇总数据
        total_receivable = sum(float(r.total_amount or 0) for r in receivables)
        total_received = sum(float(r.received_amount or 0) for r in receivables)
        total_remaining = sum(float(r.remaining_amount or 0) for r in receivables)
        receivable_count = len(receivables)
        received_count = len([r for r in receivables if r.status == 2])

        summary = {
            'total_receivable': total_receivable,
            'total_received': total_received,
            'total_remaining': total_remaining,
            'receivable_count': receivable_count,
            'received_count': received_count
        }

        # 构建明细列表
        details = []
        for r in receivables:
            details.append({
                'receivable_no': r.receivable_no,
                'related_no': r.related_no,
                'related_type': r.related_type,
                'related_type_text': RELATED_TYPE_MAP.get(r.related_type, r.related_type),
                'total_amount': float(r.total_amount or 0),
                'received_amount': float(r.received_amount or 0),
                'remaining_amount': float(r.remaining_amount or 0),
                'status': r.status,
                'status_text': STATUS_MAP.get(r.status, '未知'),
                'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else ''
            })

        # 获取相关收款流水
        record_query = FinanceRecord.query.filter(
            FinanceRecord.related_type == 'receivable'
        )

        # 获取该客户的所有应收单号
        receivable_nos = [r.receivable_no for r in receivables]
        if receivable_nos:
            record_query = record_query.filter(FinanceRecord.related_no.in_(receivable_nos))
        else:
            record_query = record_query.filter(FinanceRecord.related_no == '')

        if start_date:
            record_query = record_query.filter(FinanceRecord.created_at >= start_date)
        if end_date:
            record_query = record_query.filter(FinanceRecord.created_at <= end_date + ' 23:59:59')

        records_data = record_query.order_by(FinanceRecord.created_at.desc()).all()

        records = []
        for r in records_data:
            records.append({
                'record_no': r.id,
                'amount': float(r.amount or 0),
                'account_name': r.account_name,
                'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else ''
            })

        return jsonify({
            'code': 200,
            'data': {
                'customer_info': customer_info,
                'period': {
                    'start_date': start_date or '',
                    'end_date': end_date or ''
                },
                'summary': summary,
                'details': details,
                'records': records
            }
        })
    except Exception as e:
        logger.error(f'获取客户对账单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取客户对账单失败: {str(e)}'}), 500


@bp.route('/api/reconciliation/customers', methods=['GET'])
@jwt_required()
def get_customers_reconciliation():
    """客户对账单列表（多客户汇总）"""
    from models.customer import BaseCustomer
    from models.finance.account import FinanceReceivable

    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        keyword = request.args.get('keyword', '')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        # 构建客户查询
        customer_query = BaseCustomer.query
        if keyword:
            customer_query = customer_query.filter(
                db.or_(
                    BaseCustomer.customer_name.like(f'%{keyword}%'),
                    BaseCustomer.contact_name.like(f'%{keyword}%'),
                    BaseCustomer.phone.like(f'%{keyword}%')
                )
            )

        total_count = customer_query.count()
        customers = customer_query.offset((page - 1) * page_size).limit(page_size).all()

        # 构建结果列表
        result = []
        for customer in customers:
            # 查询该客户的应收账款
            receivable_query = FinanceReceivable.query.filter(
                FinanceReceivable.customer_id == customer.id
            )

            if start_date:
                receivable_query = receivable_query.filter(FinanceReceivable.created_at >= start_date)
            if end_date:
                receivable_query = receivable_query.filter(FinanceReceivable.created_at <= end_date + ' 23:59:59')

            receivables = receivable_query.all()

            total_receivable = sum(float(r.total_amount or 0) for r in receivables)
            total_received = sum(float(r.received_amount or 0) for r in receivables)
            total_remaining = sum(float(r.remaining_amount or 0) for r in receivables)

            result.append({
                'customer_id': customer.id,
                'customer_name': customer.customer_name,
                'contact': customer.contact_name,
                'phone': customer.phone,
                'total_receivable': total_receivable,
                'total_received': total_received,
                'total_remaining': total_remaining,
                'receivable_count': len(receivables)
            })

        return jsonify({
            'code': 200,
            'data': {
                'items': result,
                'total': total_count,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        logger.error(f'获取客户对账单列表失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取客户对账单列表失败: {str(e)}'}), 500


@bp.route('/api/reconciliation/supplier', methods=['GET'])
@jwt_required()
def get_supplier_reconciliation():
    """供应商对账单"""
    from models.supplier import BaseSupplier
    from models.finance.account import FinancePayable, FinanceRecord

    try:
        supplier_id = request.args.get('supplier_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not supplier_id:
            return jsonify({'code': 400, 'message': '供应商ID不能为空'}), 400

        # 获取供应商信息
        supplier = BaseSupplier.query.get(supplier_id)
        if not supplier:
            return jsonify({'code': 404, 'message': '供应商不存在'}), 404

        supplier_info = {
            'id': supplier.id,
            'name': supplier.supplier_name,
            'contact': supplier.contact_name,
            'phone': supplier.phone
        }

        # 构建应付账款查询
        payable_query = FinancePayable.query.filter(
            FinancePayable.supplier_id == supplier_id
        )

        if start_date:
            payable_query = payable_query.filter(FinancePayable.created_at >= start_date)
        if end_date:
            payable_query = payable_query.filter(FinancePayable.created_at <= end_date + ' 23:59:59')

        payables = payable_query.order_by(FinancePayable.created_at.desc()).all()

        # 计算汇总数据
        total_payable = sum(float(p.total_amount or 0) for p in payables)
        total_paid = sum(float(p.paid_amount or 0) for p in payables)
        total_remaining = sum(float(p.remaining_amount or 0) for p in payables)
        payable_count = len(payables)
        paid_count = len([p for p in payables if p.status == 2])

        summary = {
            'total_payable': total_payable,
            'total_paid': total_paid,
            'total_remaining': total_remaining,
            'payable_count': payable_count,
            'paid_count': paid_count
        }

        # 构建明细列表
        details = []
        for p in payables:
            details.append({
                'payable_no': p.payable_no,
                'related_no': p.related_no,
                'related_type': p.related_type,
                'related_type_text': RELATED_TYPE_MAP.get(p.related_type, p.related_type),
                'total_amount': float(p.total_amount or 0),
                'paid_amount': float(p.paid_amount or 0),
                'remaining_amount': float(p.remaining_amount or 0),
                'status': p.status,
                'status_text': STATUS_MAP.get(p.status, '未知'),
                'created_at': p.created_at.strftime('%Y-%m-%d %H:%M:%S') if p.created_at else ''
            })

        # 获取相关付款流水
        record_query = FinanceRecord.query.filter(
            FinanceRecord.related_type == 'payable'
        )

        # 获取该供应商的所有应付单号
        payable_nos = [p.payable_no for p in payables]
        if payable_nos:
            record_query = record_query.filter(FinanceRecord.related_no.in_(payable_nos))
        else:
            record_query = record_query.filter(FinanceRecord.related_no == '')

        if start_date:
            record_query = record_query.filter(FinanceRecord.created_at >= start_date)
        if end_date:
            record_query = record_query.filter(FinanceRecord.created_at <= end_date + ' 23:59:59')

        records_data = record_query.order_by(FinanceRecord.created_at.desc()).all()

        records = []
        for r in records_data:
            records.append({
                'record_no': r.id,
                'amount': float(r.amount or 0),
                'account_name': r.account_name,
                'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else ''
            })

        return jsonify({
            'code': 200,
            'data': {
                'supplier_info': supplier_info,
                'period': {
                    'start_date': start_date or '',
                    'end_date': end_date or ''
                },
                'summary': summary,
                'details': details,
                'records': records
            }
        })
    except Exception as e:
        logger.error(f'获取供应商对账单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取供应商对账单失败: {str(e)}'}), 500


@bp.route('/api/reconciliation/suppliers', methods=['GET'])
@jwt_required()
def get_suppliers_reconciliation():
    """供应商对账单列表（多供应商汇总）"""
    from models.supplier import BaseSupplier
    from models.finance.account import FinancePayable

    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        keyword = request.args.get('keyword', '')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        # 构建供应商查询
        supplier_query = BaseSupplier.query
        if keyword:
            supplier_query = supplier_query.filter(
                db.or_(
                    BaseSupplier.supplier_name.like(f'%{keyword}%'),
                    BaseSupplier.contact_name.like(f'%{keyword}%'),
                    BaseSupplier.phone.like(f'%{keyword}%')
                )
            )

        total_count = supplier_query.count()
        suppliers = supplier_query.offset((page - 1) * page_size).limit(page_size).all()

        # 构建结果列表
        result = []
        for supplier in suppliers:
            # 查询该供应商的应付账款
            payable_query = FinancePayable.query.filter(
                FinancePayable.supplier_id == supplier.id
            )

            if start_date:
                payable_query = payable_query.filter(FinancePayable.created_at >= start_date)
            if end_date:
                payable_query = payable_query.filter(FinancePayable.created_at <= end_date + ' 23:59:59')

            payables = payable_query.all()

            total_payable = sum(float(p.total_amount or 0) for p in payables)
            total_paid = sum(float(p.paid_amount or 0) for p in payables)
            total_remaining = sum(float(p.remaining_amount or 0) for p in payables)

            result.append({
                'supplier_id': supplier.id,
                'supplier_name': supplier.supplier_name,
                'contact': supplier.contact_name,
                'phone': supplier.phone,
                'total_payable': total_payable,
                'total_paid': total_paid,
                'total_remaining': total_remaining,
                'payable_count': len(payables)
            })

        return jsonify({
            'code': 200,
            'data': {
                'items': result,
                'total': total_count,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        logger.error(f'获取供应商对账单列表失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取供应商对账单列表失败: {str(e)}'}), 500


@bp.route('/api/reconciliation/account', methods=['GET'])
@jwt_required()
def get_account_reconciliation():
    """账户对账单"""
    from models.finance.account import FinanceAccount, FinanceRecord

    try:
        account_id = request.args.get('account_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not account_id:
            return jsonify({'code': 400, 'message': '账户ID不能为空'}), 400

        # 获取账户信息
        account = FinanceAccount.query.get(account_id)
        if not account:
            return jsonify({'code': 404, 'message': '账户不存在'}), 404

        account_info = {
            'id': account.id,
            'account_name': account.account_name,
            'account_type': account.account_type,
            'account_no': account.account_no
        }

        # 计算期初余额
        if start_date:
            # 获取start_date前的最后一条流水
            last_record_before = FinanceRecord.query.filter(
                FinanceRecord.account_id == account_id,
                FinanceRecord.created_at < start_date
            ).order_by(FinanceRecord.created_at.desc()).first()

            if last_record_before:
                opening_balance = float(last_record_before.balance_after or 0)
            else:
                opening_balance = float(account.balance or 0)
        else:
            opening_balance = float(account.balance or 0)

        # 计算期末余额
        if end_date:
            # 获取end_date当天的最后一条流水
            last_record_in_period = FinanceRecord.query.filter(
                FinanceRecord.account_id == account_id,
                FinanceRecord.created_at <= end_date + ' 23:59:59'
            ).order_by(FinanceRecord.created_at.desc()).first()

            if last_record_in_period:
                closing_balance = float(last_record_in_period.balance_after or 0)
            else:
                closing_balance = opening_balance
        else:
            closing_balance = float(account.balance or 0)

        # 构建流水查询
        record_query = FinanceRecord.query.filter(
            FinanceRecord.account_id == account_id
        )

        if start_date:
            record_query = record_query.filter(FinanceRecord.created_at >= start_date)
        if end_date:
            record_query = record_query.filter(FinanceRecord.created_at <= end_date + ' 23:59:59')

        records_data = record_query.order_by(FinanceRecord.created_at.desc()).all()

        # 计算本期收入和支出
        total_income = sum(float(r.amount or 0) for r in records_data if r.record_type == 1)
        total_expense = sum(float(r.amount or 0) for r in records_data if r.record_type == 2)
        net_amount = total_income - total_expense

        # 构建流水列表
        records = []
        for r in records_data:
            record_type_text = '收入' if r.record_type == 1 else '支出'
            records.append({
                'record_type': r.record_type,
                'record_type_text': record_type_text,
                'amount': float(r.amount or 0),
                'balance_before': float(r.balance_before or 0),
                'balance_after': float(r.balance_after or 0),
                'related_type': r.related_type,
                'related_type_text': RELATED_TYPE_MAP.get(r.related_type, r.related_type or ''),
                'related_no': r.related_no,
                'remark': getattr(r, 'remark', '') or '',
                'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else ''
            })

        return jsonify({
            'code': 200,
            'data': {
                'account_info': account_info,
                'period': {
                    'start_date': start_date or '',
                    'end_date': end_date or ''
                },
                'opening_balance': opening_balance,
                'closing_balance': closing_balance,
                'total_income': total_income,
                'total_expense': total_expense,
                'net_amount': net_amount,
                'records': records
            }
        })
    except Exception as e:
        logger.error(f'获取账户对账单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取账户对账单失败: {str(e)}'}), 500


@bp.route('/api/reconciliation/accounts', methods=['GET'])
@jwt_required()
def get_accounts_reconciliation():
    """账户对账单列表（多账户汇总）"""
    from models.finance.account import FinanceAccount, FinanceRecord

    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        # 查询所有账户
        account_query = FinanceAccount.query

        total_count = account_query.count()
        accounts = account_query.offset((page - 1) * page_size).limit(page_size).all()

        # 构建结果列表
        result = []
        for account in accounts:
            # 计算期初余额
            if start_date:
                last_record_before = FinanceRecord.query.filter(
                    FinanceRecord.account_id == account.id,
                    FinanceRecord.created_at < start_date
                ).order_by(FinanceRecord.created_at.desc()).first()

                if last_record_before:
                    opening_balance = float(last_record_before.balance_after or 0)
                else:
                    opening_balance = float(account.balance or 0)
            else:
                opening_balance = float(account.balance or 0)

            # 计算期末余额
            if end_date:
                last_record_in_period = FinanceRecord.query.filter(
                    FinanceRecord.account_id == account.id,
                    FinanceRecord.created_at <= end_date + ' 23:59:59'
                ).order_by(FinanceRecord.created_at.desc()).first()

                if last_record_in_period:
                    closing_balance = float(last_record_in_period.balance_after or 0)
                else:
                    closing_balance = opening_balance
            else:
                closing_balance = float(account.balance or 0)

            # 查询本期流水
            record_query = FinanceRecord.query.filter(
                FinanceRecord.account_id == account.id
            )

            if start_date:
                record_query = record_query.filter(FinanceRecord.created_at >= start_date)
            if end_date:
                record_query = record_query.filter(FinanceRecord.created_at <= end_date + ' 23:59:59')

            records_data = record_query.all()

            total_income = sum(float(r.amount or 0) for r in records_data if r.record_type == 1)
            total_expense = sum(float(r.amount or 0) for r in records_data if r.record_type == 2)
            net_amount = total_income - total_expense

            result.append({
                'account_id': account.id,
                'account_name': account.account_name,
                'account_type': account.account_type,
                'account_no': account.account_no,
                'opening_balance': opening_balance,
                'closing_balance': closing_balance,
                'total_income': total_income,
                'total_expense': total_expense,
                'net_amount': net_amount,
                'record_count': len(records_data)
            })

        return jsonify({
            'code': 200,
            'data': {
                'list': result,
                'total': total_count,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        logger.error(f'获取账户对账单列表失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取账户对账单列表失败: {str(e)}'}), 500
