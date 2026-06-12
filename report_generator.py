"""
对比报告生成器 - 支持文本和HTML两种格式
"""
import json
from typing import Dict, List
from datetime import datetime
from analyzer import translate_name


# 增益/减益时间轴全局 WoW 风格配色（不随职业变化，确保同职业对比也能看清）
# A 侧：烈焰橙红（纯色强对比）
AURA_BAND_A_BG = "linear-gradient(180deg, rgba(255,123,0,0.95) 0%, rgba(255,42,0,0.85) 100%)"
AURA_BAND_A_GLOW = "0 0 6px rgba(255,82,0,0.6)"
AURA_TEXT_A = "#ff7b00"
# B 侧：邪能蓝绿，并叠加 45° 斜向纹理，用颜色+纹路双重区分
AURA_BAND_B_BG = "linear-gradient(180deg, rgba(0,229,201,0.90) 0%, rgba(0,102,255,0.85) 100%), repeating-linear-gradient(45deg, rgba(255,255,255,0.12) 0px, rgba(255,255,255,0.12) 2px, transparent 2px, transparent 6px)"
AURA_BAND_B_GLOW = "0 0 6px rgba(0,180,220,0.55)"
AURA_TEXT_B = "#00e5c9"


def format_number(n: int) -> str:
    """格式化大数字（带正负号）"""
    sign = "+" if n > 0 else ""
    n = abs(n)
    if n >= 1_000_000:
        return f"{sign}{n/1_000_000:.2f}M"
    elif n >= 1_000:
        return f"{sign}{n/1_000:.1f}K"
    return f"{sign}{n}"


def format_dps(dps: float) -> str:
    """格式化DPS"""
    if dps >= 1_000_000:
        return f"{dps/1_000_000:.2f}M"
    elif dps >= 1_000:
        return f"{dps/1_000:.1f}K"
    return f"{dps:.0f}"


def format_wcl_number(n: int) -> str:
    """WCL 风格数字格式化（不带符号，如 680.9k, 13.1k）"""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}k"
    return str(n)


def format_wcl_signed(n: int) -> str:
    """WCL 风格数字格式化（带正负号，如 +266.9k, -13.1k）"""
    sign = "+" if n > 0 else "-" if n < 0 else ""
    n = abs(n)
    if n >= 1_000_000:
        return f"{sign}{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{sign}{n/1_000:.1f}k"
    return f"{sign}{n}"


def build_wcl_damage_data(entries, casts_dict, total_damage, duration_sec):
    """构建 WCL 风格的伤害数据表"""
    merged = {}
    for entry in entries:
        name = translate_name(entry.get("name", "Unknown"))
        if name == "Unknown" or not name:
            continue
        total = entry.get("total", 0) or entry.get("totalReduced", 0)
        hits = entry.get("hitCount", 0)
        crits = entry.get("critHitCount", 0) + entry.get("critTickCount", 0)
        ticks = entry.get("tickCount", 0)
        misses = entry.get("missCount", 0)
        uptime = entry.get("uptime", 0)  # DOT 持续时间(ms)
        uses = entry.get("uses", 0)  # DOT 施放次数

        if name in merged:
            m = merged[name]
            m["total"] += total
            m["hits"] += hits
            m["crits"] += crits
            m["ticks"] += ticks
            m["misses"] += misses
            m["uptime"] += uptime
            # uses 是施法次数，重复条目（中英双语）代表的是同一次施法，不应累加
            if uses > m["uses"]:
                m["uses"] = uses
        else:
            merged[name] = {
                "total": total, "hits": hits, "crits": crits,
                "ticks": ticks, "misses": misses, "uptime": uptime, "uses": uses
            }

    result = []
    for name, data in merged.items():
        total = data["total"]
        hits = data["hits"]
        ticks = data["ticks"]
        crits = data["crits"]
        total_hits = hits + ticks
        pct = (total / total_damage) * 100 if total_damage > 0 else 0

        # 施法次数：优先从 casts 数据获取，DOT 也可用 uses
        cast_count = casts_dict.get(name, {}).get("count", 0)
        if cast_count == 0 and data["uses"] > 0:
            cast_count = data["uses"]

        avg_cast = total / max(cast_count, 1) if cast_count > 0 else 0
        avg_hit = total / max(total_hits, 1) if total_hits > 0 else 0
        crit_rate = (crits / max(total_hits, 1)) * 100 if total_hits > 0 else 0
        uptime_pct = (data["uptime"] / (duration_sec * 1000)) * 100 if duration_sec > 0 else 0
        dps = total / max(duration_sec, 1)

        result.append({
            "name": name, "pct": pct, "total": total,
            "casts": cast_count, "avg_cast": avg_cast,
            "hits": total_hits, "avg_hit": avg_hit,
            "crit_rate": crit_rate, "uptime": uptime_pct, "dps": dps,
        })

    result.sort(key=lambda x: x["total"], reverse=True)
    return result


def build_combined_damage_data(entries_a, casts_a, total_a, duration_a,
                                entries_b, casts_b, total_b, duration_b):
    """合并两次战斗的伤害数据，按最大总伤害倒序排列"""
    dmg_a = build_wcl_damage_data(entries_a, casts_a, total_a, duration_a)
    dmg_b = build_wcl_damage_data(entries_b, casts_b, total_b, duration_b)

    # 建立索引
    dict_a = {row["name"]: row for row in dmg_a}
    dict_b = {row["name"]: row for row in dmg_b}
    all_names = set(dict_a.keys()) | set(dict_b.keys())

    combined = []
    for name in all_names:
        a = dict_a.get(name)
        b = dict_b.get(name)
        max_total = max(a["total"] if a else 0, b["total"] if b else 0)

        def diff(val_b, val_a, fmt="number"):
            """计算差值并格式化"""
            if a is None or b is None:
                return None, "neutral"
            delta = val_b - val_a
            cls = "positive" if delta > 0 else "negative" if delta < 0 else "neutral"
            if fmt == "pct":
                return f"{delta:+.1f}%", cls
            elif fmt == "rate":
                return f"{delta:+.1f}%", cls
            elif fmt == "number":
                return format_wcl_signed(int(delta)), cls
            elif fmt == "wcl_number":
                return format_wcl_signed(int(delta)), cls
            return str(delta), cls

        def get_val(row, key, default=0):
            return row.get(key, default) if row else default

        row_a = a or {}
        row_b = b or {}

        combined.append({
            "name": name,
            "max_total": max_total,
            "a": a,
            "b": b,
            "diff": {
                "total": diff(get_val(row_b, "total"), get_val(row_a, "total"), "wcl_number"),
                "pct": diff(get_val(row_b, "pct"), get_val(row_a, "pct"), "pct"),
                "casts": diff(get_val(row_b, "casts"), get_val(row_a, "casts")),
                "avg_cast": diff(get_val(row_b, "avg_cast"), get_val(row_a, "avg_cast"), "wcl_number"),
                "hits": diff(get_val(row_b, "hits"), get_val(row_a, "hits")),
                "avg_hit": diff(get_val(row_b, "avg_hit"), get_val(row_a, "avg_hit"), "wcl_number"),
                "crit_rate": diff(get_val(row_b, "crit_rate"), get_val(row_a, "crit_rate"), "rate"),
                "uptime": diff(get_val(row_b, "uptime"), get_val(row_a, "uptime"), "pct"),
                "dps": diff(get_val(row_b, "dps"), get_val(row_a, "dps"), "wcl_number"),
            }
        })

    combined.sort(key=lambda x: x["max_total"], reverse=True)
    return combined


class TextReportGenerator:
    """文本报告生成器"""
    
    def generate(self, comparison: Dict, analyzer) -> str:
        """生成文本对比报告"""
        lines = []
        fa = comparison["fight_a"]
        fb = comparison["fight_b"]
        players = comparison["players"]
        is_single = len(players) == 1
        
        # 标题
        lines.append("=" * 80)
        if is_single and players:
            p = players[0]
            marker = "🔺" if p.dps_delta > 0 else "🔻" if p.dps_delta < 0 else "➖"
            lines.append(f"WCL 玩家对比报告 - {p.name} ({p.spec}) {marker} {p.dps_delta_pct:+.1f}%")
        else:
            lines.append("WCL 战斗记录对比分析报告")
        lines.append("=" * 80)
        lines.append("")
        
        # 警告信息
        warnings = comparison.get("warnings", [])
        if warnings:
            lines.append("⚠️ 警告:")
            for w in warnings:
                lines.append(f"  {w}")
            lines.append("")
        
        # 战斗信息
        lines.append("【战斗信息】")
        lines.append(f"  {'':25} {'战斗A':>25} {'战斗B':>25}")
        lines.append(f"  {'报告代码':25} {fa['report']:>25} {fb['report']:>25}")
        lines.append(f"  {'战斗ID':25} {fa['id']:>25} {fb['id']:>25}")
        lines.append(f"  {'Boss':25} {fa['name']:>25} {fb['name']:>25}")
        lines.append(f"  {'击杀':25} {'✓ 击杀' if fa['kill'] else '✗ 未击杀':>25} {'✓ 击杀' if fb['kill'] else '✗ 未击杀':>25}")
        lines.append(f"  {'战斗时长':25} {fa['duration_sec']:>24.1f}s {fb['duration_sec']:>24.1f}s")
        lines.append("")
        
        # 单人模式：显示更突出的核心摘要
        if is_single and players:
            p = players[0]
            active_pct_a = (p.active_time_a / max(fa['duration_sec'] * 1000, 1)) * 100
            active_pct_b = (p.active_time_b / max(fb['duration_sec'] * 1000, 1)) * 100
            
            lines.append("【核心指标】")
            lines.append(f"  {'':20} {'战斗A':>15} {'战斗B':>15} {'变化':>12}")
            lines.append(f"  {'DPS':20} {format_dps(p.dps_a):>15} {format_dps(p.dps_b):>15} {p.dps_delta:>+11.0f}")
            lines.append(f"  {'总伤害':20} {format_number(p.damage_a):>15} {format_number(p.damage_b):>15} {format_number(p.damage_b - p.damage_a):>12}")
            lines.append(f"  {'装等':20} {p.ilvl_a:>15.1f} {p.ilvl_b:>15.1f} {p.ilvl_delta:>+11.1f}")
            lines.append(f"  {'活跃度':20} {active_pct_a:>14.1f}% {active_pct_b:>14.1f}% {active_pct_b - active_pct_a:>+10.1f}%")
            lines.append("")
        else:
            # 多人模式：显示概览表格
            lines.append("【DPS 变化概览】")
            lines.append(f"  {'玩家':15} {'职业':12} {'装等':>6} {'战斗A DPS':>12} {'战斗B DPS':>12} {'变化':>10} {'变化%':>8}")
            lines.append("  " + "-" * 77)
            
            for p in players:
                delta_str = f"{p.dps_delta:+.0f}"
                delta_pct_str = f"{p.dps_delta_pct:+.1f}%"
                marker = "🔺" if p.dps_delta > 0 else "🔻" if p.dps_delta < 0 else "➖"
                lines.append(
                    f"  {p.name:15} {p.spec:12} {max(p.ilvl_a, p.ilvl_b):>6.1f} "
                    f"{format_dps(p.dps_a):>12} {format_dps(p.dps_b):>12} "
                    f"{marker}{delta_str:>8} {delta_pct_str:>8}"
                )
            lines.append("")
        
        # 详细分析（每个玩家）
        for p in players:
            if abs(p.dps_delta_pct) < 0.5:  # 跳过变化太小的
                continue
                
            lines.append("-" * 80)
            lines.append(f"【{p.name} | {p.spec}】DPS: {format_dps(p.dps_a)} → {format_dps(p.dps_b)} ({p.dps_delta_pct:+.1f}%)")
            lines.append("-" * 80)
            
            # 装等变化
            if abs(p.ilvl_delta) >= 1:
                lines.append(f"  装等变化: {p.ilvl_a:.1f} → {p.ilvl_b:.1f} ({p.ilvl_delta:+.1f})")
            
            # 活跃度
            active_pct_a = (p.active_time_a / max(fa['duration_sec'] * 1000, 1)) * 100
            active_pct_b = (p.active_time_b / max(fb['duration_sec'] * 1000, 1)) * 100
            if abs(active_pct_a - active_pct_b) > 2:
                lines.append(f"  活跃度: {active_pct_a:.1f}% → {active_pct_b:.1f}%")
            
            # 施法分析
            cast_analysis = analyzer.analyze_casts(p)
            if cast_analysis["abilities"]:
                lines.append("")
                lines.append("  施法变化:")
                lines.append(f"    {'技能':20} {'次数A':>8} {'次数B':>8} {'变化':>8} {'CPM-A':>8} {'CPM-B':>8} {'变化':>8}")
                for abl in cast_analysis["abilities"][:8]:  # 前8个
                    marker = "▲" if abl["count_delta"] > 0 else "▼"
                    lines.append(
                        f"    {abl['ability']:20} {abl['count_a']:>8} {abl['count_b']:>8} "
                        f"{marker}{abl['count_delta']:+7d} {abl['cpm_a']:>8.1f} {abl['cpm_b']:>8.1f} "
                        f"{abl['cpm_delta']:>+.1f}"
                    )
            
            # Buff分析
            buff_analysis = analyzer.analyze_buffs(p)
            if buff_analysis["buffs"]:
                lines.append("")
                lines.append("  增益覆盖变化:")
                lines.append(f"    {'Buff':25} {'覆盖A':>8} {'覆盖B':>8} {'变化':>8}")
                for buff in buff_analysis["buffs"][:6]:
                    marker = "▲" if buff["uptime_delta"] > 0 else "▼"
                    lines.append(
                        f"    {buff['name']:25} {buff['uptime_a']:>7.1f}% {buff['uptime_b']:>7.1f}% "
                        f"{marker}{buff['uptime_delta']:>+.1f}%"
                    )
            
            # 伤害构成分析
            dmg_analysis = analyzer.analyze_damage_breakdown(p)
            if dmg_analysis["abilities"]:
                lines.append("")
                lines.append("  伤害构成变化:")
                lines.append(f"    {'技能':18} {'占比':>6} {'总伤变化':>10} {'均伤A':>8} {'均伤B':>8} {'变化':>8} {'暴击A':>6} {'暴击B':>6}")
                lines.append("    " + "-" * 82)
                for abl in dmg_analysis["abilities"][:10]:
                    if abs(abl["pct_delta"]) < 0.3 and abs(abl["damage_delta"]) < p.damage_a * 0.005:
                        continue
                    marker = "▲" if abl["pct_delta"] > 0 else "▼"
                    avg_marker = "▲" if abl["avg_hit_delta"] > 0 else "▼"
                    lines.append(
                        f"    {abl['ability']:18} "
                        f"{marker}{abl['pct_delta']:>+4.1f}% "
                        f"{format_number(abl['damage_delta']):>10} "
                        f"{format_number(abl['avg_hit_a']):>8} "
                        f"{format_number(abl['avg_hit_b']):>8} "
                        f"{avg_marker}{abl['avg_hit_delta']:>+6.0f} "
                        f"{abl['crit_rate_a']:>5.1f}% {abl['crit_rate_b']:>5.1f}%"
                    )
            
            lines.append("")
        
        lines.append("=" * 80)
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        
        return "\n".join(lines)


class HtmlReportGenerator:
    """HTML报告生成器（带表格高亮）"""
    
    def generate(self, comparison: Dict, analyzer) -> str:
        """生成HTML对比报告"""
        fa = comparison["fight_a"]
        fb = comparison["fight_b"]
        
        def cell_class(val):
            if val > 0:
                return "positive"
            elif val < 0:
                return "negative"
            return "neutral"
        
        warnings = comparison.get("warnings", [])
        if warnings:
            warning_items = "".join(f"<div>{w}</div>" for w in warnings)
            warnings_html = f"""
        <div class="warning-banner">
            <div class="warning-title">⚠️ 注意</div>
            {warning_items}
        </div>"""
        else:
            warnings_html = ""
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>WCL 战斗对比 - {translate_name(fa['name'])}</title>
    <style>
        :root {{
            --bg: #0d0d12;
            --bg-card: #18181f;
            --bg-table: #1f2330;
            --text: #f8d466;
            --text-light: #ece5d8;
            --positive: #1eff00;
            --negative: #ff2020;
            --neutral: #9d9d9d;
            --border: #5a4a2f;
            --gold: #f8d466;
            --gold-dark: #8a6e2f;
        }}
        body {{
            font-family: 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
            background:
                radial-gradient(circle at 15% 20%, rgba(90, 74, 47, 0.2) 0%, transparent 35%),
                radial-gradient(circle at 85% 80%, rgba(90, 74, 47, 0.15) 0%, transparent 35%),
                linear-gradient(180deg, #0d0d12 0%, #15151c 50%, #0d0d12 100%);
            color: var(--text-light);
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1, h2, h3 {{
            font-family: 'Cinzel', 'Georgia', 'Times New Roman', 'Microsoft YaHei', 'PingFang SC', serif;
            color: var(--gold);
            text-shadow: 0 2px 10px rgba(248, 212, 102, 0.35), 0 0 2px rgba(0, 0, 0, 0.8);
            letter-spacing: 1px;
        }}
        h1 {{ text-align: center; margin-bottom: 10px; }}
        h2 {{
            border-bottom: 1px solid var(--gold-dark);
            padding-bottom: 8px;
            margin-top: 30px;
        }}
        h3 {{ margin-top: 25px; }}
        
        .fight-info {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .fight-card {{
            background: linear-gradient(145deg, rgba(24, 24, 31, 0.95) 0%, rgba(18, 18, 24, 0.95) 100%);
            border-radius: 8px;
            padding: 15px;
            border: 1px solid var(--border);
            box-shadow:
                inset 0 1px 0 rgba(248, 212, 102, 0.06),
                0 4px 12px rgba(0, 0, 0, 0.5);
        }}
        .fight-card.a {{ border-left: 4px solid #60a5fa; border-color: var(--border); border-left-color: #60a5fa; }}
        .fight-card.b {{ border-left: 4px solid #ff8080; border-color: var(--border); border-left-color: #ff8080; }}
        .fight-card label {{ color: var(--neutral); font-size: 0.85em; }}
        .fight-card .value {{ font-size: 1.2em; font-weight: bold; color: var(--text-light); }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            background: linear-gradient(180deg, rgba(24, 24, 31, 0.9) 0%, rgba(18, 18, 24, 0.9) 100%);
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        }}
        th {{
            background: linear-gradient(180deg, #2a2e3c 0%, #1f2330 100%);
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: var(--gold);
            border-bottom: 1px solid var(--border);
        }}
        td {{ padding: 10px 12px; border-bottom: 1px solid rgba(90, 74, 47, 0.4); }}
        tr:hover {{ background: rgba(248, 212, 102, 0.05); }}
        
        .positive {{ color: var(--positive); font-weight: bold; text-shadow: 0 0 6px rgba(30, 255, 0, 0.2); }}
        .negative {{ color: var(--negative); font-weight: bold; text-shadow: 0 0 6px rgba(255, 32, 32, 0.2); }}
        .neutral {{ color: var(--neutral); }}
        
        /* 伤害表格样式 */
        .damage-table td, .damage-table th {{ padding: 6px 10px; font-size: 0.9em; }}
        .damage-table .diff-row td {{ border-bottom: none; padding-bottom: 2px; background: rgba(90, 74, 47, 0.25); font-weight: 600; }}
        .damage-table .row-a td {{ border-bottom: 1px dashed rgba(90, 74, 47, 0.5); padding-top: 2px; padding-bottom: 2px; background: rgba(0, 0, 0, 0.15); }}
        .damage-table .row-b td {{ border-bottom: 2px solid rgba(90, 74, 47, 0.5); padding-top: 2px; padding-bottom: 6px; background: rgba(0, 0, 0, 0.25); }}
        .damage-table td:first-child {{ min-width: 100px; }}
        
        .player-section {{
            background: linear-gradient(145deg, rgba(24, 24, 31, 0.95) 0%, rgba(18, 18, 24, 0.95) 100%);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            border: 1px solid var(--border);
            box-shadow:
                inset 0 1px 0 rgba(248, 212, 102, 0.06),
                0 6px 18px rgba(0, 0, 0, 0.5);
            position: relative;
        }}
        .player-section::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 15px;
            right: 15px;
            height: 2px;
            background: linear-gradient(90deg, transparent 0%, var(--gold) 50%, transparent 100%);
            opacity: 0.5;
        }}
        .player-section::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 15px;
            right: 15px;
            height: 2px;
            background: linear-gradient(90deg, transparent 0%, var(--gold) 50%, transparent 100%);
            opacity: 0.3;
        }}
        .player-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .dps-badge {{
            font-size: 1.5em;
            font-weight: bold;
        }}
        .dps-delta {{ font-size: 0.8em; margin-left: 10px; }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .stats-box {{
            background: rgba(0, 0, 0, 0.25);
            border-radius: 8px;
            padding: 15px;
            border: 1px solid rgba(90, 74, 47, 0.4);
        }}
        .stats-box h4 {{ margin-top: 0; color: #8ec5ff; }}
        
        .tag {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            margin-left: 5px;
            border: 1px solid;
        }}
        .tag.kill {{ background: rgba(30, 255, 0, 0.1); color: var(--positive); border-color: rgba(30, 255, 0, 0.3); }}
        .tag.wipe {{ background: rgba(255, 32, 32, 0.1); color: var(--negative); border-color: rgba(255, 32, 32, 0.3); }}
        
        .footer {{
            text-align: center;
            color: var(--neutral);
            margin-top: 40px;
            padding: 20px;
            font-size: 0.85em;
            border-top: 1px solid var(--border);
        }}
        
        /* 增益/减益时间轴 */
        .aura-section {{ margin-top: 15px; }}
        .aura-toggle {{
            width: 100%;
            padding: 12px 18px;
            background: linear-gradient(180deg, #2a2e3c 0%, #1f2330 100%);
            color: var(--gold);
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }}
        .aura-toggle:hover {{
            background: linear-gradient(180deg, #35394c 0%, #2a2e3c 100%);
            border-color: var(--gold-dark);
        }}
        .aura-toggle .toggle-icon {{ font-size: 0.8em; transition: transform 0.2s; }}
        .aura-content {{
            overflow: hidden;
            transition: max-height 0.4s ease, opacity 0.3s ease;
            max-height: 3000px;
            opacity: 1;
        }}
        .aura-content.collapsed {{
            max-height: 0;
            opacity: 0;
        }}
        .aura-category {{ margin-top: 18px; }}
        .aura-category h5 {{
            color: #8ec5ff;
            margin: 0 0 10px 0;
            padding-bottom: 6px;
            border-bottom: 1px solid rgba(90, 74, 47, 0.5);
            font-size: 0.95em;
        }}
        .aura-row {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 5px 0;
            border-bottom: 1px solid rgba(90, 74, 47, 0.3);
        }}
        .aura-name {{
            width: 130px;
            font-size: 0.85em;
            flex-shrink: 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .aura-uptime {{
            width: 90px;
            text-align: center;
            font-size: 0.8em;
            color: var(--neutral);
            flex-shrink: 0;
            line-height: 1.3;
        }}
        .aura-uptime .upt-a {{ color: #ff7b00; }}
        .aura-uptime .upt-b {{ color: #00e5c9; }}
        .aura-timeline {{
            flex: 1;
            min-width: 140px;
        }}
        .timeline-line {{
            height: 8px;
            background: rgba(0,0,0,0.35);
            border-radius: 2px;
            position: relative;
            margin: 1px 0;
            overflow: hidden;
            border: 1px solid rgba(90, 74, 47, 0.3);
        }}
        .timeline-band {{
            position: absolute;
            height: 100%;
            border-radius: 1px;
            min-width: 2px;
        }}
        .line-a .timeline-band {{ background: linear-gradient(180deg, rgba(255,123,0,0.95) 0%, rgba(255,42,0,0.85) 100%); box-shadow: 0 0 6px rgba(255,82,0,0.6); }}
        .line-b .timeline-band {{ background: linear-gradient(180deg, rgba(0,229,201,0.90) 0%, rgba(0,102,255,0.85) 100%), repeating-linear-gradient(45deg, rgba(255,255,255,0.12) 0px, rgba(255,255,255,0.12) 2px, transparent 2px, transparent 6px); box-shadow: 0 0 6px rgba(0,180,220,0.55); }}
        .aura-uses {{
            width: 60px;
            text-align: right;
            font-size: 0.8em;
            color: var(--neutral);
            flex-shrink: 0;
        }}
        .aura-legend {{
            display: flex;
            gap: 16px;
            font-size: 0.8em;
            color: var(--neutral);
            margin-bottom: 8px;
            justify-content: flex-end;
        }}
        .aura-legend span {{ display: flex; align-items: center; gap: 4px; }}
        .legend-dot {{ width: 10px; height: 10px; border-radius: 2px; display: inline-block; }}
        .legend-a {{ background: linear-gradient(180deg, rgba(255,123,0,0.95) 0%, rgba(255,42,0,0.85) 100%); }}
        .legend-b {{ background: linear-gradient(180deg, rgba(0,229,201,0.90) 0%, rgba(0,102,255,0.85) 100%), repeating-linear-gradient(45deg, rgba(255,255,255,0.12) 0px, rgba(255,255,255,0.12) 2px, transparent 2px, transparent 6px); }}
        
        /* 时间轴结束标记（带箭头） */
        .timeline-end-marker {{
            position: absolute;
            top: 0;
            height: 100%;
            width: 3px;
            border-radius: 2px;
            z-index: 3;
            cursor: help;
        }}
        .timeline-end-marker::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -3px;
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 5px solid;
        }}
        .line-a .timeline-end-marker {{
            background: rgba(255, 82, 0, 0.95);
            box-shadow: 0 0 5px rgba(255, 82, 0, 0.7);
        }}
        .line-a .timeline-end-marker::before {{ border-bottom-color: rgba(255, 82, 0, 0.95); }}
        .line-b .timeline-end-marker {{
            background: rgba(0, 180, 220, 0.95);
            box-shadow: 0 0 5px rgba(0, 180, 220, 0.7);
        }}
        .line-b .timeline-end-marker::before {{ border-bottom-color: rgba(0, 180, 220, 0.95); }}
        
        /* 未覆盖区间 */
        .timeline-gap {{
            position: absolute;
            height: 100%;
            border-radius: 1px;
            background: transparent;
            cursor: help;
            z-index: 1;
        }}
        .timeline-gap:hover {{ background: rgba(255, 255, 255, 0.08); }}
        
        /* 警告横幅 */
        .warning-banner {{
            background: rgba(90, 20, 20, 0.25);
            border: 1px solid rgba(255, 80, 80, 0.4);
            border-radius: 8px;
            padding: 14px 18px;
            margin: 16px 0 24px 0;
            color: #ffcccc;
            font-size: 0.95em;
            box-shadow: 0 0 12px rgba(255, 50, 50, 0.15);
        }}
        .warning-banner .warning-title {{
            font-weight: bold;
            margin-bottom: 6px;
            color: #ff9999;
            text-shadow: 0 0 6px rgba(255, 80, 80, 0.3);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚔️ WCL 战斗记录对比分析</h1>
        
        {warnings_html}
        
        <h2>📊 DPS 变化概览</h2>
        <table>
            <tr>
                <th>战斗记录</th>
                <th>Boss名称</th>
                <th>玩家名称</th>
                <th>职业/专精</th>
                <th>装等</th>
                <th>击杀时长</th>
                <th>总DPS</th>
                <th>总CPM</th>
            </tr>
"""
        
        if not comparison["players"]:
            html += """
            <tr><td colspan="8" style="text-align:center; color:#94a3b8; padding:20px;">
                未找到共同玩家数据。可能原因：<br>
                1. 输入的玩家名字和 WCL 记录中的名字不匹配<br>
                2. 该玩家未参与其中一次战斗<br>
                3. API 数据获取失败<br>
                请检查控制台输出获取详细调试信息。
            </td></tr>
"""
        
        for p in comparison["players"]:
            cast_analysis = analyzer.analyze_casts(p)
            total_casts_a = cast_analysis["total_casts_a"]
            total_casts_b = cast_analysis["total_casts_b"]
            cpm_a = total_casts_a / (fa['duration_sec'] / 60) if fa['duration_sec'] > 0 else 0
            cpm_b = total_casts_b / (fb['duration_sec'] / 60) if fb['duration_sec'] > 0 else 0
            cpm_delta = cpm_b - cpm_a
            cls = cell_class(p.dps_delta)
            cls_cpm = cell_class(cpm_delta)

            # 时长变化：减少=绿色(好)，增加=红色(坏)
            duration_delta = fb['duration_sec'] - fa['duration_sec']
            cls_duration = "positive" if duration_delta < 0 else "negative" if duration_delta > 0 else "neutral"

            # 装等变化
            ilvl_delta = p.ilvl_b - p.ilvl_a
            cls_ilvl = cell_class(ilvl_delta)

            spec_name = translate_name(p.spec) + translate_name(p.class_name)

            name_a = fa.get('player_name', p.name)
            name_b = fb.get('player_name', p.name)

            # 战斗A行
            html += f"""
            <tr>
                <td><span style="color:#60a5fa">●</span> {name_a}</td>
                <td>{translate_name(fa['name'])}</td>
                <td><strong>{name_a}</strong></td>
                <td>{spec_name}</td>
                <td>{p.ilvl_a:.1f}</td>
                <td>{fa['duration_sec']:.0f}s</td>
                <td>{format_dps(p.dps_a)}</td>
                <td>{cpm_a:.1f}</td>
            </tr>"""
            # 战斗B行
            html += f"""
            <tr>
                <td><span style="color:var(--text)">●</span> {name_b}</td>
                <td>{translate_name(fb['name'])}</td>
                <td><strong>{name_b}</strong></td>
                <td>{spec_name}</td>
                <td class="{cls_ilvl}">{p.ilvl_b:.1f} <span style="font-size:0.85em">({ilvl_delta:+.1f})</span></td>
                <td class="{cls_duration}">{fb['duration_sec']:.0f}s <span style="font-size:0.85em">({duration_delta:+.0f}s)</span></td>
                <td class="{cls}">{format_dps(p.dps_b)} <span style="font-size:0.85em">({p.dps_delta:+.0f})</span></td>
                <td class="{cls_cpm}">{cpm_b:.1f} <span style="font-size:0.85em">({cpm_delta:+.1f})</span></td>
            </tr>"""
        
        html += "</table>"
        
        # 伤害构成表（放在概览下面，针对所有相关玩家）
        for p in comparison["players"]:
            cast_analysis = analyzer.analyze_casts(p)
            casts_a_dict = {a["ability"]: {"count": a["count_a"]} for a in cast_analysis["abilities"]}
            casts_b_dict = {a["ability"]: {"count": a["count_b"]} for a in cast_analysis["abilities"]}

            combined = build_combined_damage_data(
                p.damage_breakdown_a, casts_a_dict, p.damage_a, fa['duration_sec'],
                p.damage_breakdown_b, casts_b_dict, p.damage_b, fb['duration_sec']
            )

            dmg_title = f"⚔️ {name_a} vs {name_b} 伤害构成" if name_a != name_b else "⚔️ 伤害构成"
            if combined:
                html += f'''
        <div class="player-section">
            <div class="aura-section">
                <button class="aura-toggle" onclick="toggleAura(this)">
                    <span>{dmg_title}</span>
                    <span class="toggle-icon">▼</span>
                </button>
                <div class="aura-content">
                    <div class="stats-box" style="overflow-x: auto;">
                        <table class="damage-table">
                            <tr>
                                <th>技能</th>
                                <th>伤害</th>
                                <th>施法次数</th>
                                <th>单次伤害</th>
                                <th>跳数</th>
                                <th>每跳伤害</th>
                                <th>暴击率</th>
                                <th>覆盖</th>
                                <th>DPS</th>
                            </tr>
'''
                for item in combined[:12]:
                    name = translate_name(item["name"])
                    a = item.get("a")
                    b = item.get("b")
                    diff = item["diff"]

                    def fmt(row, key, pct=False, uptime=False, dps=False):
                        if row is None:
                            return "-"
                        val = row.get(key, 0)
                        if dps:
                            return f"{val:.0f}"
                        if pct:
                            return f"{val:.1f}%"
                        if uptime:
                            return f"{val:.1f}%" if val > 0 else "-"
                        if key in ("casts", "hits"):
                            return str(int(val)) if val > 0 else "-"
                        return format_wcl_number(int(val))

                    def cell(val, cls):
                        if val is None:
                            return '<td class="neutral">-</td>'
                        return f'<td class="{cls}">{val}</td>'

                    def dmg_cell(row):
                        if row is None:
                            return "-"
                        return f'{fmt(row, "total")} <span style="color:var(--neutral)">({fmt(row, "pct", pct=True)})</span>'

                    # 第1行：变化
                    html += f"""
                    <tr class="diff-row">
                        <td><strong>{name}</strong></td>
                        {cell(diff["total"][0] if diff["total"] else None, diff["total"][1] if diff["total"] else "neutral")}
                        {cell(diff["casts"][0] if diff["casts"] else None, diff["casts"][1] if diff["casts"] else "neutral")}
                        {cell(diff["avg_cast"][0] if diff["avg_cast"] else None, diff["avg_cast"][1] if diff["avg_cast"] else "neutral")}
                        {cell(diff["hits"][0] if diff["hits"] else None, diff["hits"][1] if diff["hits"] else "neutral")}
                        {cell(diff["avg_hit"][0] if diff["avg_hit"] else None, diff["avg_hit"][1] if diff["avg_hit"] else "neutral")}
                        {cell(diff["crit_rate"][0] if diff["crit_rate"] else None, diff["crit_rate"][1] if diff["crit_rate"] else "neutral")}
                        {cell(diff["uptime"][0] if diff["uptime"] else None, diff["uptime"][1] if diff["uptime"] else "neutral")}
                        {cell(diff["dps"][0] if diff["dps"] else None, diff["dps"][1] if diff["dps"] else "neutral")}
                    </tr>"""

                    # 第2行：战斗A
                    html += f"""
                    <tr class="row-a">
                        <td><span style="color:var(--neutral)">{name_a}</span></td>
                        <td>{dmg_cell(a)}</td>
                        <td>{fmt(a, 'casts')}</td>
                        <td>{fmt(a, 'avg_cast')}</td>
                        <td>{fmt(a, 'hits')}</td>
                        <td>{fmt(a, 'avg_hit')}</td>
                        <td>{fmt(a, 'crit_rate', pct=True)}</td>
                        <td>{fmt(a, 'uptime', uptime=True)}</td>
                        <td>{fmt(a, 'dps', dps=True)}</td>
                    </tr>"""

                    # 第3行：战斗B
                    html += f"""
                    <tr class="row-b">
                        <td><span style="color:var(--neutral)">{name_b}</span></td>
                        <td>{dmg_cell(b)}</td>
                        <td>{fmt(b, 'casts')}</td>
                        <td>{fmt(b, 'avg_cast')}</td>
                        <td>{fmt(b, 'hits')}</td>
                        <td>{fmt(b, 'avg_hit')}</td>
                        <td>{fmt(b, 'crit_rate', pct=True)}</td>
                        <td>{fmt(b, 'uptime', uptime=True)}</td>
                        <td>{fmt(b, 'dps', dps=True)}</td>
                    </tr>"""

                html += '''
                        </table>
                    </div>
                </div>
            </div>
        </div>'''
        
        # 增益模块直接跟在伤害构成后面，不再插入姓名板
        
        # 增益/减益覆盖模块（独立折叠区域）
        all_aura_data = []
        for p in comparison["players"]:
            aura = analyzer.analyze_buffs(p)
            if aura["buffs"] or aura["debuffs"]:
                all_aura_data.append((p, aura))
        
        if all_aura_data:
            dur_a = fa['duration_sec']
            dur_b = fb['duration_sec']
            max_dur = max(dur_a, dur_b)
            
            def merge_intervals(intervals):
                """合并重叠区间"""
                if not intervals:
                    return []
                sorted_ints = sorted(intervals, key=lambda x: x[0])
                merged = [list(sorted_ints[0])]
                for s, e in sorted_ints[1:]:
                    if s <= merged[-1][1]:
                        merged[-1][1] = max(merged[-1][1], e)
                    else:
                        merged.append([s, e])
                return merged

            def calc_gaps(intervals, total=100.0):
                """计算未覆盖区间"""
                merged = merge_intervals(intervals)
                gaps = []
                if not merged:
                    gaps.append((0, total))
                else:
                    if merged[0][0] > 0:
                        gaps.append((0, merged[0][0]))
                    for i in range(len(merged) - 1):
                        if merged[i][1] < merged[i+1][0]:
                            gaps.append((merged[i][1], merged[i+1][0]))
                    if merged[-1][1] < total:
                        gaps.append((merged[-1][1], total))
                return gaps

            def render_timeline(bands, dur_sec, end_pct, label="", band_bg=None, glow=None):
                """渲染完整时间轴：bands + gaps + 结束标记"""
                parts = []
                # 覆盖区间
                for s_pct, e_pct in bands:
                    s_unified = s_pct * dur_sec / max_dur
                    e_unified = e_pct * dur_sec / max_dur
                    w = max(0.3, e_unified - s_unified)
                    s_sec = s_pct * dur_sec / 100
                    e_sec = e_pct * dur_sec / 100
                    d_sec = e_sec - s_sec
                    title = f"{s_sec:.1f}s ~ {e_sec:.1f}s (持续{d_sec:.1f}s)"
                    style = f"left:{max(0, s_unified):.1f}%;width:{w:.1f}%;"
                    if band_bg:
                        style += f"background:{band_bg};"
                    if glow:
                        style += f"box-shadow:{glow};"
                    parts.append(f'<div class="timeline-band" style="{style}" title="{title}"></div>')
                
                # 未覆盖区间
                gaps = calc_gaps(bands, 100.0)
                for s_pct, e_pct in gaps:
                    s_unified = s_pct * dur_sec / max_dur
                    e_unified = e_pct * dur_sec / max_dur
                    w = max(0.3, e_unified - s_unified)
                    s_sec = s_pct * dur_sec / 100
                    e_sec = e_pct * dur_sec / 100
                    d_sec = e_sec - s_sec
                    title = f"未覆盖: {s_sec:.1f}s ~ {e_sec:.1f}s (空档{d_sec:.1f}s)"
                    parts.append(f'<div class="timeline-gap" style="left:{max(0, s_unified):.1f}%;width:{w:.1f}%" title="{title}"></div>')
                
                # 结束标记（带箭头）
                if end_pct < 100:
                    title = f"{label} 战斗结束: {dur_sec:.1f}s"
                    parts.append(f'<div class="timeline-end-marker" style="left:{end_pct:.1f}%" title="{title}"></div>')
                
                return "".join(parts)
            
            end_a_pct = dur_a / max_dur * 100
            end_b_pct = dur_b / max_dur * 100
            
            aura_label_a = translate_name(fa.get('name', '战斗A'))
            aura_label_b = translate_name(fb.get('name', '战斗B'))
            aura_title = f"📊 {aura_label_a} vs {aura_label_b} 增益与减益覆盖" if aura_label_a != aura_label_b else "📊 增益与减益覆盖"
            html += f'''
        <div class="player-section">
            <div class="aura-section">
                <button class="aura-toggle" onclick="toggleAura(this)">
                    <span>{aura_title}</span>
                    <span class="toggle-icon">▶</span>
                </button>
                <div class="aura-content collapsed">
                    <div class="aura-axis-info" style="font-size:0.8em;color:var(--neutral);text-align:right;margin-bottom:8px;">
                        时间轴基准: {max_dur:.0f}s &nbsp;|&nbsp; {aura_label_a}: {dur_a:.0f}s &nbsp;|&nbsp; {aura_label_b}: {dur_b:.0f}s
                    </div>
'''
            for p, aura in all_aura_data:
                band_bg_a = AURA_BAND_A_BG
                glow_a = AURA_BAND_A_GLOW
                text_a = AURA_TEXT_A
                band_bg_b = AURA_BAND_B_BG
                glow_b = AURA_BAND_B_GLOW
                text_b = AURA_TEXT_B
                # Buffs
                if aura["buffs"]:
                    html += f'''
                    <div class="aura-category">
                        <h5>增益 (Buffs)</h5>
                        <div class="aura-legend">
                            <span><span class="legend-dot" style="background:{band_bg_a};box-shadow:{glow_a};"></span> {fa.get('player_name', p.name)}</span>
                            <span><span class="legend-dot" style="background:{band_bg_b};box-shadow:{glow_b};"></span> {fb.get('player_name', p.name)}</span>
                        </div>
                        <div class="aura-list">
'''
                    for buff in aura["buffs"]:
                        name = translate_name(buff["name"])
                        uses_a = buff["uses_a"]
                        uses_b = buff["uses_b"]
                        bands_a = buff["bands_a"]
                        bands_b = buff["bands_b"]
                        
                        end_a_style = f"background: linear-gradient(to right, rgba(0,0,0,0.25) {end_a_pct:.1f}%, rgba(0,0,0,0.5) {end_a_pct:.1f}%);"
                        end_b_style = f"background: linear-gradient(to right, rgba(0,0,0,0.25) {end_b_pct:.1f}%, rgba(0,0,0,0.5) {end_b_pct:.1f}%);"
                        
                        uptime_a = buff["uptime_a"]
                        uptime_b = buff["uptime_b"]
                        html += f'''
                            <div class="aura-row">
                                <div class="aura-name" title="{name}">{name}</div>
                                <div class="aura-uptime">
                                    <span style="color:{text_a}">{uptime_a:.1f}%</span><br><span style="color:{text_b}">{uptime_b:.1f}%</span>
                                </div>
                                <div class="aura-timeline">
                                    <div class="timeline-line line-a" style="{end_a_style}">
                                        {render_timeline(bands_a, dur_a, end_a_pct, aura_label_a, band_bg_a, glow_a)}
                                    </div>
                                    <div class="timeline-line line-b" style="{end_b_style}">
                                        {render_timeline(bands_b, dur_b, end_b_pct, aura_label_b, band_bg_b, glow_b)}
                                    </div>
                                </div>
                                <div class="aura-uses">{uses_a} / {uses_b}</div>
                            </div>
'''
                    html += '''
                        </div>
                    </div>
'''
                # Debuffs
                if aura["debuffs"]:
                    html += f'''
                    <div class="aura-category">
                        <h5>减益 (Debuffs)</h5>
                        <div class="aura-legend">
                            <span><span class="legend-dot" style="background:{band_bg_a};box-shadow:{glow_a};"></span> {fa.get('player_name', p.name)}</span>
                            <span><span class="legend-dot" style="background:{band_bg_b};box-shadow:{glow_b};"></span> {fb.get('player_name', p.name)}</span>
                        </div>
                        <div class="aura-list">
'''
                    for debuff in aura["debuffs"]:
                        name = translate_name(debuff["name"])
                        uses_a = debuff["uses_a"]
                        uses_b = debuff["uses_b"]
                        bands_a = debuff["bands_a"]
                        bands_b = debuff["bands_b"]
                        uptime_a = debuff["uptime_a"]
                        uptime_b = debuff["uptime_b"]
                        
                        end_a_style = f"background: linear-gradient(to right, rgba(0,0,0,0.25) {end_a_pct:.1f}%, rgba(0,0,0,0.5) {end_a_pct:.1f}%);"
                        end_b_style = f"background: linear-gradient(to right, rgba(0,0,0,0.25) {end_b_pct:.1f}%, rgba(0,0,0,0.5) {end_b_pct:.1f}%);"
                        
                        html += f'''
                            <div class="aura-row">
                                <div class="aura-name" title="{name}">{name}</div>
                                <div class="aura-uptime">
                                    <span style="color:{text_a}">{uptime_a:.1f}%</span><br><span style="color:{text_b}">{uptime_b:.1f}%</span>
                                </div>
                                <div class="aura-timeline">
                                    <div class="timeline-line line-a" style="{end_a_style}">
                                        {render_timeline(bands_a, dur_a, end_a_pct, aura_label_a, band_bg_a, glow_a)}
                                    </div>
                                    <div class="timeline-line line-b" style="{end_b_style}">
                                        {render_timeline(bands_b, dur_b, end_b_pct, aura_label_b, band_bg_b, glow_b)}
                                    </div>
                                </div>
                                <div class="aura-uses">{uses_a} / {uses_b}</div>
                            </div>
'''
                    html += '''
                        </div>
                    </div>
'''
            html += '''
                </div>
            </div>
        </div>
'''
        
        html += f"""
        <div class="footer">
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | WCL Compare Tool</p>
        </div>
    </div>
    <script>
        function toggleAura(btn) {{
            const content = btn.nextElementSibling;
            const icon = btn.querySelector('.toggle-icon');
            content.classList.toggle('collapsed');
            icon.textContent = content.classList.contains('collapsed') ? '▶' : '▼';
        }}
    </script>
</body>
</html>"""
        
        return html
