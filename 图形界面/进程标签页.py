"""
进程管理标签页组件
"""

from functools import partial
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QLabel,
    QComboBox, QMessageBox, QInputDialog, QGroupBox, QGridLayout
)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QColor
from 核心.进程说明 import 获取进程说明


class 进程标签页(QWidget):
    """进程管理标签页"""

    刷新请求 = Signal(str, bool)  # 排序字段, 倒序
    搜索请求 = Signal(str)
    终止请求 = Signal(int, bool, str)  # PID, 强制, 密码
    优先级请求 = Signal(int, int, str)  # PID, 优先级, 密码
    系统资源请求 = Signal()

    def __init__(self):
        super().__init__()
        self.所有进程 = []
        self.当前排序字段 = 'cpu使用率'
        self.当前倒序 = True
        self.自动刷新定时器 = None
        self.初始化界面()
        self.启动自动刷新()

    def 初始化界面(self):
        """初始化UI"""
        布局 = QVBoxLayout(self)

        # 系统资源监控区域
        self.创建系统资源区域(布局)

        # 控制栏
        控制布局 = QHBoxLayout()

        # 搜索框
        控制布局.addWidget(QLabel("搜索:"))
        self.搜索框 = QLineEdit()
        self.搜索框.setPlaceholderText("输入进程名、PID、用户名或命令...")
        self.搜索框.setMaximumWidth(300)
        self.搜索框.textChanged.connect(self.本地搜索)
        控制布局.addWidget(self.搜索框)

        # 排序选择
        控制布局.addWidget(QLabel("排序:"))
        self.排序选择 = QComboBox()
        self.排序选择.addItems(["CPU使用率", "内存使用率", "PID", "进程名", "用户"])
        self.排序选择.currentTextChanged.connect(self.排序改变)
        控制布局.addWidget(self.排序选择)

        # 刷新按钮
        刷新按钮 = QPushButton("🔄 刷新")
        刷新按钮.clicked.connect(self.手动刷新)
        控制布局.addWidget(刷新按钮)

        # 自动刷新开关
        self.自动刷新开关 = QComboBox()
        self.自动刷新开关.addItems(["自动刷新: 3秒", "自动刷新: 5秒", "自动刷新: 10秒", "关闭自动刷新"])
        self.自动刷新开关.currentTextChanged.connect(self.切换自动刷新)
        控制布局.addWidget(self.自动刷新开关)

        控制布局.addStretch()
        布局.addLayout(控制布局)

        # 进度条
        self.进度条 = QProgressBar()
        self.进度条.setVisible(False)
        self.进度条.setMaximum(0)  # 不确定进度
        布局.addWidget(self.进度条)

        # 进程表格
        self.表格 = QTableWidget()
        self.表格.setColumnCount(10)
        self.表格.setHorizontalHeaderLabels([
            "PID", "进程名", "用途说明", "用户", "CPU%", "内存%", "内存", "状态", "优先级", "操作"
        ])

        # 设置列宽度
        header = self.表格.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # PID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 进程名
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # 用途说明
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 用户
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # CPU
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # 内存%
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # 内存
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # 状态
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # 优先级
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)  # 操作
        self.表格.setColumnWidth(9, 200)

        # 设置表格属性
        self.表格.setAlternatingRowColors(True)
        self.表格.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.表格.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # 启用列标题点击排序
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self.列标题点击)

        布局.addWidget(self.表格)

    def 创建系统资源区域(self, 父布局):
        """创建系统资源监控区域"""
        资源组 = QGroupBox("系统资源监控")
        资源布局 = QGridLayout()

        # CPU
        资源布局.addWidget(QLabel("CPU:"), 0, 0)
        self.cpu标签 = QLabel("0.0%")
        self.cpu标签.setStyleSheet("font-weight: bold; font-size: 14px;")
        资源布局.addWidget(self.cpu标签, 0, 1)

        # 内存
        资源布局.addWidget(QLabel("内存:"), 0, 2)
        self.内存标签 = QLabel("0.0%")
        self.内存标签.setStyleSheet("font-weight: bold; font-size: 14px;")
        资源布局.addWidget(self.内存标签, 0, 3)

        # 负载
        资源布局.addWidget(QLabel("负载:"), 0, 4)
        self.负载标签 = QLabel("0.00")
        self.负载标签.setStyleSheet("font-weight: bold; font-size: 14px;")
        资源布局.addWidget(self.负载标签, 0, 5)

        资源组.setLayout(资源布局)
        父布局.addWidget(资源组)

    def 启动自动刷新(self):
        """启动自动刷新定时器"""
        if self.自动刷新定时器:
            self.自动刷新定时器.stop()

        self.自动刷新定时器 = QTimer()
        self.自动刷新定时器.timeout.connect(self.自动刷新)
        self.自动刷新定时器.start(3000)  # 默认3秒

    def 切换自动刷新(self, 选项):
        """切换自动刷新间隔"""
        if self.自动刷新定时器:
            self.自动刷新定时器.stop()

        if "3秒" in 选项:
            self.自动刷新定时器.start(3000)
        elif "5秒" in 选项:
            self.自动刷新定时器.start(5000)
        elif "10秒" in 选项:
            self.自动刷新定时器.start(10000)
        # 关闭则不启动

    def 自动刷新(self):
        """自动刷新进程列表"""
        self.刷新请求.emit(self.当前排序字段, self.当前倒序)
        self.系统资源请求.emit()

    def 手动刷新(self):
        """手动刷新"""
        self.显示进度条()
        self.刷新请求.emit(self.当前排序字段, self.当前倒序)
        self.系统资源请求.emit()

    def 排序改变(self, 排序文本):
        """排序改变"""
        排序映射 = {
            "CPU使用率": "cpu使用率",
            "内存使用率": "内存使用率",
            "PID": "pid",
            "进程名": "名称",
            "用户": "用户"
        }
        self.当前排序字段 = 排序映射.get(排序文本, "cpu使用率")
        self.手动刷新()

    def 列标题点击(self, 列索引):
        """列标题点击排序"""
        列映射 = {
            0: "pid",           # PID
            1: "名称",          # 进程名
            3: "用户",          # 用户
            4: "cpu使用率",     # CPU%
            5: "内存使用率",    # 内存%
            8: "优先级",        # 优先级
        }

        if 列索引 in 列映射:
            新排序字段 = 列映射[列索引]

            # 如果点击同一列，切换排序方向
            if 新排序字段 == self.当前排序字段:
                self.当前倒序 = not self.当前倒序
            else:
                self.当前排序字段 = 新排序字段
                # 数值类型默认降序，文本类型默认升序
                self.当前倒序 = 列索引 in [4, 5]  # CPU和内存默认降序

            # 本地排序（不重新请求数据）
            self._本地排序()

    def _本地排序(self):
        """本地排序当前显示的进程"""
        if not self.所有进程:
            return

        # 排序字段映射
        排序键函数 = {
            "pid": lambda p: p.pid,
            "名称": lambda p: p.名称.lower(),
            "用户": lambda p: p.用户.lower(),
            "cpu使用率": lambda p: p.cpu使用率,
            "内存使用率": lambda p: p.内存使用率,
            "优先级": lambda p: p.优先级,
        }

        键函数 = 排序键函数.get(self.当前排序字段, lambda p: p.cpu使用率)

        排序后 = sorted(self.所有进程, key=键函数, reverse=self.当前倒序)
        self.显示进程列表(排序后)

    def 本地搜索(self):
        """本地搜索过滤"""
        关键词 = self.搜索框.text().lower()

        if not 关键词:
            self.显示进程列表(self.所有进程)
            return

        过滤结果 = [
            proc for proc in self.所有进程
            if (关键词 in proc.名称.lower() or
                关键词 in proc.用户.lower() or
                关键词 in proc.命令行.lower() or
                关键词 == str(proc.pid))
        ]
        self.显示进程列表(过滤结果)

    def 显示进程列表(self, 进程列表):
        """显示进程列表"""
        self.所有进程 = 进程列表
        self.表格.setRowCount(len(进程列表))

        for 行号, 进程 in enumerate(进程列表):
            # PID
            pid项 = QTableWidgetItem(str(进程.pid))
            pid项.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.表格.setItem(行号, 0, pid项)

            # 进程名
            名称项 = QTableWidgetItem(进程.名称)
            名称项.setToolTip(进程.命令行)
            self.表格.setItem(行号, 1, 名称项)

            # 用途说明
            用途 = 获取进程说明(进程.名称)
            用途项 = QTableWidgetItem(用途)
            用途项.setForeground(QColor(100, 100, 100))  # 灰色文字
            self.表格.setItem(行号, 2, 用途项)

            # 用户
            用户项 = QTableWidgetItem(进程.用户)
            self.表格.setItem(行号, 3, 用户项)

            # CPU使用率
            cpu项 = QTableWidgetItem(f"{进程.cpu使用率}%")
            cpu项.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # CPU高亮
            if 进程.cpu使用率 > 50:
                cpu项.setBackground(QColor(255, 200, 200))
            self.表格.setItem(行号, 4, cpu项)

            # 内存使用率
            内存项 = QTableWidgetItem(f"{进程.内存使用率}%")
            内存项.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # 内存高亮
            if 进程.内存使用率 > 50:
                内存项.setBackground(QColor(255, 200, 200))
            self.表格.setItem(行号, 5, 内存项)

            # 内存使用量
            内存量项 = QTableWidgetItem(进程.内存使用量)
            内存量项.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.表格.setItem(行号, 6, 内存量项)

            # 状态
            状态项 = QTableWidgetItem(进程.状态)
            状态项.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.表格.setItem(行号, 7, 状态项)

            # 优先级
            优先级项 = QTableWidgetItem(str(进程.优先级))
            优先级项.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.表格.setItem(行号, 8, 优先级项)

            # 操作按钮
            操作容器 = QWidget()
            操作布局 = QHBoxLayout(操作容器)
            操作布局.setContentsMargins(2, 2, 2, 2)

            终止按钮 = QPushButton("终止")
            终止按钮.clicked.connect(partial(self.终止进程, 进程.pid, 进程.名称, False))
            操作布局.addWidget(终止按钮)

            强制终止按钮 = QPushButton("强制")
            强制终止按钮.clicked.connect(partial(self.终止进程, 进程.pid, 进程.名称, True))
            操作布局.addWidget(强制终止按钮)

            优先级按钮 = QPushButton("优先级")
            优先级按钮.clicked.connect(partial(self.调整优先级, 进程.pid, 进程.名称, 进程.优先级))
            操作布局.addWidget(优先级按钮)

            self.表格.setCellWidget(行号, 9, 操作容器)

    def 更新系统资源(self, 资源信息):
        """更新系统资源显示"""
        if not 资源信息:
            return

        cpu = 资源信息.get('cpu使用率', 0)
        内存 = 资源信息.get('内存使用率', 0)
        负载 = 资源信息.get('负载1分钟', 0)

        # 更新显示
        self.cpu标签.setText(f"{cpu:.1f}%")
        self.内存标签.setText(f"{内存:.1f}% ({资源信息.get('内存已用', '0')} / {资源信息.get('内存总量', '0')})")
        self.负载标签.setText(f"{负载:.2f}")

        # 根据使用率设置颜色
        if cpu > 80:
            self.cpu标签.setStyleSheet("font-weight: bold; font-size: 14px; color: red;")
        elif cpu > 50:
            self.cpu标签.setStyleSheet("font-weight: bold; font-size: 14px; color: orange;")
        else:
            self.cpu标签.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")

        if 内存 > 80:
            self.内存标签.setStyleSheet("font-weight: bold; font-size: 14px; color: red;")
        elif 内存 > 50:
            self.内存标签.setStyleSheet("font-weight: bold; font-size: 14px; color: orange;")
        else:
            self.内存标签.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")

    def 终止进程(self, pid, 进程名, 强制):
        """终止进程"""
        操作 = "强制终止" if 强制 else "终止"
        回复 = QMessageBox.question(
            self,
            f"⚠️ 确认{操作}",
            f"确定要{操作}进程 {进程名} (PID: {pid}) 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if 回复 == QMessageBox.StandardButton.Yes:
            self.终止请求.emit(pid, 强制, "")

    def 调整优先级(self, pid, 进程名, 当前优先级):
        """调整进程优先级"""
        优先级, 确认 = QInputDialog.getInt(
            self,
            "调整优先级",
            f"进程: {进程名} (PID: {pid})\n"
            f"当前优先级: {当前优先级}\n\n"
            f"请输入新的优先级 (-20到19，越小优先级越高):",
            当前优先级,
            -20,
            19,
            1
        )

        if 确认:
            self.优先级请求.emit(pid, 优先级, "")

    def 显示进度条(self):
        """显示进度条"""
        self.进度条.setVisible(True)

    def 隐藏进度条(self):
        """隐藏进度条"""
        self.进度条.setVisible(False)

    def 停止定时器(self):
        """停止定时器"""
        if self.自动刷新定时器:
            self.自动刷新定时器.stop()
            self.自动刷新定时器 = None

