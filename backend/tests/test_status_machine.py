"""状态机一致性测试。

覆盖技师工作流涉及的核心状态写值：
- cancel_workorder: 应写 status=7 (WO_STATUS_MAP['已取消'])
- cancel_receiveorder: 应写 status=15 (RO_STATUS_MAP['已取消'])
- 客户拒绝报价: 应写 status=17 (新状态,不再与外店取回待测试 14 冲突)
- dispatch finish_dispatch: 写 status=5 后 status_name 应与 WO_STATUS_MAP[5] 一致
"""
import pytest


@pytest.fixture
def app():
    from app import create_app
    from extensions import db
    # 必须在 create_all 前 import 所有 model，否则 SQLAlchemy 不知道表结构
    from models.workorder import WorkOrder  # noqa
    from models.receive import ReceiveOrder  # noqa
    from models.dispatch.record import DispatchRecord  # noqa
    from models.system import SysUser  # noqa
    app = create_app('testing')
    with app.app_context():
        db.session.execute(db.text(
            'CREATE TABLE IF NOT EXISTS jwt_blacklist ('
            '  jti TEXT PRIMARY KEY,'
            '  revoked_at DATETIME NOT NULL,'
            '  expires_at DATETIME NOT NULL'
            ')'
        ))
        db.session.commit()
        db.create_all()
    yield app


@pytest.fixture
def db(app):
    from extensions import db as _db
    return _db


def test_cancel_workorder_writes_status_7(app, db):
    """工单取消后 status 应为 7（已取消），不是 10。"""
    from models.workorder import WorkOrder
    from app.services.workorder_service import cancel_workorder

    with app.app_context():
        order = WorkOrder(wo_no='WO-CANCEL-1', status=0, customer_name='测试客户')
        db.session.add(order)
        db.session.commit()

        cancel_workorder(order, '客户改主意', 1, 'tester')
        db.session.commit()

        assert order.status == 7, f'期望 7 (已取消)，实际 {order.status}'
        assert order.status_name == '已取消'


def test_cancel_workorder_rejects_settled(app, db):
    """已完成的工单不能再次取消。"""
    from models.workorder import WorkOrder
    from app.services.workorder_service import cancel_workorder

    with app.app_context():
        order = WorkOrder(wo_no='WO-CANCEL-2', status=6, customer_name='测试客户')
        db.session.add(order)
        db.session.commit()

        with pytest.raises(ValueError):
            cancel_workorder(order, '试图取消', 1, 'tester')


def test_cancel_receiveorder_writes_status_15(app, db):
    """接件单取消后 status 应为 15（已取消），不是 14。"""
    from models.receive import ReceiveOrder
    from app.services.receive_service import cancel_receiveorder

    with app.app_context():
        order = ReceiveOrder(receive_no='RO-CANCEL-1', status=0, customer_name='测试客户')
        db.session.add(order)
        db.session.commit()

        cancel_receiveorder(order, '客户改主意', 1, 'tester')
        db.session.commit()

        assert order.status == 15, f'期望 15 (已取消)，实际 {order.status}'


def test_cancel_receiveorder_rejects_completed(app, db):
    """已完成的接件单（status=9）不能再次取消。"""
    from models.receive import ReceiveOrder
    from app.services.receive_service import cancel_receiveorder

    with app.app_context():
        order = ReceiveOrder(receive_no='RO-CANCEL-2', status=9, customer_name='测试客户')
        db.session.add(order)
        db.session.commit()

        with pytest.raises(ValueError):
            cancel_receiveorder(order, '试图取消', 1, 'tester')


def test_quote_rejected_writes_status_17(app, db):
    """客户拒绝报价应写 status=17（新状态），不是 14（外店取回待测试）。"""
    from app.blueprints.receive import RO_STATUS_MAP
    from models.receive import ReceiveOrder

    with app.app_context():
        # 准备：接件单处于"待客户确认"(3) 状态
        order = ReceiveOrder(receive_no='RO-Q-1', status=3, customer_name='客户')
        db.session.add(order)
        db.session.commit()
        order_id = order.id

        # 通过 HTTP 模拟客户拒绝报价
        from flask_jwt_extended import create_access_token
        token = create_access_token(
            identity='1',
            additional_claims={'permissions': ['receive:edit'], 'role_code': 'admin'},
        )
        client = app.test_client()
        res = client.post(
            f'/api/receiveorders/{order_id}/confirm',
            json={'confirmed': 2, 'reject_reason': '价格太贵'},
            headers={'Authorization': f'Bearer {token}'},
        )
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'

        db.session.refresh(order)
        assert order.status == 17, f'期望 17 (客户拒绝报价)，实际 {order.status}'
        assert RO_STATUS_MAP[order.status] != '外店取回待测试'  # 不应错乱


def test_finish_dispatch_status_consistent(app, db):
    """dispatch finish_dispatch 后工单 status 和 status_name 应一致。"""
    from app.blueprints.dispatch import bp as dispatch_bp
    # 确保 dispatch 蓝图已注册
    assert dispatch_bp.name in app.blueprints

    from models.workorder import WorkOrder
    from models.dispatch.record import DispatchRecord
    from app.blueprints.workorder import WO_STATUS_MAP

    with app.app_context():
        wo = WorkOrder(wo_no='WO-DISP-1', status=4, customer_name='客户')
        db.session.add(wo)
        db.session.commit()
        wo_id = wo.id

        record = DispatchRecord(
            wo_id=wo_id,
            staff_id=1,
            staff_name='技师A',
            dispatch_time=__import__('datetime').datetime.now(),
        )
        db.session.add(record)
        db.session.commit()
        record_id = record.id

        # 走 HTTP 调用 finish
        from flask_jwt_extended import create_access_token
        token = create_access_token(
            identity='1',
            additional_claims={'permissions': ['dispatch:edit'], 'role_code': 'admin'},
        )
        client = app.test_client()
        res = client.post(
            f'/api/dispatch/{record_id}/finish',
            headers={'Authorization': f'Bearer {token}'},
        )
        assert res.status_code == 200, f'期望 200, 实际 {res.status_code}: {res.get_json()}'

        db.session.refresh(wo)
        # status 必须是 WO_STATUS_MAP 里有的值
        assert wo.status in WO_STATUS_MAP, f'status {wo.status} 不在 WO_STATUS_MAP'
        # status_name 必须等于 WO_STATUS_MAP[status]，不能错乱
        assert wo.status_name == WO_STATUS_MAP[wo.status], \
            f'status_name={wo.status_name} 与 WO_STATUS_MAP[{wo.status}]={WO_STATUS_MAP[wo.status]} 不一致'


def test_change_status_rejects_undefined_target(app, db):
    """change_workorder_status 不应允许跳到 WO_STATUS_MAP 中不存在的 status。"""
    from models.workorder import WorkOrder
    from app.services.workorder_service import change_workorder_status
    from app.blueprints.workorder import WO_STATUS_MAP

    with app.app_context():
        wo = WorkOrder(wo_no='WO-CHG-1', status=0, customer_name='客户')
        db.session.add(wo)
        db.session.commit()

        # 尝试跳到 status=8（WO_STATUS_MAP 没有 8）
        with pytest.raises(ValueError):
            change_workorder_status(wo, 8, '跳到 8', 1, 'tester')

        # 尝试跳到 status=9（WO_STATUS_MAP 没有 9）
        with pytest.raises(ValueError):
            change_workorder_status(wo, 9, '跳到 9', 1, 'tester')

        # 已修复后：8 和 9 不在 WO_STATUS_MAP，应被 WO_STATUS_TRANSITIONS 拒绝
        # WO_STATUS_TRANSITIONS[0] = [1, 7]，所以 8 和 9 都不在合法目标
        # 实际行为是被 transition 检查拒绝（raise ValueError）
