"""统计分析蓝图（5 个统计端点，纯聚合查询）。

迁移自 source-code/app.py 中 15446-15970 行附近的原始路由代码。

业务规则：
- revenue:  按月统计收入/支出
- employee: 按员工统计工单/提成
- customer: 按客户统计销售/回款
- product:  按产品统计销售量/销售额
- dashboard: 仪表盘汇总

跨子域依赖：
- SalesOrder / SalesReceipt / SalesReturn     (models.sales.*)
- PurchaseOrder                              (models.purchase.order)
- FinanceReceivable / FinancePayable          (models.finance.account)
- BaseCustomer / BaseSupplier                (models.customer / models.supplier)
- WorkOrder                                  (models.workorder)
- SysUser                                    (models.system)
- Salary / Expense                           (models.finance.account)

按"函数内懒加载"惯例，仅在需要时 import 模型。
"""
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from extensions import db
from app.utils import to_dict
from app.security import get_current_user_id

logger = logging.getLogger(__name__)

bp = Blueprint('statistics', __name__)


@bp.route('/api/statistics/revenue', methods=['GET'])
@jwt_required()
def revenue_statistics():
    """营收统计API"""
    try:
        from models.sales.order import SalesOrder, SalesOrderItem
        from models.workorder.order import WorkOrder
        from models.finance.account import FinanceReceivable
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        group_by = request.args.get('group_by', 'day')  # day/week/month

        if not start_date or not end_date:
            return jsonify({'code': 400, 'message': '缺少必要参数: start_date, end_date'}), 400

        # 构建日期范围条件
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        end_dt_str = end_date + ' 23:59:59'

        # 1. 销售单统计 (status=1或2)
        sales_query = SalesOrder.query.filter(
            SalesOrder.created_at >= start_date,
            SalesOrder.created_at <= end_dt_str,
            SalesOrder.status.in_([1, 2])
        )
        total_sales = float(sum(s.actual_amount or 0 for s in sales_query.all()))
        sales_count = sales_query.count()

        # 2. 工单统计 (settlement_status=1)
        workorder_query = WorkOrder.query.filter(
            WorkOrder.created_at >= start_date,
            WorkOrder.created_at <= end_dt_str,
            WorkOrder.settlement_status == 1
        )
        total_workorders = float(sum(w.total_amount or 0 for w in workorder_query.all()))
        workorder_count = workorder_query.count()

        # 3. 回款统计 (status=2)
        received_query = FinanceReceivable.query.filter(
            FinanceReceivable.created_at >= start_date,
            FinanceReceivable.created_at <= end_dt_str,
            FinanceReceivable.status == 2
        )
        total_received = float(sum(r.total_amount or 0 for r in received_query.all()))

        # 4. 未回款统计 (status=0或1)
        unreceived_query = FinanceReceivable.query.filter(
            FinanceReceivable.created_at >= start_date,
            FinanceReceivable.created_at <= end_dt_str,
            FinanceReceivable.status.in_([0, 1])
        )
        total_unreceived = float(sum(
            ((r.total_amount or 0) - (r.received_amount or 0)) for r in unreceived_query.all()
        ))

        # 5. 趋势数据
        trend_data = []
        if group_by == 'day':
            from sqlalchemy import func
            # 销售按天统计
            sales_by_day = db.session.query(
                func.date(SalesOrder.created_at).label('date'),
                func.sum(SalesOrder.actual_amount).label('amount')
            ).filter(
                SalesOrder.created_at >= start_date,
                SalesOrder.created_at <= end_dt_str,
                SalesOrder.status.in_([1, 2])
            ).group_by(func.date(SalesOrder.created_at)).all()

            # 工单按天统计
            wo_by_day = db.session.query(
                func.date(WorkOrder.created_at).label('date'),
                func.sum(WorkOrder.total_cost).label('amount')
            ).filter(
                WorkOrder.created_at >= start_date,
                WorkOrder.created_at <= end_dt_str,
                WorkOrder.settlement_status == 1
            ).group_by(func.date(WorkOrder.created_at)).all()

            # 合并数据
            date_map = {}
            for d, amt in sales_by_day:
                date_str = d.strftime('%Y-%m-%d') if d else ''
                if date_str not in date_map:
                    date_map[date_str] = {'sales_amount': 0, 'workorder_amount': 0}
                date_map[date_str]['sales_amount'] = float(amt or 0)

            for d, amt in wo_by_day:
                date_str = d.strftime('%Y-%m-%d') if d else ''
                if date_str not in date_map:
                    date_map[date_str] = {'sales_amount': 0, 'workorder_amount': 0}
                date_map[date_str]['workorder_amount'] = float(amt or 0)

            for date_key in sorted(date_map.keys()):
                trend_data.append({
                    'date': date_key,
                    'sales_amount': date_map[date_key]['sales_amount'],
                    'workorder_amount': date_map[date_key]['workorder_amount'],
                    'total_revenue': date_map[date_key]['sales_amount'] + date_map[date_key]['workorder_amount']
                })

        summary = {
            'total_sales': total_sales,
            'total_workorders': total_workorders,
            'total_revenue': total_sales + total_workorders,
            'total_received': total_received,
            'total_unreceived': total_unreceived,
            'sales_count': sales_count,
            'workorder_count': workorder_count
        }

        return jsonify({
            'code': 200,
            'data': {
                'summary': summary,
                'trend': trend_data
            }
        })

    except Exception as e:
        logger.error(f'营收统计失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'统计失败: {str(e)}'}), 500


@bp.route('/api/statistics/employee', methods=['GET'])
@jwt_required()
def employee_statistics():
    """员工业绩统计API"""
    try:
        from models.sales.order import SalesOrder
        from models.workorder.order import WorkOrder
        from models.system import SysUser
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_id = request.args.get('user_id')

        if not start_date or not end_date:
            return jsonify({'code': 400, 'message': '缺少必要参数: start_date, end_date'}), 400

        end_dt_str = end_date + ' 23:59:59'

        # 查询所有有效用户
        user_query = SysUser.query.filter(SysUser.status == 1)
        if user_id:
            user_query = user_query.filter(SysUser.id == user_id)
        users = user_query.all()

        details = []
        total_sales_count = 0
        total_sales_amount = 0
        total_workorder_count = 0
        total_workorder_amount = 0

        for user in users:
            # 统计该用户的销售单 (作为创建者或关联者)
            user_sales = SalesOrder.query.filter(
                SalesOrder.created_at >= start_date,
                SalesOrder.created_at <= end_dt_str,
                SalesOrder.status.in_([1, 2])
            ).filter(
                (SalesOrder.created_by == user.id) | (SalesOrder.salesman_id == user.id)
            ).all()

            sales_count = len(user_sales)
            sales_amount = float(sum(s.actual_amount or 0 for s in user_sales))

            # 统计该用户的工单 (按assigned_to)
            user_workorders = WorkOrder.query.filter(
                WorkOrder.created_at >= start_date,
                WorkOrder.created_at <= end_dt_str,
                WorkOrder.settlement_status == 1,
                WorkOrder.assigned_to == user.id
            ).all()

            workorder_count = len(user_workorders)
            workorder_amount = float(sum(w.total_amount or 0 for w in user_workorders))

            if sales_count > 0 or workorder_count > 0:
                details.append({
                    'user_id': user.id,
                    'user_name': user.real_name or user.username,
                    'department': user.department or '',
                    'sales_count': sales_count,
                    'sales_amount': sales_amount,
                    'workorder_count': workorder_count,
                    'workorder_amount': workorder_amount,
                    'total_amount': sales_amount + workorder_amount
                })

                total_sales_count += sales_count
                total_sales_amount += sales_amount
                total_workorder_count += workorder_count
                total_workorder_amount += workorder_amount

        # 按总业绩排序
        details.sort(key=lambda x: x['total_amount'], reverse=True)

        summary = {
            'total_employees': len(details),
            'total_sales_count': total_sales_count,
            'total_sales_amount': total_sales_amount,
            'total_workorder_count': total_workorder_count,
            'total_workorder_amount': total_workorder_amount
        }

        return jsonify({
            'code': 200,
            'data': {
                'summary': summary,
                'details': details
            }
        })

    except Exception as e:
        logger.error(f'员工业绩统计失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'统计失败: {str(e)}'}), 500


@bp.route('/api/statistics/customer', methods=['GET'])
@jwt_required()
def customer_statistics():
    """客户业绩统计API"""
    try:
        from models.sales.order import SalesOrder
        from models.finance.account import FinanceReceivable
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        customer_id = request.args.get('customer_id')

        if not start_date or not end_date:
            return jsonify({'code': 400, 'message': '缺少必要参数: start_date, end_date'}), 400

        end_dt_str = end_date + ' 23:59:59'

        # 查询销售单
        sales_query = SalesOrder.query.filter(
            SalesOrder.created_at >= start_date,
            SalesOrder.created_at <= end_dt_str,
            SalesOrder.status.in_([1, 2])
        )
        if customer_id:
            sales_query = sales_query.filter(SalesOrder.customer_id == customer_id)
        sales_orders = sales_query.all()

        # 按客户分组统计
        customer_stats = {}
        for order in sales_orders:
            cid = order.customer_id
            cname = order.customer_name or '未知客户'
            if cid not in customer_stats:
                customer_stats[cid] = {
                    'customer_id': cid,
                    'customer_name': cname,
                    'order_count': 0,
                    'total_amount': 0,
                    'received_amount': 0
                }
            customer_stats[cid]['order_count'] += 1
            customer_stats[cid]['total_amount'] += float(order.actual_amount or 0)

        # 查询回款记录
        receivable_query = FinanceReceivable.query.filter(
            FinanceReceivable.created_at >= start_date,
            FinanceReceivable.created_at <= end_dt_str
        )
        if customer_id:
            receivable_query = receivable_query.filter(FinanceReceivable.customer_id == customer_id)
        receivables = receivable_query.all()

        for rec in receivables:
            cid = rec.customer_id
            if cid and cid in customer_stats:
                customer_stats[cid]['received_amount'] += float(rec.received_amount or 0)

        # 转换为列表并排序
        top_customers = list(customer_stats.values())
        top_customers.sort(key=lambda x: x['total_amount'], reverse=True)

        total_orders = sum(c['order_count'] for c in top_customers)
        total_amount = sum(c['total_amount'] for c in top_customers)
        total_received = sum(c['received_amount'] for c in top_customers)

        summary = {
            'total_customers': len(top_customers),
            'total_orders': total_orders,
            'total_amount': total_amount,
            'total_received': total_received
        }

        return jsonify({
            'code': 200,
            'data': {
                'summary': summary,
                'top_customers': top_customers[:20]  # 返回前20名
            }
        })

    except Exception as e:
        logger.error(f'客户业绩统计失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'统计失败: {str(e)}'}), 500


@bp.route('/api/statistics/product', methods=['GET'])
@jwt_required()
def product_statistics():
    """产品业绩统计API"""
    try:
        from models.sales.order import SalesOrder, SalesOrderItem
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date or not end_date:
            return jsonify({'code': 400, 'message': '缺少必要参数: start_date, end_date'}), 400

        end_dt_str = end_date + ' 23:59:59'

        # 查询销售单明细
        from sqlalchemy import func
        items_query = db.session.query(SalesOrderItem).join(
            SalesOrder, SalesOrderItem.order_id == SalesOrder.id
        ).filter(
            SalesOrder.created_at >= start_date,
            SalesOrder.created_at <= end_dt_str,
            SalesOrder.status.in_([1, 2])
        )

        items = items_query.all()

        # 按产品统计
        product_stats = {}
        category_stats = {}

        for item in items:
            pid = item.product_id
            if pid not in product_stats:
                product_stats[pid] = {
                    'product_id': pid,
                    'product_name': item.product_name or '未知产品',
                    'category_name': item.category_name or '未分类',
                    'total_quantity': 0,
                    'total_amount': 0
                }
            product_stats[pid]['total_quantity'] += float(item.quantity or 0)
            product_stats[pid]['total_amount'] += float(item.total_price or 0)

        # 按分类统计
        for pid, stat in product_stats.items():
            cat_name = stat['category_name']
            if cat_name not in category_stats:
                category_stats[cat_name] = {
                    'category_name': cat_name,
                    'product_count': 0,
                    'total_quantity': 0,
                    'total_amount': 0
                }
            category_stats[cat_name]['product_count'] += 1
            category_stats[cat_name]['total_quantity'] += stat['total_quantity']
            category_stats[cat_name]['total_amount'] += stat['total_amount']

        # 转换为列表并排序
        top_products = list(product_stats.values())
        top_products.sort(key=lambda x: x['total_amount'], reverse=True)

        category_list = list(category_stats.values())
        category_list.sort(key=lambda x: x['total_amount'], reverse=True)

        total_quantity = sum(p['total_quantity'] for p in top_products)
        total_amount = sum(p['total_amount'] for p in top_products)

        summary = {
            'total_products': len(top_products),
            'total_quantity': total_quantity,
            'total_amount': total_amount
        }

        return jsonify({
            'code': 200,
            'data': {
                'summary': summary,
                'top_products': top_products[:20],  # 返回前20名
                'category_stats': category_list
            }
        })

    except Exception as e:
        logger.error(f'产品业绩统计失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'统计失败: {str(e)}'}), 500


@bp.route('/api/statistics/dashboard', methods=['GET'])
@jwt_required()
def dashboard_statistics():
    """综合仪表盘数据API"""
    try:
        from models.sales.order import SalesOrder
        from models.workorder.order import WorkOrder
        from models.finance.account import FinanceReceivable
        from models.inventory.stock import Inventory
        today = datetime.now().strftime('%Y-%m-%d')
        today_start = today + ' 00:00:00'
        today_end = today + ' 23:59:59'

        # 本月日期范围
        current_year = datetime.now().year
        current_month = datetime.now().month
        month_start = f'{current_year}-{current_month:02d}-01'
        month_end = today_end

        # 1. 今日数据
        today_sales = SalesOrder.query.filter(
            SalesOrder.created_at >= today_start,
            SalesOrder.created_at <= today_end,
            SalesOrder.status.in_([1, 2])
        ).all()
        today_sales_count = len(today_sales)
        today_sales_amount = float(sum(s.actual_amount or 0 for s in today_sales))

        today_workorders = WorkOrder.query.filter(
            WorkOrder.created_at >= today_start,
            WorkOrder.created_at <= today_end,
            WorkOrder.settlement_status == 1
        ).all()
        today_workorder_count = len(today_workorders)
        today_workorder_amount = float(sum(w.total_amount or 0 for w in today_workorders))

        today_data = {
            'sales_count': today_sales_count,
            'sales_amount': today_sales_amount,
            'workorder_count': today_workorder_count,
            'workorder_amount': today_workorder_amount
        }

        # 2. 本月数据
        month_sales = SalesOrder.query.filter(
            SalesOrder.created_at >= month_start,
            SalesOrder.created_at <= month_end,
            SalesOrder.status.in_([1, 2])
        ).all()
        month_sales_count = len(month_sales)
        month_sales_amount = float(sum(s.actual_amount or 0 for s in month_sales))

        month_workorders = WorkOrder.query.filter(
            WorkOrder.created_at >= month_start,
            WorkOrder.created_at <= month_end,
            WorkOrder.settlement_status == 1
        ).all()
        month_workorder_count = len(month_workorders)
        month_workorder_amount = float(sum(w.total_amount or 0 for w in month_workorders))

        # 本月应收和回款
        month_receivables = FinanceReceivable.query.filter(
            FinanceReceivable.created_at >= month_start,
            FinanceReceivable.created_at <= month_end
        ).all()
        month_receivable_amount = float(sum(r.total_amount or 0 for r in month_receivables))
        month_received_amount = float(sum(r.received_amount or 0 for r in month_receivables))

        month_data = {
            'sales_count': month_sales_count,
            'sales_amount': month_sales_amount,
            'workorder_count': month_workorder_count,
            'workorder_amount': month_workorder_amount,
            'receivable_amount': month_receivable_amount,
            'received_amount': month_received_amount
        }

        # 3. 待处理数据
        pending_orders = SalesOrder.query.filter(SalesOrder.status == 0).count()
        pending_workorders = WorkOrder.query.filter(WorkOrder.settlement_status == 0).count()
        pending_receivables = FinanceReceivable.query.filter(
            FinanceReceivable.status.in_([0, 1])
        ).count()

        pending_data = {
            'pending_orders': pending_orders,
            'pending_workorders': pending_workorders,
            'pending_receivables': pending_receivables
        }

        # 4. 预警信息
        alerts = []

        # 库存预警 (假设有库存模型)
        low_stock_count = 0
        try:
            low_stock_count = Inventory.query.filter(Inventory.quantity <= Inventory.min_quantity).count()
            if low_stock_count > 0:
                alerts.append({
                    'type': 'inventory',
                    'message': f'有{low_stock_count}个产品库存不足',
                    'count': low_stock_count
                })
        except:
            pass

        # 逾期未回款预警
        overdue_receivables = FinanceReceivable.query.filter(
            FinanceReceivable.status.in_([0, 1]),
            FinanceReceivable.due_date < today
        ).count()
        if overdue_receivables > 0:
            alerts.append({
                'type': 'receivable',
                'message': f'有{overdue_receivables}笔应收账款已逾期',
                'count': overdue_receivables
            })

        # 待审核预警
        if pending_orders > 0:
            alerts.append({
                'type': 'order',
                'message': f'有{pending_orders}个销售单待审核',
                'count': pending_orders
            })

        if pending_workorders > 0:
            alerts.append({
                'type': 'workorder',
                'message': f'有{pending_workorders}个工单待结算',
                'count': pending_workorders
            })

        return jsonify({
            'code': 200,
            'data': {
                'today': today_data,
                'month': month_data,
                'pending': pending_data,
                'alerts': alerts
            }
        })

    except Exception as e:
        logger.error(f'仪表盘数据统计失败: {str(e)}')
        return jsonify({'code': 500, 'message': f'统计失败: {str(e)}'}), 500
