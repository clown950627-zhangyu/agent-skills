# 深色移动端设计 token（健身 / 健康类）

抄成熟产品的成品数值，不要自己调色。以下两套都是实际抓下来的完整 token，直接搬进 `:root` 即可。

源参考：GitHub `Meliwat/awesome-ios-design-md` 下的 `design-md/fitness/hevy/DESIGN.md` 与 `whoop/DESIGN.md`。

---

## 为什么优先抄 Hevy

Hevy / Strong 这类力量记录工具的设计目标是「健身房灯光下、手是湿的、一眼看清」，正好是自用健康 App 的使用场景。它的克制程度可以完整解决「AI 感」问题：

- 只有一个行动色（蓝），其余全是灰阶
- 层次靠 1px 边框和四级灰阶，完全不靠阴影和发光
- 圆角 8-12px，字重 500-600
- 数字全部 tabular-nums

---

## 完整 token

```css
:root{
  /* 四级灰阶 —— 层次就靠这四级，不要再加阴影 */
  --canvas:#0E1116;    /* 页面底，近黑偏蓝冷。不是纯黑 #000 */
  --card:#161B22;      /* 卡片底 */
  --raised:#1F2630;    /* 卡片内部抬升块（输入框、按钮） */
  --raised2:#283040;   /* 再抬一层（激活态、弹层内部） */

  /* 分隔 */
  --border:#262C36;    /* 卡片边框 1px */
  --hairline:#1A1F26;  /* 卡片内部细分隔线 */

  /* 文字三级 */
  --text:#F0F3F6;      /* 主文字。不是纯白 #FFF */
  --text2:#8B95A5;     /* 次要 */
  --text3:#5C6675;     /* 弱化：标签、单位、占位 */

  /* 行动色 —— 全 App 只允许这一个 */
  --accent:#4C8DFF;
  --accent-soft:#14233F;  /* accent 的 12% 底，用于选中态背景 */

  /* 语义色 */
  --success:#34D399;
  --warn:#F87171;
  --gold:#D4A853;      /* 数据高亮、上次成绩 */
}
```

## 结构硬约束

```
卡片      background:var(--card); border:1px solid var(--border); border-radius:12px
          → 不要 box-shadow，深色底上阴影看不见只显脏
圆角      卡片 12px / 按钮输入框 6-8px / 弹层顶角 16px
字重      正文 400-500，小标题 600，页面标题 700，永不 800+
数字      font-variant-numeric: tabular-nums（全局挂在 body 上）
区块间距  上下 padding 20-24px，卡片之间 margin-bottom 14px，大区块间距 32-48px
字号      页面标题 22px / 卡片标题 16px / 正文 15px / 次要 13px / 标签 11px 大写 letter-spacing .8-1.2px
图标      线性 SVG，viewBox 0 0 24 24，stroke-width 1.6，fill:none，无 emoji
```

## 常见组件的正确做法

**行式组记录表格**（Strength/Hevy 的核心交互，和「卡片堆组按钮」是小程序和专业工具的分水岭）：

```css
.strow{display:grid;grid-template-columns:30px 1fr 1fr 38px;
       align-items:center;gap:8px;padding:8px 0;
       border-bottom:1px solid var(--hairline)}
.strow.head{font-size:10px;color:var(--text3);font-weight:700;
            letter-spacing:.8px;text-transform:uppercase}
```

四列 = 组号 / 重量 / 次数 / 打勾。表头用小号大写字，不要用中文大标题。

**未填写的格子显示上次的值（ghost）**，颜色降到 `--text3`、字重降到 500，点一下才进编辑。这样他一眼就知道「上次是这个重量」，不用翻记录。

**状态标签**：

```css
.ex-tag{font-size:11px;padding:3px 8px;border-radius:4px;
        background:var(--raised);color:var(--text3);font-weight:600}
.ex.done .ex-tag{background:#14332A;color:var(--success)}   /* 完成态转绿 */
```

**底部固定操作栏**：主操作 `background:var(--accent); color:#0A1424`（深色底上蓝底配近黑字，不要白字），次操作 `background:var(--raised); color:var(--text2)`。

## WHOOP 的一句话原则

> 「Black breathes」—— 黑是有呼吸的，不是空白。

含义是：深色界面不能是大片死黑，要靠**四级灰阶**把信息分出前后，靠**字重和字号对比**分层，而不是靠加框、加阴影、加颜色。

## 反面清单（写了就是 AI 感）

```
✗ 强调色用青 / 荧光绿 / 紫渐变（#00E0D0、#7B61FF 这类）
✗ linear-gradient 背景，哪怕很淡
✗ text-shadow / box-shadow 发光
✗ border-radius 18px 以上
✗ font-weight 800 / 900
✗ emoji 当图标（✓ ※ 💧 这类只能出现在纯按钮文案里，且尽量少）
✗ 纯黑 #000 底 + 纯白 #FFF 字（对比过强，刺眼且廉价）
✗ 彩色标签满屏（一个页面最多两个语义色在出现）
```
