# E阶段预查

本仓库用于提供 E 阶段预查相关的公开脚本。

## 仓库结构

```bash
.
├── .gitignore
├── nemu_check.py # NEMU 预查脚本
└── README.md
```

## NEMU 预查脚本

`nemu_check.py` 用于检查 [PA 实验](https://ysyx.oscc.cc/docs/ics-pa) 中 `NEMU` 相关部分必做内容是否已经完成。

该脚本仅用于检查相关功能是否已经实现。通过脚本检查并不意味着实现一定正确。

当前脚本覆盖的检查内容包括：
- [Getting Source Code](https://ysyx.oscc.cc/docs/ics-pa/0.6.html#getting-source-code)
- [优美地退出](https://ysyx.oscc.cc/docs/ics-pa/1.3.html#%E8%BF%90%E8%A1%8C%E7%AC%AC%E4%B8%80%E4%B8%AA%E5%AE%A2%E6%88%B7%E7%A8%8B%E5%BA%8F)
- [实现单步执行, 打印寄存器, 扫描内存](https://ysyx.oscc.cc/docs/ics-pa/1.4.html#%E6%89%AB%E6%8F%8F%E5%86%85%E5%AD%98)
- [实现算术表达式的递归求值](https://ysyx.oscc.cc/docs/ics-pa/1.5.html#%E6%95%B0%E5%AD%A6%E8%A1%A8%E8%BE%BE%E5%BC%8F%E6%B1%82%E5%80%BC)
- [实现表达式生成器](https://ysyx.oscc.cc/docs/ics-pa/1.5.html#%E5%A6%82%E4%BD%95%E6%B5%8B%E8%AF%95%E4%BD%A0%E7%9A%84%E4%BB%A3%E7%A0%81)
- [扩展表达式求值的功能](https://ysyx.oscc.cc/docs/ics-pa/1.6.html#%E6%89%A9%E5%B1%95%E8%A1%A8%E8%BE%BE%E5%BC%8F%E6%B1%82%E5%80%BC%E7%9A%84%E5%8A%9F%E8%83%BD)
- [实现监视点](https://ysyx.oscc.cc/docs/ics-pa/1.6.html#%E5%AE%9E%E7%8E%B0%E7%9B%91%E8%A7%86%E7%82%B9)

**注意事项：**
- 当 `CONFIG_ITRACE` 关闭时，脚本可能无法正确判断“单步执行”相关功能
- 当 `CONFIG_WATCHPOINT` 关闭时，脚本可能无法正确判断“监视点”相关功能
- 运行脚本前，请确保上述选项处于**启用**状态

**运行方式：**

脚本本身不要求放置在 `NEMU_HOME` 目录下。只要正确设置了 `NEMU_HOME` 环境变量，脚本放在任意位置都可以运行。

可直接通过以下命令中的一条在线运行脚本：

```bash
# bash/zsh (Recommended)
python3 <(curl -fsSL https://raw.githubusercontent.com/OSCPU/ysyx-e-exam-pre-check/master/nemu_check.py)

# 如果上述命令不支持
python3 -c "$(curl -fsSL https://raw.githubusercontent.com/OSCPU/ysyx-e-exam-pre-check/master/nemu_check.py)"
```

也可以先将脚本下载到本地，再通过 `python3` 运行：

```bash
python3 <path_to_nemu_check>
```
