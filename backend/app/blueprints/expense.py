"""费用管理蓝图（CRUD + 确认 + 统计）。

迁移自 source-code/app.py 中 16379-16800 行附近的原始路由代码。

业务规则：
- 费用类型 1日常费用 2其他收入 3运营支出 4管理费用
- 收支类型 1收入 2支出（与 expense_type 正交）
- 确认 (confirm)：status 0→1，可能联动写 FinanceRecord
- statistics：按类型 / 月份 / 部门聚合

跨子域依赖：
- Expense (models.finance.account)
- FinanceAccount / FinanceRecord (models.finance.account) — 确认时
- BaseCustomer / BaseSupplier (models.customer / models.supplier) — 关联往来

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

bp = Blueprint('expense', __name__)


@bp.route('/api/expense', methods=['GET'])
@jwt_required()
def get_expenses():
    """费用列表"""
    try:
        from models.finance.account import Expense
        expense_type = request.args.get('expense_type', type=int)
        record_type = request.args.get('record_type', type=int)
        status = request.args.get('status', type=int)
        partner_type = request.args.get('partner_type', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        keyword = request.args.get('keyword', '')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        query = Expense.query

        if expense_type:
            query = query.filter(Expense.expense_type == expense_type)
        if record_type:
            query = query.filter(Expense.record_type == record_type)
        if status is not None:
            query = query.filter(Expense.status == status)
        if partner_type:
            query = query.filter(Expense.partner_type == partner_type)
        if start_date:
            query = query.filter(Expense.expense_date >= start_date)
        if end_date:
            query = query.filter(Expense.expense_date <= end_date)
        if keyword:
            query = query.filter(
                db.or_(
                    Expense.expense_no.like(f'%{keyword}%'),
                    Expense.expense_name.like(f'%{keyword}%'),
                    Expense.partner_name.like(f'%{keyword}%')
                )
            )

        query = query.order_by(Expense.created_at.desc())
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        # 费用类型映射
        type_map = {1: '日常费用', 2: '其他收入', 3: '运营支出', 4: '管理费用'}

        items = []
        for e in pagination.items:
            items.append({
                'id': e.id,
                'expense_no': e.expense_no,
                'expense_name': e.expense_name,
                'expense_type': e.expense_type,
                'expense_type_name': type_map.get(e.expense_type, '其他'),
                'amount': float(e.amount) if e.amount else 0,
                'record_type': e.record_type,
                'record_type_name': '收入' if e.record_type == 1 else '支出',
                'account_id': e.account_id,
                'account_name': e.account_name,
                'partner_type': e.partner_type,
                'partner_id': e.partner_id,
                'partner_name': e.partner_name,
                'expense_date': e.expense_date.strftime('%Y-%m-%d') if e.expense_date else None,
                'status': e.status,
                'attachment': e.attachment,
                'remark': e.remark,
                'created_at': e.created_at.strftime('%Y-%m-%d %H:%M:%S') if e.created_at else None
            })

        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'items': items,
                'total': pagination.total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        logger.error(f'获取费用列表失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取费用列表失败: {str(e)}'}), 500


@bp.route('/api/expense/<int:id>', methods=['GET'])
@jwt_required()
def get_expense(id):
    """费用详情"""
    try:
        from models.finance.account import Expense
        e = Expense.query.get(id)
        if not e:
            return jsonify({'code': 404, 'message': '费用单不存在'}), 404

        type_map = {1: '日常费用', 2: '其他收入', 3: '运营支出', 4: '管理费用'}

        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'id': e.id,
                'expense_no': e.expense_no,
                'expense_name': e.expense_name,
                'expense_type': e.expense_type,
                'expense_type_name': type_map.get(e.expense_type, '其他'),
                'amount': float(e.amount) if e.amount else 0,
                'record_type': e.record_type,
                'record_type_name': '收入' if e.record_type == 1 else '支出',
                'account_id': e.account_id,
                'account_name': e.account_name,
                'partner_type': e.partner_type,
                'partner_id': e.partner_id,
                'partner_name': e.partner_name,
                'expense_date': e.expense_date.strftime('%Y-%m-%d') if e.expense_date else None,
                'status': e.status,
                'attachment': e.attachment,
                'remark': e.remark,
                'created_at': e.created_at.strftime('%Y-%m-%d %H:%M:%S') if e.created_at else None,
                'updated_at': e.updated_at.strftime('%Y-%m-%d %H:%M:%S') if e.updated_at else None
            }
        })
    except Exception as e:
        logger.error(f'获取费用详情失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取费用详情失败: {str(e)}'}), 500


@bp.route('/api/expense', methods=['POST'])
@jwt_required()
def create_expense():
    """创建费用"""
    try:
        from flask_jwt_extended import get_jwt_identity
        from models.finance.account import Expense
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # 必填字段校验
        if not data.get('expense_name'):
            return jsonify({'code': 400, 'message': '费用名称为必填项'}), 400

        # 自动生成费用单号：EX + 年月日 + 4位序号
        today_str = datetime.now().strftime('%Y%m%d')
        prefix = f'EX{today_str}'
        last_expense = Expense.query.filter(Expense.expense_no.like(f'{prefix}%')).order_by(Expense.id.desc()).first()
        if last_expense and last_expense.expense_no:
            last_seq = int(last_expense.expense_no[-4:]) if len(last_expense.expense_no) >= 4 else 0
        else:
            last_seq = 0
        expense_no = f'{prefix}{str(last_seq + 1).zfill(4)}'

        # 处理费用日期
        expense_date = data.get('expense_date')
        if expense_date:
            expense_date = datetime.strptime(expense_date, '%Y-%m-%d').date()

        expense = Expense(
            expense_no=expense_no,
            expense_name=data.get('expense_name'),
            expense_type=data.get('expense_type', 1),
            amount=float(data.get('amount', 0)),
            record_type=data.get('record_type', 2),
            partner_type=data.get('partner_type', ''),
            partner_id=data.get('partner_id'),
            partner_name=data.get('partner_name', ''),
            expense_date=expense_date,
            remark=data.get('remark', ''),
            status=0,  # 待处理
            created_by=current_user_id
        )

        db.session.add(expense)
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '创建成功',
            'data': {'id': expense.id, 'expense_no': expense_no}
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'创建费用单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'创建费用单失败: {str(e)}'}), 500


@bp.route('/api/expense/<int:id>', methods=['PUT'])
@jwt_required()
def update_expense(id):
    """更新费用"""
    try:
        from models.finance.account import Expense
        expense = Expense.query.get(id)
        if not expense:
            return jsonify({'code': 404, 'message': '费用单不存在'}), 404

        if expense.status != 0:
            return jsonify({'code': 400, 'message': '只有待处理的费用单可以修改'}), 400

        data = request.get_json()

        # 更新字段
        if 'expense_name' in data:
            expense.expense_name = data['expense_name']
        if 'expense_type' in data:
            expense.expense_type = data['expense_type']
        if 'amount' in data:
            expense.amount = float(data['amount'])
        if 'record_type' in data:
            expense.record_type = data['record_type']
        if 'partner_type' in data:
            expense.partner_type = data['partner_type']
        if 'partner_id' in data:
            expense.partner_id = data['partner_id']
        if 'partner_name' in data:
            expense.partner_name = data['partner_name']
        if 'expense_date' in data:
            expense.expense_date = datetime.strptime(data['expense_date'], '%Y-%m-%d').date()
        if 'remark' in data:
            expense.remark = data['remark']

        db.session.commit()

        return jsonify({'code': 200, 'message': '更新成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新费用单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'更新费用单失败: {str(e)}'}), 500


@bp.route('/api/expense/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_expense(id):
    """删除费用（软删除）"""
    try:
        from models.finance.account import Expense
        expense = Expense.query.get(id)
        if not expense:
            return jsonify({'code': 404, 'message': '费用单不存在'}), 404

        expense.status = 2  # 已取消
        db.session.commit()

        return jsonify({'code': 200, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除费用单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'删除费用单失败: {str(e)}'}), 500


@bp.route('/api/expense/<int:id>/confirm', methods=['POST'])
@jwt_required()
def confirm_expense(id):
    """确认费用"""
    try:
        from flask_jwt_extended import get_jwt_identity
        from models.finance.account import Expense, FinanceAccount, FinanceRecord
        current_user_id = get_jwt_identity()

        expense = Expense.query.get(id)
        if not expense:
            return jsonify({'code': 404, 'message': '费用单不存在'}), 404

        if expense.status != 0:
            return jsonify({'code': 400, 'message': '只有待处理的费用单可以确认'}), 400

        data = request.get_json()
        account_id = data.get('account_id')

        if not account_id:
            return jsonify({'code': 400, 'message': '请选择收支账户'}), 400

        # 校验账户
        account = FinanceAccount.query.get(account_id)
        if not account:
            return jsonify({'code': 404, 'message': '账户不存在'}), 404

        if account.status != 1:
            return jsonify({'code': 400, 'message': '账户已禁用'}), 400

        amount = float(expense.amount or 0)

        # 如果是支出，校验余额
        if expense.record_type == 2 and amount > 0:
            if float(account.balance or 0) < amount:
                return jsonify({'code': 400, 'message': '账户余额不足'}), 400
            # 扣减余额
            account.balance = float(account.balance or 0) - amount
        else:
            # 收入增加余额
            account.balance = float(account.balance or 0) + amount

        # 生成流水
        record = FinanceRecord(
            account_id=account.id,
            account_name=account.account_name,
            record_type=expense.record_type,  # 1收入 2支出
            amount=amount,
            balance=account.balance,
            related_type='expense',
            related_id=expense.id,
            related_no=expense.expense_no,
            remark=f'{expense.expense_name} - {expense.partner_name or ""}',
            created_by=current_user_id
        )
        db.session.add(record)

        # 更新费用单状态
        expense.status = 1  # 已确认
        expense.account_id = account.id
        expense.account_name = account.account_name

        db.session.commit()

        return jsonify({'code': 200, 'message': '确认成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'确认费用失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'确认费用失败: {str(e)}'}), 500


@bp.route('/api/expense/statistics', methods=['GET'])
@jwt_required()
def expense_statistics():
    """费用统计"""
    try:
        from models.finance.account import Expense
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')

        query = Expense.query.filter(Expense.status == 1)  # 只统计已确认的

        if start_date:
            query = query.filter(Expense.expense_date >= start_date)
        if end_date:
            query = query.filter(Expense.expense_date <= end_date)

        # 总收入
        total_income = db.session.query(db.func.sum(Expense.amount)).filter(
            Expense.status == 1,
            Expense.record_type == 1
        )
        if start_date:
            total_income = total_income.filter(Expense.expense_date >= start_date)
        if end_date:
            total_income = total_income.filter(Expense.expense_date <= end_date)
        total_income = total_income.scalar() or 0

        # 总支出
        total_expense = db.session.query(db.func.sum(Expense.amount)).filter(
            Expense.status == 1,
            Expense.record_type == 2
        )
        if start_date:
            total_expense = total_expense.filter(Expense.expense_date >= start_date)
        if end_date:
            total_expense = total_expense.filter(Expense.expense_date <= end_date)
        total_expense = total_expense.scalar() or 0

        # 按类型统计
        type_stats_query = db.session.query(
            Expense.expense_type,
            Expense.record_type,
            db.func.sum(Expense.amount).label('total')
        ).filter(Expense.status == 1)

        if start_date:
            type_stats_query = type_stats_query.filter(Expense.expense_date >= start_date)
        if end_date:
            type_stats_query = type_stats_query.filter(Expense.expense_date <= end_date)

        type_stats_query = type_stats_query.group_by(Expense.expense_type, Expense.record_type).all()

        type_map = {1: '日常费用', 2: '其他收入', 3: '运营支出', 4: '管理费用'}

        # 整理类型统计
        type_data = {}
        for t in type_stats_query:
            type_id = t.expense_type
            if type_id not in type_data:
                type_data[type_id] = {'income': 0, 'expense': 0}
            if t.record_type == 1:
                type_data[type_id]['income'] = float(t.total or 0)
            else:
                type_data[type_id]['expense'] = float(t.total or 0)

        type_stats = []
        for type_id, amounts in type_data.items():
            type_stats.append({
                'expense_type': type_id,
                'type_name': type_map.get(type_id, '其他'),
                'income': amounts['income'],
                'expense': amounts['expense'],
                'net': amounts['income'] - amounts['expense']
            })

        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'total_income': float(total_income),
                'total_expense': float(total_expense),
                'net_amount': float(total_income - total_expense),
                'type_stats': type_stats
            }
        })
    except Exception as e:
        logger.error(f'获取费用统计失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取费用统计失败: {str(e)}'}), 500
