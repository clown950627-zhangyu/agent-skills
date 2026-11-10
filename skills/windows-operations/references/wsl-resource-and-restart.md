# WSL 资源配置与「从内部重启 WSL」

给 WSL 定内存上限、扩容 swap、以及在不丢掉当前回复的前提下重启整个 WSL 虚拟机。

## 1. 先量宿主机，再定上限

```bash
<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile \
  -Command "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB"
```

WSL2 默认拿走宿主物理内存的约 50%。上限一旦超过宿主物理内存，Windows 侧会被挤到换页，整机发卡。8G 机器给 WSL 4G 是安全值，不要照搬「物理内存的一半」以外的更大数字。

顺带确认 WSL 版本，决定能用哪些键：

```bash
<C盘>/Windows/System32/wsl.exe --version | head -3
```

`autoMemoryReclaim` 需要 WSL 2.0+，`vmIdleTimeout` 需要 Win11 的 WSL。

## 2. .wslconfig 模板

路径固定在 Windows 用户目录（不是 WSL 里）：`<C盘>/Users/<用户名>/.wslconfig`

```ini
[wsl2]
memory=4GB
swap=4GB
swapFile=C:\\Users\\<用户名>\\wsl-swap.vhdx
autoMemoryReclaim=gradual
pageReporting=true
```

要点：

- **swap 是长驻服务的救命阀**。WSL 默认 swap 只有 1G，网关/浏览器这类峰值进程一顶就 OOM。给到与内存同量级（4G/4G）比单纯加内存更有效。
- **不要设 `vmIdleTimeout`**。它会在 VM 空闲时把整个发行版关掉，连带杀掉网关、定时任务等长驻进程——看起来像「服务半夜自己死了」。
- 改完必须 `wsl --shutdown` 才生效，改文件本身不动现有 VM。

## 3. 从 WSL 内部重启 WSL

`wsl.exe --shutdown` 会关掉发起它的那棵进程树，所以直接调用等于自杀：命令执行到一半自己被杀，关机流程可能不完整。让 Windows 侧在虚拟机之外替你执行：

```bash
TARGET=$(<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile \
  -Command "(Get-Date).AddMinutes(2).ToString('HH:mm')" | tr -d '\r')

<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command \
  "schtasks /Create /TN HermesWSLRestart /TR 'C:\Windows\System32\wsl.exe --shutdown' /SC ONCE /ST $TARGET /F"
```

任务计划程序独立于 WSL 进程树，2 分钟延迟足够把回复发给用户。**先把「接下来会发生什么」讲清楚再挂任务**，否则用户只看到窗口突然断开。

收尾：重启后删除一次性任务 `schtasks /Delete /TN HermesWSLRestart /F`。

## 4. 重启后 VM 不会自己醒

`wsl --shutdown` 之后没有进程触发 WSL，虚拟机保持关闭状态——用户必须**手动开一次 WSL 终端**才会重新启动。这点必须明确告诉用户，否则他以为服务挂了。

自动恢复的前提两条，重启前就要确认：

```bash
cat /etc/wsl.conf                              # 需要 [boot] systemd=true
loginctl show-user $USER -p Linger             # 需要 Linger=yes
systemctl --user is-enabled hermes-gateway.service
```

三者齐备时，开一次终端 → systemd 起来 → enabled 的 user service（含网关）自动拉起，不用敲任何命令。缺 linger 时 user manager 不启动，服务不会自启。

## 5. 生效验证

```bash
free -h                    # Mem total 与 Swap total 是否为新值
swapon --show              # swap 来源与大小
cat /proc/meminfo | head -3
```
