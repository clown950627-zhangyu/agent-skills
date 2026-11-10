# OpenClaw 故障诊断参考

## 会话记录：Node.js 版本不兼容导致 Gateway 无法启动

### 现象

OpenClaw 本地部署"崩溃"，进程列表中无 openclaw 或 node.exe 相关进程，端口 18789 未监听。

### 诊断路径

1. **确认进程状态**
   ```bash
   ps aux | grep -i openclaw          # WSL 侧无进程
   <C盘>/Windows/System32/tasklist.exe /FI "IMAGENAME eq node.exe" /NH   # Windows 侧也无
   ```

2. **定位安装目录**
   ```bash
   # OpenClaw 全局安装位置
   ls <C盘>/Users/<user>/AppData/Roaming/npm/node_modules/openclaw/
   # 版本：2026.7.1-2
   ```

3. **尝试直接运行以获取错误**
   ```bash
   # ❌ 错误：WSL路径格式不被Windows node.exe识别
   <C盘>/Program\ Files/nodejs/node.exe <C盘>/Users/<用户名>/AppData/Roaming/npm/node_modules/openclaw/dist/index.js --version
   # → Error: Cannot find module '\\wsl.localhost\\Ubuntu\\mnt\\c\\Users\\...'

   # ✅ 正确：使用Windows原生路径格式
   <C盘>/Program\ Files/nodejs/node.exe "C:\Users\<用户名>\AppData\Roaming\npm\node_modules\openclaw\dist\index.js" --version
   # → openclaw requires Node >=22.22.3 <23, >=24.15.0 <25, or >=25.9.0.
   # → Detected: node 25.8.1
   ```

4. **验证配置文件完整性**
   ```bash
   # openclaw.json 是 UTF-8 BOM 编码，Python读取需指定 encoding='utf-8-sig'
   python3 -c "import json; d=json.load(open('<C盘>/Users/<用户名>/.openclaw/openclaw.json', encoding='utf-8-sig')); print(d['gateway'])"
   ```

5. **检查日志和稳定性报告**
   | 文件 | 内容 |
   |------|------|
   | `~/.openclaw/logs/config-health.json` | 配置健康状态，最后已知良好配置的hash |
   | `~/.openclaw/logs/stability/*.json` | 崩溃/未处理异常的快照（含进程信息、错误堆栈、事件序列）|
   | `~/.openclaw/gateway.cmd` | 旧版Gateway启动批处理脚本 |
   | `~/.openclaw/logs/gateway-restart.log` | 重启日志（记录每次重启尝试的源和结果）|

### 根因

Node.js **v25.8.1** 不满足 openclaw 2026.7.1-2 的版本要求。该版本要求：
- `>=22.22.3 && <23`
- `>=24.15.0 && <25`
- `>=25.9.0`

v25.8.1 落在 `>=25.0.0 && <25.9.0` 的间隙中，被明确拒绝启动。

### 修复方案

| 方案 | 操作 | 适用场景 |
|------|------|---------|
| **升级Node.js** | 安装 v25.9.0+ | 最新特性，但可能遇到其他兼容问题 |
| **降级Node.js到LTS** | 安装 v24.15.0+ (LTS) | 更稳定，推荐 |

### 关键技巧

**从WSL运行Windows node.exe必须使用Windows路径格式**

```bash
# ❌ 失败 — WSL的 <C盘>/... 路径不被Windows node识别
<C盘>/Program\ Files/nodejs/node.exe <C盘>/Users/.../index.js

# ✅ 成功 — 使用Windows原生路径格式（即使在WSL中调用）
<C盘>/Program\ Files/nodejs/node.exe "C:\Users\<用户名>\AppData\Roaming\npm\node_modules\openclaw\dist\index.js" --version
```

这是因为 Node.js for Windows 在解析模块路径时，会将 `<C盘>/...` 解析为 UNC 路径 `\wsl.localhost\Ubuntu\mnt\c\...`，而WSL的drvfs挂载点不在Windows的模块解析路径中。

**快速获取应用版本兼容性错误**

对于任何通过npm全局安装的Node.js CLI工具，如果怀疑版本问题：
```bash
<C盘>/Program\ Files/nodejs/node.exe "C:\Users\<user>\AppData\Roaming\npm\node_modules\<package>\dist\index.js" --version
```
通常 `--version` 或 `--help` 会在早期就触发版本检查，给出明确的兼容性要求。
