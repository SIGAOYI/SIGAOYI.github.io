---
layout:     post
title:      "用Charles在iOS上抓包"
subtitle:   "Wireshark is so easy MAMA no worry"
date:       2017-10-17
author:     "龟龟"
header-img: "http://cdn.tdagroup.cn/2017-09-18-banner.jpeg"
tags:
    - 笔记
    - 效率
    - 前端
---

>Vue.js 放弃中...

来总结一下用Charles在iOS上抓包的方法。

本文分三个部分：

[一、Mac客户端 下载安装激活](#0)

[二、Mac/iPhone证书 下载安装信任](#1)

[三、抓](#2)


<br/>

>我是看不见的分割线

<br/>

<p id="0"></p>
## 一、Mac客户端 下载安装激活

首先安装一枚Charles Mac版，俗称花瓶的抓包神器。

[官网下载地址](https://www.charlesproxy.com/)

![](http://cdn.tdagroup.cn/2017-10-17-1.png)
<small class="img-hint">如图所示下载最新版本</small>

下载并安装后打开并激活,Charles提供15天的免费试用，购买正价为30$。

`顺便说一句，破解版Charles偶发中文乱码，抓包数据不显示等问题,而且更新也不及时，建议购买正版神器。`

打开Charles后，点击菜单栏的Proxy->Proxy Settings...

勾选：HTTP Proxy，并设置Port为8888。

如下图：

![](http://cdn.tdagroup.cn/2017-10-17-2.png)
![](http://cdn.tdagroup.cn/2017-10-17-3.png)

<p id="1"></p>
## 二、iPhone证书 下载安装信任

安装好Mac客户端，就拿起手机开始配置iPhone了。

### 先用Mac建立同iPhone的代理通道

打开自己电脑的系统偏好设置->网络->选中现在连着的wifi,以查到自己这个电脑在现在这个wifi里的IP地址，比如我现在这个就是192.168.0.115（建议最好用私人或普通开放网络，用公司内网可能会有限制会出现代理失败的问题）

![](http://upload-images.jianshu.io/upload_images/2155136-404b2e0bea921839.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

然后确保手机也连接了同一个wifi，然后进入手机的wifi配置(wifi名称右边的蓝色“i”图标)，将http代理改为:192.168.0.115；端口：8888。点击左上角返回。返回后系统会自动设置代理重新连接。

这时候你的手机上网的过程中就要经过你的电脑了。刚用手机打开一个联网的程序，你的电脑上应该会显示一个弹窗问你【allow】还是【deny】肯定不能拒绝啊就点allow吧。这个只有第一次才弹窗。点了同意之后你手机发出的每一个请求都会被拦截出痕迹。

![](http://upload-images.jianshu.io/upload_images/2469183-8630cf0087d20187.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
![](http://upload-images.jianshu.io/upload_images/2469183-874a256420dcae1f.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

`注意：开启花瓶代理后，要关闭所有其他形式的代理，如爱国SS、爱国VPN等。`

### 再安装SSL证书到手机设备

点击 Help -> SSL Proxying -> Install Charles Root Certificate on a Mobile Device

![](http://upload-images.jianshu.io/upload_images/2469183-8f47a1b1c1540ef7.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

![](http://upload-images.jianshu.io/upload_images/2469183-c7f6ad4a204b0bd4.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
<small class="img-hint">出现弹窗得到地址[chls.pro/ssl](chls.pro/ssl)</small>

在手机Safari浏览器输入地址 chls.pro/ssl，出现证书安装页面，点击安装
手机设置有密码的输入密码进行安装

![](http://upload-images.jianshu.io/upload_images/2469183-7ed4a5c8c2a36217.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
<small class="img-hint">`注意：安装信任证书需保持电脑对手机的代理状态`</small>

`iOS 10.3及以上的系统，需要在 设置→通用→关于本机→证书信任设置 里面启用完全信任Charles证书`

![](http://cdn.tdagroup.cn/2017-10-17-4.png)
<small class="img-hint">图示为iOS11界面</small>

### 最后Charles设置Proxy

![](http://upload-images.jianshu.io/upload_images/2469183-2c460b4652797ccf.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)
<small class="img-hint">Proxy -> SSL Proxying Settings...</small>

![](http://upload-images.jianshu.io/upload_images/2469183-11eb2be75eae13fb.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

勾选Enable SSL Proxying,点击Add

`Host填写：*`

`Port填写：443`

<p id="2"></p>
## 三、抓

    大

    功

    告

    成

    ！

让手机重新发送https请求，可看到抓包

![](http://upload-images.jianshu.io/upload_images/2469183-5f1b21912781d466.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

`注意：不抓包请关闭手机HTTP代理，否则断开与电脑连接后会连不上网`

Charles还有不少好玩的网络调试功能，等我放弃Vue了再来说说。



































----
<br />
<table border="0">
    <tr border="0">
        <td>
            <img src="http://cdn.tdagroup.cn/0%20%2837%29.gif">
        </td>
        <td>
            <img src="http://cdn.tdagroup.cn/1490924677.png">
        </td>
    </tr>
    <tr>
        <td style="text-align:center">
            <span>不收钱</span>
        </td>
        <td style="text-align:center">
            <span>加好友</span>
        </td>
    </tr>
</table>
