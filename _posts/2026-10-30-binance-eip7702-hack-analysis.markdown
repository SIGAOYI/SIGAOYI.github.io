---
layout: post
title: "币安 63.6 亿美元惊魂夜全景复盘：EIP-7702 代码委派机制、50 笔预签名盲狙与十链签名基建失守"
subtitle: "分钟级还原 2026-10-30 加密史最大安全事件：为什么说 EIP-7702 并非协议漏洞，以及 23 字节 0xef0100 指针如何绕过传统提币风控并在 3 分 24 秒内搬空 Binance 14？"
date: 2026-10-30
author: "龟龟"
header-img: "/img/home-bg.jpg"
catalog: true
tags:
  - 区块链安全
  - 以太坊
  - EIP-7702
  - 币安
  - 深度研报
  - 看板
---

> **核心导读与研报信源**：
> * **专题视频线索**：感谢深度观察创作者 **[云雷](https://v.douyin.com/a5uu-qxlg0s/)** 发布的专题解析作品《[今早 BN 被盗 60 亿美金，EIP-7702 的劫持漏洞与原理解析](https://v.douyin.com/a5uu-qxlg0s/)》。
> * **链上取证与安全机构信源**：综合区块链情报机构 **[TRM Labs 官方溯源报告](https://www.trmlabs.com/resources/blog/north-korea-steals-usd-6-36-billion-from-binance-in-the-largest-hack-in-history)**、链上数据平台 **[Bitquery 十链资金流向审计](https://bitquery.io/investigations/binance-hack)** 与 **[做市商滑点损耗分析](https://bitquery.io/investigations/binance-hack-who-profited)**、慢雾（SlowMist）创始人 **[余弦（Cos）技术定性](https://news.marsbit.co/flash/20261030084915298213.html)**（参见 **[PANews 报道](https://www.panewslab.com/zh/articles/01a18a4a-804e-737a-ac3c-d01404838778)**）、**[The Defiant 交易权限拆解](https://thedefiant.io/news/security/binance-labeled-wallet-swept-minutes-after-eip-7702-delegation)**、**[Elliptic 威胁情报分析](https://www.elliptic.co/insights/binance-largest-hack-in-history/)**、**[Blockaid 签名系统风险报告](https://blockaid.io/blog/binance-55b-hack-using-advanced-ai-models-blockaid-detects-the-biggest-theft-in-crypto-history)**、**[Hard2bit 签名架构与 DORA 合规复盘](https://hard2bit.com/en/blog/binance-hack-eip-7702-signing-infrastructure-dora/)**，以及 **[律动 BlockBeats 深度技术复盘](https://news.cnyes.com/news/id/6641689)**、**[40 分钟完整时间线追踪](https://m.cnyes.com/news/id/6641566)** 与 **[Etherscan 链上原始交易记录](https://etherscan.io/tx/0x53bd38b816c23e74134786c29a8c18d792777998a3b9326047b583100e88e2f3)**。
> * **核心命题**：北京时间 2026 年 10 月 30 日凌晨 04:04 至 08:06（UTC 时间 10 月 29 日 20:04 至 30 日 00:06），币安（Binance）分布在 **10 条公链上的至少 17 个热钱包**遭遇协同洗劫，按事发时市价折算累计流出约 **63.6 亿美元**（规模约为 2025 年 2 月 Bybit 15 亿美元被盗案的 **4.2 倍**）。在占受损总额近六成（37.9 亿美元）的以太坊主战场上，攻击者向币安核心热钱包 `Binance 14`（`0x28C6…1d60`）提交了一笔包含 **50 份连续交易计数器（Nonce）预签名**的 **EIP-7702** 授权交易，仅用 **3 分 24 秒**便在单笔交易中扫空 **167,464 枚 ETH、16.15 亿枚 USDT 及 62 种代币（约 25 亿美元）**。究竟什么是 EIP-7702？它真是舆论初期恐慌传言的“以太坊底层协议漏洞”吗？为什么一套原本旨在提升用户体验的账户抽象标准，会演变为穿透交易所风控防线的超级清扫器？

---

### 一、 交互式全景看板：分钟级时间线、EIP-7702 指针拆解与十链资金追踪

我们将全案 **6 大演进阶段（精确到秒的链上时间戳）**、**EIP-7702 委托指针（`0xef0100`）三步攻击架构图**、**10 条公链受损与 27 亿美元冻结分布**以及**机构级安全防御清单**封装为如下深色交互式看板（手机与平板端轻触任意时间线卡片，即可在卡片正下方就地展开链上取证详情）：

<p align="center" style="margin-top: 15px;">
  <a href="/dashboards/binance_eip7702_hack_analysis.html" target="_blank" class="btn btn-default">在新窗口全屏浏览看板 ↗</a>
</p>

<iframe src="/dashboards/binance_eip7702_hack_analysis.html" width="100%" height="960px" frameborder="0" style="border-radius: 8px; border: 1px solid #24324f; margin-top: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.25);"></iframe>

---

### 二、 核心量化指标与事实核查矩阵（Fact-Check & Key Metrics）

事件爆发初期，社交媒体上流传着从“28 亿美元”、“56 亿美元”到“63.6 亿美元”等多个版本的损失数字，并伴随大量将矛头指向“以太坊 Pectra 升级协议漏洞”的误读。我们交叉比对 [TRM Labs](https://www.trmlabs.com/resources/blog/north-korea-steals-usd-6-36-billion-from-binance-in-the-largest-hack-in-history)、[Bitquery](https://bitquery.io/investigations/binance-hack) 与 [律动 BlockBeats](https://news.cnyes.com/news/id/6641689) 的链上逐笔审计，梳理出以下八大核心量化事实：

| 评估维度 | 关键量化数据 | 链上取证与技术核查结论（附权威信源溯源） |
| :--- | :--- | :--- |
| **1. 十链累计流出总额** | **$63.6 亿美元**（币安/Bitquery 口径约 $63 亿） | 按资产转出时刻现价计算，10 条公链累计流出约 **63.6 亿美元**（[TRM Labs](https://www.trmlabs.com/resources/blog/north-korea-steals-usd-6-36-billion-from-binance-in-the-largest-hack-in-history)）。早期“25 亿–28 亿美元”仅统计了 `Binance 14` 首笔交易，“56 亿美元”则漏计了瑞波链（XRP Ledger）无共享地址的 2.96 亿美元及后续 6 轮追加清扫。 |
| **2. 历史规模坐标** | **Bybit 案（$15 亿）的 4.24 倍** | 创下人类加密资产史最大单次被盗纪录，远超 2025 年 2 月 Bybit 案（$15 亿）、2022 年 Ronin 跨链桥案（$6.25 亿）与 2021 年 Poly Network 案（$6.11 亿）（[Bitquery](https://bitquery.io/investigations/binance-hack)）。 |
| **3. 攻击者身份归因** | **朝鲜 TraderTraitor（Lazarus 子集）** | [TRM Labs](https://www.trmlabs.com/resources/blog/north-korea-steals-usd-6-36-billion-from-binance-in-the-largest-hack-in-history)、[Elliptic](https://www.elliptic.co/insights/binance-largest-hack-in-history/) 与 [Blockaid](https://blockaid.io/blog/binance-55b-hack-using-advanced-ai-models-blockaid-detects-the-biggest-theft-in-crypto-history) 以高置信度归因于朝鲜国家级黑客组织 **TraderTraitor**（与 2025 年 Bybit 案及 2026 年 4 月 KelpDAO 案同源）。 |
| **4. 核心漏洞定性** | **签名基建失守（非 EIP-7702 协议漏洞）** | [慢雾余弦](https://news.marsbit.co/flash/20261030084915298213.html) 与 ZeroDev 创始人 Derek Chiang 均明确指出：**EIP-7702 协议本身零漏洞**。比特币、Solana、XRP、波场等另外 9 条不支持 EIP-7702 的异构公链在同一窗口签发了合法转账，证实攻击者攻破的是币安**内部热钱包跨链签名审批/调度系统**。 |
| **5. 预签名盲狙批次** | **单笔打包 50 份连续 Nonce 授权（1 份命中）** | 针对 `Binance 14` 高频提币导致交易计数器（Nonce）不断跳动的特性，攻击者预先导出了 Nonce 从 `18,914,775` 到 `18,914,824` 的 **50 份连续授权**，49 份失效、1 份精准命中（[BlockBeats](https://news.cnyes.com/news/id/6641689)）。 |
| **6. 首笔原子清扫耗时** | **3 分 24 秒 / Gas 费仅 0.0004 ETH（<$1）** | 04:20:59（BJT）写入 `0xef0100` 委托指针，04:24:23 触发 [单笔清扫交易 `0x53bd38b8...`](https://etherscan.io/tx/0x53bd38b816c23e74134786c29a8c18d792777998a3b9326047b583100e88e2f3)，瞬间转走 **167,464 枚 ETH、16.15 亿枚 USDT 及 62 种 ERC-20 代币**，钱包仅剩 1 枚 ETH。 |
| **7. 恶意委托驻留时长** | **3 小时 45 分钟（累计触发 7 轮清扫）** | 从 04:21 BJT 注入指针至 08:06 BJT 正式撤销，恶意代码在 `Binance 14` 上持续驻留近 4 小时，期间对新充值资金又执行了 **6 次追加清扫**（[TRM Labs](https://www.trmlabs.com/resources/blog/north-korea-steals-usd-6-36-billion-from-binance-in-the-largest-hack-in-history)）。 |
| **8. 紧急冻结与当前敞口** | **已冻结/夺回 ~$27.0 亿 vs 黑客控制 ~$32.0 亿** | Tether（冻结 17.59 亿 USDT）、Circle（冻结 8.25 亿 USDC）、Ripple（冻结 4,050 万 RLUSD）、WLFI（冻结 2,780 万 USD1）与 Arbitrum 安全委员会（强行夺回 $3,000 万）合计拦截约 **27 亿美元**；黑客在支付 10%–15% 滑点溢价（损耗 $1.19 亿）强行换仓后，现持有 **508,621 枚 ETH、18,270 枚 BTC** 等约 **32 亿美元**抗审查资产（[Bitquery](https://bitquery.io/investigations/binance-hack)）。 |

---

### 三、 科普图解：什么是 EIP-7702？它如何把热钱包变成黑客的“提款机”？

对于非以太坊底层开发背景的读者，要看懂这场 63.6 亿美元惊天劫案的技术内幕，首先需要理清一个最核心的因果关系：**EIP-7702 不是黑客撬开币安金库大门的“万能钥匙”，而是黑客在骗取金库管理员盖章之后，用来在 3 分钟内搬空整座金库的“全自动传送带”。**

![EIP-7702 权限委派与批量清扫攻击机制图解](/img/eip7702_delegation_attack_diagram.jpg)

#### 1. 背景科普：以太坊的两类账户与 EIP-7702 的设计初衷

在以太坊虚拟机（EVM）的传统架构中，账户被严格划分为两个互不相通的物种：

1. **外部拥有账户（EOA, Externally Owned Account）**：即普通用户和交易所最常用的私钥钱包（如本次涉事的 `Binance 14`，地址 `0x28C6…1d60`）。它由一对加密公私钥控制，账户状态里的代码字段（`code`）永远是空的（`0x`）。
   * **天然短板**：EOA 极其“笨拙”，不支持编写程序逻辑。如果钱包里有 ETH 和 63 种 ERC-20 代币，想要全部转走，私钥持有人必须老老实实签发 **64 笔独立交易**，不仅耗时漫长，而且在交易所环境下，短时间内连续发出 64 笔异常提币极易触发风控系统的频率熔断。
2. **智能合约账户（Smart Contract Account）**：由部署在链上的代码控制，没有私钥，但支持复杂的批量打包交易（Batching）、社交恢复与权限分级。

为了让数十亿普通 EOA 钱包无需迁移地址就能享受智能合约的便利，以太坊在 **2025 年 Pectra 硬分叉升级**中正式上线了由 Vitalik Buterin 等人联合提出的 **[EIP-7702 标准](https://thedefiant.io/news/security/binance-labeled-wallet-swept-minutes-after-eip-7702-delegation)**（引入了全新的交易类型 `0x04`）。

用一句话通俗概括 **EIP-7702 的工作机制**：
> **它允许一个普通私钥钱包（EOA）签发一张“代码租用授权书”，在自己的 `code` 字段里写入一个 23 字节的指针（`0xef0100` + 目标智能合约地址）。从此以后，这个钱包的地址、余额和私钥统统不变，但任何人调用这个钱包地址时，以太坊虚拟机会自动加载那份外挂合约的代码，并在该钱包自己的资产抽屉里执行。**

从计算机底层状态来看，普通 EOA 账户与被注入 EIP-7702 指针后的账户状态差异如下：

$$\text{Standard EOA State: } \quad \sigma[\text{Binance 14}]_{\text{code}} = \varnothing \quad (\text{keccak256} = \texttt{0xc5d246...})$$

$$\text{EIP-7702 Delegated State: } \quad \sigma[\text{Binance 14}]_{\text{code}} = \underbrace{\texttt{0xef0100}}_{\text{3-byte Magic Prefix}} \parallel \underbrace{\texttt{0x63e8...6fAe}}_{\text{20-byte Attacker Contract}} \quad (23\text{ Bytes})$$

这里最关键的设计细节是**执行上下文（Execution Context）**：当外部地址向 `Binance 14` 发起调用时，EVM 采用类似于 `DELEGATECALL`（委托调用）的语义去执行黑客合约 `0x63e8…6fAe` 中的逻辑——这意味着在黑客代码运行期间，环境变量中的“当前账户”（`address(this)`）依然是 `Binance 14` 本身！因此，黑客代码无需再索取任何私钥签名，就可以直接以 `Binance 14` 主人的身份，在**同一笔原子交易**内调用 63 个代币合约的 `transfer()` 函数，把所有资产一次性划走。

---

#### 2. 致命盲区：为什么交易所的 HSM / MPC 风控系统没能拦住它？

既然 EIP-7702 需要 `Binance 14` 的私钥签发授权才能生效，而币安拥有行业顶级的硬件安全模块（HSM，即物理隔离的加密签名黑盒）与多方安全计算（MPC，将私钥分片保存在多台服务器中协同签名），为什么还会签出这份要命的授权？

正如 [Blockaid 首席执行官 Ido Ben-Natan](https://hard2bit.com/en/blog/binance-hack-eip-7702-signing-infrastructure-dora/)、[TRM Labs](https://www.trmlabs.com/resources/blog/north-korea-steals-usd-6-36-billion-from-binance-in-the-largest-hack-in-history) 与 [律动 BlockBeats](https://news.cnyes.com/news/id/6641689) 所剖析的：**HSM 与 MPC 保护的是“私钥不被明文偷走”，但并不负责判断“业务层提交过来的这笔请求该不该签”。**

大型交易所的热钱包每天要自动处理数以万计的用户提币请求，不可能由人工逐笔肉眼审批，必须依赖一套自动化的**签名前置审批流水线（Pre-Signing Policy Engine）**：

```
+-----------------------------------------------------------------------------------+
| 传统交易所热钱包自动签名风控模型 vs EIP-7702 降维打击                               |
+-----------------------------------------------------------------------------------+

【常规提币请求】 -> [风控规则引擎检查] -> 1. 转账金额 (Value) 是否超过单笔阈值？
                                       -> 2. 接收方地址 (To) 是否在风险黑名单？
                                       -> 3. ERC-20 transfer(to, amount) 额度是否异常？

【EIP-7702 授权】 -> [风控规则引擎检查] -> 1. 转账金额 (Value) == 0 ETH (无资金移动！)
                                       -> 2. 无 ERC-20 transfer 调用数据！
                                       -> 3. 签名结构：keccak256(0x05 || chain_id || address || nonce)
                                       ==> ❌ 旧版风控引擎未解析 0x05/0x04 语义，误判为无害操作放行！
```

问题的症结就在这里：
* **初步渗透入口**：据 [币安初步调查披露及 Hard2bit 报道](https://hard2bit.com/en/blog/binance-hack-eip-7702-signing-infrastructure-dora/)，攻击者（朝鲜 TraderTraitor 组织）疑似先通过社会工程学手段（如伪装招聘面试的 **Contagious Interview** 攻击）控制了内部 DevOps 工程师的终端设备，进而渗透至用于发起提币签名请求的后端服务容器（币安 CEO Richard Teng 随后补充表示发现了不止一处突破点，系多因素叠加所致）。
* **签名前置审批的认知盲区**：当攻击者通过内部服务容器向以太坊热钱包签名接口下发 EIP-7702 授权签名请求时，传统的风控审批规则主要盯着两个字段：**“转多少钱（Amount）”**和**“转给谁（Recipient Address）”**。
* 然而，EIP-7702 授权签名既没有转账金额（`value = 0`），也不包含代币转移指令——**它改写的不是“从钱包里转出多少钱”，而是“这个钱包地址本身是什么”**。在尚未针对 EIP-7702 升级语义解析器的旧版签名网关眼中，这串以 `0x05` 魔数开头的哈希摘要看起来就像一笔毫无资金风险的普通配置签名，于是痛快地盖下了印章。

---

#### 3. 工程诡计：为什么要一口气打包“50 笔连续 Nonce 预签名”？

在链上取证中，最令安全研究员拍案叫绝（也最能暴露攻击者权限边界）的细节，是北京时间 04:20:59 上链的那笔授权交易里，竟然整整齐齐塞满了 **50 份针对 `Binance 14` 的 EIP-7702 授权签名**，其交易计数器（`nonce`）从 `18,914,775` 一直排到 `18,914,824`（[BlockBeats](https://news.cnyes.com/news/id/6641689)、[Bitquery](https://bitquery.io/investigations/binance-hack)）。

为什么黑客不直接签 1 份，而要一口气签 50 份？这恰恰揭示了当时的真实攻防态势：

1. **严格的 Nonce 相等约束**：根据 EIP-7702 协议规范，每一份授权元组（Authorization Tuple）的签名内容定义为：
   $$\text{digest} = \text{keccak256}\Big(\texttt{0x05} \parallel \text{rlp}\big([\text{chain\_id}, \text{contract\_address}, \text{nonce}]\big)\Big)$$
   当矿工（验证者）打包这笔交易时，EVM 会逐一校验列表中的授权元组：只有当元组里填写的 $\text{nonce}$ 与目标钱包 `Binance 14` 在**当前区块执行瞬间**的真实交易计数 $\text{nonce}_{\text{current}}$ **完全相等**时，委托才会生效；只要差了 1 个数，该份授权就会被静默跳过作废。
2. **高频热钱包的“移动靶”难题**：`Binance 14` 作为币安最繁忙的以太坊提币主钱包，每分钟都在自动向外发送正常用户的提币交易，其链上 $\text{nonce}_{\text{current}}$ 就像高速旋转的秒表一样时刻跳动。
3. **跨系统的时间差补偿（散弹枪盲狙策略）**：如果黑客已经把 `Binance 14` 的明文私钥偷到了自己电脑上，他完全可以在本地实时读取链上最新 Nonce 并毫秒级签出唯一准确的 1 份授权。他之所以必须**提前批量生成 50 个连号签名**，证明他当时**并没有拿到明文私钥**，而是通过被攻陷的币安内部签名服务接口（MPC/HSM 网关）批量提交了签名申请！为了防止在“从内部接口导出签名”到“通过外部黑客地址广播上链”的几分钟时间差内，`Binance 14` 因正常提币导致 Nonce 跑偏，攻击者干脆预留了覆盖未来 50 笔提币窗口的连续签名包：
   $$\{\text{Auth}_i \mid \text{nonce}_i = 18,914,775 + i, \quad i \in [0, 49]\}$$
   最终上链执行时，前序已经跑过的和后续尚未到达的 **49 份授权全部失效，唯独正中靶心的那 1 份生效**——瞬间将 `Binance 14` 变成了黑客清扫器合约 `0x63e8…6fAe` 的傀儡外壳。

---

### 四、 惊魂夜分钟级全景时间线：从提前 36 小时彩排到 4 小时攻防拉锯

结合 [TRM Labs](https://www.trmlabs.com/resources/blog/north-korea-steals-usd-6-36-billion-from-binance-in-the-largest-hack-in-history)、[Bitquery](https://bitquery.io/investigations/binance-hack)、[The Defiant](https://thedefiant.io/news/security/binance-labeled-wallet-swept-minutes-after-eip-7702-delegation) 与 [鉅亨網/律动完整时间线](https://m.cnyes.com/news/id/6641566)，我们将这场横跨 10 条公链的闪电战按时间轴（同时标注北京时间 BJT `UTC+8` 与协调世界时 `UTC`）完整复原如下：

#### 第一阶段：风暴前夜的社工渗透与三轮链上彩排（10 月 27 日 – 10 月 30 日 00:30 BJT）

* **10 月 27 日（事发前 3 天）**：币安安全团队公开披露，在过去一周内拦截了多起与朝鲜黑客相关的 **[Contagious Interview（传染性面试）](https://news.cnyes.com/news/id/6641689)** 攻击——攻击者伪装成招聘方或合作方，通过面试代码测试诱导开发人员运行恶意程序。但事后回看，内部签名审批链路的某处入口已在此期间埋下隐患。
* **10 月 28 日上午起（事发前 36 小时）**：攻击者主控发起地址 `0x7C86…5CA0` 陆续从混币器 **Tornado Cash** 收到 3 笔各约 `0.1 ETH`（含一笔 `0.0983 ETH`）的提币，专门用于储备后续部署合约与触发清扫的燃气费（Gas）（[TRM Labs](https://www.trmlabs.com/resources/blog/north-korea-steals-usd-6-36-billion-from-binance-in-the-largest-hack-in-history)、[The Defiant](https://thedefiant.io/news/security/binance-labeled-wallet-swept-minutes-after-eip-7702-delegation)）。
* **10 月 29 日 10:29 BJT（02:29 UTC）**：攻击者在以太坊主网部署第一版测试清扫合约 `0x19be…f2bf`（后在调试中被弃用）。
* **10 月 29 日 21:51 – 22:24 BJT（13:51 – 14:24 UTC）**：攻击者向两个自备的外部测试钱包写入 EIP-7702 委托，并于 22:20 和 22:24 发起**第 1、第 2 次实弹演练**（首次调用疑似遇到小瑕疵，4 分钟后修正重测并成功掏空测试钱包）。
* **10 月 29 日 23:59 – 10 月 30 日 00:30 BJT（15:59 – 16:30 UTC）**：攻击者部署最终投产版、未开源验证的极简清扫器合约 **`0x63e8…6fAe`**——反编译字节码显示，该合约内仅有一个核心函数 `sweep(address pool, address[] depositors)`，唯一功能就是将当前地址内的全部 ETH 与指定代币列表悉数转入黑客收款池，且带有严格的调用者身份校验（仅允许攻击者操作地址触发）。00:21 至 00:30 BJT，攻击者换用第三个外部测试钱包完成**第 3 次终极彩排**，并将测试资金归集回自身，随后进入长达 **3 小时 51 分钟的静默潜伏期**（[CNYES](https://m.cnyes.com/news/id/6641566)）。

#### 第二阶段：20 分钟十链同步总攻与 Binance 14 瞬间失守（10 月 30 日 04:04 – 04:25 BJT）

* **04:04 – 04:09 BJT（20:04 – 20:09 UTC）｜第一枪在 XRP Ledger 打响**：
  5 个币安瑞波链（XRP Ledger）热钱包率先签发异常高手续费转账，将 **2.3346 亿枚 XRP（价值约 2.96 亿–3.00 亿美元）**集中转入单一黑客地址 `rK21t6…gfzMx`，每个热钱包仅留存最低账户激活准备金（[TRM Labs](https://www.trmlabs.com/resources/blog/north-korea-steals-usd-6-36-billion-from-binance-in-the-largest-hack-in-history)）。
* **04:10 BJT（20:10 UTC）｜Solana 与以太坊 L2 紧随其后**：
  币安 Solana 热钱包向黑客地址 `AffzFD…yGigBEaU` 转出 **970,500 枚 SOL（约 9,600 万美元）**；几乎同一时刻，Optimism（~$480 万）、Arbitrum（~$3,200 万，含 8,426 枚 ETH 与 7,460 万枚 ARB）与 Base（~$270 万）上的币安热钱包相继通过普通签名交易向外流出资金（[Bitquery](https://bitquery.io/investigations/binance-hack)）。
* **04:20:00 – 04:22:00 BJT（20:20 – 20:22 UTC）｜比特币 14.8 亿美元出逃与波场沦陷**：
  * **比特币主网**：币安 BTC 热钱包支付约平日 2 倍的矿工费，单笔转出 **18,270 枚 BTC（约 14.7 亿–14.8 亿美元）**。资金到账的同一区块内，黑客立即启动 **剥离链（Peel Chain，即通过连续交易将大额资金像剥洋葱一样拆分为规整的 1,000 BTC 和 100 BTC 子钱包）**，最终分散静置在 19 个地址中。
  * **波场（TRON）**：不到两分钟内，币安波场热钱包签发转账，向黑客转出 **6.127 亿枚 USDT 与 4,640 万枚 TRX（合计约 6.28 亿美元）**。
* **04:20:59 BJT（20:20:59 UTC）｜EIP-7702 指针刺入 `Binance 14`**：
  攻击者操作钱包向以太坊主网广播了那笔包含 **50 份连续 Nonce 预签名**的 EIP-7702 授权交易。随着其中 1 份命中当前 Nonce，币安最大的以太坊热钱包 `Binance 14`（`0x28C6…1d60`）的代码字段被正式覆写为 `0xef0100` + `0x63e8…6fAe`。
* **04:24:23 BJT（20:24:23 UTC）｜3 分 24 秒后的 25 亿美元单笔原子清扫**：
  授权生效仅 **3 分 24 秒**后，攻击者操作地址调用 `Binance 14` 上的 `sweep()` 函数（[交易哈希 `0x53bd38b8...`](https://etherscan.io/tx/0x53bd38b816c23e74134786c29a8c18d792777998a3b9326047b583100e88e2f3)）。在這一笔交易内，`Binance 14` 像自己给自己搬家一样，将 **167,464 枚 ETH、16.15 亿枚 USDT 以及另外 62 种 ERC-20 代币（当时价值约 25 亿–28 亿美元）**一次性转入黑客接收地址，钱包内仅剩 1 枚 ETH，而整笔世纪大劫案的链上 Gas 手续费仅为 **`0.0004 ETH`（不到 1 美元）**！
* **04:24:47 BJT（20:24:47 UTC）｜第二以太坊热钱包与 8.23 亿 USDC 联动失守**：
  仅隔 24 秒，币安**第二个以太坊热钱包**（未挂载 EIP-7702）通过普通私钥签名直接向黑客连发 9 笔转账（含 28,006 枚 ETH、5,570 万 USDT、2,590 万 RLUSD，合计约 1.74 亿美元）；与此同时，由于已被劫持的 `Binance 14` 恰好担任币安另一个独立智能合约账户的**执行者（Executor）**，攻击者顺藤摸瓜调用该权限，从该智能账户中直接抽走了 **8.23 亿枚 USDC**（[TRM Labs](https://www.trmlabs.com/resources/blog/north-korea-steals-usd-6-36-billion-from-binance-in-the-largest-hack-in-history)、[The Defiant](https://thedefiant.io/news/security/binance-labeled-wallet-swept-minutes-after-eip-7702-delegation)）。至此，以太坊单链总损失定格在约 **37.9 亿美元（含 200,630 枚 ETH 与 185 种代币）**。

#### 第三阶段：链上生死竞速——黑客溢价 15% 狂买 ETH vs 发行方 27 亿美元紧急冻结（04:41 – 08:18 BJT）

中心化稳定币（USDT、USDC、RLUSD、USD1）的智能合约内置了行政黑名单函数（`addBlackList` / `freeze`）。深知这一点的朝鲜黑客团队，在得手后的第一秒就展开了与全球稳定币发行方的读秒竞速：

1. **不计成本的链上抛售与借贷套现（损耗 $1.19 亿滑点）**：
   * 在以太坊上，攻击者跳过了需要复杂跨链桥的路径，直接杀入 **UniswapX** 与 **1inch Fusion**（这两者属于基于意图 Intent 的聚合协议，由专业做市商充当 Resolver/Filler 填单）以及 Uniswap 流动性池，疯狂倾销手中的 USDT 与各类山寨币以换取无法被冻结的原生 **ETH**（[Bitquery](https://bitquery.io/investigations/binance-hack-who-profited)）。
   * 为了追求极致的成交速度，黑客将滑点容忍度调得极高，以平均约 **$2,650 / ETH** 的价格扫货（而当时市场公允价格仅为 **$2,300 – $2,350 / ETH**，相当于主动承受了 **10%–15% 的巨额溢价**），仅在 DEX 兑换滑点上就白白损失了约 **1.19 亿美元**（其中套利交易者与 MEV 机器人截留了约 6,000 万美元利润）。
   * 此外，黑客还将 **6,000 万枚 USDT** 存入借贷协议 **Aave** 作为抵押品，直接借出约 **19,760 枚 ETH**（随后 Aave 紧急冻结了相关市场）；在波场上，黑客将 **3 亿枚 USDT** 存入 **JustLend**，并通过 **SunSwap** 将 **2.34 亿枚 USDT** 强行兑换为 **TRX**。
   * 经过这一系列闪电换仓，黑客从币安直接盗走的原币虽然只有 **200,630 枚 ETH**，但其通过抛售 7.29 亿枚稳定币和代币额外买进了约 **308,000 枚 ETH**，使其最终控制的以太坊总量暴增 **2.5 倍**至 **508,621 枚 ETH**！
2. **四大稳定币发行方与 Arbitrum 委员会联手拦截 27 亿美元**：
   * **04:57 BJT（20:57 UTC）**：World Liberty Financial 率先反应，冻结主接收地址中的 WLFI 代币，随后于 06:10 BJT（22:10 UTC）冻结 **2,780 万枚 USD1** 稳定币，并在 06:26 BJT 冻结了 `Binance 14` 热钱包内的 USD1 以防继续被扫。
   * **05:04 BJT（21:04 UTC）**：**Circle** 配合执法机构精准拉闸，一举冻结主接收钱包内的 **8.23 亿枚 USDC**，随后又追冻了黑客从 Avalanche 兑换并跨链至以太坊的 156 万枚 USDC（合计锁定约 **8.25 亿枚 USDC**）。
   * **Tether 分 11 批锁定 17.59 亿枚 USDT**：在以太坊与波场被盗的共计 24.88 亿枚 USDT 中，**Tether** 成功锁定了 **17.59 亿枚 USDT（拦截率达 71%）**，但其中 6 次冻结指令落地时，对应中转钱包已被黑客提前一步清空（[Bitquery](https://bitquery.io/investigations/binance-hack)）。
   * **06:01 BJT（22:01 UTC）**：在黑客通过两跳地址于 05:42–06:01 间抛售掉 4,800 万枚 RLUSD 后，**Ripple** 成功冻结了剩余的 **4,050 万枚 RLUSD**。
3. **匪夷所思的 3 小时 45 分钟委托驻留与 6 次追加抽血**：
   * 在首轮清扫完成后，`Binance 14` 上的 EIP-7702 恶意代码指针依然稳稳挂在链上。随着零散充值和自动归集资金继续流入该地址，攻击者分别于北京时间 **04:41、04:59、05:04、05:44、06:39 和 07:56**（对应 UTC 20:41 至 23:56）又气定神闲地调用了 **6 次 `sweep()`**（全晚累计清扫 7 次）！
   * 最耐人寻味的一幕发生在 **06:55 BJT（22:55 UTC）**：链上记录显示，币安团队此时正在使用 `Binance 14` 的同一把私钥，手动把钱包里还没被黑客扫走的零碎长尾代币转回自己的安全钱包——**然而即便在这一刻，运维团队依然没有用这把钥匙签发一笔撤销 EIP-7702 委托的交易**（[BlockBeats](https://news.cnyes.com/news/id/6641689)）！
   * **07:05 BJT（23:05 UTC）**：距离首波攻击两个半小时后，币安在 **Avalanche（~$2,800 万）** 与 **Polygon（~$1,000 万）** 上的热钱包再次遭遇第二波延时签名转出。
   * **08:06 – 08:18 BJT（00:06 – 00:18 UTC）**：在恶意指针驻留长达 **3 小时 45 分钟**后，币安终于向链上提交了撤销 `Binance 14` EIP-7702 授权的签名；几乎同时（08:08 BJT），**Arbitrum 安全委员会（Security Council）**启动紧急链上治理干预，强行从黑客 Arbitrum 钱包中划回 **8,426 枚 ETH 与 7,460 万枚 ARB（价值约 3,000 万美元）**（[TRM Labs](https://www.trmlabs.com/resources/blog/north-korea-steals-usd-6-36-billion-from-binance-in-the-largest-hack-in-history)、[MarsBit](https://news.marsbit.co/20261030120310440893.html)）。

---

### 五、 深度复盘：这场 63.6 亿美元大劫案留给加密行业的三大铁律

当舆论场的喧嚣逐渐散去，技术社区必须直面一个冷酷的现实：**即使稳定币发行方与 L2 委员会以创纪录的速度冻结了约 27 亿美元，攻击者目前在 9 个以太坊囤币地址（共持 508,621 ETH）、19 个比特币地址（共持 18,270 BTC）以及 XRP、Solana、TRON 钱包中，依然牢牢控制着约 32 亿美元（按抗审查硬通货计价约 24 亿–32 亿美元）无法被任何中心化机构冻结的资产。**

为什么拥有最严密安全团队的头部交易所，会在 40 分钟内被撕开如此巨大的口子？

#### 1. 铁律一：MPC 与 HSM 保护的是“密钥存储”，而不是“签名意图”

在过去五年的机构托管演进中，行业过度迷信多方安全计算（MPC）与硬件安全模块（HSM），认为“只要私钥碎片没有被拼凑导出，热钱包就是绝对安全的”。

然而，2025 年 2 月的 Bybit 15 亿美元被盗案（篡改 Safe 多签前端 UI 诱导签名）与 2026 年 10 月的币安 63.6 亿美元被盗案（渗透后端提币调度服务下发跨链签名指令），共同敲响了**“盲签时代”的丧钟**：
* 当攻击者通过被感染的工程师笔记本电脑或微服务容器，直接站在了“向签名机发送合法指令”的上游位置时，HSM 和 MPC 只不过是一个忠实执行命令的印章机器。
* 更致命的是，币安在 10 条采用完全不同椭圆曲线算法（ECDSA `secp256k1` 与 EdDSA `Ed25519`）的公链热钱包，竟然在 20 分钟内被同一个攻击源先后调动签名——这表明**各条公链的热钱包签名请求在架构上共享了同一个集中式的业务调度网关或权限凭证**，缺乏跨链物理隔离与独立二次鉴权。

#### 2. 铁律二：账户抽象（EIP-7702）改变了“交易的本体论”，风控引擎必须升级

正如慢雾创始人余弦所言，即便没有 EIP-7702，已经控制了签名系统的黑客依然可以像在比特币和波场上那样，通过签发普通转账盗走资产。**但 EIP-7702 在以太坊上的滥用，确实将单次签名的破坏力与隐蔽性放大了至少一个数量级：**
* **突破频率限制**：原本需要签发 64 笔独立交易才能搬空的 ETH 与 63 种 ERC-20 代币，借助 EIP-7702 指针注入后，只需 **1 次授权 + 1 次外部调用**即可在单笔交易内原子级扫空，不给风控系统任何“发现首笔异常后中断后续提币”的反应窗口。
* **持久化寄生（Persistent Hijacking）**：传统盗币是一次性的，钱转走后交易就结束了；而 EIP-7702 写入的 23 字节代码指针是一个**常驻后门**。只要受害机构没有在第一时间用原私钥签署指向零地址（`0x0000000000000000000000000000000000000000`）的撤销授权，该热钱包就永远装着黑客的清扫程序，后续每一笔不明真相的用户充值都会成为黑客的囊中之物。
* **强制防御改造**：所有中心化交易所、托管商与金库系统，必须在 HSM/MPC 硬件底层固件中**默认硬编码拦截 `0x04` 交易类型与 `0x05` 授权签名前缀**；同时对所有自有 EOA 地址建立区块级 `eth_getCode` 监控，一旦发现普通热钱包的 `code` 字段不再为空，必须在同一个区块周期内自动触发充提熔断并广播预置的撤销签名。

#### 3. 铁律三：意图撮合协议（Intent Solvers）成为黑客反冻结的“高速公路”

在早年的加密盗窃案中，黑客拿到百亿级别的 USDT/USDC 后往往束手无策，因为普通 AMM 池（如 Uniswap V2/V3）的链上流动性分散，且需要多步交互。而在本次事件中，黑客在短短几十分钟内就通过 **UniswapX** 与 **1inch Fusion** 倾销了数亿美元的被盗 USDT（其中两个 UniswapX Filler 地址就承接了 2.45 亿 USDT 订单）（[Bitquery](https://bitquery.io/investigations/binance-hack-who-profited)）。

原因在于这类新一代“意图撮合协议”引入了链下做市商（Solvers / Market Makers）竞价填单机制——黑客愿意让渡 **10%–15% 的巨额价格折扣（滑点）**，激励自动化做市商机器人在毫秒级时间内掏出自己库存里的干净 ETH 完成对手方交割，等到几十分钟后 Tether 的冻结指令赶到时，价值数亿美元的“可冻结稳定币”早已变成了黑客冷钱包里“不可冻结的原生 ETH”，而接盘了脏款 USDT 的做市商或流动性池则不得不面对合规与冻结风险。未来 12–24 个月内，针对 **DEX Solver 与链上借贷池的毫秒级威胁情报接入（Real-time Address Screening）**将成为机构合规的必争之地。

---

### 六、 核心专业概念通俗词典（Glossary for Non-Specialists）

为了方便跨学科读者无障碍掌握本文涉及的密码学与以太坊底层工程术语，我们将核心概念归纳如下：

| 专业术语 | 英文全称 / 字节标识 | 通俗知性解析（跨领域类比） |
| :--- | :--- | :--- |
| **EOA 账户** | Externally Owned Account（外部拥有账户） | 类似于**“只认印章的传统银行存折”**。由一对公私钥控制，本身没有任何自动执行代码的能力，每转一笔钱都必须由主人亲自盖一次章（私钥签名）。 |
| **EIP-7702** | Ethereum Improvement Proposal 7702（交易类型 `0x04`） | 以太坊 2025 年 Pectra 升级引入的新特性，相当于允许传统存折签一份**“外包代管协议”**，把存折的操作逻辑临时委托给某个外部智能程序（写入 23 字节 `0xef0100 + 合约地址` 指针），从而让普通钱包瞬间具备一键批量转账等高级功能。 |
| **DELEGATECALL** | Delegate Call（委托调用上下文） | 一种特殊的代码执行方式：好比你请了一位外部管家（黑客清扫合约）进入你的私人金库（`Binance 14`），管家在金库里执行的每一个搬钱动作，在门卫（ERC-20 代币合约）看来都完全等同于**金库主人亲自下令**。 |
| **Nonce** | Number Used Once（账户交易计数器） | 类似于支票本上的**“连续流水支票号”**。钱包每发出一笔交易，号码自动加 1。为了防止别人把你以前签过的支票复印再刷一次，系统规定只有支票号与当前最新流水号严丝合缝时才予兑付。黑客连签 50 个连号，就是为了赌中高速跳动中的那一个当前流水号。 |
| **HSM / MPC** | Hardware Security Module / Multi-Party Computation | 机构级密钥保护技术：好比把公章锁进防弹玻璃箱里，由机械臂根据审批系统的电子信号自动盖章。它能防止小偷把公章偷走，但如果**上游审批电脑中毒发出了错误的盖章指令**，机械臂依然会忠实地盖下真章。 |
| **Peel Chain** | Peel Chain（剥离链洗钱手法） | 比特币链上常见的一种资金拆分技术：一条主资金流在连续多个区块中，像削土豆皮一样每次剥离出规整的 100 BTC 或 1,000 BTC 打入新地址，剩余资金继续流向下一跳，借此增加链上追踪的复杂度。 |
| **Intent Solver** | 意图撮合求解器（如 UniswapX / 1inch Fusion） | 用户只需声明“我想用 1 亿 USDT 换 ETH，哪怕贵 15% 也行”，链下待命的专业做市商机器人（Solver）看到如此丰厚的价差利润，便会毫秒级主动拿自己的 ETH 替用户完成兑换。 |
