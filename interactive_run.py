#!/usr/bin/env python3
"""
交互式运行入口 - 引导用户输入参数并执行对比
支持：粘贴 WCL 完整链接自动解析、锁定单个玩家对比
使用 WCL v2 GraphQL API，需要 OAuth Token
"""
import os
import sys
import subprocess
import re

from report_generator import get_report_path


def get_saved_key():
    """读取已保存的API Key"""
    key_file = os.path.join(os.path.dirname(__file__), ".wcl_api_key")
    if os.path.exists(key_file):
        with open(key_file, "r", encoding="utf-8") as f:
            key = f.read().strip()
        if key:
            return key
    return None


def parse_wcl_url(url_or_code):
    """从各种输入中提取 Report Code 和可选的 Fight ID"""
    url_or_code = url_or_code.strip()

    code_match = re.search(r'/reports/([a-zA-Z0-9]+)', url_or_code)
    if code_match:
        report_code = code_match.group(1)
        fight_match = re.search(r'[?#&]fight=(\d+)', url_or_code)
        if fight_match:
            return report_code, fight_match.group(1)
        return report_code, None

    if re.match(r'^[a-zA-Z0-9]+$', url_or_code) and len(url_or_code) >= 5:
        return url_or_code, None

    return None, None


def main():
    if sys.platform == "win32":
        os.environ["PYTHONIOENCODING"] = "utf-8"
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    print("=" * 60)
    print("WCL 战斗记录对比分析工具")
    print("=" * 60)
    print()
    print("使用 WCL v2 GraphQL API，需要 OAuth Access Token")
    print("如果还没有 Token，请先运行 [获取V2Token.vbs]")
    print()

    # 检查 API Key
    api_key = get_saved_key()
    if api_key:
        print(f"已检测到保存的 API Key: {api_key[:20]}...")
        choice = input("是否使用已保存的 Key? (回车=是, n=重新输入): ").strip().lower()
        if choice == "n":
            api_key = input("请输入新的 WCL v2 API Key: ").strip()
    else:
        print("未检测到保存的 API Key。")
        print("请先运行 [获取V2Token.vbs] 获取 OAuth Token")
        print()
        api_key = input("请输入 API Key (或回车退出): ").strip()
    
    if not api_key:
        print("错误: API Key 不能为空")
        input("按回车退出...")
        return

    # 保存 Key（可选）
    key_file = os.path.join(os.path.dirname(__file__), ".wcl_api_key")
    if not os.path.exists(key_file) or api_key != get_saved_key():
        save = input("是否保存这个 API Key 供以后使用? (y/n): ").strip().lower()
        if save == "y":
            with open(key_file, "w", encoding="utf-8") as f:
                f.write(api_key)
            print("已保存!")

    print()
    print("-" * 60)
    print("输入两次战斗的信息:")
    print("-" * 60)
    print()

    # 第一次战斗
    while True:
        raw = input("第一次战斗 (链接或Code): ").strip()
        report_a, fight_a_auto = parse_wcl_url(raw)
        if report_a:
            break
        print("  无法解析，请检查输入。支持格式:")
        print("     https://www.warcraftlogs.com/reports/ABC123#fight=2")
        print("     或直接输入: ABC123")

    if fight_a_auto:
        print(f"  从链接中解析出 Fight ID: {fight_a_auto}")
        confirm = input(f"  使用该 ID 吗? (回车=是, 或输入新ID): ").strip()
        fight_a = confirm if confirm else fight_a_auto
    else:
        fight_a = input("第一次战斗的 ID (数字, 回车默认1): ").strip() or "1"

    # 第二次战斗
    while True:
        raw = input("第二次战斗 (链接或Code): ").strip()
        report_b, fight_b_auto = parse_wcl_url(raw)
        if report_b:
            break
        print("  无法解析，请检查输入。")

    if fight_b_auto:
        print(f"  从链接中解析出 Fight ID: {fight_b_auto}")
        confirm = input(f"  使用该 ID 吗? (回车=是, 或输入新ID): ").strip()
        fight_b = confirm if confirm else fight_b_auto
    else:
        fight_b = input("第二次战斗的 ID (数字, 回车默认1): ").strip() or "1"

    # 锁定玩家（强制要求）
    print()
    print("-" * 60)
    while True:
        target = input("要对比的玩家名字: ").strip()
        if target:
            break
        print("  必须输入一个玩家名字")

    print()
    print("=" * 60)
    print("对比参数确认:")
    print(f"  战斗A: {report_a} #{fight_a}")
    print(f"  战斗B: {report_b} #{fight_b}")
    print(f"  锁定玩家: {target}")
    print("=" * 60)
    print()

    confirm = input("确认执行? (回车=是, n=取消): ").strip().lower()
    if confirm == "n":
        print("已取消")
        input("按回车退出...")
        return

    # 生成带时间戳的报告路径
    report_path = get_report_path(
        prefix="report",
        suffix=".html",
        project_root=os.path.dirname(os.path.abspath(__file__)),
        include_random=False,
    )

    # 构建命令
    python = r"C:\Program Files\Python312\python.exe"
    main_script = os.path.join(os.path.dirname(__file__), "main.py")

    cmd = [
        python, main_script,
        "--api-key", api_key,
        "--player", target,
        "--output", report_path,
        report_a, fight_a,
        report_b, fight_b
    ]

    print()
    print("正在执行对比分析，请稍候...")
    print("(数据量大时可能需要几十秒)")
    print()

    # 执行
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        print()

        # 打印 stdout
        if result.stdout:
            for line in result.stdout.splitlines():
                if line.strip():
                    print(line)

        if result.returncode == 0:
            print()
            print("对比完成!")
            if os.path.exists(report_path):
                print(f"HTML 报告已生成: {report_path}")
                try:
                    import webbrowser
                    webbrowser.open(os.path.abspath(report_path))
                except Exception:
                    pass
        else:
            print()
            print(f"运行出错 (返回码: {result.returncode})")
            print()
            if result.stderr:
                print("【错误详情】")
                print(result.stderr)
                print()

            err_lower = (result.stderr or "").lower()
            if "unauthorized" in err_lower or "401" in err_lower:
                print("提示: API Key 无效或已过期")
                print("   请重新运行 [获取V2Token.vbs] 获取新 Token")
            elif "not found" in err_lower or "404" in err_lower:
                print("提示: 报告代码或战斗ID不存在，请检查输入")
            elif "network" in err_lower or "connection" in err_lower:
                print("提示: 网络连接问题，请检查网络")
    except Exception as e:
        print(f"启动失败: {e}")

    print()
    input("按回车键关闭窗口...")


if __name__ == "__main__":
    main()
