"""
数据模型定义
"""

from dataclasses import dataclass


@dataclass
class 软件包:
    """软件包数据模型"""
    名称: str
    版本: str
    状态: str  # installed, available, upgradable
    中文名: str = ""
    用途: str = ""
    可删除: str = "未知"
    重要性: str = "未知"
    描述: str = ""

    def __repr__(self):
        return f"软件包(名称={self.名称}, 版本={self.版本}, 状态={self.状态})"


@dataclass
class 进程:
    """进程数据模型"""
    pid: int
    名称: str
    用户: str
    cpu使用率: float
    内存使用率: float
    内存使用量: str  # 如 "123.4 MB"
    状态: str  # running, sleeping, stopped, zombie
    优先级: int  # nice值
    命令行: str = ""
    启动时间: str = ""

    def __repr__(self):
        return f"进程(PID={self.pid}, 名称={self.名称}, CPU={self.cpu使用率}%, 内存={self.内存使用率}%)"

