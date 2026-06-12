# WCL 战斗记录对比分析工具 - 项目迭代记录

> 本文档用于记录本项目的迭代历程、最终完整需求以及后续迭代参考。
> 最后更新：2026-06-12

---

## 一、项目概述

**项目名称**：WCL 战斗记录对比分析工具

**项目用途**：对比魔兽世界《Warcraft Logs》(WCL) 两次战斗记录，自动分析指定玩家 DPS 变化的原因。

**当前部署状态**：
- 代码托管：GitHub (`https://github.com/eosphorosfu-source/wcl-compare`)
- 在线访问：PythonAnywhere 免费服务器 (`https://eosphoros.pythonanywhere.com`)

---

## 二、项目迭代历程

### 阶段 1：代码上传到 GitHub

**目标**：将本地项目推送到 GitHub，解决网络访问问题。

**主要工作**：
1. 诊断 GitHub 访问失败问题（HTTPS 连接被重置）。
2. 配置 Git 使用本地代理端口 7890（Clash）：
   ```bash
   git config --global http.proxy http://127.0.0.1:7890
   git config --global https.proxy http://127.0.0.1:7890
   git config --global http.sslBackend openssl
   ```
3. 发现 GitHub 仓库不存在，协助在 GitHub 创建同名仓库。
4. 将本地 `main` 分支推送到 GitHub。

**结果**：项目代码成功上传到 GitHub。

---

### 阶段 2：生成报告文件整理

**目标**：将根目录下堆积的临时 HTML 报告文件整理到独立目录，并为后续生成文件加入时间戳。

**主要工作**：
1. 创建 `reports/` 目录。
2. 将根目录下已有的 `tmp*.html`、`report.html`、`demo_report.html` 迁移到 `reports/`。
3. 在 `report_generator.py` 新增辅助函数：
   - `get_reports_dir()`：获取报告输出目录
   - `generate_report_filename()`：生成带时间戳的文件名
   - `get_report_path()`：生成完整报告路径
4. 改造各入口的报告输出逻辑：
   - `web_app.py`：网页版分析结果保存为 `reports/report_YYYYMMDD_HHMMSS_xxxxxx.html`
   - `demo.py`：演示报告保存为 `reports/demo_report_YYYYMMDD_HHMMSS.html`
   - `interactive_run.py`：交互式报告保存为 `reports/report_YYYYMMDD_HHMMSS.html`
   - `main.py` 与 `README.md`：示例命令指向 `reports/` 目录
5. 更新 `.gitignore`，忽略 `reports/` 目录。
6. 从 Git 仓库中删除已追踪的临时 HTML 文件，保持仓库根目录干净。

**结果**：
- 仓库根目录不再 cluttered
- 后续所有生成报告自动进入 `reports/` 并带时间戳
- 避免同名文件互相覆盖

---

### 阶段 3：部署到 PythonAnywhere

**目标**：将 Web 应用部署到免费网站，让其他人可以在线使用。

**主要工作**：
1. 评估部署方案：
   - Render 需要绑定信用卡，用户不接受。
   - 选择 **PythonAnywhere**（免费、无需信用卡、适合 Flask）。
2. 添加 PythonAnywhere WSGI 入口文件 `wsgi.py`。
3. 调整 `render.yaml` 以兼容 Render（后续如需要可继续使用）。
4. 在 PythonAnywhere 上：
   - 通过 ZIP 上传方式导入代码（因用户无法复制粘贴长 Token）
   - 创建虚拟环境并安装依赖
   - 创建 Flask Web 应用
   - 配置 WSGI 文件
   - 配置 Virtualenv
   - 在 WSGI 文件中设置 `WCL_API_KEY` 环境变量
5. 修复 WSGI 文件缩进导致的 `IndentationError`。
6. 测试网页版完整流程：解析 URL → 读取战斗列表 → 读取角色 → 生成对比报告。

**结果**：
- 网站成功部署并可正常使用。
- 网页版核心功能测试通过。

---

## 三、最终完整需求

### 3.1 核心功能需求

1. **WCL URL 解析**
   - 支持完整 WCL 链接（含 `#fight=` 或 `?fight=`）
   - 支持纯 Report Code（16 位字母数字）

2. **战斗列表读取**
   - 输入 Report Code 后，列出该报告下所有 Boss 战
   - 显示战斗名称、是否击杀、时长、难度

3. **角色列表读取**
   - 选择 Boss 战后，列出该战斗中的玩家角色
   - 显示角色名、职业、天赋、装等、DPS

4. **对比分析**
   - 选择两次战斗和同一职业的玩家后，执行对比
   - 生成 HTML 可视化报告，包含：
     - DPS / 总伤害 / 装等 / 活跃度变化
     - 施法次数与 CPM 变化
     - Buff / Debuff 覆盖率变化
     - 伤害构成变化（占比、均伤、暴击率）
     - 非同 Boss 战斗的提示警告

5. **报告输出**
   - 所有 HTML 报告保存到 `reports/` 目录
   - 文件名包含时间戳，避免覆盖

### 3.2 部署需求

1. **目标平台**：免费、无需信用卡的 Python 托管平台（当前使用 PythonAnywhere）
2. **访问方式**：通过浏览器访问公共 URL
3. **环境变量**：必须配置 `WCL_API_KEY`
4. **无需修改代码即可部署**：通过 `wsgi.py` 或 `render.yaml` 支持一键部署

### 3.3 安全需求

1. `WCL_API_KEY` 不得提交到 GitHub（已通过 `.gitignore` 忽略 `.wcl_api_key`）
2. 线上部署时通过环境变量或 WSGI 文件注入 API Key
3. 不暴露源代码中的敏感信息

### 3.4 代码质量需求

1. 生成文件不 clutter 仓库根目录
2. 文件名具有可读性和唯一性（时间戳）
3. 支持后续继续迭代和扩展

---

## 四、技术架构

### 4.1 技术栈

- **后端框架**：Flask
- **WSGI 服务器**：Gunicorn（Render）/ mod_wsgi（PythonAnywhere）
- **HTTP 客户端**：requests
- **API**：WCL GraphQL v2 API
- **前端**：原生 HTML + CSS + JavaScript（内联在 `templates/index.html`）

### 4.2 核心文件结构

```
wcl_compare/
├── analyzer.py              # 对比分析核心逻辑
├── ability_translations.json # 技能/Buff 中文翻译缓存
├── demo.py                  # 演示脚本（无需 API Key）
├── interactive_run.py       # 交互式命令行入口
├── main.py                  # CLI 入口
├── report_generator.py      # 文本 & HTML 报告生成器
├── requirements.txt         # Python 依赖
├── setup_v2_token.py        # 获取 WCL v2 Token 脚本
├── translation_manager.py   # 翻译管理器
├── web_app.py               # Flask Web 应用入口
├── wcl_client.py            # WCL API 客户端
├── wsgi.py                  # PythonAnywhere WSGI 入口
├── render.yaml              # Render 部署配置
├── templates/
│   └── index.html           # Web 前端页面
├── reports/                 # 生成的 HTML 报告（gitignored）
└── .wcl_api_key             # 本地 API Key（gitignored）
```

### 4.3 部署架构

```
用户浏览器
    │
    ▼
PythonAnywhere Web Server (Apache + mod_wsgi)
    │
    ▼
WSGI 文件 (/var/www/xxx_pythonanywhere_com_wsgi.py)
    │
    ▼
web_app.py (Flask)
    │
    ▼
WCL GraphQL v2 API
```

---

## 五、配置说明

### 5.1 本地开发

1. 获取 WCL v2 API Token：
   - 双击 `获取V2Token.vbs`
   - 或运行 `python setup_v2_token.py`
2. Token 保存在 `.wcl_api_key`（已被 gitignore）
3. 启动网页版：
   ```bash
   python web_app.py
   ```

### 5.2 PythonAnywhere 部署

1. 上传代码（ZIP 或 git clone）
2. 创建虚拟环境并安装依赖：
   ```bash
   python3.12 -m venv ~/.virtualenvs/wcl-compare
   source ~/.virtualenvs/wcl-compare/bin/activate
   pip install -r requirements.txt
   ```
3. 创建 Web App → Flask → Python 3.12
4. WSGI 文件内容：
   ```python
   import os
   import sys

   os.environ['WCL_API_KEY'] = '你的TOKEN'

   sys.path.insert(0, '/home/<用户名>/wcl-compare')
   from web_app import app as application
   ```
5. Virtualenv：`/home/<用户名>/.virtualenvs/wcl-compare`
6. 点击 Reload

---

## 六、已知问题与限制

### 6.1 PythonAnywhere 免费版限制

1. **自动休眠**：15 分钟无访问会进入睡眠，首次访问需等待 30 秒左右唤醒。
2. **CPU 时间限制**：每天有一定额度，大量分析可能受限。
3. **无自定义域名**：免费版只能使用 `xxx.pythonanywhere.com`。
4. **文件系统为临时存储**：服务重启后 `reports/` 中旧报告会丢失（但报告生成后立刻打开，通常不影响）。

### 6.2 WCL API 限制

1. 有速率限制，大量数据获取可能较慢。
2. Token 可能过期，需要重新获取。
3. WCL 服务器不稳定时可能返回 500 错误。

### 6.3 当前代码限制

1. 报告文件存储在服务器本地，没有持久化数据库。
2. 没有用户系统，所有访问者共享同一个 API Key。
3. 网页前端为单文件内联 HTML，未做代码拆分。

---

## 七、后续迭代建议

### 7.1 功能增强

- [ ] 支持对比多个玩家（一次选择多个角色）
- [ ] 支持保存历史报告到数据库或云存储
- [ ] 支持用户登录，隔离不同用户的 API Key 和历史记录
- [ ] 增加报告分享链接（短链接）
- [ ] 支持导出 PDF 报告
- [ ] 增加更多对比维度（治疗、承伤等）

### 7.2 部署优化

- [ ] 将报告文件持久化到对象存储（如 AWS S3、阿里云 OSS）
- [ ] 配置自定义域名
- [ ] 升级到付费托管平台以获得更好稳定性
- [ ] 添加健康检查和日志监控

### 7.3 代码优化

- [ ] 将前端 HTML/CSS/JS 拆分为独立静态文件
- [ ] 添加单元测试
- [ ] 优化 WCL API 请求，减少调用次数
- [ ] 添加异常处理和用户友好的错误提示
- [ ] 使用配置文件管理环境变量，替代硬编码

### 7.4 安全加固

- [ ] 将 API Key 从 WSGI 文件迁移到 PythonAnywhere Environment Variables（如界面支持）
- [ ] 对用户输入做更严格的校验
- [ ] 防止 SSRF 和路径遍历攻击

---

## 八、关键配置速查

### Git 代理配置（本地）
```bash
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
git config --global http.sslBackend openssl
```

### PythonAnywhere WSGI 文件
路径：`/var/www/<用户名>_pythonanywhere_com_wsgi.py`

```python
import os
import sys

os.environ['WCL_API_KEY'] = '你的TOKEN'

sys.path.insert(0, '/home/<用户名>/wcl-compare')
from web_app import app as application
```

### PythonAnywhere 虚拟环境
```
/home/<用户名>/.virtualenvs/wcl-compare
```

---

## 九、总结

本项目从一个本地命令行工具，逐步迭代为可在线访问的 Web 应用。核心完成了三件事：

1. **代码上云**：项目代码托管到 GitHub，解决协作和部署基础。
2. **文件治理**：生成报告统一进入 `reports/` 目录并带时间戳，仓库结构清晰。
3. **在线部署**：成功部署到 PythonAnywhere，他人可通过浏览器直接使用。

后续迭代可围绕功能增强、部署稳定性、代码质量和安全性四个方向展开。
