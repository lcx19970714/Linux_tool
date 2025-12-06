# Linux 软件管理工具

一个基于 PySide6 的图形化 Linux 系统管理工具，支持多种包管理器。

## 功能特性

- **软件包管理** - 支持 apt、yum、dnf、pacman、zypper 等主流包管理器
- **进程管理** - 查看和管理系统进程
- **垃圾清理** - 清理系统垃圾文件
- **软件清理** - 清理不需要的软件包

## 系统要求

- Python 3.10+
- Linux 操作系统
- 支持的包管理器之一（apt/yum/dnf/pacman/zypper）

## 安装

```bash
# 安装依赖
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 项目结构

```
Linux工具/
├── main.py           # 程序入口
├── requirements.txt  # 依赖列表
├── 核心/             # 核心功能模块
│   ├── 包管理器.py   # 包管理器核心逻辑
│   ├── 进程管理.py   # 进程管理功能
│   ├── 垃圾清理.py   # 垃圾清理功能
│   ├── 软件清理.py   # 软件清理功能
│   ├── 密码管理.py   # 密码管理（sudo权限）
│   └── 数据模型.py   # 数据模型定义
├── 图形界面/         # GUI模块
│   ├── 主窗口.py     # 主窗口
│   ├── 标签页.py     # 软件管理标签页
│   ├── 进程标签页.py # 进程管理标签页
│   ├── 垃圾清理标签页.py # 垃圾清理标签页
│   └── 工作线程.py   # 后台工作线程
└── 配置/             # 配置模块
    └── 设置.py       # 应用设置
```

## 依赖

- PySide6 - Qt6 Python 绑定
- psutil - 系统进程信息库

## 许可证

MIT License
