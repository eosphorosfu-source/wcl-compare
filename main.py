#!/usr/bin/env python3
"""
WCL 战斗记录对比分析工具 (v2 GraphQL API)

用法:
    python main.py <report_a> <fight_a> <report_b> <fight_b> [options]

示例:
    python main.py ABC123 1 DEF456 2 --player "张三"
    python main.py ABC123 1 DEF456 2 --player "张三" -o reports/report.html
    python main.py --list-fights ABC123
"""
import argparse
import os
import sys

from wcl_client import WCLClient
from analyzer import FightComparator
from report_generator import TextReportGenerator, HtmlReportGenerator


def get_api_key() -> str:
    """获取已保存的 WCL v2 API Key"""
    key_file = os.path.join(os.path.dirname(__file__), ".wcl_api_key")
    if os.path.exists(key_file):
        with open(key_file, "r", encoding="utf-8") as f:
            key = f.read().strip()
        if key:
            return key
    return ""


def main():
    parser = argparse.ArgumentParser(
        description="对比魔兽世界WCL两次战斗记录，分析DPS变化原因",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用 WCL v2 GraphQL API，需要 OAuth Access Token

获取方式：
  1. 双击 [获取V2Token.vbs]
  2. 按提示注册 OAuth App 并获取 Token

支持输入 WCL 完整链接或纯 Report Code
        """
    )

    parser.add_argument("report_a", nargs="?", help="第一次战斗的报告代码")
    parser.add_argument("fight_a", nargs="?", type=int, help="第一次战斗的ID")
    parser.add_argument("report_b", nargs="?", help="第二次战斗的报告代码")
    parser.add_argument("fight_b", nargs="?", type=int, help="第二次战斗的ID")
    parser.add_argument("-p", "--player", required=True, help="要对比的玩家名字（必填）")
    parser.add_argument("-o", "--output", help="输出文件路径（.html后缀生成HTML报告）")
    parser.add_argument("--list-fights", metavar="REPORT_CODE", help="列出报告中的所有战斗")
    parser.add_argument("--api-key", help="WCL v2 API OAuth Token（或设置 WCL_API_KEY 环境变量）")

    args = parser.parse_args()

    # 修复 Windows 控制台编码
    if sys.platform == "win32":
        import os as os_mod
        os_mod.environ["PYTHONIOENCODING"] = "utf-8"
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    # 获取 API Key
    api_key = args.api_key or os.environ.get("WCL_API_KEY", "") or get_api_key()
    if not api_key:
        print("错误: 需要提供 WCL v2 API OAuth Token")
        print()
        print("获取方式:")
        print("  1. 双击 [获取V2Token.vbs]")
        print("  2. 按提示注册 OAuth App 并获取 Token")
        print("  3. 或使用 --api-key 参数传入")
        sys.exit(1)

    # 创建客户端
    client = WCLClient(api_key)
    comparator = FightComparator(client)

    # 列出战斗模式
    if args.list_fights:
        print(f"获取报告 {args.list_fights} 的战斗列表...")
        try:
            report = client.get_report(args.list_fights)
            print(f"\n报告标题: {report['title']}")
            print(f"副本: {report['zone']['name']}")
            print(f"\n{'ID':>4} {'Boss名称':<25} {'击杀':>6} {'时长':>10} {'难度':>8}")
            print("-" * 60)
            for fight in report["fights"]:
                # 只列出 Boss 战
                if not fight.get("encounterID"):
                    continue
                duration = (fight["endTime"] - fight["startTime"]) / 1000
                kill_str = "击杀" if fight["kill"] else "未击杀"
                diff_names = {1: "随机", 3: "普通", 4: "英雄", 5: "史诗"}
                diff = diff_names.get(fight["difficulty"], f"{fight['difficulty']}")
                print(f"{fight['id']:>4} {fight['name']:<25} {kill_str:>6} {duration:>8.1f}s {diff:>8}")
        except Exception as e:
            print(f"获取失败: {e}")
        return

    # 检查必要参数
    if not all([args.report_a, args.fight_a is not None, args.report_b, args.fight_b is not None]):
        parser.print_help()
        print("\n示例:")
        print('  python main.py ABC123 1 DEF456 2 --player "张三"')
        print('  python main.py ABC123 1 DEF456 2 --player "张三" -o reports/report.html')
        print('  python main.py --list-fights ABC123')
        sys.exit(1)

    # 执行对比
    try:
        print("=" * 60)
        print("WCL 战斗记录对比分析")
        print("=" * 60)
        print()

        comparison = comparator.compare_fights(
            args.report_a, args.fight_a,
            args.report_b, args.fight_b,
            target_player=args.player
        )

        # 生成报告
        if args.output and args.output.endswith(".html"):
            generator = HtmlReportGenerator()
            report = generator.generate(comparison, comparator)
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"\nHTML 报告已保存: {args.output}")
            import webbrowser
            webbrowser.open(os.path.abspath(args.output))
        else:
            generator = TextReportGenerator()
            report = generator.generate(comparison, comparator)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(report)
                print(f"\n文本报告已保存: {args.output}")
            else:
                print(report)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
