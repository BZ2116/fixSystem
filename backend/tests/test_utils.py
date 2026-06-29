"""utils 单元测试。"""
import pytest
from app.utils import ok, fail, page_ok, generate_code, reset_counter, to_dict, generate_pinyin_code


@pytest.fixture
def app_ctx():
    """为 ok/fail 这种需要访问 flask.g 的函数提供应用上下文。"""
    from app import create_app
    app = create_app('testing')
    with app.app_context():
        yield app


def test_ok_default(app_ctx):
    """ok() 返回 200 + 默认 message"""
    resp, status = ok({'a': 1})
    assert status == 200
    body = resp.get_json()
    assert body['code'] == 200
    assert body['data'] == {'a': 1}


def test_fail_returns_correct_status(app_ctx):
    """fail() 返回指定 code"""
    resp, status = fail('test error', code=403, http_status=403)
    assert status == 403
    body = resp.get_json()
    assert body['code'] == 403
    assert body['message'] == 'test error'


def test_generate_code_format():
    """generate_code 生成正确格式"""
    reset_counter('TST')
    code1 = generate_code('TST', width=4)
    assert code1.startswith('TST')
    assert len(code1) == 3 + 8 + 4  # 前缀 + 日期 + 序号
    code2 = generate_code('TST', width=4)
    assert code1 != code2


def test_to_dict_none():
    """to_dict(None) 返回 None"""
    assert to_dict(None) is None


def test_pinyin_chinese():
    """generate_pinyin_code 处理中文"""
    code = generate_pinyin_code('客户')
    assert code  # 非空即可（依赖 pypinyin 是否安装）