"""
技能/Buff/Boss 名称翻译管理器
- 合并代码内置映射 + 用户本地映射文件
- 遇到未翻译的英文名称时，通过免费在线翻译 API 抓取中文名
- 自动保存新翻译到 ability_translations.json
"""
import json
import os
import re
import time
import urllib.parse
from typing import Dict, Optional

import requests


# 本地用户翻译缓存文件
TRANSLATIONS_FILE = os.path.join(os.path.dirname(__file__), "ability_translations.json")

# 在线翻译 API：MyMemory（免费，无需 Key，有速率限制）
MYMEMORY_URL = "https://api.mymemory.translated.net/get"


def _load_user_translations() -> Dict[str, str]:
    """加载用户本地翻译缓存"""
    if os.path.exists(TRANSLATIONS_FILE):
        try:
            with open(TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {}


def _save_user_translations(translations: Dict[str, str]) -> None:
    """保存用户本地翻译缓存"""
    try:
        with open(TRANSLATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[翻译缓存保存失败] {e}")


def _is_english(name: str) -> bool:
    """简单判断名称是否为英文（包含 ASCII 字母）"""
    if not name:
        return False
    # 如果包含中文字符（CJK 统一表意文字），认为是中文
    if re.search(r"[\u4e00-\u9fff]", name):
        return False
    # 如果只包含数字、符号、空格，不认为是需要翻译的英文
    if re.search(r"[a-zA-Z]", name):
        return True
    return False


def _clean_online_result(text: str) -> Optional[str]:
    """清理在线翻译返回结果，过滤掉 API 警告信息"""
    if not text:
        return None
    text = text.strip()
    # MyMemory 限额用完时会在译文里加警告
    if "MYMEMORY" in text.upper():
        return None
    # 如果翻译完还是英文，认为没翻成功
    if not re.search(r"[\u4e00-\u9fff]", text):
        return None
    return text


def _lookup_online_translation(name: str) -> Optional[str]:
    """
    使用 MyMemory 免费翻译接口把英文名称译为中文。
    有请求速率限制，失败时返回 None。
    """
    if not name or not _is_english(name):
        return None

    try:
        params = {
            "q": name,
            "langpair": "en|zh-CN",
        }
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(
            MYMEMORY_URL,
            params=params,
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        translated = data.get("responseData", {}).get("translatedText", "")
        return _clean_online_result(translated)
    except Exception:
        return None


class TranslationManager:
    """翻译管理器：内置映射 + 本地缓存 + 在线翻译"""

    def __init__(self, built_in_translations: Optional[Dict[str, str]] = None):
        self._built_in = dict(built_in_translations) if built_in_translations else {}
        self._user = _load_user_translations()
        self._pending: set = set()  # 记录已经打印过提示的未翻译名称，避免刷屏
        self._last_online_call: float = 0.0  # 控制在线翻译调用频率

    def translate(self, name: str, spell_id: Optional[int] = None) -> str:
        """
        将名称翻译为中文。
        - 空字符串直接返回
        - 先查内置映射
        - 再查用户本地缓存
        - 如果是英文且未找到，尝试在线翻译
        - 所有新翻译自动写入 ability_translations.json
        """
        if not name:
            return name

        # 已经是中文（含 CJK 字符），无需翻译
        if re.search(r"[\u4e00-\u9fff]", name):
            return name

        # 内置映射
        if name in self._built_in:
            return self._built_in[name]

        # 用户缓存
        if name in self._user:
            return self._user[name]

        # 不是英文（纯数字/符号），不处理
        if not _is_english(name):
            return name

        # 在线翻译（加简单限速，避免触发 API 限制）
        now = time.time()
        elapsed = now - self._last_online_call
        if elapsed < 0.35:  # 两次请求间隔至少 350ms
            time.sleep(0.35 - elapsed)
        self._last_online_call = time.time()

        cn_name = _lookup_online_translation(name)
        if cn_name:
            self._user[name] = cn_name
            _save_user_translations(self._user)
            return cn_name

        # 未翻译，记录提示一次
        if name not in self._pending:
            self._pending.add(name)
            print(f"[待翻译] {name}")

        return name

    def add_translation(self, en_name: str, zh_name: str) -> None:
        """手动添加翻译，并保存到本地缓存"""
        self._user[en_name] = zh_name
        _save_user_translations(self._user)
        self._pending.discard(en_name)

    def get_pending(self) -> list:
        """获取当前未翻译的英文名称列表"""
        return sorted(self._pending)


# 全局默认实例
_default_manager: Optional[TranslationManager] = None


def get_manager() -> TranslationManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = TranslationManager()
    return _default_manager


def translate_name(name: str, spell_id: Optional[int] = None) -> str:
    """兼容旧接口的翻译函数"""
    return get_manager().translate(name, spell_id=spell_id)
