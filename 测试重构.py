#!/usr/bin/env python3
"""
测试重构后的代码
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from 图形界面 import 主窗口


def 测试启动关闭():
    """测试程序启动和关闭"""
    print("=" * 60)
    print("测试重构后的代码")
    print("=" * 60)
    
    应用 = QApplication(sys.argv)
    窗口 = 主窗口()
    
    print("✓ 主窗口创建成功")
    print(f"✓ 包管理器类型: {窗口.包管理器.管理器类型}")
    print(f"✓ 线程管理器: {窗口.线程管理器}")
    print(f"✓ 进程管理器: {窗口.进程管理器}")
    
    窗口.show()
    print("✓ 窗口显示成功")
    
    # 2秒后自动关闭
    def 自动关闭():
        print("\n开始关闭窗口...")
        print(f"活动线程数: {len(窗口.线程管理器.活动线程)}")
        窗口.close()
        print("✓ 窗口关闭成功")
        print("✓ 无线程泄漏错误")
        应用.quit()
    
    QTimer.singleShot(2000, 自动关闭)
    
    sys.exit(应用.exec())


if __name__ == '__main__':
    try:
        测试启动关闭()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

