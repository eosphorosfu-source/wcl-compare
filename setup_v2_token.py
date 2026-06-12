#!/usr/bin/env python3
"""
WCL v2 API OAuth Token 获取工具

步骤：
1. 访问 https://www.warcraftlogs.com/api/clients/
2. 登录 WCL 账号
3. 点击 "Create Client"
4. 名称随便填（如 MyWCLTool），Redirect URI 填 http://localhost
5. 创建后得到 Client ID 和 Client Secret
6. 在本脚本中输入，自动获取长期有效的 Access Token
"""
import os
import sys
import base64
import requests


def get_token(client_id: str, client_secret: str) -> str:
    """用 OAuth client_credentials 流程获取 Access Token"""
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    
    resp = requests.post(
        "https://www.warcraftlogs.com/oauth/token",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={"grant_type": "client_credentials"},
        timeout=30
    )
    resp.raise_for_status()
    data = resp.json()
    return data["access_token"]


def test_token(token: str) -> bool:
    """测试 Token 是否能访问 v2 API"""
    query = """
    query {
        userData {
            currentUser {
                name
            }
        }
    }
    """
    resp = requests.post(
        "https://www.warcraftlogs.com/api/v2/client",
        json={"query": query},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        timeout=15
    )
    if resp.status_code == 200:
        data = resp.json()
        if "errors" not in data and data.get("data", {}).get("userData", {}).get("currentUser"):
            return True
    return False


def main():
    if sys.platform == "win32":
        os.environ["PYTHONIOENCODING"] = "utf-8"
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    
    print("=" * 60)
    print("WCL v2 API OAuth Token 获取工具")
    print("=" * 60)
    print()
    print("请先完成以下步骤：")
    print()
    print("1. 用浏览器打开：")
    print("   https://www.warcraftlogs.com/api/clients/")
    print()
    print("2. 登录你的 WCL 账号")
    print()
    print("3. 点击 [Create Client]")
    print("   - Name: 随便填（如 MyWCLTool）")
    print("   - Redirect URI: http://localhost")
    print("   - 点击 [Create Client]")
    print()
    print("4. 记下页面上显示的 Client ID 和 Client Secret")
    print()
    input("按回车继续...")
    print()
    
    client_id = input("Client ID: ").strip()
    client_secret = input("Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("错误: Client ID 和 Client Secret 都不能为空")
        input("按回车退出...")
        return
    
    print()
    print("正在获取 Access Token...")
    try:
        token = get_token(client_id, client_secret)
        print(f"✅ 获取成功! Token: {token[:30]}...")
        print()
        
        print("正在测试 Token...")
        if test_token(token):
            print("✅ Token 有效，可以访问 v2 API!")
        else:
            print("⚠️ Token 获取成功但测试失败，可能权限不足")
        
        # 保存
        save = input("\n是否保存这个 Token 供以后使用? (y/n): ").strip().lower()
        if save == "y":
            key_file = os.path.join(os.path.dirname(__file__), ".wcl_api_key")
            with open(key_file, "w", encoding="utf-8") as f:
                f.write(token)
            print(f"✅ 已保存到: {key_file}")
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ 获取失败: {e}")
        if e.response.status_code == 401:
            print("   提示: Client ID 或 Client Secret 不正确")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    print()
    input("按回车退出...")


if __name__ == "__main__":
    main()
