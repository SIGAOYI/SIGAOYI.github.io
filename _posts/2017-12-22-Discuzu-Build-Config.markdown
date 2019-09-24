---
layout:     post
title:      "用DiscuzX3.2建站玩耍"
subtitle:   "The Story of Enjoy Discuz"
date:       2017-12-22
author:     "龟龟"
header-img: "http://cdn.tdagroup.cn/pexels-photo-175411.jpeg"
tags:
    - 笔记
    - Discuz
    - 论坛
    - 建站
    - 站长
---

>Vue.js 放弃中...



## **目录:**

## [一、简述](#0)

## [二、安装配置](#1)

## [三、配置文件](#2)


<p id="0"></p>

## 一、简述


Discuz是主流的社区论坛管理方案，小米论坛、威锋论坛等国内知名论坛均使用的是Discuz的框架进行二次开发和内容管理，这里不多赘述。

有一件轶事可以分享一下：

>Discuz的第一位商业用户是“香港警察俱乐部”（Discuz亦为其量身订造了特有的程序），当时候Discuz的作者戴志康还在念大学，在沈阳的大学宿舍居住，香港警察俱乐部的网主每次打电话找他都要经过大学的总机转接他来听电话，那时候他连手机都还没有，可是今天他已经成为百万美元注册的集团董事了，香港警察俱乐部亦顺理成章成了他第一个商业客户，后来他的同事还跟香港警察俱乐部的网主说，正因为当初香港警察俱乐部向他购买了他写的这款程序，所以坚定了他们后来的创业道路，他笑着说：“你（香港警察俱乐部的网主）的一个不经意的决定，改变了另一个人的命运。

<p id="1"></p>

## 二、安装配置


首先去[官网](http://www.discuz.net/forum-10-1.html)下载程序安装包，我选择的是X3.2版本。

解压后部署到自己的服务器上、

关于如何部署服务器有一万种方法，这里我用的是[Ubuntu+Nginx+Mysql](https://blog.izgq.net/archives/763/)的方案。

完成服务器的部署后，就是选择一个域名解析并指向服务器。

这里以[http://www.freedivefamily.com](http://www.freedivefamily.com)为例。

接下来开始在本地浏览器中安装 Discuz! X3，在浏览器中运行： http://www.freedivefamily.com/bbs/install/ 开始全新安装。


![](http://www.discuz.net/data/attachment/forum/201304/28/133039m7f83jye3fsqgf0q.gif.thumb.jpg)

阅读授权协议后点击“我同意”，系统会自动检查环境及文件目录权限，这里文件读写状态出现异常的同学请自行谷歌解决，因为我一次通关。

检测成功，点击“下一步”，即进入检测服务器环境以及设置 UCenter 界面，如下图所示：

![](http://www.discuz.net/data/attachment/forum/201304/28/133039wn8cihhf1fk8chnk.gif.thumb.jpg)

点击“下一步”，进入安装数据库的界面，如下图所示：

![](http://www.discuz.net/data/attachment/forum/201304/28/133040b7b3g7z7b7urg2bp.gif.thumb.jpg)

填写好 Discuz! X 数据库信息及管理员信息。
点击“下一步”，系统会自动安装数据库直至完毕。

安装成功后，就会自动跳转到Discuz的欢迎界面。

![](http://www.discuz.net/data/attachment/forum/201304/28/133041r7g9ux7geq557rx7.gif.thumb.jpg)

这里，建议直接开通云平台，因为后期通过后台再开通会遇到很多问题，亲测采坑。

至此，Discuz! X3.2 已经成功地安装完毕!

<p id="2"></p>

## 三、配置文件

Discuz！安装成功后，后台配置都很简单，难度就在于站内优化和SEO相关设置了。

简单总结就是：生命不息，优化不止……

除此之外，特别介绍一下几个基本的配置文件

配置文件：

config下config_global.php，config_ucenter.php，uc_server\data下的config.inc.php

主要说配置文件config下config_ucenter.php和uc_server\data下的config.inc.php

配置文件config下config_ucenter.php对应后台--站长--ucenter设置

UCenter 应用 ID:1 　　　define('UC_APPID', '1');

UCenter 通信密钥:B0Z9k2pbX7j5J1H9zfgdVeDaY8I2I2zfUc00C1J4B4ga9fNdOed7X7p3S5ubD2ba

define('UC_KEY', 'B0Z9k2pbX7j5J1H9zfgdVeDaY8I2I2zfUc00C1J4B4ga9fNdOed7X7p3S5ubD2ba');

UCenter 访问地址:http://localhost/uc_server 　　define('UC_API', 'http://localhost/uc_server');

UCenter IP 地址:127.0.0.1 　　define('UC_IP', '127.0.0.1');

UCenter 连接方式:数据库方式 　　define('UC_CONNECT', 'mysql');

UCenter 数据库服务器:localhost 　　define('UC_DBHOST', 'localhost');

UCenter 数据库用户名:root 　　define('UC_DBUSER', 'root');

UCenter 数据库密码:***　　 define('UC_DBPW', '123');

UCenter 数据库名:x2 　　define('UC_DBNAME', 'x2');

UCenter 表前缀:pre_ucenter_ 　　define('UC_DBTABLEPRE', '`x2`.pre_ucenter_');


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
