---
layout:     post
title:      "Adobe和windows虚拟机是Mac启动速度的天敌"
subtitle:   "Adobe startup piss off please..."
date:       2018-09-30
author:     "龟龟"
header-img: "http://cdn.oneonebao.com/2017-05-15-bg.png"
tags:
    - mac优化
    - 启动项优化
---

>Vue.js 放弃中...

最近还在纠结升不升Mojave，毕竟多了一些有的没的新功能，手痒；

另一方面，又担心苹果新系统必bug定律在我身上应验；

但更重要的是，本身现在登陆就会卡三秒，新系统是否会变本加厉?

直到国庆前闲的没事干的今天，突然醒悟过来，开机后登陆用户卡三秒，是否是因为……

开机自动启动项，太多？！



![系统启动项管理](http://cdn.oneonebao.com/Xnip2018-09-30_11-58-25.png)

这是什么情况，就一个启动项啊！！简直见鬼了。

但，稍微研究一下就发现，mac系统有2个地方储存开启项文件，后缀都是`.plist`。

`/Library/Preferences`

`/Library/LaunchAgents`

`/System/Library/LaunchAgents`

用来储存当前用户的启动项，只和用户有关，不在系统的启动项内。

cd过去一看，惊呆了

![](http://cdn.oneonebao.com/Xnip2018-09-30_12-05-49.png)
<small class="img-hint">这仅仅是`/Library/Preferences`一个路径下的垃圾文件</small>


Adobe全家桶赤果果的自动启动了，他们是八百年一用的PR&AE，八千年一用的PS&AI……

果断删除

# 还有

`/Library/LaunchDaemons`

`/System/Library/LaunchDaemons`

![](http://cdn.oneonebao.com/Xnip2018-09-30_12-06-15.png)
<small class="img-hint">`/Library/LaunchDaemons`一个路径下的垃圾文件</small>

这是系统守护进程，换句话说就是随系统启动，不是用户登陆时启动的。

一样删除

真的是motherfuck了，95%的冗余启动项是adobe全家桶还有windows虚拟机未经告知的强奸。

再次重启系统，开机秒，登陆1秒。

完美。

[参考资料](https://blog.csdn.net/astarring/article/details/69055218)




----
<br />
<table border="0">
    <tr border="0">
        <td>
            <img src="http://cdn.oneonebao.com/0%20%2837%29.gif">
        </td>
        <td>
            <img src="http://cdn.oneonebao.com/1490924677.png">
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
