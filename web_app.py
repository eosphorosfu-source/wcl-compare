#!/usr/bin/env python3
"""
WCL 对比分析工具 - Web 入口
用法: python web_app.py
"""
import os
import re
import sys
import tempfile
from urllib.parse import urlparse, parse_qs

from flask import Flask, jsonify, render_template, request, send_from_directory

from wcl_client import WCLClient
from analyzer import FightComparator, PlayerCompareData, translate_name
from report_generator import HtmlReportGenerator

app = Flask(__name__, template_folder="templates", static_folder="static")


def get_api_key() -> str:
    key_file = os.path.join(os.path.dirname(__file__), ".wcl_api_key")
    if os.path.exists(key_file):
        with open(key_file, "r", encoding="utf-8") as f:
            key = f.read().strip()
        if key:
            return key
    return os.environ.get("WCL_API_KEY", "")


def parse_wcl_url(url: str):
    """
    解析 WCL URL，返回 (report_code, fight_id)。
    支持格式：
      - https://cn.titan.warcraftlogs.com/reports/XXXX
      - https://www.warcraftlogs.com/reports/XXXX
      - https://www.warcraftlogs.com/reports/XXXX#fight=2
      - 纯 Report Code（16 位字母数字）
    fight_id 为可选，未提供时返回 None。
    """
    url = url.strip()
    if not url:
        return None, None

    # 支持纯 report code
    if re.match(r'^[A-Za-z0-9]{16}$', url):
        return url, None

    parsed = urlparse(url)
    # 提取 report code
    match = re.search(r'/reports/([A-Za-z0-9]+)', parsed.path)
    if not match:
        return None, None
    report_code = match.group(1)

    # 提取 fight id（可选）
    fight_id = None
    query = parse_qs(parsed.query)
    if "fight" in query:
        try:
            fight_id = int(query["fight"][0])
        except (ValueError, IndexError):
            pass
    if fight_id is None and parsed.fragment:
        hash_match = re.search(r'fight[=:](\d+)', parsed.fragment)
        if hash_match:
            fight_id = int(hash_match.group(1))

    return report_code, fight_id


def get_client():
    api_key = get_api_key()
    if not api_key:
        raise Exception("未配置 WCL API Key，请先运行获取Token脚本")
    return WCLClient(api_key)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/parse-url", methods=["POST"])
def api_parse_url():
    data = request.get_json()
    url = data.get("url", "")
    report_code, fight_id = parse_wcl_url(url)
    if not report_code:
        return jsonify({"success": False, "error": "无法解析 WCL 地址，请检查链接格式"})
    return jsonify({"success": True, "report_code": report_code, "fight_id": fight_id})


@app.route("/api/fights", methods=["POST"])
def api_fights():
    """获取某个报告中的所有 Boss 战斗列表（过滤小怪/Trash 战斗）"""
    data = request.get_json()
    report_code = data.get("report_code", "")

    if not report_code:
        return jsonify({"success": False, "error": "缺少报告代码"})

    try:
        client = get_client()
        report = client.get_report(report_code)
        fights = []
        for f in report.get("fights", []):
            # 只保留 Boss 战（encounterID 有效且非 0）
            encounter_id = f.get("encounterID")
            if not encounter_id:
                continue
            duration = (f.get("endTime", 0) - f.get("startTime", 0)) / 1000
            fights.append({
                "id": f.get("id"),
                "encounter_id": encounter_id,
                "name": f.get("name", ""),
                "name_cn": translate_name(f.get("name", "")),
                "kill": f.get("kill", False),
                "duration": duration,
                "difficulty": f.get("difficulty"),
            })
        return jsonify({"success": True, "fights": fights, "report_title": report.get("title", "")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/players", methods=["POST"])
def api_players():
    data = request.get_json()
    report_code = data.get("report_code", "")
    fight_id = data.get("fight_id")

    if not report_code:
        return jsonify({"success": False, "error": "缺少报告代码"})
    if fight_id is None:
        return jsonify({"success": False, "error": "缺少战斗ID"})

    try:
        client = get_client()
        report = client.get_report(report_code)
        fight = next((f for f in report["fights"] if f["id"] == fight_id), None)
        if not fight:
            return jsonify({"success": False, "error": f"战斗 ID {fight_id} 不存在于报告中"})

        # 通过伤害排行表获取玩家信息
        entries = client.get_damage_table(report_code, fight_id)
        players = []
        seen = set()
        for entry in entries:
            pid = entry.get("id")
            if not pid or pid in seen:
                continue
            seen.add(pid)
            icon = entry.get("icon", "")
            spec = icon.split("-")[-1] if "-" in icon else icon
            players.append({
                "id": pid,
                "name": entry.get("name", ""),
                "class": entry.get("type", ""),
                "spec": spec,
                "spec_cn": translate_name(spec),
                "ilvl": entry.get("itemLevel", 0),
                "dps": entry.get("perSecondAmount", 0) or 0,
            })

        # 按DPS排序
        players.sort(key=lambda x: x["dps"], reverse=True)
        return jsonify({
            "success": True,
            "players": players,
            "fight_name": fight.get("name", ""),
            "fight_name_cn": translate_name(fight.get("name", "")),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = request.get_json()
    report_a = data.get("report_a", "")
    fight_a = data.get("fight_a")
    report_b = data.get("report_b", "")
    fight_b = data.get("fight_b")
    player_a = data.get("player_a", "")
    player_b = data.get("player_b", "")

    if not all([report_a, fight_a is not None, report_b, fight_b is not None]):
        return jsonify({"success": False, "error": "参数不完整"})
    if not player_a or not player_b:
        return jsonify({"success": False, "error": "请选择角色"})

    try:
        client = get_client()
        comparator = FightComparator(client)

        # 分别获取两次战斗中指定玩家的详细数据
        info_a, players_a = comparator.fetch_fight_data(report_a, fight_a, target_player=player_a)
        info_b, players_b = comparator.fetch_fight_data(report_b, fight_b, target_player=player_b)

        pa = next((p for p in players_a.values() if player_a.lower() in p["name"].lower()), None)
        pb = next((p for p in players_b.values() if player_b.lower() in p["name"].lower()), None)

        if not pa or not pb:
            return jsonify({"success": False, "error": "未找到玩家数据"})

        # 校验职业/天赋是否一致
        spec_a = pa.get("spec", "")
        spec_b = pb.get("spec", "")
        class_a = pa.get("class_name", "")
        class_b = pb.get("class_name", "")
        if spec_a != spec_b or class_a != class_b:
            return jsonify({
                "success": False,
                "error": f"职业/天赋不一致：\n战斗A: {pa['name']} ({translate_name(spec_a)})\n战斗B: {pb['name']} ({translate_name(spec_b)})",
                "mismatch": True,
            })

        # 构造对比数据（支持不同玩家，只要同职业）
        display_name = player_a if player_a == player_b else f"{player_a} vs {player_b}"
        pdata = PlayerCompareData(
            name=display_name,
            class_name=pa.get("class_name", ""),
            spec=pa.get("spec", ""),
            dps_a=pa.get("dps", 0),
            damage_a=pa.get("total_damage", 0),
            ilvl_a=pa.get("ilvl", 0),
            active_time_a=pa.get("active_time", 0),
            casts_a=pa.get("casts", []),
            buffs_a=pa.get("buffs", []),
            debuffs_a=pa.get("debuffs", []),
            damage_breakdown_a=pa.get("damage_breakdown", []),
            dps_b=pb.get("dps", 0),
            damage_b=pb.get("total_damage", 0),
            ilvl_b=pb.get("ilvl", 0),
            active_time_b=pb.get("active_time", 0),
            casts_b=pb.get("casts", []),
            buffs_b=pb.get("buffs", []),
            debuffs_b=pb.get("debuffs", []),
            damage_breakdown_b=pb.get("damage_breakdown", []),
        )

        # 判断是否为不同 Boss 战
        same_boss = info_a.encounter_id == info_b.encounter_id and info_a.encounter_id != 0

        comparison = {
            "fight_a": {
                "report": report_a,
                "id": fight_a,
                "encounter_id": info_a.encounter_id,
                "name": info_a.encounter_name,
                "kill": info_a.kill,
                "duration_sec": info_a.duration_ms / 1000,
                "difficulty": info_a.difficulty,
                "player_name": player_a,
            },
            "fight_b": {
                "report": report_b,
                "id": fight_b,
                "encounter_id": info_b.encounter_id,
                "name": info_b.encounter_name,
                "kill": info_b.kill,
                "duration_sec": info_b.duration_ms / 1000,
                "difficulty": info_b.difficulty,
                "player_name": player_b,
            },
            "same_boss": same_boss,
            "warnings": [] if same_boss else [
                "提示：两次战斗不是同一个 Boss（" +
                f"战斗A: {info_a.encounter_name}，战斗B: {info_b.encounter_name}" +
                "），战斗环境、机制和时间轴可能完全不同，对比结果仅供参考。"
            ],
            "players": [pdata]
        }

        generator = HtmlReportGenerator()
        html = generator.generate(comparison, comparator)

        # 保存到临时文件并返回
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8", dir=os.path.dirname(__file__)) as f:
            f.write(html)
            report_path = f.name

        filename = os.path.basename(report_path)
        return jsonify({"success": True, "report_file": filename})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})


@app.route("/reports/<path:filename>")
def serve_report(filename):
    safe_name = os.path.basename(filename)
    report_dir = os.path.dirname(__file__)
    return send_from_directory(report_dir, safe_name)


if __name__ == "__main__":
    if sys.platform == "win32":
        os.environ["PYTHONIOENCODING"] = "utf-8"
    app.run(host="0.0.0.0", port=5000, debug=False)
