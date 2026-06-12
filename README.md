# WCL 战斗记录对比分析工具

对比魔兽世界 Warcraft Logs (WCL) 两次战斗记录，自动分析 DPS 变化的原因。

## 功能特性

- **支持粘贴 WCL 完整链接**：自动解析 Report Code 和 Fight ID
- **锁定单个玩家对比**：只分析指定玩家，聚焦核心变化
- **施法分析**：对比各技能的施法次数和 CPM（每分钟施法次数）
- **增益覆盖**：对比重要 Buff/Debuff 的覆盖率和使用次数
- **伤害构成**：分析各技能在总伤害中的占比、**均伤变化、暴击率**
- **装等检测**：检测装备等级变化
- **活跃度分析**：检测输出时间占比变化

## 前置要求：获取 WCL v2 API Token

本工具使用 **WCL GraphQL v2 API**，需要正确的 **OAuth Access Token**。

### 方式1：双击自动获取（推荐）

1. **双击 `获取V2Token.vbs`**
2. 按提示打开 `https://www.warcraftlogs.com/api/clients/`
3. 登录 WCL 账号，点击 **[Create Client]**
4. 填写：
   - **Name**: 随便填（如 `MyWCLTool`）
   - **Redirect URI**: `http://localhost`
5. 点击 **[Create Client]**
6. 记下 **Client ID** 和 **Client Secret**
7. 在脚本中输入，自动获取并保存 Token

### 方式2：命令行获取

```bash
cd wcl_compare
"C:\Program Files\Python312\python.exe" setup_v2_token.py
```

> Token 只需获取一次，保存后以后直接使用。

## 快速开始

### 方式1：双击运行（推荐）

进入 `wcl_compare` 文件夹：

1. **双击 `获取V2Token.vbs`** — 首次使用，获取并保存 API Token
2. **双击 `启动对比工具.vbs`** — 命令行交互式对比
3. **双击 `启动网页版.vbs`** — 启动 Web 页面，粘贴日志地址后选择 Boss 战和角色进行对比

### 方式2：命令行

```bash
cd wcl_compare

# 列出报告中的所有战斗
"C:\Program Files\Python312\python.exe" main.py --list-fights REPORT_CODE

# 对比两次战斗（锁定玩家）
"C:\Program Files\Python312\python.exe" main.py ABC123 1 DEF456 2 --player "玩家名字"

# 生成 HTML 可视化报告（保存到 reports/ 目录）
"C:\Program Files\Python312\python.exe" main.py ABC123 1 DEF456 2 --player "玩家名字" -o reports/report.html
```

> **报告文件存放位置**：网页版、交互式运行和演示脚本生成的 HTML 报告会自动保存到 `reports/` 目录，文件名包含时间戳（如 `report_20260612_101144_abc123.html`），避免重复覆盖。

## 输入格式

### 战斗链接 / Report Code

支持三种输入方式：

| 输入方式 | 示例 |
|---------|------|
| 完整 WCL 链接 | `https://www.warcraftlogs.com/reports/ABC123#fight=2` |
| 带参数的链接 | `https://www.warcraftlogs.com/reports/ABC123?fight=3` |
| 纯 Report Code | `ABC123` |

> Report Code 是 WCL 报告链接中 `/reports/` 后面的那串字符，区分大小写。

### Fight ID

一个报告里通常包含多次尝试（灭了 N 把后击杀）。每次尝试就是一个 Fight：

```
Fight 1 = 第一次尝试
Fight 2 = 第二次尝试（击杀了）
```

在 WCL 网页左侧可以看到所有战斗列表。

## 报告解读

### 核心指标
- **DPS 变化**：两次战斗的 DPS 对比
- **总伤害变化**：该玩家的总输出变化
- **装等变化**：装备等级变化
- **活跃度变化**：实际输出时间占比变化

### 施法变化
- **次数变化**：某个技能施法次数变少/变多
- **CPM 变化**：每分钟施法次数，反映手速和循环流畅度

### 增益覆盖
- **覆盖率**：如 重要爆发Buff、职业机制Buff 的覆盖时间百分比
- **使用次数**：如 药水、种族技能 的使用次数

### 伤害构成变化
| 列 | 说明 |
|----|------|
| 占比变化 | 该技能在总伤害中的占比增减 |
| 总伤变化 | 该技能总伤害的变化量 |
| 均伤A/B | 平均每次命中的伤害 |
| 均伤变化 | 平均伤害的变化（反映装等/属性变化） |
| 暴击A/B | 暴击率百分比 |

## 常见 DPS 变化原因

| 现象 | 可能原因 |
|------|---------|
| 施法次数减少 | 走位过多、被点名、死亡 |
| CPM 下降 | GCD 浪费、手感生疏、循环错误 |
| Buff 覆盖降低 | 爆发时机不对、触发不好 |
| 关键技能占比变化 | 天赋/装备变更、优先级错误 |
| 均伤下降 | 装等降低、属性不对、武器伤害下降 |
| 暴击率波动 | 纯随机因素、样本量小（单次战斗） |

## 项目结构

```
wcl_compare/
├── 获取V2Token.vbs           ← 首次使用，获取 API Token
├── 启动对比工具.vbs           ← 双击运行交互式对比
├── 启动网页版.vbs / .bat      ← 双击启动 Web 对比页面
├── 启动演示.vbs              ← 双击运行演示报告
├── wcl_client.py             ← WCL v2 GraphQL API 客户端
├── analyzer.py               ← 对比分析核心逻辑
├── translation_manager.py    ← 英文名称自动翻译管理器
├── ability_translations.json ← 用户本地翻译缓存
├── report_generator.py       ← 文本 & HTML 报告生成
├── main.py                   ← CLI 入口
├── interactive_run.py        ← 交互式入口
├── web_app.py                ← Web 应用入口
├── setup_v2_token.py         ← Token 获取脚本
└── README.md                 ← 本文档
```

## 英文名称自动翻译

工具会优先从 WCL 请求中文名称，并按以下顺序处理仍显示英文的技能/Buff/Boss：

1. 代码内置映射表（`analyzer.py` 中的 `NAME_TRANSLATIONS`）
2. 用户本地缓存（`ability_translations.json`）
3. 通过 MyMemory 免费在线翻译接口译为中文
4. 以上都失败时保留英文，并在控制台输出 `[待翻译] 英文名称`

**注意**：在线翻译不保证 100% 符合游戏内官方译名，但基本能看懂。如需精确译名，可手动修改 `ability_translations.json`。

**手动补充翻译**：直接编辑 `ability_translations.json`，按 `"英文名称": "中文名称"` 添加即可，例如：

```json
{
  "Rune of Power": "能量符文",
  "Icy Veins": "冰冷血脉"
}
```

## 注意事项

1. **API 限制**：WCL API 有速率限制，大量数据获取可能需要时间
2. **战斗差异**：不同击杀速度会影响爆发技能覆盖次数
3. **随机因素**：单次战斗暴击率波动可能高达 ±5%
4. **建议**：对比时最好选取 **同难度** 的战斗，结果更有参考价值

## 故障排除

| 问题 | 解决方案 |
|------|---------|
| `API Key 无效或已过期` | 重新运行 `获取V2Token.vbs` 获取新 Token |
| `500 Server Error` | WCL 服务器暂时不稳定，等几分钟再试 |
| `找不到玩家` | 检查玩家名字拼写，注意区分大小写 |
| `报告不存在` | 检查 Report Code 是否正确 |
