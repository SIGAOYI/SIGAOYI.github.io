---
layout:     post
title:      "Mac-Mysql8.0-Yii2的一点小坑"
subtitle:   "..."
date:       2018-09-17
author:     "龟龟"
header-img: "http://image.lawootrip.com/2017-05-15-bg.png"
tags:
    - Mysql
    - Yii2
    - Mac
    - 环境配置
---

>Vue.js 放弃中...

在Mac Sierra 10.13.6部署Yii2+Mysql8.0+Nginx，遇到几个小坑，备忘如下：

### 1. Mysql报错：`The server quit without updating PID file`

一把梭：完全卸载Mysql，并用brew install mysql重新安装;

## 卸载

依次执行：

        brew uninstall mysql 

        sudo rm /usr/local/var/mysql 

        sudo rm -rf /usr/local/mysql* 

        sudo rm -rf /Library/LaunchDaemons/com.oracle 

        brew cleanup 

===我只用了上面这五行==== 

        sudo rm -rf /Library/StartupItems/MySQLCOM 

        sudo rm -rf /Library/PreferencePanes/My* 

        rm -rf ~/Library/PreferencePanes/My* 

        sudo rm -rf /Library/Receipts/mysql* 

        sudo rm -rf /Library/LaunchDaemons/com.oracle 

        sudo rm -rf /var/db/receipts/com.mysql.* 

其实不同的安装方式有些东西的存储位置不一样，删除完检查一下下面这些文件是否删除了，没有的话则删除掉：


`/usr/local/Cellar` 里的mysql文件 

`/usr/local/var` 里的mysql文件 

`/tmp` 里的mysql.sock, mysql.sock.lock, my.cnf文件 

pid文件和err文件都在`/usr/local/var/mysql`里确保删除了 

brew安装的安装包存储在`/usr/local/Library/Cache/Homebrew`也可以一并删除 

执行

        brew cleanup

## 安装

        brew install mysql

执行

        mysql.server start

如果报错，99%的可能是老版本的mysql没有卸载干净，重新检查卸载流程；

接下来执行配置脚本

        /usr/local/opt/mysql/bin/mysql_secure_installation //mysql 提供的配置向导

安装成功


### 2. Yii2报错：`SQLSTATE[HY000] [2054] The server requested authentication method unknown to the client`

发生这种错误，是由于MySQL 8默认使用了新的密码验证插件：caching_sha2_password，而之前的PHP版本中所带的mysqlnd无法支持这种验证。解决这个问题，有两种办法。

一种办法是升级PHP支持MySQL 8的新验证插件。

PHP 7.2.8和PHP 7.1.20已经可以支持caching_sha2_password，直接连接MySQL 8。

目前PHP 7.0.31和PHP 5.6.37还无法支持caching_sha2_password，不知道后续版本是否会做出支持。

可以通过phpinfo()函数了解当前安装的PHP是否支持caching_sha2_password：



如果不能升级PHP，可以在MySQL 8中创建（或修改）使用caching_sha2_password插件的账户，使之使用mysql_native_password，这样先前版本的PHP就可以连接使用了。

1. 在CREATE USER时，使用IDENTIFIED WITH xxx_plugin BY 'password'，比如：

        CREATE USER 'native'@'localhost' IDENTIFIED WITH mysql_native_password BY 'password!2#4';

2. 使用ALTER USER修改已有账户的验证插件：

        ALTER USER 'native'@'localhost' IDENTIFIED WITH mysql_native_password

或

        ALTER USER 'native'@'localhost' IDENTIFIED WITH mysql_native_password BY '123123';

采用前一种方式，账户的密码将被清除；`123123`将为账户设置的新密码。

/etc/my.cnf配置文件中，有一行：

`# default-authentication-plugin=mysql_native_password`

请删除注释符号“#”并重新启动mysqld使之生效，此后创建的账户均默认使用mysql_native_password。

如果完成MySQL Server的安装之后，在没有启动过mysqld服务的情况下修改/etc/my.cnf配置，那么启动mysqld之后创建的'root'@'localhost'账户也是使用mysql_native_password插件的。

### 3. Yii2报错`SQLSTATE[42000]: Syntax error or access violation: 1055 Expression`

![](https://cloud.githubusercontent.com/assets/1667825/15820229/6b9a7286-2be8-11e6-90a7-bf31332dddcf.png)<small class="img-hint">分组问题报错</small>

这个就非常简单了

在Mysql的配置文件my.cnf设置中，添加：

        sql_mode=TRADITIONAL


[参考资料](http://dev.mysql.com/doc/refman/5.7/en/sql-mode.html)


----
<br />
<table border="0">
    <tr border="0">
        <td>
            <img src="http://image.lawootrip.com/0%20%2837%29.gif">
        </td>
        <td>
            <img src="http://image.lawootrip.com/1490924677.png">
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
