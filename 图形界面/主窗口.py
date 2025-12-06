"""
主窗口 - 重构版
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QTabWidget,
    QMessageBox, QInputDialog, QLineEdit
)
from PySide6.QtGui import QFont, QAction
from PySide6.QtCore import QTimer
from 核心 import 包管理器, 进程管理器
from 核心.密码管理 import 密码管理
from 核心.软件清理 import 软件清理
from 配置 import 配置
from .标签页 import 软件标签页
from .进程标签页 import 进程标签页
from .垃圾清理标签页 import 垃圾清理标签页
from .工作线程 import 工作线程, 任务类型


class 线程管理器:
    """管理所有后台线程的生命周期"""

    def __init__(self):
        self.活动线程 = []

    def 添加(self, 线程: 工作线程):
        """添加线程到管理列表"""
        self.清理已完成()
        self.活动线程.append(线程)
        线程.finished.connect(lambda: self._标记完成(线程))

    def _标记完成(self, 线程: 工作线程):
        """标记线程已完成"""
        pass  # 线程会在清理时被移除

    def 清理已完成(self):
        """清理已完成的线程"""
        self.活动线程 = [t for t in self.活动线程 if t.isRunning()]

    def 停止所有(self):
        """停止所有运行中的线程"""
        for 线程 in self.活动线程:
            if 线程.isRunning():
                线程.停止()
        self.活动线程.clear()


class 主窗口(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        # 核心管理器
        self.包管理器 = 包管理器()
        self.进程管理器 = 进程管理器()

        # 线程管理
        self.线程管理器 = 线程管理器()

        # 首次显示标志
        self._已首次显示 = False

        self.初始化界面()
        self.恢复窗口状态()
    
    def 初始化界面(self):
        """初始化UI"""
        self.setWindowTitle("Linux 软件管理工具")
        
        # 创建菜单栏
        self.创建菜单栏()
        
        # 主窗口
        中央窗口 = QWidget()
        self.setCentralWidget(中央窗口)
        主布局 = QVBoxLayout(中央窗口)
        
        # 标题
        标题 = QLabel("Linux 软件管理工具")
        标题字体 = QFont()
        标题字体.setPointSize(14)
        标题字体.setBold(True)
        标题.setFont(标题字体)
        主布局.addWidget(标题)
        
        # 显示当前包管理器
        管理器标签 = QLabel(f"检测到的包管理器: {self.包管理器.管理器类型 or '未检测到'}")
        主布局.addWidget(管理器标签)
        
        # 标签页
        self.标签页 = QTabWidget()
        主布局.addWidget(self.标签页)

        # 软件管理标签页（合并搜索和已安装）
        self.软件标签页 = 软件标签页()
        self.软件标签页.包管理器 = self.包管理器  # 设置包管理器引用
        self.软件标签页.搜索请求.connect(self.搜索软件)
        self.软件标签页.刷新请求.connect(self.刷新已安装)
        self.软件标签页.安装请求.connect(self.安装软件)
        self.软件标签页.卸载请求.connect(self.卸载软件)
        self.标签页.addTab(self.软件标签页, "📦 软件管理")

        # 进程管理标签页
        self.进程标签页 = 进程标签页()
        self.进程标签页.刷新请求.connect(self.刷新进程列表)
        self.进程标签页.搜索请求.connect(self.搜索进程)
        self.进程标签页.终止请求.connect(self.终止进程)
        self.进程标签页.优先级请求.connect(self.调整进程优先级)
        self.进程标签页.系统资源请求.connect(self.获取系统资源)
        self.标签页.addTab(self.进程标签页, "⚙️ 进程管理")

        # 垃圾清理标签页
        self.垃圾清理标签页 = 垃圾清理标签页()
        self.标签页.addTab(self.垃圾清理标签页, "🧹 垃圾清理")
    
    def showEvent(self, 事件):
        """窗口显示事件"""
        super().showEvent(事件)
        if not self._已首次显示:
            self._已首次显示 = True
            # 延迟加载，避免阻塞UI
            QTimer.singleShot(100, self.刷新已安装)

    def _构建文件列表(self, 相关文件: dict) -> str:
        """构建文件列表显示文本"""
        文本 = ""
        if 相关文件['配置文件']:
            文本 += f"  📁 配置文件: {len(相关文件['配置文件'])} 个\n"
        if 相关文件['缓存文件']:
            文本 += f"  📁 缓存文件: {len(相关文件['缓存文件'])} 个\n"
        if 相关文件['桌面图标']:
            文本 += f"  📁 桌面图标: {len(相关文件['桌面图标'])} 个\n"
        if 相关文件['其他文件']:
            文本 += f"  📁 其他文件: {len(相关文件['其他文件'])} 个\n"

        总数 = sum(len(v) for v in 相关文件.values())
        if 总数 == 0:
            文本 = "  (没有找到相关文件)"
        else:
            文本 += f"\n  总计: {总数} 个文件"
        return 文本

    def 创建菜单栏(self):
        """创建菜单栏"""
        菜单栏 = self.menuBar()
        
        # 文件菜单
        文件菜单 = 菜单栏.addMenu("文件(&F)")
        退出动作 = QAction("退出(&Q)", self)
        退出动作.triggered.connect(self.close)
        文件菜单.addAction(退出动作)
        
        # 帮助菜单
        帮助菜单 = 菜单栏.addMenu("帮助(&H)")
        关于动作 = QAction("关于(&A)", self)
        关于动作.triggered.connect(self.显示关于)
        帮助菜单.addAction(关于动作)
    
    def _执行任务(self, 任务: 任务类型, 管理器, 成功回调=None, **参数):
        """统一的任务执行方法"""
        self.软件标签页.显示进度条()

        线程 = 工作线程(任务, 管理器, **参数)
        self.线程管理器.添加(线程)

        线程.结果.connect(lambda 结果: self._处理结果(结果, 成功回调))
        线程.错误.connect(lambda e: self._处理错误(e))
        线程.完成.connect(self.软件标签页.隐藏进度条)

        if 任务 in [任务类型.卸载软件, 任务类型.终止进程, 任务类型.调整优先级]:
            线程.需要密码.connect(lambda: self._处理需要密码(任务, 参数))

        线程.start()
        return 线程

    def _处理结果(self, 结果, 回调=None):
        """处理任务结果"""
        if 回调:
            回调(结果)

    def _处理错误(self, 错误信息: str):
        """处理任务错误"""
        self.软件标签页.隐藏进度条()
        self.进程标签页.隐藏进度条()
        QMessageBox.critical(self, "错误", 错误信息)

    def _处理需要密码(self, 任务: 任务类型, 原参数: dict):
        """统一的密码处理"""
        self.软件标签页.隐藏进度条()
        self.进程标签页.隐藏进度条()

        密码, 确认 = QInputDialog.getText(
            self, "需要密码", "请输入 sudo 密码:",
            QLineEdit.EchoMode.Password
        )

        if 确认 and 密码:
            原参数['密码'] = 密码
            管理器 = self.包管理器 if 任务 in [任务类型.卸载软件] else self.进程管理器
            self._执行任务(任务, 管理器, **原参数)

    def 搜索软件(self, 关键词):
        """搜索软件"""
        self._执行任务(
            任务类型.搜索软件,
            self.包管理器,
            self.软件标签页.显示结果,
            关键词=关键词
        )

    def 刷新已安装(self):
        """刷新已安装软件"""
        self._执行任务(
            任务类型.获取已安装,
            self.包管理器,
            self.软件标签页.显示已安装
        )

    def 安装软件(self, 软件包名):
        """安装软件"""
        回复 = QMessageBox.question(
            self, "确认", f"确定要安装 {软件包名} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if 回复 == QMessageBox.StandardButton.Yes:
            def 成功回调(结果):
                if 结果.get('成功'):
                    QMessageBox.information(self, "成功", f"{软件包名} 安装成功")

            self._执行任务(
                任务类型.安装软件,
                self.包管理器,
                成功回调,
                软件包名=软件包名
            )
    
    def 卸载软件(self, 软件包名):
        """卸载软件"""
        信息 = self.包管理器.获取软件包信息(软件包名)
        中文名 = 信息.get('中文名', 软件包名)

        if not 信息.get('可删除', True):
            QMessageBox.warning(
                self, "⚠️ 无法删除",
                f"❌ {中文名} ({软件包名}) 是系统关键软件包，不能删除！\n\n"
                f"重要性: {信息.get('重要性', '未知')}\n"
                f"说明: {信息.get('说明', '系统核心，绝对不能删除')}"
            )
            return

        相关文件 = 软件清理.搜索相关文件(软件包名)
        文件列表文本 = self._构建文件列表(相关文件)

        回复 = QMessageBox.question(
            self, "⚠️ 确认卸载",
            f"确定要卸载 {中文名} ({软件包名}) 吗？\n\n"
            f"用途: {信息.get('用途', '未知')}\n"
            f"可删除: {'✓ 是' if 信息.get('可删除', True) else '✗ 否'}\n\n"
            f"将清理以下相关文件:\n{文件列表文本}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if 回复 == QMessageBox.StandardButton.Yes:
            密码 = 密码管理.读取密码()
            if not 密码:
                密码, 确认 = QInputDialog.getText(
                    self, "需要密码",
                    "请输入 sudo 密码（将被加密保存以便后续使用）:",
                    QLineEdit.EchoMode.Password
                )
                if not 确认 or not 密码:
                    return

            def 成功回调(结果):
                if 结果.get('成功'):
                    消息 = 结果.get('消息', f"✓ {软件包名} 卸载成功")
                    QMessageBox.information(self, "✓ 卸载成功", 消息)
                    self.刷新已安装()

            self._执行任务(
                任务类型.卸载软件,
                self.包管理器,
                成功回调,
                软件包名=软件包名,
                密码=密码
            )
    
    def 刷新进程列表(self, 排序字段, 倒序):
        """刷新进程列表"""
        线程 = 工作线程(
            任务类型.获取进程,
            self.进程管理器,
            排序字段=排序字段,
            倒序=倒序
        )
        self.线程管理器.添加(线程)
        线程.结果.connect(self.进程标签页.显示进程列表)
        线程.错误.connect(self._处理错误)
        线程.完成.connect(self.进程标签页.隐藏进度条)
        线程.start()

    def 搜索进程(self, 关键词):
        """搜索进程"""
        self.进程标签页.显示进度条()
        线程 = 工作线程(
            任务类型.搜索进程,
            self.进程管理器,
            关键词=关键词
        )
        self.线程管理器.添加(线程)
        线程.结果.connect(self.进程标签页.显示进程列表)
        线程.错误.connect(self._处理错误)
        线程.完成.connect(self.进程标签页.隐藏进度条)
        线程.start()

    def 获取系统资源(self):
        """获取系统资源"""
        线程 = 工作线程(任务类型.获取系统资源, self.进程管理器)
        self.线程管理器.添加(线程)
        线程.结果.connect(self.进程标签页.更新系统资源)
        线程.start()

    def 终止进程(self, pid, 强制, 密码):
        """终止进程"""
        self.进程标签页.显示进度条()

        def 成功回调(结果):
            if 结果.get('成功'):
                QMessageBox.information(self, "成功", 结果.get('消息', '操作成功'))
                self.进程标签页.手动刷新()
            else:
                QMessageBox.warning(self, "失败", 结果.get('消息', '操作失败'))

        self._执行任务(
            任务类型.终止进程,
            self.进程管理器,
            成功回调,
            pid=pid,
            强制=强制,
            密码=密码
        )

    def 调整进程优先级(self, pid, 优先级, 密码):
        """调整进程优先级"""
        self.进程标签页.显示进度条()

        def 成功回调(结果):
            if 结果.get('成功'):
                QMessageBox.information(self, "成功", 结果.get('消息', '操作成功'))
                self.进程标签页.手动刷新()
            else:
                QMessageBox.warning(self, "失败", 结果.get('消息', '操作失败'))

        self._执行任务(
            任务类型.调整优先级,
            self.进程管理器,
            成功回调,
            pid=pid,
            优先级=优先级,
            密码=密码
        )

    def 显示关于(self):
        """显示关于对话框"""
        QMessageBox.information(
            self,
            "关于",
            "Linux 系统管理工具 v2.0\n\n"
            "一个基于 PySide6 的图形化 Linux 系统管理工具\n\n"
            "功能:\n"
            "• 软件包管理 (apt, yum, dnf, pacman, zypper)\n"
            "• 进程管理 (查看、终止、调整优先级)\n"
            "• 系统资源监控 (CPU、内存、负载)"
        )
    
    def 恢复窗口状态(self):
        """恢复窗口状态"""
        宽度 = 配置.获取('窗口宽度', 1000)
        高度 = 配置.获取('窗口高度', 600)
        self.setGeometry(100, 100, 宽度, 高度)
    
    def closeEvent(self, 事件):
        """关闭事件 - 清理所有资源"""
        # 停止所有线程
        self.线程管理器.停止所有()

        # 停止进程标签页的定时器
        if hasattr(self, '进程标签页'):
            self.进程标签页.停止定时器()

        # 保存窗口状态
        配置.设置('窗口宽度', self.width())
        配置.设置('窗口高度', self.height())

        事件.accept()

