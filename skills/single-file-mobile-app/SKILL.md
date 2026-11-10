---
name: single-file-mobile-app
description: 做自用单文件 HTML App（提醒/打卡/记录）时读。先规划后写码、内嵌图库、手机验证、交付。
version: 1.0.0
author: 小爱
license: MIT
metadata:
  hermes:
    tags: [App, PWA, 单文件, localStorage, 移动端]
    related_skills: [health-lifestyle-business, visual-content-production]
---

# 单文件移动端 App

## When to Use

- 用户要「做个 App」「提醒软件」「打卡系统」「记录工具」，**先自己用、不上架**
- 要一个手机上能打开、能存数据、离线可用的工具
- 要在网页里嵌真实照片/图例库

不适用：需要真正后台推送/开机自启/系统权限的 → 走安卓 WebView 壳打包（`android-webview-apk-packaging`），但仍先用单文件 HTML 把内容跑通。

## 铁律零：先规划，后写码（跳过这步必返工）

**用户原话：「缺乏规划，我们重新开始」—— 他给的是规划，不是代码。** 直接写 HTML 一路加功能，结果必然是主页面选错、功能散、图标临时画、数据结构只有一个 localStorage 键，前面写的全要重来。

开写之前必须走完这八步，其中 **0-5 步是纸面工作，一步代码都不要写**：

```
第 0 步  需求      解决什么问题？给谁用？不做什么？（边界最重要）
第 1 步  信息架构   几个页面？怎么跳？谁是主页面？（先定主页面）
第 2 步  线框图     每页长什么样？元素放哪？（做成能点的 HTML 静态稿，不是图片）
第 3 步  视觉规范   配色、字体、launcher 图标、间距、圆角
第 4 步  数据模型   存什么？按功能分键，不要塞进一个 state
第 5 步  技术选型   纯 HTML / 纯原生 / 混合（HTML + 原生通知桥）
第 6 步  分阶段开发  一期只做什么？
第 7 步  真机验证   装上去用一天
第 8 步  迭代
```

### 主页面怎么定 —— 先问「他什么时候打开」，不要默认

**不要默认「今日」，也不要默认某个功能模块。主页面由「打开时机」决定：**

| 他说的打开时机 | 主页面 |
|:---|:---|
| 早上起来先看一眼今天要做什么 | 今日（各条业务线平权） |
| **健身时打开，手机拿在手上或放器械边** | **主场景页（当天课表），一秒进入，不点任何东西** |
| 晚上睡前回填今天的数据 | 今日 / 记录 |
| 「吃药和小提示驻留在系统里」 | 这句是强信号 —— 说明这些不该占主界面，靠通知推，把主页面让给主场景 |

**判断句：「他打开 App 的那一刻，最想看到的是哪一屏」—— 那一屏就是主页面，不是你以为该有的总览页。**

Tab 数量：自用 App **三到四个**（主场景 / 记录或数据 / 我的）。五个以上要么砍，要么说明需求没收窄。

### 规划稿要回答用户的六问

用户会这样验收规划：**步骤是什么 → 要不要先做框架 → 主页面是什么 → 有哪些大功能 → 大功能里有什么小细节 → 图标什么样**。规划文档缺任何一问都算没写完。

**每块大功能底下必须给「小细节」清单**，例如训练模块：显示上次成绩、点组按钮弹重量/次数记录、记完自动开始休息倒计时、休息时显示下一组是哪组、全部做完弹训练总结。只写「训练记录」四个字等于没写。

### 「智能建议」的入口 = 训练后的一张选择题

用户原话：「运动结束后给他上个选择题，有针对性地收集训练效果，然后给他最个性化的建议」。

```
客观数据（重量/次数）  ×  主观数据（强度感受/疼痛）  →  才能出个性化建议
```

设计约束：

```
· 训练完成后自动弹出，不要让他手动进
· 5 题，每题一次点击，总共 10 秒答完（健身完手是湿的、注意力是散的）
· 只问机器测不出来的：整体强度够不够 / 哪个动作最吃力 / 关节有没有不适 / 体力状态 / 明天怎么安排
· 建议只出现在「训练结束总结」+「每周报告」，不要放训练页顶部做实时提示
```

没有这张选择题，App 只能输出通用废话；有了它，同一个规则引擎才能同时扮营养师 / 教练 / 护士三种口吻。

### 规划完必须让用户拍板的决策项

列成编号清单一次性给出（主页面、Tab 数量、要不要记重量这类关键取舍、技术方案、图标方案），**不要自己拍板**。他答完再画线框图，线框图确认了再开发。

## 铁律零之二：先有「用户资料」，再有功能

一旦 App 里要有任何「根据你的情况给建议」的能力（补剂推荐、训练调整、营养餐），**用户资料就是地基，不是可选项**：

```
资料要收：年龄 / 性别 / 身高 / 体重 / 腰围 / 目标
        + 基础疾病（多选）+ 用药清单 + 过敏史
```

**基础疾病是分流器** —— 补剂该不该推、训练要避开哪些动作、营养餐怎么配，全靠这一项分支。没有它，「个性化建议」只能输出通用废话；有了它，同一个引擎能同时扮营养师 / 教练 / 护士三种口吻。

**别把某一个人的数据写死进通用功能。** 他本人的痛风+糖尿病是**验收用的第一个样本**，不是产品假设（原话：「补剂这一块先不考虑是我使用」）。功能要设计成「谁填了资料谁能用」，否则第二个用户进来就得重写。

### 资料在首次启动一次性收完，之后不再打扰

**用户原话：「病史，补剂这些在登陆时候就一次性填写，不用每次都填哈」。**

只做一个「随时能进去改的资料页」是不够的 —— 第一次打开时资料是空的，所有依赖资料的规则全部不生效，等于白做。必须是**首次引导流程（onboarding）**：

```
第 1 屏  欢迎：这个 App 会用你的资料做什么 + 免责声明（不是医疗器械）
第 2 屏  基本：年龄 / 身高 / 体重 / 目标值（尿酸、饮水这类可量化的目标）
第 3 屏  目标（多选）
第 4 屏  基础疾病（多选）—— 勾完立刻回显「已启用 N 条保护规则」
第 5 屏  他在吃哪些补剂 —— 用刚选的疾病过滤，不能吃的当场标红并写原因
→ 完成时写 localStorage 的 onboarded 标记；之后每次打开直接进主场景页
```

```js
if(!profile.onboarded){ 显示引导页; 底部 dock 隐藏 }
else { 直接进主场景页; renderEx() }
```

**第 4、5 屏是引导的价值点，不是走过场** —— 疾病一勾马上回显命中了哪些规则、补剂马上标红写原因，用户当场就看见「这 App 真懂我」。没有这两处实时回显，五屏引导在他眼里就是五屏表单，填到第三屏就烦了。

引导页只填一次，改资料的口子留在「我的」里。**不要为了省事把资料页当引导用** —— 资料页是横向铺开给他改的，引导是纵向一步步问的，两者顺序感和心理负担完全不同。

每屏一屏一件事，底部固定「上一步 / 下一步」（第一屏隐藏上一步，最后一屏按钮文案改「开始使用」），顶部给 `N / 5` + 细进度条。

疾病 → 补剂/训练/营养 的规则表在 `health-lifestyle-business` 技能的 `references/supplement-condition-rules.md`。

### 定位一升级，旧代码立刻不作数（汇报时必须分开说）

定位从「训练记录工具」变成「随身营养师 + 教练 + 护士」之后，那个能跑、能装、签名验证通过的原型，
**不是「完成了 80%」，是一个别的产品**。它缺资料层、缺按病过滤的补剂库、缺选择题与建议引擎。

```
✅ 汇报分两列：
   能跑的旧原型 —— 列它真有的（课表/组数/倒计时/图库/APK）
   新定位还缺什么 —— 逐条列，带估时
❌ 不要说「APK 打包成功了，项目快完了」
```

**定位每变一次，一页纸的 Must 必须重写一遍再开新代码。** 拿旧 Must 直接往下加功能，
加出来的必然是拼不起来的两半。

## 为什么是单文件 HTML

```
原生 App  → 要签名、要上架、要审核，自用完全不值
框架项目  → node_modules、构建、部署，一个提醒工具不值得
单文件 HTML → 双击就能开，微信/QQ 传过去就能用，加到主屏和 App 一样
```

**顺序：单文件 HTML 跑通内容 → 他确认内容对了 → 才打包成 APK。** 反过来先打包，内容一改就要重打包。

## 铁律：图例用真实照片，不要自己画

**用户原话：「每次做的图标都好丑」。** 任何代表真实物体/人体动作的地方（动作示意、器械、产品、食材），**用真实照片库，不要手绘 SVG、不要 emoji、不要占位色块**。emoji 只能出现在按钮这种纯功能位置。

### 健身动作图库：free-exercise-db

```
仓库  github.com/yuhonas/free-exercise-db
授权  The Unlicense —— 完全公有领域，可商用
规模  876 个动作，每个 2 张照（0.jpg 起始位 / 1.jpg 结束位）
数据  dist/exercises.json（982KB），字段含 name / equipment / level / primaryMuscles / instructions / images / id
图片  raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/{id}/{0|1}.jpg
```

拉全套图片必须先设代理，再按 id 批量 curl；**下载后校验 `stat -c%s > 3000`，小于这个数是 404 页面存成了 jpg。**

常用 id 对照（中文计划 → 库里 id）：蝴蝶机 `Butterfly`、器械推胸 `Leverage_Chest_Press`、上斜推胸 `Incline_Dumbbell_Press`、下斜推胸 `Decline_Barbell_Bench_Press`、臀桥 `Butt_Lift_Bridge`、罗马尼亚硬拉 `Romanian_Deadlift`、髋外展 `Thigh_Abductor`、站姿提踵 `Standing_Calf_Raises`、高位下拉 `Wide-Grip_Lat_Pulldown`、坐姿划船 `Seated_Cable_Rows`、面拉 `Face_Pull`、哑铃弯举 `Dumbbell_Bicep_Curl`、腿举 `Leg_Press`、平板支撑 `Plank`、椭圆机 `Elliptical_Trainer`。
库里没有靠墙静蹲 —— 这类缺项就给文字要点，不要用相似动作的图冒充。

## 去 AI 感：抄成熟产品的 token，不要靠感觉配

**用户原话：「界面ai感太强，你学习研究并借鉴一下国外相关app的设计风格」。** 「AI 感」不是玄学，是六条具体特征，逐条反着做就干净了：

| AI 感来源 | 反着做 |
|:---|:---|
| 电光青 / 荧光紫强调色 | 全 App 只留**一个**低饱和行动色（推荐蓝 `#4C8DFF`） |
| 渐变背景、发光、glow | 纯色分层，靠 1px 边框拉开层次，不用阴影 |
| 圆角 18-24px 的「软糯」卡片 | 圆角 8-12px |
| 字重 800-900 喊口号 | 字重 500-600，页面标题 700 封顶 |
| emoji 当图标 | 线性 SVG 图标，`stroke-width:1.6`、`fill:none` |
| 间距靠内边距凑 | 大区块间距 32-48px 显式拉开 |

配色别自己调，直接搬成品 token：Hevy / WHOOP 两套完整数值（四级灰阶、accent、语义色、字号间距刻度、行式表格 CSS）见 `references/ios-fitness-design-tokens.md`。

**⚠️ 别把营销物料的视觉风格搬到工具界面上。** 用户对「宣传图 / VI / 海报」要的是深色底 + 电光青 `#00E5FF` + 发光 + 网格；但这套用在**要天天用的工具 App 界面**上就是「AI 感太强」，必被驳回。分界线是：

```
营销物料 / 海报 / 封面 / 视频  → 可以电光青、可以发光、可以大字距，目的是一眼抓住
工具 App / 后台 / 仪表盘      → 单行动色、无发光无渐变、克制灰阶，目的是天天看也不腻
```

同一个用户，两套标准，不要混。做 App 时一律走 Hevy token。

WHOOP 的设计原则一句话：**「Black breathes」—— 黑是有呼吸的，不是空白。** 深色底上靠四级灰阶（canvas → card → raised → raised2）分信息层级，不要靠加边框加阴影。

**数字必须 `font-variant-numeric: tabular-nums`**（挂在 body 上即可）。训练时数字一跳就是外行。

**改版顺序**：先把 token 全局换掉，再逐屏调结构。token 换了 AI 感去掉一半，还剩下的那部分一定是结构问题（比如组记录用卡片堆而不是行式表格）。

## 图片内嵌：压到 18KB 一张

```python
im = Image.open(f).convert('RGB')
nw = 420; nh = int(im.size[1] * nw / im.size[0])
im = im.resize((nw, nh), Image.LANCZOS)
buf = io.BytesIO(); im.save(buf, 'JPEG', quality=74, optimize=True, progressive=True)
b64 = 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()
```

**420px 宽 / q74 ≈ 18KB → base64 后 25KB。** 30 张 = 555KB，加上骨架整个 HTML 0.74MB —— 单文件传手机舒服的上限就在 1MB 左右。别再大，手机上打开会卡。

图片数据用 Python 注入模板：模板里写占位符 `const IMG = __IMG_DATA__;`，生成时 `HTML.replace('__IMG_DATA__', json.dumps(b64map))`。**不要手写 base64 进 HTML 文件。**

## 骨架：sticky 头 + 滚动内容 + 固定底栏

```css
.hd  { position:sticky; top:0;    z-index:10; backdrop-filter:blur(18px); }
body{ padding-bottom:130px; }        /* = 底栏高度 + 安全区，少了会盖住最后一张卡 */
.dock{ position:fixed; bottom:0; left:0; right:0; z-index:20;
       padding:11px 14px calc(11px + env(safe-area-inset-bottom)); }
```

**`padding-bottom` 必须显式给，且要大于底栏实际高度。** 底栏盖住正文是这类 App 最常见的返工点，因为首屏截图上看起来就像「文字被截断了」。

固定底栏只放 1 行主操作（记录 + 主计时）。**统计数字合并进按钮文案**（`💧 1200 ml`），不要单独占一行 —— 两行底栏会吃掉训练页最宝贵的一屏。

## localStorage：按日期分 key

```js
const key = 'tz_' + new Date().toISOString().slice(0,10);
let state = JSON.parse(localStorage.getItem(key) || '{"sets":{},"water":0}');
const save = () => localStorage.setItem(key, JSON.stringify(state));
```

每次改动都同步 `save()`，不要等页面关闭 —— 手机上页面被切走就再也不回来了。

## 音效：必须等用户第一次触摸才解锁

**这是最容易漏的坑：Web Audio 在没有用户手势前是 suspended 状态，训练时提示音一声都不响。**

```js
let actx = null;
document.body.addEventListener('touchstart', function once(){
  try{ actx = actx || new (window.AudioContext||window.webkitAudioContext)();
       if(actx.state === 'suspended') actx.resume(); }catch(e){}
  document.body.removeEventListener('touchstart', once);
});
```

计时结束要响两遍（间隔约 480ms），一遍在健身房根本听不见。配合 `navigator.vibrate(ms)`。

## 交互三态：待练 / 当前 / 完成

组按钮不能只有「点过/没点过」两态。三态才符合训练时的心智：

```
灰底灰字   = 还没做
青色描边   = 现在该做这一组（自动指向第一个未完成）
绿底打勾   = 已完成
```

一键完成一组后**自动弹出组间休息倒计时**，不要让他再点一次 —— 训练时手是湿的、注意力是散的。

## 验证：必须用 CDP 模拟手机视口

```python
# 正确：真改 CSS 视口
cdp("Emulation.setDeviceMetricsOverride", width=390, height=844,
    deviceScaleFactor=2, mobile=True)
```

**顺序有讲究：先 `setDeviceMetricsOverride`，再 `goto_url`。** 先导航后设视口，截出来还是桌面窗口尺寸（宽 > 高）。而且 **`new_tab()` 会把 Emulation override 清掉** —— 要换页用 `goto_url()`，或者 new_tab 之后重新设一遍。

判断视口到底生效没有，只看这一行：

```python
print(js("[window.innerWidth, window.innerHeight]"))   # 必须 [390, 844] 这种竖屏值
```

打印出来宽 > 高（比如 `[780, 437]`）就是没生效，**别去改 CSS**，是调用顺序错了。

**`chrome --headless --window-size=390,844 --force-device-scale-factor=2` 不会改变 CSS 视口** —— 它只改输出像素尺寸，页面仍按桌面宽度布局，截图上右侧内容被裁。看到这个现象**不要以为布局坏了去改 CSS**，是截图方法错了。

截图后逐项确认，不要只看「有没有报错」：

```python
print(js("document.querySelectorAll('.pic img').length"))            # 图片数量对不对
print(js("Array.from(document.querySelectorAll('.pic img')).every(i=>i.naturalWidth>0)"))  # base64 真的解出图了
print(js("document.querySelectorAll('.med-item').length"))           # 关键卡片渲染了
```

`naturalWidth > 0` 是内嵌 base64 是否有效的唯一可靠判据 —— `src` 有值不代表图能显示。

## 交付

```
D:\<项目目录>\<项目>\<子目录>\<名称>.html      ← 正式存档
C:\Users\<用户名>\Desktop\<名称>.html            ← 用户随手双击
```

两个都写。用户极度偏好可视化 GUI、讨厌命令行 —— **交付话术里不要出现「起个本地服务器」当主推方案**，先说「双击桌面那个文件就能用」。手机端落地再单独谈（打包 APK 或静态托管），不要混在一起讲。

### 打包成 APK 后必须回验（唯一能证明“装进去的就是你看过的那个版本”）

```python
z = zipfile.ZipFile(APK)
inner = z.read("assets/www/index.html")
src   = open(HTML, "rb").read()
assert hashlib.sha256(inner).hexdigest() == hashlib.sha256(src).hexdigest()
print(len(inner), len(src))   # 字节数也要对，不能只比 sha
```

**为什么要比哈希：** 生成链是「脚本 → HTML → 拷进 assets → 打包」，中间任何一步用了旧文件，装上去的就是旧版。`len()` 相等、`sha256` 相等两条都过才算真同步。

配套三道一起跑：`aapt2 dump badging`（包名/应用名/versionCode/minSdk）→ `apksigner verify --verbose`（必须 Verifies）→ `zipfile.testzip()`（返回 None）。

**aapt2 会把 res 文件名混淆成 `res/9w.png` 这种** —— 图标不在哪个已知路径，从 `dump badging` 的 `application: icon='res/9w.png'` 那一行拿到实际文件名，再用 zipfile 解出来看。

## 已踩过的坑

- **用药/次要卡片占首屏太大** → 训练页主体必须是训练，次要信息折叠或降到底部。
- **`launcher` 图标不能自己拍板**：程序画的几何图形（哪怕画得对——哑铃一眼认得出）依然会被批「很通用」，因为健身 App 九成都是纯哑铃。**出 3 个方案让用户选**（例如：进度环+器材剪影 / 日历+勾 / 汉字），每个方案写一句「优势/劣势」。图标和小程序内的视觉语言要同色系。
- **数据模型不能只有一个 state 键**：按功能分键（`profile` / `plan` / `log_YYYY-MM-DD` / `body` / `settings`），否则第二天想加「体重趋势」时发现历史只存了当天的组数。导出/导入用 JSON 打包全键，比同步云端简单可靠。
- **浏览器工具的文件路径**：browser_exec 的 Chrome 在 WSL 里跑，`file:///C:/...` 会返 `ERR_FILE_NOT_FOUND`。先把文件 `shutil.copy` 到 `/tmp/` 再用 `file:///tmp/...`。
- **页面里不要用 `alert()` / `confirm()`**：`alert()` 阻塞 JS 线程，browser_exec 的 `Runtime.evaluate` 会一路等到超时，整个验证流程卡死（看起来像「浏览器挂了」，其实是弹窗没人点）。校验失败一律用页面内 toast：`position:fixed` + `opacity` 过渡 + 2 秒自动消失，不阻塞也更好看。真机上系统弹窗同样丑。
- **进度条太淡** 会被当成普通分隔线 → 进度值同时给文字数字。
- **emoji 当图标** → 只允许在按钮上，内容区一律真实照片。
- **交付前先想「打开了算不算提醒」**：单文件 HTML / WebView 壳只能做到「打开才看到」，做不到「到点自动弹通知」。**交付时主动说清这条边界**，不要让用户装了才发现不会响。

### 要真后台定时提醒，选 Capacitor 不要裸 WebView

裸 WebView 里加原生通知要自己写 AlarmManager + Notification 桥，每个坑都要踩一遍。**Capacitor 有现成插件：**

```
capacitorjs.com/docs/apis/local-notifications
官方原文：schedule device notifications locally
         (i.e. without a server sending push notifications)
→ 本地排通知，不需要服务器；且复用全部 HTML 代码不推翻
```

**⚠️ Android 12+ 必加精确闹钟权限**，否则系统为了省电会把通知往后挪（可能晚几十分钟）—— 提醒类 App 这是致命的：

```
SCHEDULE_EXACT_ALARM（写进 AndroidManifest.xml）
即使加了权限，用户仍可在设置里关掉 → 用 checkExactNotificationSetting() 查状态并提示
```

**技术路线三段（一步一步换，不推翻前一步）：**

```
第一版  单文件 HTML + localStorage（零构建、零审核，改一行就生效）
第二版  要准时后台提醒 → Capacitor 套壳 + LocalNotifications
第三版  要读健康数据/手表/蓝牙 → 转原生（WebView 拿不到 HealthKit）
```

**不要为了「看起来像个 App」而先套壳上架**：自用工具上架带来的是审核、隐私声明、每年适配成本，收益接近零。
