"""
WCL GraphQL v2 API 客户端
需要正确的 OAuth Access Token（不是网页 Session Token）
"""
import requests
import time
from typing import Dict, List, Any


WCL_API_URL = "https://www.warcraftlogs.com/api/v2/client"


class WCLClient:
    """WCL GraphQL API 客户端"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        # 处理 Bearer 前缀
        token = api_key.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept-Language": "zh-CN,zh;q=0.9"
        })

    def _query(self, query: str, variables: Dict = None, retries: int = 2) -> Dict:
        """执行 GraphQL 查询，带重试"""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        last_error = None
        for attempt in range(retries + 1):
            try:
                response = self.session.post(WCL_API_URL, json=payload, timeout=30)

                if response.status_code >= 500:
                    last_error = f"WCL 服务器错误 ({response.status_code})"
                    if attempt < retries:
                        wait = 2 ** attempt
                        print(f"  WCL 服务器暂时不可用，{wait}秒后重试...")
                        time.sleep(wait)
                        continue
                    response.raise_for_status()

                if response.status_code == 401:
                    raise Exception("API Key 无效或已过期。请先运行 [获取V2Token.vbs] 获取正确的 OAuth Token")

                response.raise_for_status()
                data = response.json()

                if "errors" in data:
                    error_msg = str(data["errors"])
                    raise Exception(f"GraphQL Error: {error_msg}")

                return data["data"]

            except requests.exceptions.Timeout:
                last_error = "请求超时"
                if attempt < retries:
                    time.sleep(2 ** attempt)
                    continue
            except requests.exceptions.ConnectionError:
                last_error = "连接错误"
                if attempt < retries:
                    time.sleep(2 ** attempt)
                    continue

        raise Exception(f"WCL API 请求失败: {last_error}")

    def get_report(self, report_code: str) -> Dict:
        """获取报告基本信息和所有战斗列表"""
        query = """
        query getReport($code: String!) {
            reportData {
                report(code: $code) {
                    code
                    title
                    startTime
                    endTime
                    zone { id name }
                    fights {
                        id
                        encounterID
                        name
                        kill
                        startTime
                        endTime
                        size
                        difficulty
                        fightPercentage
                    }
                }
            }
        }
        """
        result = self._query(query, {"code": report_code})
        return result["reportData"]["report"]

    def get_composition(self, report_code: str, fight_id: int) -> List[Dict]:
        """获取团队构成"""
        query = """
        query getComposition($code: String!, $fightIDs: [Int]!) {
            reportData {
                report(code: $code) {
                    table(fightIDs: $fightIDs, dataType: Composition)
                }
            }
        }
        """
        result = self._query(query, {
            "code": report_code,
            "fightIDs": [fight_id]
        })
        table = result["reportData"]["report"]["table"]
        return table.get("data", {}).get("composition", [])

    def get_damage_table(self, report_code: str, fight_id: int, source_id: int = None) -> List[Dict]:
        """获取伤害排行表"""
        query = """
        query getDamage($code: String!, $fightIDs: [Int], $sourceID: Int) {
            reportData {
                report(code: $code) {
                    table(fightIDs: $fightIDs, dataType: DamageDone, sourceID: $sourceID)
                }
            }
        }
        """
        variables = {
            "code": report_code,
            "fightIDs": [fight_id]
        }
        if source_id:
            variables["sourceID"] = source_id
        result = self._query(query, variables)
        table = result["reportData"]["report"]["table"]
        return table.get("data", {}).get("entries", [])

    def get_casts(self, report_code: str, fight_id: int, source_id: int) -> List[Dict]:
        """获取玩家施法记录（分页获取全部）"""
        all_events = []
        next_page = None

        query = """
        query getCasts($code: String!, $fightIDs: [Int]!, $sourceID: Int!, $startTime: Float) {
            reportData {
                report(code: $code) {
                    events(
                        fightIDs: $fightIDs,
                        sourceID: $sourceID,
                        dataType: Casts,
                        useAbilityIDs: false,
                        startTime: $startTime
                    ) {
                        data {
                            type
                            timestamp
                            ability {
                                guid
                                name
                                abilityIcon
                            }
                            sourceID
                            targetID
                        }
                        nextPageTimestamp
                    }
                }
            }
        }
        """

        while True:
            variables = {
                "code": report_code,
                "fightIDs": [fight_id],
                "sourceID": source_id
            }
            if next_page:
                variables["startTime"] = next_page

            result = self._query(query, variables)
            events_data = result["reportData"]["report"]["events"]
            all_events.extend(events_data["data"])

            next_page = events_data.get("nextPageTimestamp")
            if not next_page:
                break

        return all_events

    def get_buffs(self, report_code: str, fight_id: int, source_id: int) -> List[Dict]:
        """获取增益覆盖"""
        return self._get_auras(report_code, fight_id, source_id, "Buffs")

    def get_debuffs(self, report_code: str, fight_id: int, source_id: int) -> List[Dict]:
        """获取减益覆盖"""
        return self._get_auras(report_code, fight_id, source_id, "Debuffs")

    def _get_auras(self, report_code: str, fight_id: int, source_id: int, data_type: str) -> List[Dict]:
        """通用获取光环数据"""
        query = f"""
        query getAuras($code: String!, $fightIDs: [Int]!, $sourceID: Int!) {{
            reportData {{
                report(code: $code) {{
                    table(fightIDs: $fightIDs, dataType: {data_type}, sourceID: $sourceID)
                }}
            }}
        }}
        """
        result = self._query(query, {
            "code": report_code,
            "fightIDs": [fight_id],
            "sourceID": source_id
        })
        table = result["reportData"]["report"]["table"]
        return table.get("data", {}).get("auras", [])
