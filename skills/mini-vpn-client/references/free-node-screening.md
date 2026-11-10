# 免费公开节点：源、筛选流程、实测数据

## 一、公开源（拉取时带 `-A 'clash.meta'`，与付费订阅同一个 UA 规则）

```
https://raw.githubusercontent.com/anaer/Sub/main/clash.yaml                    （clash yaml，量最大）
https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/clash.yml
https://raw.githubusercontent.com/chengaopan/AutoMergePublicNodes/master/list.yml
https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub                 （base64 订阅，需自己解）
```

- 这四个仓库基本每天都在 push，**内容新鲜不代表节点能活**；不要因为“刚更新”就认为质量好。
- GitHub raw 在境内直连不稳，用本机代理拉：`export https_proxy=http://<网关IP>:7890`。
- 文件大小差异很大（100KB ~ 600KB）。先看 size 再解析；404 说明仓库改名/删了，换一个，不要反复试同一个。

## 二、实测结论（直接拿去说服用户）

```
3 个源合并去重        2692 个节点（vless 1053 / vmess 1014 / trojan 372 / 其余少量）
分层抽样              24 个（每个源取 8 个带地区关键词的节点）
活下来                1 个（德国，1829 ms，google/youtube/chatgpt 全 200）
同时间付费节点         美国2 = 2193 ms
```

结论：**命中率约 4%，速度不比付费强。** 要凑出 5 个可用，得测 120 个左右——人工挑没意义，必须机器筛。

## 三、筛选流程（写成定时任务才有价值）

```
① 拉源          4 个源 → /tmp/freenodes/srcN.yaml
② 解析合并      yaml.safe_load → proxies[] → 按 server:port 去重
                只留 vless / vmess / trojan / hysteria2（ss/http/wireguard 在 mihomo 上容易炸）
③ 抽样          带地区关键词的优先（美国|US|日本|JP|新加坡|SG|香港|HK|韩国|KR|台湾|TW|德国|DE|英国|UK）
                每个源取 8~10 个，控制在 30 个以内——一次测几百个会 504
④ 生成测试配置  独立端口 7895 / 9095，proxy-groups 一个 select 组，rules 就一条 MATCH,组名
⑤ 启动隔离实例  C:\Windows\Temp\freetest\ 里跑，杀的时候按 CommandLine 带 'freetest' 精确匹配
⑥ 测延迟        逐个 GET /proxies/<urlencode(name)>/delay?timeout=2500&url=http://www.gstatic.com/generate_204
⑦ 真站点复验    切到候选 → Invoke-WebRequest -Proxy http://127.0.0.1:7895 打 google/youtube/chatgpt
                只看 gstatic 延迟会被骗，必须看目标站状态码
⑧ 输出          把活的节点写进一份干净的 config.yaml（不写订阅链接），给电脑版/手机版导入
```

第 ⑥ 步的坑：`GET /group/<名>/delay` 一次测全部虽然快，但成员上百时 mihomo 会直接返回 **504**；
160 个必爆，20 个以内能过。要么分组，要么逐个测。

## 四、必须对用户说的三句话

1. **命中率**：今天活的，明天大概率全死；公开源等于公开靶子，谁都能扫。
2. **安全**：免费节点 = 陌生人的服务器，明文流量全看得见。只用来查资料/看图，不登任何账号（eBay、Payoneer、ChatGPT、微信、银行）。
3. **别用它替代付费线**：付费那份是每天干活用的，免费这份只当备份/省钱补充。

## 五、什么时候不要走这条路

- 用户要做跨境收款、看店铺后台、登 ChatGPT —— 一律付费线路，免费节点等于把账号送人。
- 用户嫌麻烦、要“稳定”—— 直接说免费不稳定，别为了省几十块搭进去一下午。
