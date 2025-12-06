"""
垃圾清理标签页组件
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QLabel,
    QCheckBox, QMessageBox, QTreeWidget, QTreeWidgetItem, QSplitter
)
from PySide6.QtCore import Signal, Qt, QThread
from 核心 import 垃圾清理器, 垃圾项


class 垃圾清理线程(QThread):
    """垃圾清理工作线程"""
    进度更新 = Signal(int)
    扫描到文件 = Signal(object)
    扫描完成 = Signal(list)
    清理完成 = Signal(dict)

    def __init__(self, 任务类型: str, 清理器: 垃圾清理器, 垃圾列表: list = None):
        super().__init__()
        self.任务类型 = 任务类型
        self.清理器 = 清理器
        self.垃圾列表 = 垃圾列表 if 垃圾列表 else []

    def run(self):
        if self.任务类型 == '扫描':
            垃圾文件 = self.清理器.扫描垃圾文件(self.进度更新.emit, self.扫描到文件.emit)
            self.扫描完成.emit(垃圾文件)
        elif self.任务类型 == '清理':
            结果 = self.清理器.清理选中的垃圾(self.垃圾列表, self.进度更新.emit)
            self.清理完成.emit(结果)

    def 取消(self):
        if self.任务类型 == '扫描':
            self.清理器.取消扫描()
        self.quit()


class 垃圾清理标签页(QWidget):
    """垃圾清理标签页"""

    def __init__(self):
        super().__init__()
        self.清理器 = 垃圾清理器()
        self.垃圾列表 = []
        self.当前过滤类型 = None  # None表示显示全部
        self.工作线程 = None
        self._正在更新类型树 = False
        self._正在更新表格 = False
        self.初始化界面()

    def 初始化界面(self):
        """初始化界面"""
        主布局 = QVBoxLayout(self)

        # 操作栏
        操作布局 = QHBoxLayout()
        self.扫描按钮 = QPushButton("扫描垃圾文件")
        self.扫描按钮.clicked.connect(self.开始扫描)
        操作布局.addWidget(self.扫描按钮)

        self.清理按钮 = QPushButton("清理选中垃圾")
        self.清理按钮.setEnabled(False)
        self.清理按钮.clicked.connect(self.开始清理)
        操作布局.addWidget(self.清理按钮)

        刷新按钮 = QPushButton("刷新")
        刷新按钮.clicked.connect(self.更新统计信息)
        操作布局.addWidget(刷新按钮)

        清空回收站按钮 = QPushButton("清空回收站")
        清空回收站按钮.clicked.connect(self.清空回收站)
        操作布局.addWidget(清空回收站按钮)

        操作布局.addStretch()

        self.统计标签 = QLabel("请先扫描垃圾文件")
        操作布局.addWidget(self.统计标签)

        主布局.addLayout(操作布局)

        # 进度条
        self.进度条 = QProgressBar()
        self.进度条.setVisible(False)
        主布局.addWidget(self.进度条)

        # 分割器
        分割器 = QSplitter(Qt.Horizontal)

        # 左侧类型树
        左侧面板 = QWidget()
        左侧布局 = QVBoxLayout(左侧面板)
        左侧布局.addWidget(QLabel("垃圾文件分类"))

        self.类型树 = QTreeWidget()
        self.类型树.setHeaderLabel("类型")
        self.类型树.itemClicked.connect(self.类型树点击)
        self.类型树.itemChanged.connect(self.类型树勾选改变)
        左侧布局.addWidget(self.类型树)

        控制布局 = QHBoxLayout()
        全选按钮 = QPushButton("全选")
        全选按钮.clicked.connect(self.全选)
        控制布局.addWidget(全选按钮)

        取消选择按钮 = QPushButton("取消选择")
        取消选择按钮.clicked.connect(self.取消选择)
        控制布局.addWidget(取消选择按钮)
        控制布局.addStretch()
        左侧布局.addLayout(控制布局)

        分割器.addWidget(左侧面板)

        # 右侧表格
        右侧面板 = QWidget()
        右侧布局 = QVBoxLayout(右侧面板)
        右侧布局.addWidget(QLabel("垃圾文件列表"))

        self.垃圾表格 = QTableWidget()
        self.垃圾表格.setColumnCount(5)
        self.垃圾表格.setHorizontalHeaderLabels(["选择", "类型", "文件名", "大小", "路径"])
        self.垃圾表格.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.垃圾表格.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.垃圾表格.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.垃圾表格.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.垃圾表格.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.垃圾表格.setAlternatingRowColors(True)
        self.垃圾表格.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.垃圾表格.setSortingEnabled(True)
        右侧布局.addWidget(self.垃圾表格)

        分割器.addWidget(右侧面板)
        分割器.setStretchFactor(0, 1)
        分割器.setStretchFactor(1, 3)

        主布局.addWidget(分割器)

    def 获取显示列表(self) -> list:
        """根据当前过滤类型获取要显示的垃圾列表"""
        if self.当前过滤类型 is None:
            return self.垃圾列表
        return [g for g in self.垃圾列表 if g.类型 == self.当前过滤类型]

    def 添加表格行(self, 垃圾: 垃圾项):
        """向表格添加一行"""
        行号 = self.垃圾表格.rowCount()
        self.垃圾表格.insertRow(行号)

        复选框 = QCheckBox()
        复选框.setChecked(垃圾.是否选中)
        复选框.stateChanged.connect(lambda state, g=垃圾: self.表格复选框改变(g, state))
        self.垃圾表格.setCellWidget(行号, 0, 复选框)

        self.垃圾表格.setItem(行号, 1, QTableWidgetItem(垃圾.类型))
        self.垃圾表格.setItem(行号, 2, QTableWidgetItem(Path(垃圾.路径).name))

        大小项 = QTableWidgetItem(self.清理器.格式化大小(垃圾.大小))
        大小项.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.垃圾表格.setItem(行号, 3, 大小项)

        self.垃圾表格.setItem(行号, 4, QTableWidgetItem(垃圾.路径))

    def 刷新表格(self):
        """根据当前过滤条件刷新表格"""
        self._正在更新表格 = True
        self.垃圾表格.setRowCount(0)
        显示列表 = self.获取显示列表()
        for 垃圾 in 显示列表:
            self.添加表格行(垃圾)
        self._正在更新表格 = False
        self.更新统计信息()

    def 刷新类型树(self):
        """刷新类型树"""
        self._正在更新类型树 = True
        self.类型树.clear()

        if not self.垃圾列表:
            self._正在更新类型树 = False
            return

        # 按类型分组统计
        类型统计 = {}
        总大小 = 0
        总选中数 = 0

        for 垃圾 in self.垃圾列表:
            if 垃圾.类型 not in 类型统计:
                类型统计[垃圾.类型] = {'数量': 0, '大小': 0, '选中数': 0}
            类型统计[垃圾.类型]['数量'] += 1
            类型统计[垃圾.类型]['大小'] += 垃圾.大小
            if 垃圾.是否选中:
                类型统计[垃圾.类型]['选中数'] += 1
                总选中数 += 1
            总大小 += 垃圾.大小

        # 创建类型项
        for 类型, 统计 in 类型统计.items():
            项文本 = f"{类型} ({统计['数量']}项, {self.清理器.格式化大小(统计['大小'])})"
            类型项 = QTreeWidgetItem(self.类型树)
            类型项.setText(0, 项文本)
            类型项.setData(0, Qt.UserRole, 类型)
            类型项.setFlags(类型项.flags() | Qt.ItemIsUserCheckable)

            if 统计['选中数'] == 统计['数量']:
                类型项.setCheckState(0, Qt.Checked)
            elif 统计['选中数'] > 0:
                类型项.setCheckState(0, Qt.PartiallyChecked)
            else:
                类型项.setCheckState(0, Qt.Unchecked)

        # 创建总计项
        总项 = QTreeWidgetItem(self.类型树)
        总项.setText(0, f"全部 ({len(self.垃圾列表)}项, {self.清理器.格式化大小(总大小)})")
        总项.setData(0, Qt.UserRole, None)
        总项.setFlags(总项.flags() | Qt.ItemIsUserCheckable)

        if 总选中数 == len(self.垃圾列表):
            总项.setCheckState(0, Qt.Checked)
        elif 总选中数 > 0:
            总项.setCheckState(0, Qt.PartiallyChecked)
        else:
            总项.setCheckState(0, Qt.Unchecked)

        self.类型树.expandAll()
        self._正在更新类型树 = False

    def 更新统计信息(self):
        """更新统计信息"""
        显示列表 = self.获取显示列表()
        if not 显示列表:
            self.统计标签.setText("请先扫描垃圾文件")
            return

        总大小 = sum(g.大小 for g in 显示列表)
        选中列表 = [g for g in 显示列表 if g.是否选中]
        选中大小 = sum(g.大小 for g in 选中列表)

        self.统计标签.setText(
            f"总计: {len(显示列表)}项, {self.清理器.格式化大小(总大小)} | "
            f"已选: {len(选中列表)}项, {self.清理器.格式化大小(选中大小)}"
        )

    def 表格复选框改变(self, 垃圾: 垃圾项, 状态: int):
        """表格复选框状态改变"""
        if self._正在更新表格:
            return
        垃圾.是否选中 = (状态 == Qt.Checked)
        self.刷新类型树()
        self.更新统计信息()

    def 类型树点击(self, 项: QTreeWidgetItem, 列: int):
        """类型树项被点击（过滤显示）"""
        类型 = 项.data(0, Qt.UserRole)
        self.当前过滤类型 = 类型
        self.刷新表格()

    def 类型树勾选改变(self, 项: QTreeWidgetItem, 列: int):
        """类型树勾选状态改变（批量选中/取消）"""
        if self._正在更新类型树:
            return

        类型 = 项.data(0, Qt.UserRole)
        选中 = 项.checkState(0) == Qt.Checked

        if 类型 is None:
            # 全部项：修改所有垃圾
            for 垃圾 in self.垃圾列表:
                垃圾.是否选中 = 选中
        else:
            # 特定类型：修改该类型的垃圾
            for 垃圾 in self.垃圾列表:
                if 垃圾.类型 == 类型:
                    垃圾.是否选中 = 选中

        self.刷新表格()
        self.刷新类型树()

    def 全选(self):
        """全选所有垃圾"""
        for 垃圾 in self.垃圾列表:
            垃圾.是否选中 = True
        self.刷新表格()
        self.刷新类型树()

    def 取消选择(self):
        """取消选择所有垃圾"""
        for 垃圾 in self.垃圾列表:
            垃圾.是否选中 = False
        self.刷新表格()
        self.刷新类型树()

    def 开始扫描(self):
        """开始扫描垃圾文件"""
        self.扫描按钮.setEnabled(False)
        self.清理按钮.setEnabled(False)
        self.进度条.setVisible(True)
        self.进度条.setValue(0)
        self.统计标签.setText("正在扫描...")

        self.垃圾列表 = []
        self.当前过滤类型 = None
        self.类型树.clear()
        self.垃圾表格.setRowCount(0)

        self.工作线程 = 垃圾清理线程('扫描', self.清理器)
        self.工作线程.进度更新.connect(self.进度条.setValue)
        self.工作线程.扫描到文件.connect(self.实时添加文件)
        self.工作线程.扫描完成.connect(self.扫描完成)
        self.工作线程.start()

    def 实时添加文件(self, 垃圾: 垃圾项):
        """实时添加扫描到的文件"""
        self.垃圾列表.append(垃圾)
        self.统计标签.setText(f"已扫描 {len(self.垃圾列表)} 个文件")

        # 如果没有过滤或匹配当前过滤，添加到表格
        if self.当前过滤类型 is None or 垃圾.类型 == self.当前过滤类型:
            self.添加表格行(垃圾)

    def 扫描完成(self, 垃圾文件: list):
        """扫描完成"""
        self.扫描按钮.setEnabled(True)
        self.清理按钮.setEnabled(True)
        self.进度条.setVisible(False)

        self.垃圾列表 = 垃圾文件
        self.刷新类型树()
        self.更新统计信息()

    def 开始清理(self):
        """开始清理"""
        选中列表 = [g for g in self.垃圾列表 if g.是否选中]

        if not 选中列表:
            QMessageBox.warning(self, "警告", "请先选择要清理的垃圾文件")
            return

        选中大小 = sum(g.大小 for g in 选中列表)
        回复 = QMessageBox.question(
            self, "确认清理",
            f"确定要清理选中的 {len(选中列表)} 个文件吗？\n"
            f"释放空间: {self.清理器.格式化大小(选中大小)}\n\n"
            f"此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if 回复 != QMessageBox.StandardButton.Yes:
            return

        self.扫描按钮.setEnabled(False)
        self.清理按钮.setEnabled(False)
        self.进度条.setVisible(True)
        self.进度条.setValue(0)
        self.统计标签.setText("正在清理...")

        self.工作线程 = 垃圾清理线程('清理', self.清理器, 选中列表)
        self.工作线程.进度更新.connect(self.进度条.setValue)
        self.工作线程.清理完成.connect(self.清理完成)
        self.工作线程.start()

    def 清理完成(self, 结果: dict):
        """清理完成"""
        self.扫描按钮.setEnabled(True)
        self.进度条.setVisible(False)

        if 结果['成功']:
            QMessageBox.information(
                self, "清理完成",
                f"成功清理 {结果['成功数']} 个文件\n"
                f"释放空间: {self.清理器.格式化大小(结果['清理大小'])}\n"
                f"失败: {结果['失败数']} 个"
            )
            self.开始扫描()
        else:
            QMessageBox.warning(self, "清理失败", "清理过程中出现错误")

    def 清空回收站(self):
        """清空回收站"""
        回复 = QMessageBox.question(
            self, "确认清空",
            "确定要清空回收站吗？\n\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if 回复 != QMessageBox.StandardButton.Yes:
            return

        结果 = self.清理器.清空回收站()

        if 结果['成功']:
            QMessageBox.information(
                self, "完成",
                f"回收站已清空\n释放空间: {self.清理器.格式化大小(结果['清理大小'])}"
            )
        else:
            QMessageBox.warning(self, "警告", "清空回收站失败")
