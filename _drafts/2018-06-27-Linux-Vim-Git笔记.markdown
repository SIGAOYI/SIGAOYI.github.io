---
layout:     post
title:      "Ubuntu Vim Git日常问题汇总"
subtitle:   "Be lord of your Ubuntu"
date:       2018-06-27
author:     "龟龟"
header-img: "http://image.lawootrip.com/pexels-photo-175411.jpeg"
tags:
    - 笔记
    - Linux
    - Ubuntu
    - Git
    - Vim
---

>Vue.js 放弃中...



## **目录:**

## [一、Vim](#0)

## [二、Ubuntu](#1)

## [三、Git](#2)


<p id="0"></p>

## 一、Vim

配置文件的路径：`etc/vim/vimrc`

#### 基本配置

"开启语法高亮

syntax on

"依文件类型设置自动缩进

filetype indent plugin on

 
"显示当前的行号列号：

set ruler

"在状态栏显示正在输入的命令

set showcmd

 
"关闭/打开配对括号高亮

"NoMatchParen

DoMatchParen

行号的显示与隐藏[3]：

"显示行号：

set number

"为方便复制，用<F2>开启/关闭行号显示:

nnoremap <F2> :set nonumber!<CR>:set foldcolumn=0<CR>

启用Modeline（即允许被编辑的文件以注释的形式设置Vim选项，详见Vim Wiki: Modeline magic）[4]：

set modeline

如果终端使用的是深色背景：


"为深色背景调整配色

set background=dark



<p id="1"></p>

## 二、Ubuntu



<p id="2"></p>

## 三、Git

参考1：[如何克服解决Git冲突的恐惧症？（Git分支策略）](https://mp.weixin.qq.com/s/CeGtTDxpFxRBQ0zJrqxSQg)


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
