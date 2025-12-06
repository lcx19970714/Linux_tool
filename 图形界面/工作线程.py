"""
后台工作线程 - 重构版
"""

from enum import Enum, auto
from typing import Any
from PySide6.QtCore import QThread, Signal


class 任务类型(Enum):
    """任务类型枚举"""
    搜索软件 = auto()
    获取已安装 = auto()
    安装软件 = auto()
    卸载软件 = auto()
    获取进程 = auto()
    搜索进程 = auto()
    获取系统资源 = auto()
    终止进程 = auto()
    调整优先级 = auto()


class 工作线程(QThread):
    """统一的后台工作线程"""

    完成 = Signal()
    错误 = Signal(str)
    结果 = Signal(object)
    需要密码 = Signal()

    def __init__(self, 任务: 任务类型, 管理器: Any, **参数):
        super().__init__()
        self.任务 = 任务
        self.管理器 = 管理器
        self.参数 = 参数
        self._停止标志 = False

    def 停止(self):
        """请求停止线程"""
        self._停止标志 = True
        self.wait(3000)  # 等待最多3秒
        if self.isRunning():
            self.terminate()

    def run(self):
        """执行后台任务"""
        try:
            if self._停止标志:
                return

            结果 = None

            # 软件包任务
            if self.任务 == 任务类型.搜索软件:
                结果 = self.管理器.搜索(self.参数['关键词'])

            elif self.任务 == 任务类型.获取已安装:
                结果 = self.管理器.获取已安装()

            elif self.任务 == 任务类型.安装软件:
                成功 = self.管理器.安装(self.参数['软件包名'])
                结果 = {'成功': 成功}

            elif self.任务 == 任务类型.卸载软件:
                结果 = self.管理器.卸载(
                    self.参数['软件包名'],
                    self.参数.get('密码')
                )
                if 结果.get('需要密码'):
                    self.需要密码.emit()
                    return

            # 进程任务
            elif self.任务 == 任务类型.获取进程:
                结果 = self.管理器.获取所有进程(
                    self.参数.get('排序字段', 'cpu使用率'),
                    self.参数.get('倒序', True)
                )

            elif self.任务 == 任务类型.搜索进程:
                结果 = self.管理器.搜索进程(self.参数['关键词'])

            elif self.任务 == 任务类型.获取系统资源:
                结果 = self.管理器.获取系统资源()

            elif self.任务 == 任务类型.终止进程:
                结果 = self.管理器.终止进程(
                    self.参数['pid'],
                    self.参数.get('强制', False),
                    self.参数.get('密码')
                )
                if 结果.get('需要密码'):
                    self.需要密码.emit()
                    return

            elif self.任务 == 任务类型.调整优先级:
                结果 = self.管理器.调整优先级(
                    self.参数['pid'],
                    self.参数['优先级'],
                    self.参数.get('密码')
                )
                if 结果.get('需要密码'):
                    self.需要密码.emit()
                    return

            if not self._停止标志:
                self.结果.emit(结果)

        except Exception as e:
            if not self._停止标志:
                self.错误.emit(str(e))

        finally:
            if not self._停止标志:
                self.完成.emit()

