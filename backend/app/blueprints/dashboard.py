"""仪表盘统计聚合接口。

迁移自 source-code/app.py 中 4352-4450 行附近的原始路由代码。
保持行为完全一致：基础实体计数、工单按状态分组、最近 7 天趋势统计。

注意：仪表盘是跨表聚合查询（customer / supplier / product / workorder / finance），
不涉及写操作，且查询逻辑固定，因此未做 try-import 容错。
"""
from datetime import datetime, timedelta

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from extensions import db
from models.customer import BaseCustomer
from models.finance import FinanceRecord
from models.product import ProductInfo
from models.supplier import BaseSupplier
from models.workorder import WorkOrder

bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """获取仪表盘统计数据。"""
    today = datetime.now().date()

    # 基础统计
    customer_count = BaseCustomer.query.filter_by(status=1).count()
    supplier_count = BaseSupplier.query.filter_by(status=1).count()
    product_count = ProductInfo.query.filter_by(status=1).count()

    # 工单统计
    wo_total = WorkOrder.query.count()
    wo_pending = WorkOrder.query.filter(WorkOrder.status.in_([0, 1, 2, 3, 4, 5, 6, 7])).count()
    wo_completed = WorkOrder.query.filter_by(status=9).count()
    wo_today = WorkOrder.query.filter(db.func.date(WorkOrder.created_at) == today).count()

    # 今日收入
    today_records = FinanceRecord.query.filter(
        FinanceRecord.record_type == 1,
        db.func.date(FinanceRecord.created_at) == today
    ).all()
    today_income = sum(float(r.amount or 0) for r in today_records)

    # 待处理工单按状态分组
    wo_by_status = db.session.query(
        WorkOrder.status,
        db.func.count(WorkOrder.id)
    ).filter(WorkOrder.status < 9).group_by(WorkOrder.status).all()

    status_stats = {s: c for s, c in wo_by_status}

    return jsonify({
        'code': 200,
        'data': {
            'customer_count': customer_count,
            'supplier_count': supplier_count,
            'product_count': product_count,
            'wo_total': wo_total,
            'wo_pending': wo_pending,
            'wo_completed': wo_completed,
            'wo_today': wo_today,
            'today_income': today_income,
            'wo_status_stats': {
                'pending': status_stats.get(0, 0),
                'accepted': status_stats.get(1, 0),
                'assigning': status_stats.get(2, 0),
                'processing': status_stats.get(3, 0),
                'waiting_parts': status_stats.get(4, 0),
                'waiting_audit': status_stats.get(5, 0),
                'parts_inbound': status_stats.get(6, 0),
                'repairing': status_stats.get(7, 0),
                'waiting_settle': status_stats.get(8, 0)
            }
        }
    })


@bp.route('/workorder-trend', methods=['GET'])
@jwt_required()
def get_workorder_trend():
    """获取工单趋势数据（最近7天）。"""
    today = datetime.now().date()
    result = []

    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        count = WorkOrder.query.filter(db.func.date(WorkOrder.created_at) == date).count()
        completed = WorkOrder.query.filter(
            db.func.date(WorkOrder.actual_time) == date,
            WorkOrder.status == 9
        ).count()
        result.append({
            'date': date.strftime('%m-%d'),
            'count': count,
            'completed': completed
        })

    return jsonify({'code': 200, 'data': result})


@bp.route('/income-trend', methods=['GET'])
@jwt_required()
def get_income_trend():
    """获取收入趋势数据（最近7天）。"""
    today = datetime.now().date()
    result = []

    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        records = FinanceRecord.query.filter(
            FinanceRecord.record_type == 1,
            db.func.date(FinanceRecord.created_at) == date
        ).all()
        income = sum(float(r.amount or 0) for r in records)
        result.append({
            'date': date.strftime('%m-%d'),
            'income': income
        })

    return jsonify({'code': 200, 'data': result})