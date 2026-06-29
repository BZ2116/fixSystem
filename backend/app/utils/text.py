"""文本处理工具：拼音首字母生成（用于商品/客户编码）。"""
import re

try:
    from pypinyin import lazy_pinyin
    _HAS_PYPINYIN = True
except ImportError:
    _HAS_PYPINYIN = False


def generate_pinyin_code(text: str) -> str:
    """从中文文本生成拼音首字母编码。例如 '客户A' → 'KHA'。
    非中文字符直接保留。"""
    if not text:
        return ''
    if _HAS_PYPINYIN:
        parts = lazy_pinyin(text)
        return ''.join(p[0].upper() for p in parts if p)
    # fallback: 取每个字符首字母（中文用 unicode 首字符）
    return ''.join(c[0].upper() if c else '' for c in text)