from datetime import datetime

from extensions import db
from .._base import BigIntPK


class Office(db.Model):
    """办公室/办事处"""
    __tablename__ = 'office'
    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='办公室名称')
    code = db.Column(db.String(50), unique=True, comment='办公室编码')
    sort_order = db.Column(db.Integer, default=0, comment='排序')
    status = db.Column(db.Integer, default=1, comment='状态：1启用 0禁用')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'sort_order': self.sort_order,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }