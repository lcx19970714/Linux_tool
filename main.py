#!/usr/bin/env python3
"""
Linux 软件管理工具
一个基于PySide6的图形化Linux包管理工具
支持 apt, yum, dnf, pacman, zypper 等包管理器
"""

import sys
from PySide6.QtWidgets import QApplication  # pylint: disable=no-name-in-module
from 图形界面 import 主窗口  # pylint: disable=non-ascii-module-import


def 主程序():  # pylint: disable=non-ascii-name
    """主程序入口"""
    应用 = QApplication(sys.argv)  # pylint: disable=non-ascii-name
    窗口 = 主窗口()  # pylint: disable=non-ascii-name
    窗口.show()
    sys.exit(应用.exec())


if __name__ == '__main__':
    主程序()
