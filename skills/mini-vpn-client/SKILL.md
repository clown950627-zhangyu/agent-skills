---
name: mini-vpn-client
description: 自建 Clash/mihomo 客户端时读。含订阅 UA 坑、PS 编码坑。
version: 1.0.0
---

# 自建 mihomo 客户端（Windows）

部署在 `C:\MiniVPN\`：官方 mihomo 内核 + 自写 HTML 界面 + 订阅更新/系统代理脚本。

## 铁律

1. **不自研协议**。内核用官方 mihomo（MetaCubeX/mihomo releases），安全性和抗封锁都靠它；自己做的是界面和运维层。
2. **中文路径本身不是问题，编码才是问题**。历史上踩的坑是「中文路径 + 无 BOM 的 .ps1」两个因素叠在一起（报 `TerminatorExpectedAtEndOfString` 或“无法识别为 cmdlet”），不是中文路径的错。按下面第 3 条把编码做对之后，工具装 `<项目目录>` 这类中文目录完全跑得通（已验证：带 BOM 的 .ps1 + 纯 ASCII 的 .vbs/.bat + `%LOCALAPPDATA%` 快捷方式）。**用户要求项目文件归档进 `<项目目录>`，别为了避中文路径就把它塞到 `C:\MiniVPN` 这种散落位置**；内核这类无脚本的二进制放哪都行，关键是脚本的编码。
3. **所有 .ps1 必须写 UTF-8 带 BOM**：`open(p,"wb").write(b"\xef\xbb\xbf"+text.encode("utf-8"))`。否则中文字符串直接语法错。

## 订阅拉取的 UA 坑

同一个订阅链接，UA 不对直接 403：

| UA | 结果 |
|:--|:--|
| `clash.meta` | **200 ✅** |
| `Clash/1.18.0` | 200 ✅ |
| `mihomo/1.19.33` | 403 ❌ |
| `ClashforWindows/0.20.39` | 403 ❌ |
| 浏览器 UA | 404 ❌ |

拉订阅统一用 `curl -sSL -A 'clash.meta'`。

## 关键套路

- **只拿订阅里的 proxies / proxy-groups / rules / dns**，端口和控制接口自己写头：
  `mixed-port: 7890` / `external-controller: 127.0.0.1:9090` / `mode: rule`
  并把订阅自带的 `port` / `socks-port` / `external-controller` / `allow-lan` 行删掉，避免冲突。
- **Clash Verge 自带的内核不开控制接口**（只有 7890 监听，9090 死活不通）。要折腾 API 就用官方 mihomo。
- **下载官方内核走 gh-proxy**：`https://gh-proxy.com/https://github.com/MetaCubeX/mihomo/releases/download/...`（直连 GitHub release 会 TLS 断）。
- **一揽子测速**：`GET /group/{分组名urlencode}/delay?timeout=5000&url=<gstatic>` 一次拿全部节点，不必逐个调。
- **延迟低 ≠ 好用**。实测有节点 gstatic 702ms 但 google/youtube 全 000。选节点要看真实站点：`curl -x http://127.0.0.1:7890 https://www.google.com` 看是否 302/200。

## 订阅链接的处置（凭证纪律）

订阅地址 = 机场账号的钥匙（带 token），等于凭证：

- **能让他自己写文件就让他写**：`C:\MiniVPN\订阅链接.txt`，我读文件，不接聊天里的链接。
- **他不在电脑旁、只能发聊天时**：收，但只用一次 —— 不落盘、不打印完整 URL、不写进记忆，拉完立即 `rm` 临时 yaml。
- 生成的 `config.yaml` 只留节点，**不含订阅链接**。
- 完事提醒一句：QQ/微信消息留档，介意就去机场面板点“重置订阅地址”。

## 诊断顺序（先分清是谁的毛病）

```
1. DNS 解析 + TCP 端口探测      → 判断机场死没死
2. 官方内核跑最小配置 + 真站点    → 判断客户端的问题还是机场的
3. 全组 delay 测速              → 挑候选
4. 逐个候选跑 google/youtube    → 定默认节点
```

**TCP 端口通 ≠ 代理可用。**域名能解析、26 个节点端口全通，旧客户端依然全部超时 —— 问题在客户端（内核不开控制接口/配置错），不在订阅。先把“机场死没死”用端口探测排除掉，再换客户端复测，别一上来就换订阅。

## PowerShell 5.1 中文 JSON 会乱码（GUI 里必踩）

`Invoke-RestMethod` 在响应头无 `charset` 时按 Latin-1 解，节点中文名（`美国1`/`香港`）变成 `å\x8f¯å\x9b½` → 拼 API URL 返回 `Resource not found`，或 `-like "*美国*"` 永远匹配不上，看起来像「接口里没这个节点」。

**正解（GUI 内也适用）——读字节显式 UTF-8：**

```powershell
function Get-Json([string]$url) {
    $resp  = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 8
    $txt   = [System.Text.Encoding]::UTF8.GetString($resp.RawContentStream.ToArray())
    return $txt | ConvertFrom-Json
}
```

备选：`curl.exe` 写文件 + Python 读。只在一次性诊断里用，不要写进 GUI。

## 切节点：`PUT /proxies/{组名}`，请求体必须是 UTF-8 字节

```powershell
$enc  = [uri]::EscapeDataString($group)        # 组名先 URL 编码（含空格、中文、顿号）
$json = '{"name":"' + $node + '"}'
Invoke-RestMethod -Uri "http://127.0.0.1:9090/proxies/$enc" -Method Put `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($json)) `
    -ContentType "application/json; charset=utf-8" -TimeoutSec 6 | Out-Null
```

- **`-Body` 传字符串会按 ANSI 编码发出**，服务端收到乱码名 → 400 或静默不切。这是「脚本跑完不报错但节点没变」的头号原因。
- 切完必须回读 `GET /proxies` 看该组 `.now` 是否等于目标名，**再**用真站点验一次；只看 PUT 的 204/200 不算数。
- 切节点不需要重载配置、不需要重启内核。改 `config.yaml` 才需要重启。

## 开关台 GUI（便携版，交付给他自己用）

**现行版本就在** `<项目目录>`（`vpn.ps1` + `启动.vbs` + `install.ps1` + `安装.bat` + `mihomo.exe` + `geoip.metadb` + `config.yaml` + `configs\`），打包件 `<项目目录>`（约 26MB）。要改就改这份，别重新造一个；旧的 `C:\MiniVPN` 是散放的内核目录。

用户要的功能集合固定成这样，不要自己减：**开关 / 代理组 / 国家筛选 / 节点列表 / 测延迟 / 一键切某国 / 导入配置 / 刷新配置**。

结构（PowerShell WinForms，零依赖，单文件 `vpn.ps1` + `.vbs` 静默拉起）：

| 控件 | 实现 |
|:--|:--|
| 状态灯 | `Get-Process mihomo` 有/无，顺便显示 PID、代理端口 |
| 代理组下拉 | `GET /proxies` 里 `type -eq 'Selector'` |
| 国家下拉 | 对节点名做关键词匹配（美国/香港/日本/台湾/韩国/新加坡/马来/越南/德国/法国/英国/泰国）→ 其余归「其它」；选完只列该国节点 |
| 节点列表 | `组.all` 过滤，当前节点标青色；**列要带延迟列**，测速后回填 |
| 测延迟 | 逐节点 `GET /proxies/{name}/delay?timeout=4000&url=http://www.gstatic.com/generate_204`；<400 绿、<900 白、超时灰 |
| 导入配置 | `OpenFileDialog` → 拷进 `configs\`（留档）再覆盖 `config.yaml` → 重启核心 |
| 刷新配置 | 杀进程 → 重起 → 重新拉 `/proxies` |

四个坑：

1. **默认组不能选 `GLOBAL`**。`GLOBAL` 也是 `Selector` 类型且节点最多，但里面混着组名，选它当主组后「切美国」会切错层。优先选名字里带机场关键词（如 `可可`）的组；匹配不到再退到第一个。
2. **`.vbs` 用 `WScript.Shell.Run(cmd, 0, False)` 藏掉控制台，且 `.vbs` 只写 ASCII**（`dir = fso.GetParentFolderName(WScript.ScriptFullName)` 取自身目录，不要写死中文路径；路径里带中文也能正常拼进 `-File` 参数），`cmd` 里 `-WindowStyle Hidden -File <绝对路径>`；`.vbs` 存 UTF-16 LE 带 BOM，`.ps1` 存 UTF-8 带 BOM。
3. **验收不能靠抢前台**——`SetForegroundWindow` 被前台锁拒；用 `PrintWindow(hwnd, hdc, 2)` 抓窗口自己的位图再 `vision_analyze`（详见 `windows-operations` §3）。
4. **打包给别人电脑用**：`Compress-Archive` 整个目录成 zip（内核 + geoip + `config.yaml` 一起打，装完即用不用重导订阅），对方解压 → 双击 `安装.bat`（拷到 `%LOCALAPPDATA%` + 建桌面快捷方式）→ 双击快捷方式。不写注册表、不装服务。


## 界面要点

- 主分组名不可写死（机场会起“可可云-收藏此官网…”这种长名）。用 `Selector` 类型里节点数最多的那个作主分组。
- mihomo 控制接口默认 `Access-Control-Allow-Origin: *`，`file://` 打开的 HTML 直接 fetch 127.0.0.1:9090 没问题。
- WSL 里的浏览器访问不到 Windows 的 127.0.0.1:9090 → **在 WSL 浏览器里验证界面会假失败**，要在 Windows 浏览器里看。

## 文件职责

```
C:\MiniVPN\
  启动.vbs          双击：内核静默启动 + 打开界面（纯 ASCII）
  mihomo.exe        官方内核
  config.yaml       头(端口/控制接口) + 订阅的 proxies/groups/rules
  restart.ps1       重启内核（换配置后用）
  更新订阅.ps1      读 订阅链接.txt → 拉取 → 校验 → 备份 → 重启
  系统代理.ps1      on/off 改 HKCU Internet Settings
  check.ps1         出口实测
  ui\index.html     深色 + 电光青界面
```

## Chrome（用户级安装，不需管理员）

- 下载 per-user 安装器（12.7MB）：`https://dl.google.com/chrome/install/latest/chrome_installer.exe`，走代理下
- 静默装：`chrome_installer.exe /silent /install` → 装到 `%LOCALAPPDATA%\Google\Chrome\Application`，**不弹 UAC**
- **铁律：Chrome headless 不读 Windows 系统代理**，必须加 `--proxy-server=http://127.0.0.1:7890`；不加时 Google 全挂、百度正常，很容易误判成“没装好”
- 开始菜单快捷方式用 `WScript.Shell.CreateShortcut` 把 Arguments 写成 `--proxy-server=http://127.0.0.1:7890`（用户级目录不需管理员）

## 生命周期：双入口，我启我停

用户的立场很明确：**电脑上的 VPN 归我用，他不会操作，不用时不能挂着**。所以交付形态固定成两个双击入口：

| 文件 | 作用 |
|:--|:--|
| `启动.vbs` | 内核静默启动 + 打开界面（纯 ASCII，`Start-Process -WindowStyle Hidden`） |
| `关闭.vbs` | 先关系统代理 → 再 kill mihomo → `MsgBox` 报结果 |

- 我做事需要出墙时自己起，**做完自己关**（`stopcore.ps1`：杀进程 + 关代理 + 回读 7890/9090 不再监听）。

### 用户说「我能不能自己开关」时：交付带状态的窗口，不是 bat

这句话的意思是「别再让我去点客户端托盘、也别给我黑窗口」。交付物必须是**双击就开、一眼看见当前状态**的小窗口，落在桌面。

形状：PowerShell WinForms（零依赖）—— 一个标题 + 一个状态灯（● 已开启 青色 / ○ 已关闭 灰）+ 开/关两个按钮；外层 `.vbs` 用 `sh.Run(cmd, 0, False)` 静默拉起（`0` = 不弹控制台窗口），桌面放 `.lnk`。

四条必须做到的：

1. **改完注册表要通知系统**，否则浏览器不认，用户点了「开启」还是打不开：
   ```powershell
   [WI]::InternetSetOption([IntPtr]::Zero, 39, [IntPtr]::Zero, 0)   # SETTINGS_CHANGED
   [WI]::InternetSetOption([IntPtr]::Zero, 37, [IntPtr]::Zero, 0)   # REFRESH
   ```
2. **`.ps1` 存 UTF-8 带 BOM**，否则中文标题/按钮变乱码。
3. **`.vbs` 存 UTF-16 LE 带 BOM**：VBScript 不认 UTF-8 无 BOM，含中文的路径会被按 ANSI 解成乱码，静默启动直接失败。写盘：`open(p,"wb").write(b"\xff\xfe"+s.encode("utf-16-le"))`。
4. **验证窗口真起来了**（WSL 截不到 Windows 桌面）：`Get-Process powershell | ? MainWindowTitle` 取标题，但这标题经管道回 WSL 必乱码——用 `Out-File -Encoding utf8` 写到 `C:\Windows\Temp\x.txt` 再 `read_file` 读，字对了才算成。

配套一句解释给他：「mihomo 一直常驻，这个窗口只管浏览器走不走代理」——否则他会以为开关一次等于开关两个东西。

### ⭐ 超时就是“该起 VPN 了”的信号——不要先问，直接起再重试

用户原话：*"超时了就开 vpn 再试试呢"*。凡是碰到以下任一现象，**先起内核再重试一次**，
而不是回头报告“搜索超时了 / 拿不到数据”：

```text
npx / npm 包拉不下来·GitHub API 返回空或超时·海外站点 403/超时·skills.sh 之类境外服务
```

````bash
# 起（WSL 一行，不用打开界面）
powershell.exe -NoProfile -Command "Start-Process -FilePath 'C:\MiniVPN\mihomo.exe' -ArgumentList '-d','C:\MiniVPN' -WindowStyle Hidden"
# 验（204 才算通；WSL 用默认网关当代理地址）
curl -s -m 15 -x http://$(ip route | awk '/default/{print $3}'):7890 -o /dev/null -w '%{http_code}' https://www.google.com/generate_204
````

- WSL 的代理地址是 **Windows 主机在 WSL 里的网关 IP**（`ip route` 第一个 default），
  不是 127.0.0.1；实测为 `172.30.x.1:7890`。
- 起之前先查 `Get-Process mihomo` 是否已在跑，避免重复启动。
- 用完不需要主动关（他若问“很卡/耗电”再关）；不要为了省事把代理写进全局环境变量。
- 不做开机自启：他不用它开机常驻，自启只会多一层他看不懂的后台。
- 关闭顺序必须是**先关系统代理再杀内核**，反了会出现“代理开着但内核已死”的上网断流。

## 内核在跑 ≠ 浏览器走代理（先查系统代理开关）

现象：`mihomo.exe` 在跑，WSL 里 `curl -x 网关IP:7890` 打 google 全通，**但 Windows 上的 Chrome 什么境外站都打不开**。

不要重启内核。先查开关：

```bash
<C盘>/Windows/System32/reg.exe query \
  "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" \
  | grep -Ei "ProxyEnable|ProxyServer"
```

`ProxyEnable = 0x0` 就是关着（`ProxyServer` 可能已经写好 `127.0.0.1:7890` 但没启用）。从 WSL 直接打开，**HKCU 不需要管理员**：

```bash
<C盘>/Windows/System32/reg.exe add \
  "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" \
  /v ProxyEnable /t REG_DWORD /d 1 /f
```

改完让用户在 Chrome 里直接重试，不用重启浏览器。

**WSL 的 curl 走通不代表 Windows 浏览器也走代理** —— 两套代理设置是独立的，必须分别验。看到「浏览器打不开」先量系统代理，再谈节点。

## 退役旧客户端（Clash Verge）

不需要管理员，也不会弹 UAC：

```powershell
Start-Process -FilePath "C:\Program Files\Clash Verge\uninstall.exe" -ArgumentList "/S" -Wait
```

四步清干净（漏一步就会留下带节点密码的残留）：

1. 先备份 `%APPDATA%\io.github.clash-verge-rev.clash-verge-rev\`（30MB 左右，含订阅/节点）到业务库，
   再删原目录——**删用户的配置前先能补回**。
2. 跑 `uninstall.exe /S`，验证 `clash-verge.exe` 已不存在。
3. 删 `%APPDATA%` 配置目录（卸载器不会动它）。
4. 回扫 `Program Files` / `Program Files (x86)` / `%LOCALAPPDATA%` 下 `*lash*` 是否还有残留。

卸载后必须复测自建的那套（起内核 → `curl -x` 打 google → 关内核），确认两者无依赖。

## 选节点：按目标站选，不按延迟选

同一机场的美国节点常常出现「google 302 但 chatgpt 000」：数据中心 IP 段被 Cloudflare 重点拦。
按用途分流，并把结论告诉用户而不是只报延迟：

| 场景 | 选 |
|:--|:--|
| 日常网页/YouTube/代码站 | 香港、台湾（延迟低且全站通） |
| 需要美国出口 | 逐个试 `美国1/2/3`，选 google 302 + youtube 200 的那个；chatgpt 多半仍 000/403 |
| 只看网页快不快 | 只看 gstatic 延迟会被误导（702ms 的节点可能 google/youtube 全 000） |

**但「某站点必须美国节点才能用」时，连通性优先级高于延迟**：800ms 的美国节点能让 chatgpt.com 返回 200，300ms 的香港节点不行。判据是目标站的状态码，不是 gstatic 延迟排行。测完三个美国节点直接选能通的那个（哪怕最慢），并告诉他为什么。

## 验收口径

至少跑通这五个：gstatic 204 / google 302 / youtube 200 / api.github 200 / chatgpt 非 000。
chatgpt 返回 403 是节点 IP 被 Cloudflare 拦，不算不通，但要告诉用户换节点。

## 测陌生节点：先建隔离测试实例，绝不碰在跑的主实例

要试一批陌生节点（免费源、新机场、别人的订阅）时，**另起一套实例**，别往用户正在用的 `config.yaml` 里塞：

```text
独立目录    C:\Windows\Temp\freetest\   （拷一份 mihomo.exe + 测试用 config.yaml）
独立端口    mixed-port 7895  /  external-controller 127.0.0.1:9095
启动        Start-Process mihomo.exe -ArgumentList '-d','C:\Windows\Temp\freetest' -WindowStyle Hidden
清理        按命令行带 'freetest' 精确匹配杀：Get-CimInstance Win32_Process -Filter "Name='mihomo.exe'"
            | ? CommandLine -like '*freetest*' | % { Stop-Process -Id $_.ProcessId -Force }
            ——绝不用 Stop-Process -Name mihomo，那会杀掉用户正在用的那条线
```

**必须带对照组**：先用已知能用的付费节点测一次延迟，确认测量通路本身没问题，再去判“这批节点全死”。
没有对照组的「0 个可用」分不清是节点死还是自己测错（端口不对、实例没起、API 不通）。

**WSL 连不到 Windows 的 127.0.0.1**，把 `external-controller` 改成 `0.0.0.0` 也常被主机防火墙挡住。
探测一律写成 `.ps1` 从 Windows 侧用 `-File` 跑，结果 `Out-File -Encoding UTF8` 落文件、WSL 用 `encoding='utf-8-sig'` 读回。
连不上就当基线，别在“为什么 WSL 连不上 9095”上耗时间。

**批量测速不要一次测几百个**：`GET /group/<组>/delay` 对 160 个节点会直接返 504。
分层抽样（每个源取 8 个）+ 逐个 `GET /proxies/<urlencode(name)>/delay?timeout=2500` 才能拿到可信结果。

## 免费公开节点：能用，但命中率 ~4%，只能做不涉账号的事

实测口径（3 个当日更新的公开源、去重 2692 个、分层抽样 24 个）：**只有 1 个活下来**，1829 ms，
google/youtube/chatgpt 均 200；同一时间付费节点 2193 ms。免费的并不更快，只是不要钱。

- 命中率低不要紧，**机器筛**：拉源 → 测延迟 → 用真实站点复验 → 把活的合并成一份 `config.yaml`。
  手挑一次没意义，第二天全变。源地址与完整筛选流程见 `references/free-node-screening.md`。
- **安全是硬伤**：免费节点是陌生人的服务器，明文流量全在他眼里。规矩：只用于查资料/看图；
eBay、Payoneer、ChatGPT 登录、微信、银行一律走付费线路。这条要主动告诉用户，不要等他问。

## 手机端 / 全屋：能做与做不到

用户问“安卓和鸿蒙能不能装”时，先分清手机是哪代鸿蒙——它决定有没有得做：

| 设备 | 能不能 | 做法 |
|:--|:--|:--|
| 安卓 / 鸿蒙 2·3·4（还能装 APK） | ✅ | 装 Clash Meta for Android（同为 mihomo 内核），导入同一份 `config.yaml` 就完事 |
| 鸿蒙 NEXT（5.x，纯血） | ❌ | 不认 APK，只能装 HAP；第三方自签应用拿不到系统 VPN 权限。直说做不到，给替代（旧手机 / 电脑端） |

**不要为“做个手机版 VPN”去写 App**：手机 VPN 必须是系统级 VpnService，自研要签名和系统权限，成本远超收益。
现成内核 + 自己那份配置就是正解。

**省钱的正解往往是“共用一份订阅”，不是换更便宜的机场**：`config.yaml` 里 `allow-lan: true` 时，
局域网设备在 WiFi 设置里手动填 `电脑IP:7890` 就能走同一条线，零额外成本、不用买新订阅。

## 集成进路由器 / 交换机：先分清三层东西

```
家用二层交换机   做不到——没 CPU、没系统，纯转发芯片
路由器          能，前提是能刷 OpenWrt（ARM 版 mihomo + tproxy 透明代理）；光猫一体机基本刷不了
旁路由（推荐）   不动路由器，让这台 M920q 开透明代理、局域网网关指过来
                性能比路由器强一个量级、可远程维护；代价是主机侧要开转发/NAT
```

**必须提前说的坑**：全屋走代理会连带影响国内业务（外卖后台、抖音、微信支付、银行）——分流规则没配好
就是又卡又被风控。不要一刀切全局。

用户只是“说说想法看能不能实现”时，回答可行性就收住：不下单买硬件、不改网络配置。
他说“不需要”“省一点用”就是到此为止。
