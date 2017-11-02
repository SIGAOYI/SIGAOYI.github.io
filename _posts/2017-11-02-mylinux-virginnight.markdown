---
layout:     post
title:      "Ubuntu下Nginx配置笔记"
subtitle:   "The Story of Linux..."
date:       2017-11-02
author:     "龟龟"
header-img: "http://image.lawootrip.com/2017-05-15-bg.png"
tags:
    - 笔记
    - 服务器
    - Linux
---

>Vue.js 放弃中...

阿里云双十一活动还算良心,赶紧买个服务器自己玩.

本着日后方便科学上网的原则,买了2核4G,1M带宽的香港节点3年,搭载Ubuntu 16.0402系统镜像.

本地环境:MAC OS Sierra 10.12.3

**本文分四个部分:**

[一、使用SSH通过MAC同Ubuntu建立连接](#0)

[二、Ubuntu服务器基本设置](#1)

[三、环境搭建](#2)

[四、配置多个站点](#3)

<p id="0"></p>
### 一、使用SSH通过MAC同Ubuntu建立连接

#### 1.Ubuntu端

在ubuntu终端上输入`root@ubuntu:~$ sudo apt-get install openssh-server`命令安装openssh-server.(阿里云生成的系统登陆后,默认是root角色)

一般报错有两个可能的原因,一个是apt版本过老,办法是update一下;另一个是apt的lists损坏,办法是用如下命令来删除已经损坏的lists.

    `root@ubuntu:~$ sudo rm /var/lib/apt/lists/* -vf`



#### 2.MAC端

在终端上输入

    ssh root@your_server_ip

跟着指引输入服务器密码即可,是不是敲简单.

如果不想每次输入IP,可以在 /.ssh/config 里进行配置,🌰如下:

    Host mylinux
        HostName ***.***.***.***
        Port 22
        User root
        IdentityFile /Users/***/.ssh/mylinux \\这里是ssh私钥的路径,不作不用动

像上面这样配置后,每次只需要在终端敲入:

    ssh mylinux

即可!

找不到`/Users/***/.ssh`文件夹?
用下面的命令可以显示MAC隐藏文件.

    defaults write com.apple.finder AppleShowAllFiles -bool true


<p id="1"></p>
### 二、Ubuntu服务器基本设置

#### 使用root登录服务器

首先我们需要使用刚刚配置好的root用户ssh登录服务器:

    local$ ssh root@SERVER_IP_ADDRESS

前面的local$表示是在本地机器操作,在服务器端,该提示符会类似`root@my-remote-server:~$`这种形式,后边会看到。

>Tips: 如果使用的是腾讯云，其初始登录默认使用的是用户ubuntu，并不是root。因此，使用ssh ubuntu@your_server_ip登录之后可以修改下root的密码，然后就可以切换到用户root了。

修改密码命令如下：

    ubuntu@VM-42-158-ubuntu:~$ sudo passwd root
    Enter new UNIX password:
    Retype new UNIX password:
    passwd: password updated successfully

有可能还需要编辑配置文件/etc/ssh/sshd_config中的PermitRootLogin的设置。

    buntu@VM-42-158-ubuntu:~$ su
    Password:
    root@VM-42-158-ubuntu:/#

#### 新增超级用户权限用户

root用户虽然强大,但是正是由于太强大了,所以显得不够安全,因此通常情况下我们需要创建一个新的用户,然后给他设置超级用户(superuser)权限,这样就可以安全的进行各种操作了。

使用root用户登录,做如下操作:

    root@my-remote-server:~$ adduser dennis
    root@my-remote-server:~$ usermod -aG sudo dennis


这里就将新创建的用户加入了sudo用户组,就具有了超级用户的权限。更详细的信息可以参考[这个教程](https://www.digitalocean.com/community/tutorials/how-to-edit-the-sudoers-file-on-ubuntu-and-centos)。

然后我们就可以以新创建的用户登录了:

    root@my-remote-server:~# su - dennis
    dennis@my-remote-server:~$

<p id="2"></p>
### 三、环境搭建

#### 安装Nginx

在ubuntu上安装软件很简单,使用apt-get即可。注意由于权限问题,需要在前面加sudo。

    sudo apt-get update
    sudo apt-get install nginx

>**踩坑提醒**

##### 安装Nginx时出现错误

    dennis@my-remote-server:~$ sudo apt-get install nginx
    Reading package lists... Done
    Building dependency tree
    Reading state information... Done
    nginx is already the newest version (1.10.0-0ubuntu0.16.04.2).
    0 upgraded, 0 newly installed, 0 to remove and 42 not upgraded.
    2 not fully installed or removed.
    After this operation, 0 B of additional disk space will be used.
    Do you want to continue? [Y/n]
    Setting up nginx-core (1.10.0-0ubuntu0.16.04.2) ...
    Job for nginx.service failed because the control process exited with error code. See "systemctl status nginx.service" and "journalctl -xe" for details.
    invoke-rc.d: initscript nginx, action "start" failed.
    dpkg: error processing package nginx-core (--configure):
     subprocess installed post-installation script returned error exit status 1
    dpkg: dependency problems prevent configuration of nginx:
     nginx depends on nginx-core (>= 1.10.0-0ubuntu0.16.04.2) | nginx-full (>= 1.10.0-0ubuntu0.16.04.2) | nginx-light (>= 1.10.0-0ubuntu0.16.04.2) | nginx-extras (>= 1.10.0-0ubuntu0.16.04.2); however:
      Package nginx-core is not configured yet.
      Package nginx-full is not installed.
      Package nginx-light is not installed.
      Package nginx-extras is not installed.
     nginx depends on nginx-core (<< 1.10.0-0ubuntu0.16.04.2.1~) | nginx-full (<< 1.10.0-0ubuntu0.16.04.2.1~) | nginx-light (<< 1.10.0-0ubuntu0.16.04.2.1~) | nginx-extras (<< 1.10.0-0ubuntu0.16.04.2.1~); however:
      Package nginx-core is not configured yet.
      Package nginx-full is not installed.
      Package nginx-light is not installed.
      Package nginx-extras is not installed.
    dpkg: error processing package nginx (--configure):
     dependency problems - leaving unconfigured
    Errors were encountered while processing:
     nginx-core
     nginx
    E: Sub-process /usr/bin/dpkg returned an error code (1)


原因分析

Google了一下,发现出现这种错误,一般应该是由于其他应用占用了80端口。可以这样来看下:

    dennis@myserver:~$ sudo netstat -nlp
    sudo: unable to resolve host myserver
    [sudo] password for dennis:
    Active Internet connections (only servers)
    Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
    tcp        0      0 0.0.0.0:111             0.0.0.0:*               LISTEN      132/rpcbind
    tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN      332/apache2
    tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      269/sshd
    tcp        0      0 0.0.0.0:25              0.0.0.0:*               LISTEN      454/master
    tcp6       0      0 :::111                  :::*                    LISTEN      132/rpcbind
    tcp6       0      0 :::22                   :::*                    LISTEN      269/sshd


果然80端口被默认安装的apache给占掉了,所以需要干掉占用80端口的apache2：

    sudo kill -9 332

运行apt-get命令更新或安装软件出现Setting locale failed错误

    perl: warning: Setting locale failed.
    perl: warning: Please check that your locale settings:
    	LANGUAGE = (unset),
    	LC_ALL = (unset),
    	LC_CTYPE = "en_US.UTF-8",
    	LANG = "en_US.UTF-8"
        are supported and installed on your system.
    perl: warning: Falling back to the standard locale ("C").
    locale: Cannot set LC_CTYPE to default locale: No such file or directory
    locale: Cannot set LC_MESSAGES to default locale: No such file or directory
    locale: Cannot set LC_ALL to default locale: No such file or directory

解决办法：

    sudo ap-get update
    apt-get install language-pack-en

##### Nginx 常用目录

内容

/var/www/html: 保存web网页内容的默认目录

服务器配置

/etc/nginx: nginx 配置目录。所有Nginx相关的配置文件都在这里。
/etc/nginx/nginx.conf: Nginx主配置文件,进行全局默认设置。
/etc/nginx/sites-available: 针对每个”server blocks”独立的配置文件。这里的配置文件并不被直接使用,只有软连接到site-enabled的配置才会真正生效。
/etc/nginx/sites-enabled/: 针对每个”server blocks”独立的配置文件。由sites-available链接过来。
/etc/nginx/snippets: 一些配置脚本片段。

服务器日志

`/var/log/nginx/access.log: `默认保存所有与web服务交互的请求。
`/var/log/nginx/error.log: `Nginx的错误日志

#### 顺便安装一下MySQL

##### 安装

    sudo apt-get update
    sudo apt-get install mysql-server

##### 配置

    sudo mysql_secure_installation

##### 查看MySQL的版本：

    mysql --version

##### 初始化

    sudo mysqld --initialize

如果是如上面那样通过apt-get安装的，这一步通常已经被做了。因此会有如下错误提示：

    [ERROR] --initialize specified but the data directory has files in it. Aborting.

##### MySQL的启动和停止

    sudo /etc/init.d/mysql start
    sudo /etc/init.d/mysql stop
    sudo /etc/init.d/mysql restart

或者

    sudo start mysql
    sudo stop mysql
    sudo restart mysql

##### 测试连接

可以通过`mysqladmin -p -u root version`命令来测试一下mysql连接是否正常。

    dennis@my-remote-server:/var/www/html$ mysqladmin -p -u root version
    Enter password:
    mysqladmin  Ver 8.42 Distrib 5.7.13, for Linux on x86_64
    Copyright (c) 2000, 2016, Oracle and/or its affiliates. All rights reserved.
    Oracle is a registered trademark of Oracle Corporation and/or its
    affiliates. Other names may be trademarks of their respective
    owners.
    Server version		5.7.13-0ubuntu0.16.04.2
    Protocol version	10
    Connection		Localhost via UNIX socket
    UNIX socket		/var/run/mysqld/mysqld.sock
    Uptime:			19 min 14 sec
    Threads: 1  Questions: 8  Slow queries: 0  Opens: 115  Flush tables: 1  Open tables: 34  Queries per second avg: 0.006

##### 创建数据库及新的数据库用户

    mysql -u root -p

用密码登录成功之后执行下面的sql语句创建一个数据库，名叫lawootrip

    CREATE DATABASE lawootrip DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci;

安全起见，我们为这个数据库创建一个单独的用户：

    GRANT ALL ON wordpress.* TO 'lawootripuser'@'localhost' IDENTIFIED BY 'password';
    FLUSH PRIVILEGES;
    EXIT;

在外网通过IP直接访问操作数据库

默认情况下,我们只能在服务器上通过localhost访问MySQL,如果需要通过IP从外网访问,需要进行相应的设置。

1) 修改授权

    GRANT ALL ON lawootrip.* TO 'lawootripuser'@'%' IDENTIFIED BY 'password';
    FLUSH PRIVILEGES;
    EXIT;

如果需要,还可以指定特定的IP地址(替换上面的%即可)。

或者可以直接修改表:

    mysql -u root -p
    mysql> use mysql;
    mysql> update user set host = '%' where user = 'root';
    mysql> select user, host from user;
    +------------------+-----------+
    | user             | host      |
    +------------------+-----------+
    | mysql.sys        | localhost |
    | root             | localhost |
    | wordpressuser    | %         |
    +------------------+-----------+
    3 rows in set (0.00 sec)

2) 修改配置文件

配置文件位置为/etc/mysql/mysql.conf.d/mysqld.cnf,注释掉其中一行:

    bind-address  =127.0.0.1

重启MySQL即可:

    sudo service mysql restart

##### 配置Nginx

打开配置文件：

    sudo vim /etc/nginx/sites-available/default

作如下修改（具体可以参考[这里的说明](https://www.digitalocean.com/community/tutorials/how-to-install-wordpress-with-lemp-on-ubuntu-16-04)）

    server {
        . . .
        location = /favicon.ico { log_not_found off; access_log off; }
        location = /robots.txt { log_not_found off; access_log off; allow all; }
        location ~* \.(css|gif|ico|jpeg|jpg|js|png)$ {
            expires max;
            log_not_found off;
        }
        . . .
    }

对try_files做如下修改：

    server {
        . . .
        location / {
            #try_files $uri $uri/ =404;
            try_files $uri $uri/ /index.php$is_args$args;
        }
        . . .
    }

然后检查配置文件的正确性，并重启Nginx：

    sudo nginx -t
    //If no errors were reported, reload Nginx by typing:
    sudo systemctl reload nginx


<p id="3"></p>
### 四、配置多个站点

通常情况下我们需要在Web服务器上部署多个站点,使用多个不同的域名。

#### 设置新的文档目录

默认情况下,在Ubuntu上的Nginx已经默认创建了一个server block,其文档目录为/var/www/html(我们在上面安装wordpress的时候使用的就是这个默认的server block)。

如果我们需要部署多个站点,那么就需要创建多个不同的server block。假如我们需要部署两个网站:

    lawootrip.com
    lawoo.cn

这样我们就需要设置两个新的文档目录。为统一起见,我们使用xxx.com/html这种目录结构形式:

    sudo mkdir -p /var/www/lawootrip.com/html
    sudo mkdir -p /var/www/lawoo.cn/html

修改一下这两个文档目录的权限:

    sudo chown -R $USER:$USER /var/www/lawootrip.com/html
    sudo chown -R $USER:$USER /var/www/lawoo.cn/html

这里用到了环境变量`$USER`,请确保没有使用root账号进行操作。

    dennis@my-remote-server:~$ echo $USER
    dennis

至此文档目录应该配置好了。如果需要,我们可以通过下面的命令设置一下上层目录的权限:

    sudo chmod -R 755 /var/www

需要提醒的是,暂时不需要担心这两个测试域名是否可以访问的问题,后边我们会介绍在本地浏览器如何访问这两个测试域名。

#### 为每个站点创建测试文件

创建文件/var/www/lawootrip.com/html/index.html

创建文件/var/www/lawoo.cn/html/index.html

#### 为每个站点创建server block文件

如前所述,默认情况下Nginx已经配置了一个默认的server block,因此我们可以将默认的server block配置文件拷贝过来稍作修改:

    sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/lawootrip.com

打开文件:

    sudo vim /etc/nginx/sites-available/lawootrip.com

其内容如下:

    server {
            listen 80 default_server;
            listen [::]:80 default_server;
            root /var/www/html;
            index index.html index.htm index.nginx-debian.html;
            server_name _;
            location / {
                    try_files $uri $uri/ =404;
            }
    }

对其内容稍作修改,修改之后内容如下:

    server {
            listen 80;
            listen [::]:80;
            root /var/www/lawootrip.com/html;
            index index.html index.htm index.nginx-debian.html;
            server_name lawootrip.com www.lawootrip.com;
            location / {
                    try_files $uri $uri/ =404;
            }
    }

主要修改了几个地方:

* 去掉了default_server字眼。一台服务器上只能有一个default_server的配置,因此我们保留系统最初的设置为默认设置。
* 修改root目录.
* 修改server_name.

针对第二个站点lawoo.cn也做类似修改。

    sudo cp /etc/nginx/sites-available/lawoo.cn /etc/nginx/sites-available/lawoo.cn
    sudo vim /etc/nginx/sites-available/lawoo.cn

#### 激活两个站点的server block

使用如下命令:

    sudo ln -s /etc/nginx/sites-available/lawootrip.com /etc/nginx/sites-enabled/
    sudo ln -s /etc/nginx/sites-available/lawoo.cn /etc/nginx/sites-enabled/

这样这些文件(链接)就位于激活的目录内了。到目前为止我们有3个激活了的server block了。服务器根据listen指令和server_name来确定该访问那个目录。

* lawootrip.com: 响应来自lawootrip.com以及www.lawootrip.com的请求
* lawoo.cn: 响应来自lawoo.cn以及www.lawoo.cn的请求
* default: 响应没有匹配到上面两个规则的80端口的请求。

然后检查下nginx配置文件的正确性:

    sudo nginx -t

`**重启一下nginx使修改生效:**`

    sudo systemctl restart nginx

关于Nginx更多的指令介绍可以参考[这个教程](https://www.digitalocean.com/community/tutorials/understanding-nginx-server-and-location-block-selection-algorithms)。

#### 配置二级子域名及代理访问

举例来说，比如我们在我的服务器上有两个web程序，一个是之前的 lawootrip.com，另一个程序是python应用，使用端口5555，需要映射到二级域名 demo.lawootrip.com。我们应该如何设置呢？

##### 1）添加域名解析

这个步骤不多说了，在域名服务提供商网站添加一条A记录，设置域名demo.lawootrip.com。

##### 2）修改Nginx配置文件

就是我们上面提到的文件`/etc/nginx/sites-available/lawootrip.com`,添加如下内容：

    server {
        listen 80;
        server_name demo.example.com;
        location / {
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   Host      $http_host;
            proxy_pass         http://127.0.0.1:5555;
        }
    }

然后重启Nginx即可。

    sudo systemctl restart nginx

>Tips 阿里云特供

Ubuntu 在每次执行命令的时候，会报如下错误：

    $ sudo
    sudo: unable to resolve host iZj6cfyvsfiajdiy47qddhZ

iZj6cfyvsfiajdiy47qddhZ是阿里云创建服务器默认的hostname，错误其实没有什么影响，但看起来很不爽，解决方式：

    $ vim /etc/hostname
    iZj6cfyvsfiajdiy47qddhZ
    $ vim /etc/hosts
    127.0.0.1       localhost iZj6cfyvsfiajdiy47qddhZ

结尾处增加hostname.搞定.


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

[主要参考教程](https://linghucong.js.org/2016/08/18/ubuntu_1604_web_server_config_LEMP/)
