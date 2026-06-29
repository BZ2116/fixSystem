"""工资管理蓝图（CRUD + 发放 + 统计）。

迁移自 source-code/app.py 中 15975-16375 行附近的原始路由代码。

业务规则：
- 应发金额 = 基本 + 绩效 + 提成 + 补贴 - 扣款
- 实发金额 = 应发 - 个税
- 发放 (pay)：status 0→1，写 FinanceRecord（account_id 记录 + 实发金额）
- statistics：按月份/部门聚合

跨子域依赖：
- Salary (models.finance.account)
- SysUser (models.system)
- FinanceAccount / FinanceRecord (models.finance.account) — 发放时

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

bp = Blueprint('salary', __name__)


def _get_current_user_name():
    """获取当前登录用户姓名。迁移期兼容（app.py 174 行）。"""
    from flask_jwt_extended import get_jwt_identity
    from models.system import SysUser
    user_id = get_jwt_identity()
    user = SysUser.query.get(user_id)
    if user:
        return user.real_name or user.username
    return ''


@bp.route('/api/salary', methods=['GET'])
@jwt_required()
def get_salaries():
    """工资列表"""
    try:
        from models.finance.account import Salary
        user_id = request.args.get('user_id', type=int)
        department = request.args.get('department', '')
        salary_month = request.args.get('salary_month', '')
        status = request.args.get('status', type=int)
        keyword = request.args.get('keyword', '')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        query = Salary.query

        if user_id:
            query = query.filter(Salary.user_id == user_id)
        if department:
            query = query.filter(Salary.department == department)
        if salary_month:
            query = query.filter(Salary.salary_month == salary_month)
        if status is not None:
            query = query.filter(Salary.status == status)
        if keyword:
            query = query.filter(
                db.or_(
                    Salary.salary_no.like(f'%{keyword}%'),
                    Salary.user_name.like(f'%{keyword}%'),
                    Salary.position.like(f'%{keyword}%')
                )
            )

        query = query.order_by(Salary.created_at.desc())
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        items = []
        for s in pagination.items:
            items.append({
                'id': s.id,
                'salary_no': s.salary_no,
                'user_id': s.user_id,
                'user_name': s.user_name,
                'department': s.department,
                'position': s.position,
                'salary_month': s.salary_month,
                'base_salary': float(s.base_salary) if s.base_salary else 0,
                'performance_salary': float(s.performance_salary) if s.performance_salary else 0,
                'commission': float(s.commission) if s.commission else 0,
                'subsidy': float(s.subsidy) if s.subsidy else 0,
                'deduction': float(s.deduction) if s.deduction else 0,
                'should_pay': float(s.should_pay) if s.should_pay else 0,
                'tax': float(s.tax) if s.tax else 0,
                'actual_pay': float(s.actual_pay) if s.actual_pay else 0,
                'account_id': s.account_id,
                'account_name': s.account_name,
                'status': s.status,
                'remark': s.remark,
                'created_at': s.created_at.strftime('%Y-%m-%d %H:%M:%S') if s.created_at else None,
                'paid_at': s.paid_at.strftime('%Y-%m-%d %H:%M:%S') if s.paid_at else None
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
        logger.error(f'获取工资列表失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取工资列表失败: {str(e)}'}), 500


@bp.route('/api/salary/<int:id>', methods=['GET'])
@jwt_required()
def get_salary(id):
    """工资详情"""
    try:
        from models.finance.account import Salary
        s = Salary.query.get(id)
        if not s:
            return jsonify({'code': 404, 'message': '工资单不存在'}), 404

        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'id': s.id,
                'salary_no': s.salary_no,
                'user_id': s.user_id,
                'user_name': s.user_name,
                'department': s.department,
                'position': s.position,
                'salary_month': s.salary_month,
                'base_salary': float(s.base_salary) if s.base_salary else 0,
                'performance_salary': float(s.performance_salary) if s.performance_salary else 0,
                'commission': float(s.commission) if s.commission else 0,
                'subsidy': float(s.subsidy) if s.subsidy else 0,
                'deduction': float(s.deduction) if s.deduction else 0,
                'should_pay': float(s.should_pay) if s.should_pay else 0,
                'tax': float(s.tax) if s.tax else 0,
                'actual_pay': float(s.actual_pay) if s.actual_pay else 0,
                'account_id': s.account_id,
                'account_name': s.account_name,
                'status': s.status,
                'remark': s.remark,
                'created_at': s.created_at.strftime('%Y-%m-%d %H:%M:%S') if s.created_at else None,
                'updated_at': s.updated_at.strftime('%Y-%m-%d %H:%M:%S') if s.updated_at else None,
                'paid_at': s.paid_at.strftime('%Y-%m-%d %H:%M:%S') if s.paid_at else None
            }
        })
    except Exception as e:
        logger.error(f'获取工资详情失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取工资详情失败: {str(e)}'}), 500


@bp.route('/api/salary', methods=['POST'])
@jwt_required()
def create_salary():
    """创建工资单"""
    try:
        from flask_jwt_extended import get_jwt_identity
        from models.finance.account import Salary
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # 必填字段校验
        if not data.get('user_id') or not data.get('user_name') or not data.get('salary_month'):
            return jsonify({'code': 400, 'message': '员工ID、员工姓名和工资月份为必填项'}), 400

        # 自动生成工资单号：SA + 年月 + 4位序号
        month_str = data.get('salary_month', datetime.now().strftime('%Y%m'))
        prefix = f'SA{month_str.replace("-", "")}'
        last_salary = Salary.query.filter(Salary.salary_no.like(f'{prefix}%')).order_by(Salary.id.desc()).first()
        if last_salary and last_salary.salary_no:
            last_seq = int(last_salary.salary_no[-4:]) if len(last_salary.salary_no) >= 4 else 0
        else:
            last_seq = 0
        salary_no = f'{prefix}{str(last_seq + 1).zfill(4)}'

        # 计算应发金额
        base_salary = float(data.get('base_salary', 0))
        performance_salary = float(data.get('performance_salary', 0))
        commission = float(data.get('commission', 0))
        subsidy = float(data.get('subsidy', 0))
        deduction = float(data.get('deduction', 0))
        should_pay = base_salary + performance_salary + commission + subsidy - deduction

        salary = Salary(
            salary_no=salary_no,
            user_id=data.get('user_id'),
            user_name=data.get('user_name'),
            department=data.get('department', ''),
            position=data.get('position', ''),
            salary_month=data.get('salary_month'),
            base_salary=base_salary,
            performance_salary=performance_salary,
            commission=commission,
            subsidy=subsidy,
            deduction=deduction,
            should_pay=should_pay,
            tax=float(data.get('tax', 0)),
            actual_pay=float(data.get('actual_pay', 0)),
            remark=data.get('remark', ''),
            status=0,  # 待发放
            created_by=current_user_id
        )

        db.session.add(salary)
        db.session.commit()

        return jsonify({
            'code': 200,
            'message': '创建成功',
            'data': {'id': salary.id, 'salary_no': salary_no}
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'创建工资单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'创建工资单失败: {str(e)}'}), 500


@bp.route('/api/salary/<int:id>', methods=['PUT'])
@jwt_required()
def update_salary(id):
    """更新工资单"""
    try:
        from models.finance.account import Salary
        salary = Salary.query.get(id)
        if not salary:
            return jsonify({'code': 404, 'message': '工资单不存在'}), 404

        if salary.status != 0:
            return jsonify({'code': 400, 'message': '只有待发放的工资单可以修改'}), 400

        data = request.get_json()

        # 更新字段
        if 'user_id' in data:
            salary.user_id = data['user_id']
        if 'user_name' in data:
            salary.user_name = data['user_name']
        if 'department' in data:
            salary.department = data['department']
        if 'position' in data:
            salary.position = data['position']
        if 'salary_month' in data:
            salary.salary_month = data['salary_month']
        if 'base_salary' in data:
            salary.base_salary = float(data['base_salary'])
        if 'performance_salary' in data:
            salary.performance_salary = float(data['performance_salary'])
        if 'commission' in data:
            salary.commission = float(data['commission'])
        if 'subsidy' in data:
            salary.subsidy = float(data['subsidy'])
        if 'deduction' in data:
            salary.deduction = float(data['deduction'])
        if 'tax' in data:
            salary.tax = float(data['tax'])
        if 'actual_pay' in data:
            salary.actual_pay = float(data['actual_pay'])
        if 'remark' in data:
            salary.remark = data['remark']

        # 重新计算应发金额
        salary.should_pay = float(salary.base_salary or 0) + float(salary.performance_salary or 0) + \
                           float(salary.commission or 0) + float(salary.subsidy or 0) - float(salary.deduction or 0)

        db.session.commit()

        return jsonify({'code': 200, 'message': '更新成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新工资单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'更新工资单失败: {str(e)}'}), 500


@bp.route('/api/salary/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_salary(id):
    """删除工资单（软删除）"""
    try:
        from models.finance.account import Salary
        salary = Salary.query.get(id)
        if not salary:
            return jsonify({'code': 404, 'message': '工资单不存在'}), 404

        salary.status = 2  # 已取消
        db.session.commit()

        return jsonify({'code': 200, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除工资单失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'删除工资单失败: {str(e)}'}), 500


@bp.route('/api/salary/<int:id>/pay', methods=['POST'])
@jwt_required()
def pay_salary(id):
    """发放工资"""
    try:
        from flask_jwt_extended import get_jwt_identity
        from models.finance.account import Salary, FinanceAccount, FinanceRecord
        current_user_id = get_jwt_identity()
        current_user_name = _get_current_user_name()

        salary = Salary.query.get(id)
        if not salary:
            return jsonify({'code': 404, 'message': '工资单不存在'}), 404

        if salary.status != 0:
            return jsonify({'code': 400, 'message': '只有待发放的工资单可以发放'}), 400

        data = request.get_json()
        account_id = data.get('account_id')

        if not account_id:
            return jsonify({'code': 400, 'message': '请选择发放账户'}), 400

        # 校验账户
        account = FinanceAccount.query.get(account_id)
        if not account:
            return jsonify({'code': 404, 'message': '账户不存在'}), 404

        if account.status != 1:
            return jsonify({'code': 400, 'message': '账户已禁用'}), 400

        # 校验余额
        actual_pay = float(salary.actual_pay or 0)
        if actual_pay > 0 and float(account.balance or 0) < actual_pay:
            return jsonify({'code': 400, 'message': '账户余额不足'}), 400

        # 扣减账户余额
        account.balance = float(account.balance or 0) - actual_pay

        # 生成支出流水
        record = FinanceRecord(
            account_id=account.id,
            account_name=account.account_name,
            record_type=2,  # 支出
            amount=actual_pay,
            balance=account.balance,
            related_type='salary',
            related_id=salary.id,
            related_no=salary.salary_no,
            remark=f'工资发放 - {salary.user_name}({salary.salary_month})',
            created_by=current_user_id
        )
        db.session.add(record)

        # 更新工资单状态
        salary.status = 1  # 已发放
        salary.account_id = account.id
        salary.account_name = account.account_name
        salary.paid_at = datetime.now()

        db.session.commit()

        return jsonify({'code': 200, 'message': '发放成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'发放工资失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'发放工资失败: {str(e)}'}), 500


@bp.route('/api/salary/statistics', methods=['GET'])
@jwt_required()
def salary_statistics():
    """工资统计"""
    try:
        from models.finance.account import Salary
        salary_month = request.args.get('salary_month', datetime.now().strftime('%Y-%m'))

        # 基础统计
        total_should_pay = db.session.query(db.func.sum(Salary.should_pay)).filter(
            Salary.salary_month == salary_month,
            Salary.status != 2
        ).scalar() or 0

        total_actual_pay = db.session.query(db.func.sum(Salary.actual_pay)).filter(
            Salary.salary_month == salary_month,
            Salary.status != 2
        ).scalar() or 0

        total_tax = db.session.query(db.func.sum(Salary.tax)).filter(
            Salary.salary_month == salary_month,
            Salary.status != 2
        ).scalar() or 0

        total_count = Salary.query.filter(
            Salary.salary_month == salary_month,
            Salary.status != 2
        ).count()

        pending_count = Salary.query.filter(
            Salary.salary_month == salary_month,
            Salary.status == 0
        ).count()

        paid_count = Salary.query.filter(
            Salary.salary_month == salary_month,
            Salary.status == 1
        ).count()

        # 部门统计
        dept_stats = db.session.query(
            Salary.department,
            db.func.count(Salary.id).label('count'),
            db.func.sum(Salary.should_pay).label('should_pay'),
            db.func.sum(Salary.actual_pay).label('actual_pay')
        ).filter(
            Salary.salary_month == salary_month,
            Salary.status != 2
        ).group_by(Salary.department).all()

        department_stats = []
        for dept in dept_stats:
            department_stats.append({
                'department': dept.department or '未分配',
                'count': dept.count,
                'should_pay': float(dept.should_pay or 0),
                'actual_pay': float(dept.actual_pay or 0)
            })

        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': {
                'salary_month': salary_month,
                'total_should_pay': float(total_should_pay),
                'total_actual_pay': float(total_actual_pay),
                'total_tax': float(total_tax),
                'total_count': total_count,
                'pending_count': pending_count,
                'paid_count': paid_count,
                'department_stats': department_stats
            }
        })
    except Exception as e:
        logger.error(f'获取工资统计失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'获取工资统计失败: {str(e)}'}), 500
