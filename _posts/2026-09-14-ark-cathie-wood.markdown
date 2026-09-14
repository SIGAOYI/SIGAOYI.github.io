---
layout:     post
title:      "Cathie Wood / ARK 每日持仓追踪 (2026-09-14)"
subtitle:   "ARKK·ARKW·ARKG·ARKQ 全持仓快照与当日买卖变化 · 数据源：ARK 官方每日披露"
date:       2026-09-14
author:     "龟龟"
header-img: "/img/home-bg.jpg"
catalog:    true
tags:
    - 投资
    - Cathie Wood
    - ARK
    - 持仓追踪
---

> 🤖 **每交易日自动更新**。数据来自 ARK Invest 官方每日全持仓披露（assets.ark-funds.com），为公开信息；本文为基于公开数据的原创整理，**非投资建议**。选题线索来自 [Moomoo Whale Watch](https://www.moomoo.com/quote/institution-tracking)（仅作线索与致谢，未使用其文章内容）。

**数据日期：2026-09-14（周一）** ｜ 覆盖基金：4 只 ｜ 合计市值约 $11.93B

## 当日概览

- **ARKK**（ARK 旗舰·颠覆式创新）：47 只持仓，规模约 $6.40B，第一大重仓 **TSLA**（9.76%）
- **ARKW**（下一代互联网）：44 只持仓，规模约 $1.82B，第一大重仓 **TSLA**（7.71%）
- **ARKG**（基因革命）：33 只持仓，规模约 $1.81B，第一大重仓 **TXG**（10.56%）
- **ARKQ**（自动化与机器人）：39 只持仓，规模约 $1.90B，第一大重仓 **TSLA**（10.85%）

## ARKK 旗舰：前 15 大重仓（按权重）

<div id="ark_arkk_top" style="width:100%;max-width:860px;margin:18px auto;height:510px;"></div>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"></script>
<script>
(function(){
  var raw=[{"name": "CBRS", "value": 2.63}, {"name": "PLTR", "value": 2.66}, {"name": "CRWV", "value": 2.69}, {"name": "OPENAI GROUP PBC SERIES C", "value": 2.7}, {"name": "AMD", "value": 2.73}, {"name": "SHOP", "value": 3.11}, {"name": "TWST", "value": 3.19}, {"name": "TXG", "value": 3.24}, {"name": "HOOD", "value": 4.13}, {"name": "CRSP", "value": 4.45}, {"name": "COIN", "value": 4.53}, {"name": "TEM", "value": 4.8}, {"name": "CRCL", "value": 5.55}, {"name": "SPCX", "value": 6.63}, {"name": "TSLA", "value": 9.76}];
  var names=raw.map(function(d){return d.name;});
  var vals=raw.map(function(d){return d.value;});
  function draw(){
    var el=document.getElementById("ark_arkk_top");
    if(!el||!window.echarts) return;
    var ch=echarts.init(el);
    ch.setOption({
      grid:{left:8,right:56,top:10,bottom:10,containLabel:true},
      tooltip:{trigger:"axis",axisPointer:{type:"shadow"},valueFormatter:function(v){return v+"%";}},
      xAxis:{type:"value",axisLabel:{formatter:"{value}%"}},
      yAxis:{type:"category",data:names,axisLabel:{fontSize:12}},
      series:[{type:"bar",data:vals,barMaxWidth:22,
        itemStyle:{color:"#c0392b",borderRadius:[0,4,4,0]},
        label:{show:true,position:"right",formatter:"{c}%",fontSize:11}}]
    });
    window.addEventListener("resize",function(){ch.resize();});
  }
  if(window.echarts){draw();}else{var t=setInterval(function(){if(window.echarts){clearInterval(t);draw();}},100);setTimeout(function(){clearInterval(t);},6000);}
})();
</script>

<table style="width:100%;border-collapse:collapse;font-size:14px;">
<thead><tr style="text-align:left;border-bottom:2px solid #ccc;"><th>#</th><th>公司</th><th>代码</th><th style="text-align:right;">股数</th><th style="text-align:right;">市值</th><th style="text-align:right;">权重</th></tr></thead><tbody>
<tr style="border-bottom:1px solid #eee;"><td>1</td><td>TESLA INC</td><td>TSLA</td><td style="text-align:right;">1,709,212</td><td style="text-align:right;">$624.6M</td><td style="text-align:right;">9.76%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>2</td><td>SPACE EXPLORATION TECHN-CL A</td><td>SPCX</td><td style="text-align:right;">2,805,172</td><td style="text-align:right;">$424.2M</td><td style="text-align:right;">6.63%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>3</td><td>CIRCLE INTERNET GROUP INC</td><td>CRCL</td><td style="text-align:right;">3,921,752</td><td style="text-align:right;">$355.3M</td><td style="text-align:right;">5.55%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>4</td><td>TEMPUS AI INC-CL A</td><td>TEM</td><td style="text-align:right;">5,202,662</td><td style="text-align:right;">$307.0M</td><td style="text-align:right;">4.80%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>5</td><td>COINBASE GLOBAL INC -CLASS A</td><td>COIN</td><td style="text-align:right;">1,653,087</td><td style="text-align:right;">$289.7M</td><td style="text-align:right;">4.53%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>6</td><td>CRISPR THERAPEUTICS AG</td><td>CRSP</td><td style="text-align:right;">5,509,839</td><td style="text-align:right;">$285.0M</td><td style="text-align:right;">4.45%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>7</td><td>ROBINHOOD MARKETS INC - A</td><td>HOOD</td><td style="text-align:right;">2,349,965</td><td style="text-align:right;">$264.5M</td><td style="text-align:right;">4.13%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>8</td><td>10X GENOMICS INC-CLASS A</td><td>TXG</td><td style="text-align:right;">3,025,946</td><td style="text-align:right;">$207.5M</td><td style="text-align:right;">3.24%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>9</td><td>TWIST BIOSCIENCE CORP</td><td>TWST</td><td style="text-align:right;">1,605,854</td><td style="text-align:right;">$204.3M</td><td style="text-align:right;">3.19%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>10</td><td>SHOPIFY INC - CLASS A</td><td>SHOP</td><td style="text-align:right;">1,543,985</td><td style="text-align:right;">$198.8M</td><td style="text-align:right;">3.11%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>11</td><td>ADVANCED MICRO DEVICES</td><td>AMD</td><td style="text-align:right;">338,162</td><td style="text-align:right;">$174.5M</td><td style="text-align:right;">2.73%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>12</td><td>OPENAI GROUP PBC SERIES C</td><td></td><td style="text-align:right;">254,476</td><td style="text-align:right;">$172.6M</td><td style="text-align:right;">2.70%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>13</td><td>COREWEAVE INC-CL A</td><td>CRWV</td><td style="text-align:right;">1,937,429</td><td style="text-align:right;">$172.4M</td><td style="text-align:right;">2.69%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>14</td><td>PALANTIR TECHNOLOGIES INC-A</td><td>PLTR</td><td style="text-align:right;">1,018,209</td><td style="text-align:right;">$170.3M</td><td style="text-align:right;">2.66%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>15</td><td>CEREBRAS SYSTEMS INC - A</td><td>CBRS</td><td style="text-align:right;">876,403</td><td style="text-align:right;">$168.2M</td><td style="text-align:right;">2.63%</td></tr>
</tbody></table>

## 当日买卖变化（对比上一交易日）

> 首次运行，已建立基准快照；**增持/减持/新建/清仓 将从下一交易日起自动出现。**

## 其他 ARK 基金 · 前 8 大重仓

### ARKW（下一代互联网）

<table style="width:100%;border-collapse:collapse;font-size:14px;">
<thead><tr style="text-align:left;border-bottom:2px solid #ccc;"><th>#</th><th>公司</th><th>代码</th><th style="text-align:right;">股数</th><th style="text-align:right;">市值</th><th style="text-align:right;">权重</th></tr></thead><tbody>
<tr style="border-bottom:1px solid #eee;"><td>1</td><td>TESLA INC</td><td>TSLA</td><td style="text-align:right;">382,699</td><td style="text-align:right;">$139.9M</td><td style="text-align:right;">7.71%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>2</td><td>ARK BITCOIN ETF HOLDCO (ARKW)</td><td></td><td style="text-align:right;">3,775,474</td><td style="text-align:right;">$96.7M</td><td style="text-align:right;">5.33%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>3</td><td>ROBINHOOD MARKETS INC - A</td><td>HOOD</td><td style="text-align:right;">814,502</td><td style="text-align:right;">$91.7M</td><td style="text-align:right;">5.05%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>4</td><td>CIRCLE INTERNET GROUP INC</td><td>CRCL</td><td style="text-align:right;">975,879</td><td style="text-align:right;">$88.4M</td><td style="text-align:right;">4.87%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>5</td><td>SPACE EXPLORATION TECHN-CL A</td><td>SPCX</td><td style="text-align:right;">557,134</td><td style="text-align:right;">$84.2M</td><td style="text-align:right;">4.64%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>6</td><td>ADVANCED MICRO DEVICES</td><td>AMD</td><td style="text-align:right;">145,911</td><td style="text-align:right;">$75.3M</td><td style="text-align:right;">4.15%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>7</td><td>AMAZON.COM INC</td><td>AMZN</td><td style="text-align:right;">271,568</td><td style="text-align:right;">$69.7M</td><td style="text-align:right;">3.84%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>8</td><td>COINBASE GLOBAL INC -CLASS A</td><td>COIN</td><td style="text-align:right;">384,225</td><td style="text-align:right;">$67.3M</td><td style="text-align:right;">3.71%</td></tr>
</tbody></table>

### ARKG（基因革命）

<table style="width:100%;border-collapse:collapse;font-size:14px;">
<thead><tr style="text-align:left;border-bottom:2px solid #ccc;"><th>#</th><th>公司</th><th>代码</th><th style="text-align:right;">股数</th><th style="text-align:right;">市值</th><th style="text-align:right;">权重</th></tr></thead><tbody>
<tr style="border-bottom:1px solid #eee;"><td>1</td><td>10X GENOMICS INC-CLASS A</td><td>TXG</td><td style="text-align:right;">2,786,350</td><td style="text-align:right;">$191.1M</td><td style="text-align:right;">10.56%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>2</td><td>TWIST BIOSCIENCE CORP</td><td>TWST</td><td style="text-align:right;">1,184,600</td><td style="text-align:right;">$150.7M</td><td style="text-align:right;">8.33%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>3</td><td>TEMPUS AI INC-CL A</td><td>TEM</td><td style="text-align:right;">2,353,223</td><td style="text-align:right;">$138.9M</td><td style="text-align:right;">7.67%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>4</td><td>CRISPR THERAPEUTICS AG</td><td>CRSP</td><td style="text-align:right;">2,043,987</td><td style="text-align:right;">$105.7M</td><td style="text-align:right;">5.84%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>5</td><td>PERSONALIS INC</td><td>PSNL</td><td style="text-align:right;">6,469,791</td><td style="text-align:right;">$104.9M</td><td style="text-align:right;">5.79%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>6</td><td>ABSCI CORP</td><td>ABSI</td><td style="text-align:right;">10,134,917</td><td style="text-align:right;">$83.2M</td><td style="text-align:right;">4.60%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>7</td><td>GUARDANT HEALTH INC</td><td>GH</td><td style="text-align:right;">502,218</td><td style="text-align:right;">$79.0M</td><td style="text-align:right;">4.37%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>8</td><td>NATERA INC</td><td>NTRA</td><td style="text-align:right;">236,581</td><td style="text-align:right;">$77.8M</td><td style="text-align:right;">4.30%</td></tr>
</tbody></table>

### ARKQ（自动化与机器人）

<table style="width:100%;border-collapse:collapse;font-size:14px;">
<thead><tr style="text-align:left;border-bottom:2px solid #ccc;"><th>#</th><th>公司</th><th>代码</th><th style="text-align:right;">股数</th><th style="text-align:right;">市值</th><th style="text-align:right;">权重</th></tr></thead><tbody>
<tr style="border-bottom:1px solid #eee;"><td>1</td><td>TESLA INC</td><td>TSLA</td><td style="text-align:right;">563,948</td><td style="text-align:right;">$206.1M</td><td style="text-align:right;">10.85%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>2</td><td>SPACE EXPLORATION TECHN-CL A</td><td>SPCX</td><td style="text-align:right;">1,053,214</td><td style="text-align:right;">$159.3M</td><td style="text-align:right;">8.39%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>3</td><td>TERADYNE INC</td><td>TER</td><td style="text-align:right;">324,965</td><td style="text-align:right;">$123.4M</td><td style="text-align:right;">6.50%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>4</td><td>KRATOS DEFENSE &amp; SECURITY</td><td>KTOS</td><td style="text-align:right;">2,241,950</td><td style="text-align:right;">$104.7M</td><td style="text-align:right;">5.51%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>5</td><td>NVIDIA CORP</td><td>NVDA</td><td style="text-align:right;">428,976</td><td style="text-align:right;">$93.6M</td><td style="text-align:right;">4.93%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>6</td><td>ALPHABET INC-CL C</td><td>GOOG</td><td style="text-align:right;">259,897</td><td style="text-align:right;">$87.2M</td><td style="text-align:right;">4.59%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>7</td><td>PALANTIR TECHNOLOGIES INC-A</td><td>PLTR</td><td style="text-align:right;">496,166</td><td style="text-align:right;">$83.0M</td><td style="text-align:right;">4.37%</td></tr>
<tr style="border-bottom:1px solid #eee;"><td>8</td><td>ADVANCED MICRO DEVICES</td><td>AMD</td><td style="text-align:right;">155,626</td><td style="text-align:right;">$80.3M</td><td style="text-align:right;">4.23%</td></tr>
</tbody></table>

---

*本页由脚本依据 ARK 官方公开每日持仓 CSV 自动生成，仅供研究记录，不构成任何投资建议。持仓与权重每日变动，以 ARK 官方披露为准。*
