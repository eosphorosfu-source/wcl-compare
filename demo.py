#!/usr/bin/env python3
"""
演示脚本 - 使用模拟数据展示对比报告效果
无需 WCL API Key 即可预览
"""
from analyzer import FightComparator, PlayerCompareData
from report_generator import TextReportGenerator, HtmlReportGenerator


def create_mock_comparison():
    """创建模拟对比数据"""
    comparison = {
        "fight_a": {
            "report": "DEMO1",
            "id": 1,
            "name": "史诗 安苏雷克女王",
            "kill": False,
            "duration_sec": 420.5,
            "difficulty": 5
        },
        "fight_b": {
            "report": "DEMO2",
            "id": 3,
            "name": "史诗 安苏雷克女王",
            "kill": True,
            "duration_sec": 385.2,
            "difficulty": 5
        },
        "players": []
    }
    
    # 玩家1: DPS大幅提升（改进手法）
    p1 = PlayerCompareData(
        name="火焰法师A",
        class_name="Mage",
        spec="Fire",
        dps_a=1250000,
        damage_a=525000000,
        ilvl_a=628.5,
        active_time_a=380000,
        damage_breakdown_a=[
            {"name": "炎爆术", "total": 180000000, "hitCount": 80, "critHitCount": 60, "tickCount": 0, "missCount": 0},
            {"name": "火球术", "total": 120000000, "hitCount": 150, "critHitCount": 90, "tickCount": 0, "missCount": 0},
            {"name": "燃烧", "total": 100000000, "hitCount": 40, "critHitCount": 40, "tickCount": 0, "missCount": 0},
            {"name": "烈焰风暴", "total": 80000000, "hitCount": 30, "critHitCount": 20, "tickCount": 0, "missCount": 0},
            {"name": "灼烧", "total": 45000000, "hitCount": 60, "critHitCount": 30, "tickCount": 0, "missCount": 0},
        ],
        casts_a=[
            {"ability": {"name": "炎爆术"}, "type": "cast", "timestamp": 0},
            {"ability": {"name": "火球术"}, "type": "cast", "timestamp": 1000},
            {"ability": {"name": "炎爆术"}, "type": "cast", "timestamp": 2000},
            {"ability": {"name": "火球术"}, "type": "cast", "timestamp": 3000},
            {"ability": {"name": "火球术"}, "type": "cast", "timestamp": 4000},
        ] * 30,  # 模拟多次施法
        buffs_a=[
            {"name": "燃烧", "uptime": 18.5, "uses": 4, "icon": ""},
            {"name": "热力迸发", "uptime": 72.3, "uses": 0, "icon": ""},
            {"name": "狂怒战鼓", "uptime": 25.0, "uses": 2, "icon": ""},
            {"name": "元素药水", "uptime": 12.5, "uses": 2, "icon": ""},
        ],
        dps_b=1680000,
        damage_b=647000000,
        ilvl_b=630.2,
        active_time_b=370000,
        damage_breakdown_b=[
            {"name": "炎爆术", "total": 250000000, "hitCount": 110, "critHitCount": 85, "tickCount": 0, "missCount": 0},
            {"name": "火球术", "total": 140000000, "hitCount": 170, "critHitCount": 105, "tickCount": 0, "missCount": 0},
            {"name": "燃烧", "total": 140000000, "hitCount": 50, "critHitCount": 50, "tickCount": 0, "missCount": 0},
            {"name": "烈焰风暴", "total": 70000000, "hitCount": 25, "critHitCount": 18, "tickCount": 0, "missCount": 0},
            {"name": "灼烧", "total": 47000000, "hitCount": 55, "critHitCount": 28, "tickCount": 0, "missCount": 0},
        ],
        casts_b=[
            {"ability": {"name": "炎爆术"}, "type": "cast", "timestamp": 0},
            {"ability": {"name": "炎爆术"}, "type": "cast", "timestamp": 800},
            {"ability": {"name": "火球术"}, "type": "cast", "timestamp": 1600},
            {"ability": {"name": "炎爆术"}, "type": "cast", "timestamp": 2400},
            {"ability": {"name": "炎爆术"}, "type": "cast", "timestamp": 3200},
        ] * 40,
        buffs_b=[
            {"name": "燃烧", "uptime": 24.2, "uses": 5, "icon": ""},
            {"name": "热力迸发", "uptime": 78.5, "uses": 0, "icon": ""},
            {"name": "狂怒战鼓", "uptime": 28.0, "uses": 2, "icon": ""},
            {"name": "元素药水", "uptime": 15.0, "uses": 2, "icon": ""},
            {"name": "法师结界", "uptime": 35.0, "uses": 8, "icon": ""},
        ]
    )
    
    # 玩家2: DPS下降（装等提升但手法变差）
    p2 = PlayerCompareData(
        name="狂徒贼B",
        class_name="Rogue",
        spec="Outlaw",
        dps_a=1420000,
        damage_a=597000000,
        ilvl_a=626.0,
        active_time_a=390000,
        damage_breakdown_a=[
            {"name": "手枪射击", "total": 160000000, "hitCount": 200, "critHitCount": 80, "tickCount": 0, "missCount": 0},
            {"name": "影袭", "total": 140000000, "hitCount": 250, "critHitCount": 100, "tickCount": 0, "missCount": 0},
            {"name": "斩击", "total": 130000000, "hitCount": 60, "critHitCount": 30, "tickCount": 0, "missCount": 0},
            {"name": "刀锋冲刺", "total": 90000000, "hitCount": 20, "critHitCount": 8, "tickCount": 0, "missCount": 0},
            {"name": "剑刃乱舞", "total": 77000000, "hitCount": 80, "critHitCount": 32, "tickCount": 0, "missCount": 0},
        ],
        casts_a=[
            {"ability": {"name": "影袭"}, "type": "cast", "timestamp": 0},
            {"ability": {"name": "手枪射击"}, "type": "cast", "timestamp": 600},
            {"ability": {"name": "斩击"}, "type": "cast", "timestamp": 1200},
            {"ability": {"name": "影袭"}, "type": "cast", "timestamp": 1800},
            {"ability": {"name": "影袭"}, "type": "cast", "timestamp": 2400},
        ] * 55,
        buffs_a=[
            {"name": "命运骨骰", "uptime": 85.0, "uses": 12, "icon": ""},
            {"name": "正中眉心", "uptime": 45.0, "uses": 10, "icon": ""},
            {"name": "冲动", "uptime": 30.0, "uses": 3, "icon": ""},
            {"name": "狂怒战鼓", "uptime": 25.0, "uses": 2, "icon": ""},
        ],
        dps_b=1380000,
        damage_b=531000000,
        ilvl_b=631.5,
        active_time_b=350000,
        damage_breakdown_b=[
            {"name": "手枪射击", "total": 150000000, "hitCount": 170, "critHitCount": 70, "tickCount": 0, "missCount": 0},
            {"name": "影袭", "total": 130000000, "hitCount": 220, "critHitCount": 90, "tickCount": 0, "missCount": 0},
            {"name": "斩击", "total": 120000000, "hitCount": 52, "critHitCount": 25, "tickCount": 0, "missCount": 0},
            {"name": "刀锋冲刺", "total": 85000000, "hitCount": 18, "critHitCount": 7, "tickCount": 0, "missCount": 0},
            {"name": "剑刃乱舞", "total": 46000000, "hitCount": 50, "critHitCount": 20, "tickCount": 0, "missCount": 0},
        ],
        casts_b=[
            {"ability": {"name": "影袭"}, "type": "cast", "timestamp": 0},
            {"ability": {"name": "影袭"}, "type": "cast", "timestamp": 700},
            {"ability": {"name": "手枪射击"}, "type": "cast", "timestamp": 1400},
            {"ability": {"name": "斩击"}, "type": "cast", "timestamp": 2100},
            {"ability": {"name": "影袭"}, "type": "cast", "timestamp": 2800},
        ] * 45,
        buffs_b=[
            {"name": "命运骨骰", "uptime": 78.0, "uses": 10, "icon": ""},
            {"name": "正中眉心", "uptime": 38.0, "uses": 8, "icon": ""},
            {"name": "冲动", "uptime": 25.0, "uses": 2, "icon": ""},
            {"name": "狂怒战鼓", "uptime": 28.0, "uses": 2, "icon": ""},
        ]
    )
    
    # 玩家3: DPS稳定
    p3 = PlayerCompareData(
        name="惩戒骑C",
        class_name="Paladin",
        spec="Retribution",
        dps_a=1350000,
        damage_a=568000000,
        ilvl_a=628.0,
        active_time_a=385000,
        damage_breakdown_a=[
            {"name": "审判", "total": 150000000, "hitCount": 100, "critHitCount": 40, "tickCount": 0, "missCount": 0},
            {"name": "十字军打击", "total": 120000000, "hitCount": 180, "critHitCount": 72, "tickCount": 0, "missCount": 0},
            {"name": "神圣风暴", "total": 140000000, "hitCount": 80, "critHitCount": 32, "tickCount": 0, "missCount": 0},
            {"name": "最终审判", "total": 100000000, "hitCount": 50, "critHitCount": 20, "tickCount": 0, "missCount": 0},
            {"name": "灰烬觉醒", "total": 58000000, "hitCount": 15, "critHitCount": 6, "tickCount": 0, "missCount": 0},
        ],
        casts_a=[
            {"ability": {"name": "审判"}, "type": "cast", "timestamp": 0},
            {"ability": {"name": "十字军打击"}, "type": "cast", "timestamp": 1000},
            {"ability": {"name": "神圣风暴"}, "type": "cast", "timestamp": 2000},
            {"ability": {"name": "最终审判"}, "type": "cast", "timestamp": 3000},
        ] * 40,
        buffs_a=[
            {"name": "复仇之怒", "uptime": 22.0, "uses": 3, "icon": ""},
            {"name": "神圣意志", "uptime": 35.0, "uses": 0, "icon": ""},
            {"name": "狂怒战鼓", "uptime": 25.0, "uses": 2, "icon": ""},
        ],
        dps_b=1385000,
        damage_b=533000000,
        ilvl_b=629.0,
        active_time_b=355000,
        damage_breakdown_b=[
            {"name": "审判", "total": 145000000, "hitCount": 95, "critHitCount": 38, "tickCount": 0, "missCount": 0},
            {"name": "十字军打击", "total": 115000000, "hitCount": 170, "critHitCount": 68, "tickCount": 0, "missCount": 0},
            {"name": "神圣风暴", "total": 138000000, "hitCount": 78, "critHitCount": 31, "tickCount": 0, "missCount": 0},
            {"name": "最终审判", "total": 98000000, "hitCount": 48, "critHitCount": 19, "tickCount": 0, "missCount": 0},
            {"name": "灰烬觉醒", "total": 37000000, "hitCount": 12, "critHitCount": 5, "tickCount": 0, "missCount": 0},
        ],
        casts_b=[
            {"ability": {"name": "审判"}, "type": "cast", "timestamp": 0},
            {"ability": {"name": "十字军打击"}, "type": "cast", "timestamp": 1000},
            {"ability": {"name": "神圣风暴"}, "type": "cast", "timestamp": 2000},
            {"ability": {"name": "最终审判"}, "type": "cast", "timestamp": 3000},
        ] * 38,
        buffs_b=[
            {"name": "复仇之怒", "uptime": 23.0, "uses": 3, "icon": ""},
            {"name": "神圣意志", "uptime": 33.0, "uses": 0, "icon": ""},
            {"name": "狂怒战鼓", "uptime": 28.0, "uses": 2, "icon": ""},
        ]
    )
    
    comparison["players"] = [p1, p2, p3]
    comparison["players"].sort(key=lambda p: abs(p.dps_delta), reverse=True)
    
    return comparison


def main():
    import sys, os
    if sys.platform == "win32":
        os.environ["PYTHONIOENCODING"] = "utf-8"
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    print("=" * 70)
    print("WCL 战斗记录对比分析 - 演示模式")
    print("=" * 70)
    print()
    print("使用模拟数据展示报告效果，无需 WCL API Key")
    print()
    
    # 创建模拟数据
    comparison = create_mock_comparison()
    
    # 创建模拟的 comparator（只需要 analyze_* 方法）
    import types
    from analyzer import FightComparator
    
    class FakeClient:
        pass
    
    mock = FightComparator(FakeClient())
    
    # 生成文本报告
    print("【文本报告预览】")
    print()
    text_gen = TextReportGenerator()
    text_report = text_gen.generate(comparison, mock)
    print(text_report)
    
    # 生成HTML报告
    html_gen = HtmlReportGenerator()
    html_report = html_gen.generate(comparison, mock)
    
    output_file = "demo_report.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_report)
    
    print()
    print(f"✅ HTML 演示报告已保存: {output_file}")
    print()
    print("提示: 用浏览器打开 demo_report.html 查看可视化报告")
    print()
    print("实际使用 WCL 数据:")
    print('  python main.py <report_a> <fight_a> <report_b> <fight_b> --player "玩家名字"')


if __name__ == "__main__":
    main()
