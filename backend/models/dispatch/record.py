from datetime import datetime

from extensions import db
from .._base import BigIntPK


class DispatchRecord(db.Model):
    """派单记录表"""
    __tablename__ = 'dispatch_record'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    wo_id = db.Column(BigIntPK, nullable=False)  # 关联工单ID
    dispatch_type = db.Column(db.String(20), default='manual')  # 派单类型: manual/auto/grab
    dispatcher_id = db.Column(BigIntPK)  # 派单人ID
    dispatcher_name = db.Column(db.String(50))  # 派单人姓名
    staff_id = db.Column(BigIntPK)  # 技术员ID
    staff_name = db.Column(db.String(50))  # 技术员姓名
    staff_phone = db.Column(db.String(20))  # 技术员电话
    dispatch_time = db.Column(db.DateTime, default=datetime.now)  # 派单时间
    accept_status = db.Column(db.Integer, default=0)  # 接单状态: 0待接 1已接 2拒单 3超时
    accept_time = db.Column(db.DateTime)  # 接单时间
    reject_reason = db.Column(db.String(255))  # 拒单原因
    arrive_time = db.Column(db.DateTime)  # 到达时间
    start_time = db.Column(db.DateTime)  # 开始处理时间
    finish_time = db.Column(db.DateTime)  # 完成时间
    remark = db.Column(db.Text)  # 备注
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class StaffStatus(db.Model):
    """技术员实时状态表"""
    __tablename__ = 'staff_status'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    staff_id = db.Column(BigIntPK, unique=True, nullable=False)  # 技术员用户ID
    staff_name = db.Column(db.String(50))  # 姓名
    online_status = db.Column(db.Integer, default=0)  # 在线状态: 0离线 1在线 2忙碌
    current_wo_id = db.Column(BigIntPK)  # 当前工单ID
    today_count = db.Column(db.Integer, default=0)  # 今日接单数
    today_finished = db.Column(db.Integer, default=0)  # 今日完成数
    max_daily = db.Column(db.Integer, default=10)  # 每日最大接单量
    skills = db.Column(db.String(255))  # 技能标签（逗号分隔）
    rating = db.Column(db.Numeric(3, 2), default=5.00)  # 好评率
    location = db.Column(db.String(255))  # 当前位置
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class DispatchLog(db.Model):
    """派单操作日志"""
    __tablename__ = 'dispatch_log'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    wo_id = db.Column(BigIntPK, nullable=False)
    action = db.Column(db.String(50))  # 派单/接单/拒单/改派/取消
    content = db.Column(db.Text)
    operator_id = db.Column(BigIntPK)
    operator_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)