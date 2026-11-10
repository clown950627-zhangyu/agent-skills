---
name: parcel-tracking
description: 查快递/物流单号时读。含承运商识别、查询接口与「数据互相矛盾」的铁律。
version: 1.0.0
author: 小爱
license: MIT
metadata:
  hermes:
    tags: [物流, 快递, 查询, 核实]
    related_skills: [decision-advice-integrity, grounded-citations]
---

# 查快递 / 追踪物流

## When to Use

用户扔来一串单号（「最终这个快递」「追踪这个快递」），或问「到哪了」「怎么还没到」。
也可能单号夹在他转发的那一大段消息里——先认单号，再查。

## 一、先认承运商

| 单号特征 | 承运商 | kuaidi100 `type` |
|:--|:--|:--|
| `YT` + 13 位数字 | 圆通（也可能是云途 YunExpress，跨境件） | `yuantong` |
| `SF` + 12～15 位 | 顺丰 | `shunfeng` |
| `JD` + 数字 | 京东 | `jd` |
| 12 位纯数字，7 开头 | 中通 | `zhongtong` |
| `YD` 开头 | 韵达 | `yunda` |
| `JT` 开头 | 极兔 | `jtexpress` |
| `DPK` 开头 | 德邦 | `debangwuliu` |

拿不准就先用圆通/中通各试一次，返回 `status:200` 且有 `data` 的那个才对得上。

## 二、查询命令

```bash
export https_proxy=http://172.30.112.1:7890 http_proxy=http://172.30.112.1:7890
curl -s -m 25 "https://www.kuaidi100.com/query?type=yuantong&postid=<单号>&temp=$(date +%s%N)&phone=" \
  -H "User-Agent: Mozilla/5.0" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('state =', d.get('state'))
for it in d.get('data',[]): print(it['time'],'|',it['context'][:120])"
```

`state`：`0`/`1` 在途、`3` 已签收、`5` 派件中、`4` 退签/退回。
`temp` 每次换一个随机值，否则可能拿到缓存。

## 三、铁律：单一免费接口的结果不得当结论

**实测过：同一个圆通单号，同一天三次查询返回三套互斥轨迹**——扬州揽收 / 深圳新安派件中 /
重庆揽收→荆州→襄阳→枣阳到驿站。三次都返回 `status:200`、都长得像真数据。
免费聚合接口有缓存串号和反爬伪造返回，**单次结果不能当真**。

报给用户之前至少做两件事：

```
① 同一命令连跑两次，比对轨迹是否一致（不一致直接判定不可信）
② 轨迹内部自洽：揽收地 → 转运中心 → 派送地必须连得上；出现地理位置跳跃就是假数据
```

仍不确定就换渠道：`phone=` 带上收件人手机后四位（部分线路需要）、圆通官网 `yto.net.cn` 查询框、
或直接请用户发一张官方小程序截图——**让他发截图比自己猜快十倍**。

## 四、报给用户的格式

```
结论一句          到哪了 / 卡在哪 / 该谁动手（例：已到驿站，今天可去取）
时间线            倒序 3–6 条，每条「时间 + 地点 + 动作」
能打的电话        派件员 / 网点 / 官方客服，照抄轨迹里的号码
单号回显          免得他对不上是哪一单
```

不要写「预计明天到」这类推算，轨迹里没有的信息一律不编；不确定就明说「接口数据不可信，
以你手机上的为准」。

## 五、主动追踪（他要才建）

他说「追踪」「盯着这单」时才建 cron，不要自作主张：

```
cronjob_manage create
  schedule: every 2h          # 或每天早上 9 点一次
  prompt:   查 <单号>，只有状态发生变化（揽收→在途→派件→签收/异常）才用
            python3 ~/.hermes/scripts/send_qq_media.py --text "【快递】一句话" 发给他，
            没变化只输出 [SILENT]
```

同一状态只报一次，别每两小时复述一遍「还在运输中」。
