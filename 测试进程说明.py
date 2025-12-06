#!/usr/bin/env python3
"""
测试进程说明功能
"""

from 核心.进程说明 import 获取进程说明


def 测试进程说明():
    """测试进程说明功能"""
    print("=" * 60)
    print("测试进程说明功能")
    print("=" * 60)
    
    测试进程 = [
        'systemd',
        'gnome-shell',
        'firefox',
        'python3',
        'kworker/0:0',
        'NetworkManager',
        'pulseaudio',
        'dockerd',
        'chrome',
        'code',
        'gsd-power',
        'unknown-process',
    ]
    
    for 进程名 in 测试进程:
        说明 = 获取进程说明(进程名)
        状态 = "✓" if 说明 else "✗"
        print(f"{状态} {进程名:20s} -> {说明 or '(未知)'}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == '__main__':
    测试进程说明()

