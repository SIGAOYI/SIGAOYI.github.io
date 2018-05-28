---
layout:     post
title:      "Ubuntu 常用命令整理"
subtitle:   "Be lord of your Ubuntu"
date:       2018-02-06
author:     "龟龟"
header-img: "http://image.lawootrip.com/pexels-photo-175411.jpeg"
tags:
    - 笔记
    - Linux
    - Ubuntu
---

>Vue.js 放弃中...



## **目录:**

## [一、用户操作](#0)

## [二、文件操作](#1)

## [三、系统操作](#2)


<p id="0"></p>

## 一、用户操作

在root用户下，

1. 使用`who`查看目前有哪些用户登录了服务器；
2. 使用`pkill -kill -t pts/1`（数字1就是用户的[TTY](https://en.wikipedia.org/wiki/Tty_(unix))）强制退出对应用户的登陆；
3. 增加用户：`useradd test`；为新增用户添加密码：`passwd test`;
4. 删除用户：`userdel test`;
5. 用户登陆记录：`last`;
6. 用户登陆失败记录：`lastb`;
7. 查看系统下所有用户：`cat /etc/passwd |awk -F \: '{print $1}'`;


<p id="1"></p>

## 二、文件操作

文件操作命令：

1、ls

     格式：ls 目录

     ls命令用于显示文件下有哪些文件。a

2、touch

     格式：touch test1 test2 test3

     touch命令用于创建文件，可以同一时间创建多个文件。

3、rm

     格式：rm 文件    

     rm命令用于删除文件，当文件不能够被删除时可以加上 -f 选项，强制将文件删除。

4、cat

     格式：cat /proc/cpuinfo

     cat命令用于查看文件内的信息。如果只想查看某一项内容时，要加上grep选项。

     例如：cat /proc/meminfo |grep MemTotal

5、less

     格式：less /proc/meminfo

     less命令也是用来查看文件的内容的命令，但是他显示时是一屏一屏的显示地。

          a、按下空格键后进入到下一屏。

          b、还可以通过上下键来上下移动行。

          c、按下 q 键后退出查看。

6、more

     格式：more /proc/meminfo

     more命令与less命令一样用于查看文件内的内容，同样是分屏显示的。

          a、按下空格键后进入到下一屏

          b、按下 q 键后退出查看

7、cp

     格式：cp /etc/apt/sources.list /etc/aptsources.listbacker

     cp是copy的缩写用于复制文件。

8、mv

     格式：mv /home/user1/桌面/ruijie/xrgsu /usr/share/local/bin/xrgsu

     mv命令是用于移动文件的。

9、find

     格式：sudo find / -name ls

     find命令是用于查找文件：

          a、／ 表示的是查找的起始目录，

          b、-name 有了这个选项，在显示只有找到的结果才会显示出来。

          c、ls 为你要找的目录文件。



mkdir 文件夹 --/创建一个文件夹

rmdir 空文件夹名 --/删除一个空文件夹

rm 文件名 文件名 --/删除一个文件或多个文件

rm -rf 非空文件夹名 --/删除一个非空文件夹下的一切

——————

通过ssh终端从本地拷贝文件到服务器：

使用方式如下：

1、上传本地文件到服务器

    scp /path/filename username@servername:/path/

例如scp /var/www/test.php root@192.168.0.101:/var/www/ 把本机/var/www/目录下的test.php文件上传到192.168.0.101这台服务器上的/var/www/目录中

2、从服务器上下载文件

下载文件我们经常使用wget，但是如果没有http服务，如何从服务器上下载文件呢?

    scp username@servername:/path/filename /var/www/local_dir(本地目录)

例如scp root@192.168.0.101:/var/www/test.txt 把192.168.0.101上的/var/www/test.txt 的文件下载到/var/www/local_dir(本地目录)

3、从服务器下载整个目录

    scp -r username@servername:/var/www/remote_dir/(远程目录) /var/www/local_dir(本地目录)

例如:scp -r root@192.168.0.101:/var/www/test /var/www/

4、上传目录到服务器

    scp -r local_dir username@servername:remote_dir

例如：scp -r test root@192.168.0.101:/var/www/ 把当前目录下的test目录上传到服务器的/var/www/ 目录

<p id="2"></p>

## 三、系统操作

太多了，每次还是查[官方wiki](https://wiki.ubuntu.com.cn/%E5%91%BD%E4%BB%A4%E8%A1%8C%E6%8C%87%E5%8D%97#.E5.B8.B8.E7.94.A8.E6.8C.87.E4.BB.A4)快一点

Unix/Linux下一般比如想让某个程序在后台运行，很多都是使用& 在程序结尾来让程序自动运行。比如我们要运行mysql在后台：

    /usr/local/mysql/bin/mysqld_safe --user=mysql &

但是加入我们很多程序并不象mysqld一样做成守护进程，可能我们的程序只是普通程序而已，一般这种程序使用& 结尾，但是如果终端关闭，那么程序也会被关闭。但是为了能够后台运行，那么我们就可以使用nohup这个命令，比如我们有个test.php需要在后台运行，并且希望在后台能够定期运行，那么就使用nohup：

    nohup /root/test.php &
　　
提示：

    　[~]$ appending output to nohup.out

　　嗯，证明运行成功，同时把程序运行的输出信息放到当前目录的nohup.out 文件中去。

        tcpdump -i any -nn 'port 8338' -vv -X //监听端口数据

        lsof -i:端口号 //查看特定端口占用情况

        lsof -i //查看所有端口占用情况

## 四、MAC常用命令备份(plus)

结束php-fpm进程:

        sudo kill -INT `cat /usr/local/var/run/php-fpm.pid`

开始php-fpm进程：

        sudo php-fpm

设置本地80端口虚拟域名

        sudo vim /private/etc/hosts


git记住所有的https账号密码，长期

        git config --global credential.helper store

git记住所有的https账号密码，临时

        git config credential.helper 'cache --timeout=3600'

在dock创建一个透明icon，分割dock

        defaults write com.apple.dock persistent-apps -array-add '{ "tile-type" = "spacer-tile"; }' killall Dock


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
