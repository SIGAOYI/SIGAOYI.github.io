---
layout:     post
title:      "Ubuntu搭建Shadowsocks原来这么简单！！"
subtitle:   "The Story of FUCK gfw..."
date:       2017-11-14
author:     "龟龟"
header-img: "http://image.lawootrip.com/pexels-photo-175411.jpeg"
tags:
    - 笔记
    - Linux
---

>Vue.js 放弃中...


**目录:**

[一、简述](#0)

[二、基本环境](#1)

[三、配置文件](#2)

[四、配置自动运行](#3)

[五、常用命令](#4)


<p id="0"></p>

## 一、简述

本教程旨在提供简明的Ubuntu 16.04下安装服务器端Shadowsocks。不同于Ubuntu 16.04之前的教程，本文抛弃initd，转而使用Ubuntu 16.04支持的Systemd管理Shadowsocks的启动与停止，显得更为便捷。优化部分包括BBR、TCP Fast Open以及吞吐量优化。

本教程仅适用于Ubuntu 16.04及之后的版本，基于Python 3，支持IPv6。

<p id="1"></p>

## 二、基本环境

本教程使用Python 3为载体，因Python 3对应的包管理器`pip3`并未预装，首先安装`pip3`：

    sudo apt install python3-pip

因Shadowsocks作者不再维护pip中的Shadowsocks（定格在了2.8.2），我们使用下面的命令来安装最新版的Shadowsocks：

    pip3 install https://github.com/shadowsocks/shadowsocks/archive/master.zip

安装完成后可以使用下面这个命令查看Shadowsocks版本：

    sudo ssserver --version

目前会显示“Shadowsocks 3.0.0”。

<p id="2"></p>

## 三、配置文件

创建Shadowsocks配置文件所在文件夹：

    sudo mkdir /etc/shadowsocks

然后创建配置文件：

    sudo nano /etc/shadowsocks/config.json

复制粘贴如下内容：

    {
    "server":"your_server_ip",//注意：这里指本地IP或云服务器内网IP;
    "server_port":8388,
    "local_address": "127.0.0.1",
    "local_port":1080,
    "password":"mypassword",//注意修改密码“password”;
    "timeout":300,
    "method":"aes-256-cfb",
    "fast_open": false
    }

然后按Ctrl + O保存文件，Ctrl + X退出。

测试下Shadowsocks能不能正常工作了：

    ssserver -c /etc/shadowsocks/config.json

在Shadowsocks客户端添加服务器，如果你使用的是我提供的那个配置文件的话，地址填写你的IPv4地址或IPv6地址，端口号为8388，加密方法为aes-256-cfb，密码为你设置的密码。然后设置客户端使用全局模式，浏览器登录Google试试应该能直接打开了。

这时浏览器登录http://ip138.com/就会显示Shadowsocks服务器的IP啦！

测试完毕，按Ctrl + C关闭Shadowsocks。

<p id="3"></p>

## 四、配置自动运行

新建Shadowsocks管理文件

    sudo nano /etc/systemd/system/shadowsocks-server.service

复制粘贴：

    [Unit]
    Description=Shadowsocks Server
    After=network.target

    [Service]
    ExecStart=/usr/local/bin/ssserver -c /etc/shadowsocks/config.json
    Restart=on-abort

    [Install]
    WantedBy=multi-user.target

Ctrl + O保存文件，Ctrl + X退出。

启动Shadowsocks：

    sudo systemctl start shadowsocks-server

设置开机启动Shadowsocks：

    sudo systemctl enable shadowsocks-server

至此，Shadowsock服务器端的基本配置已经全部完成了！


<p id="4"></p>
#### **常用命令：**

    systemctl start shadowsocks //启动SS
    systemctl enable shadowsocks //停止SS
    systemctl status shadowsocks//查看SS状态

厉害的一个命令

    tcpdump -i any -nn 'port 8338' -vv -X //监听端口数据

>-i interface，网卡的名称，后面可以跟具体的网卡名称(ifconfig后者tcpdump -D)获取，笔者的电脑上看到any，似乎是指所有的网卡
>
>-nn 监听host或者port名，这个网上解释有一大堆，什么src host，dist host  ，比如我要抓，ip地址为127.0.0.1，端口为9002的服务器的数据包，那么命令可以写成-nn 'src host 127.0.0.1 and >port 9002'.不过实际来讲，端口肯定是被一个ip地址使用的，而且对于我来说，服务器抓包比较有意义，所以，其实有没有ip地址，似乎显得不那么重要，有端口就可以。
>
>-vv 详细信息
>
>-X 以16进制的格式输出


## 附加题、优化吞吐量

新建配置文件：

    sudo nano /etc/sysctl.d/local.conf

复制粘贴：

    # max open files
    fs.file-max = 51200
    # max read buffer
    net.core.rmem_max = 67108864
    # max write buffer
    net.core.wmem_max = 67108864
    # default read buffer
    net.core.rmem_default = 65536
    # default write buffer
    net.core.wmem_default = 65536
    # max processor input queue
    net.core.netdev_max_backlog = 4096
    # max backlog
    net.core.somaxconn = 4096

    # resist SYN flood attacks
    net.ipv4.tcp_syncookies = 1
    # reuse timewait sockets when safe
    net.ipv4.tcp_tw_reuse = 1
    # turn off fast timewait sockets recycling
    net.ipv4.tcp_tw_recycle = 0
    # short FIN timeout
    net.ipv4.tcp_fin_timeout = 30
    # short keepalive time
    net.ipv4.tcp_keepalive_time = 1200
    # outbound port range
    net.ipv4.ip_local_port_range = 10000 65000
    # max SYN backlog
    net.ipv4.tcp_max_syn_backlog = 4096
    # max timewait sockets held by system simultaneously
    net.ipv4.tcp_max_tw_buckets = 5000
    # turn on TCP Fast Open on both client and server side
    net.ipv4.tcp_fastopen = 3
    # TCP receive buffer
    net.ipv4.tcp_rmem = 4096 87380 67108864
    # TCP write buffer
    net.ipv4.tcp_wmem = 4096 65536 67108864
    # turn on path MTU discovery
    net.ipv4.tcp_mtu_probing = 1

    net.ipv4.tcp_congestion_control = bbr

运行：

    sysctl --system

编辑之前的shadowsocks-server.service文件：

    sudo nano /etc/systemd/system/shadowsocks-server.service

在`ExecStart`前插入一行，内容为：

    ExecStartPre=/bin/sh -c 'ulimit -n 51200'

即修改后的shadowsocks-server.service内容为：

    [Unit]
    Description=Shadowsocks Server
    After=network.target

    [Service]
    ExecStartPre=/bin/sh -c 'ulimit -n 51200'
    ExecStart=/usr/local/bin/ssserver -c /etc/shadowsocks/config.json
    Restart=on-abort

    [Install]
    WantedBy=multi-user.target

Ctrl + O保存文件，Ctrl + X退出。

重载shadowsocks-server.service：

    sudo systemctl daemon-reload

重启Shadowsocks：

    sudo systemctl restart shadowsocks-server

TCP Fast Open可以降低Shadowsocks服务器和客户端的延迟。实际上在上一步已经开启了TCP Fast Open，现在只需要在Shadowsocks配置中启用TCP Fast Open。

编辑config.json：

    sudo nano /etc/shadowsocks/config.json

将fast_open的值由false修改为true。Ctrl + O保存文件，Ctrl + X退出。

重启Shadowsocks：

    sudo systemctl restart shadowsocks-server

    注意：TCP Fast Open同时需要客户端的支持，即客户端Linux内核版本为3.7.1及以上；你可以在Shadowsocks客户端中启用TCP Fast Open。

    至此，Shadowsock服务器端的优化已经全部完成了！


[启蒙教程](https://www.polarxiong.com/archives/Ubuntu-16-04%E4%B8%8BShadowsocks%E6%9C%8D%E5%8A%A1%E5%99%A8%E7%AB%AF%E5%AE%89%E8%A3%85%E5%8F%8A%E4%BC%98%E5%8C%96.html)


----
<br />
<br />
<table>
<tr>
<td>
<img src="http://image.lawootrip.com/0%20%2837%29.gif"> </td>
<td>
<img src="http://image.lawootrip.com/1490924677.png"><div><small class="img-hint">这不是收钱的  加个好友而已</small></div></td>
</tr>
</table>
