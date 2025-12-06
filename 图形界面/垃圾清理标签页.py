"""
垃圾清理标签页组件
"""

from typing import List
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QLabel, QGroupBox,
    QCheckBox, QMessageBox, QTreeWidget, QTreeWidgetItem, QSplitter,
    QFrame, QScrollArea, QButtonGroup, QRadioButton, QApplication
)
from PySide6.QtCore import Signal, Qt, QThread, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QFont, QColor
from 核心 import 垃圾清理器, 垃圾项


class 垃圾清理线程(QThread):
    """垃圾清理工作线程"""
    进度更新 = Signal(int)
    扫描完成 = Signal(list)
    清理完成 = Signal(dict)

    def __init__(self, 任务类型: str, 清理器: 垃圾清理器, 垃圾列表: List = None):
        super().__init__()
        self.任务类型 = 任务类型
        self.清理器 = 清理器
        self.垃圾列表 = 垃圾列表 or []
        self.已取消 = False

    def run(self):
        if self.任务类型 == '扫描':
            垃圾文件 = self.清理器.扫描垃圾文件(self.进度更新.emit)
            self.扫描完成.emit(垃圾文件)
        elif self.任务类型 == '清理':
            结果 = self.清理器.清理选中的垃圾(self.垃圾列表, self.进度更新.emit)
            self.清理完成.emit(结果)

    def 取消(self):
        self.已取消 = True
        if self.任务类型 == '扫描':
            self.清理器.取消扫描()
        self.quit()


class 垃圾清理标签页(QWidget):
    """垃圾清理标签页"""

    def __init__(self):
        super().__init__()
        self.清理器 = 垃圾清理器()
        self.当前垃圾列表 = []
        self.工作线程 = None
        self.初始化界面()

    def 初始化界面(self):
        """初始化界面"""
        主布局 = QVBoxLayout(self)

        # 操作栏
        操作布局 = QHBoxLayout()

        # 扫描按钮
        self.扫描按钮 = QPushButton("🔍 扫描垃圾文件")
        扫描按钮样式 = """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """
        self.扫描按钮.setStyleSheet(扫描按钮样式)
        self.扫描按钮.clicked.connect(self.开始扫描)
        操作布局.addWidget(self.扫描按钮)

        # 清理按钮
        self.清理按钮 = QPushButton("🗑️ 清理选中垃圾")
        self.清理按钮.setEnabled(False)
        清理样式 = """
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """
        self.清理按钮.setStyleSheet(清理样式)
        self.清理按钮.clicked.connect(self.开始清理)
        操作布局.addWidget(self.清理按钮)

        # 刷新按钮
        刷新按钮 = QPushButton("🔄 刷新")
        刷新按钮.clicked.connect(self.刷新界面)
        操作布局.addWidget(刷新按钮)

        # 清空回收站按钮
        清空回收站按钮 = QPushButton("🗑️ 清空回收站")
        清空回收站按钮.clicked.connect(self.清空回收站)
        操作布局.addWidget(清空回收站按钮)

        操作布局.addStretch()

        # 统计信息
        self.统计标签 = QLabel("请先扫描垃圾文件")
        self.统计标签.setStyleSheet("font-weight: bold; color: #666;")
        操作布局.addWidget(self.统计标签)

        主布局.addLayout(操作布局)

        # 进度条
        self.进度条 = QProgressBar()
        self.进度条.setVisible(False)
        主布局.addWidget(self.进度条)

        # 创建分割器
        分割器 = QSplitter(Qt.Horizontal)

        # 左侧：类型树
        左侧面板 = self.创建类型树面板()
        分割器.addWidget(左侧面板)

        # 右侧：垃圾列表
        右侧面板 = self.创建垃圾列表面板()
        分割器.addWidget(右侧面板)

        # 设置分割比例
        分割器.setStretchFactor(0, 1)
        分割器.setStretchFactor(1, 3)

        主布局.addWidget(分割器)

    def 创建类型树面板(self):
        """创建类型树面板"""
        左侧面板 = QWidget()
        左侧布局 = QVBoxLayout(左侧面板)

        # 标题
        标题标签 = QLabel("垃圾文件分类")
        标题标签.setStyleSheet("font-weight: bold; font-size: 16px;")
        左侧布局.addWidget(标题标签)

        # 类型树
        self.类型树 = QTreeWidget()
        self.类型树.setHeaderLabel("类型")
        self.类型树.itemClicked.connect(self.类型树点击)
        self.类型树.itemChanged.connect(self.类型树项改变)
        左侧布局.addWidget(self.类型树)

        # 选择控制
        控制布局 = QHBoxLayout()

        全选按钮 = QPushButton("全选")
        全选按钮.clicked.connect(self.全选)
        控制布局.addWidget(全选按钮)

        取消选择按钮 = QPushButton("取消选择")
        取消选择按钮.clicked.connect(self.取消选择)
        控制布局.addWidget(取消选择按钮)

        控制布局.addStretch()
        左侧布局.addLayout(控制布局)

        return 左侧面板

    def 创建垃圾列表面板(self):
        """创建垃圾列表面板"""
        右侧面板 = QWidget()
        右侧布局 = QVBoxLayout(右侧面板)

        # 标题和筛选
        标题布局 = QHBoxLayout()

        标题标签 = QLabel("垃圾文件列表")
        标题标签.setStyleSheet("font-weight: bold; font-size: 16px;")
        标题布局.addWidget(标题标签)

        self.显示全选复选框 = QCheckBox("显示未选中")
        self.显示全选复选框.stateChanged.connect(self.过滤垃圾列表)
        标题布局.addWidget(self.显示全选复选框)

        标题布局.addStretch()
        右侧布局.addLayout(标题布局)

        # 表格
        self.垃圾表格 = QTableWidget()
        self.垃圾表格.setColumnCount(5)
        self.垃圾表格.setHorizontalHeaderLabels(["选择", "类型", "文件名", "大小", "路径"])

        # 设置列宽
        self.垃圾表格.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.垃圾表格.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.垃圾表格.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.垃圾表格.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.垃圾表格.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        # 设置表格属性
        self.垃圾表格.setAlternatingRowColors(True)
        self.垃圾表格.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.垃圾表格.setSortingEnabled(True)

        右侧布局.addWidget(self.垃圾表格)

        return 右侧面板

    def 开始扫描(self):
        """开始扫描垃圾文件"""
        self.扫描按钮.setEnabled(False)
        self.清理按钮.setEnabled(False)
        self.进度条.setVisible(True)
        self.进度条.setValue(0)
        self.统计标签.setText("正在扫描垃圾文件...")

        # 清空之前的结果
        self.当前垃圾列表 = []
        self.类型树.clear()
        self.垃圾表格.setRowCount(0)

        # 创建工作线程
        self.工作线程 = 垃圾清理线程('扫描', self.清理器)
        self.工作线程.进度更新.connect(self.进度条.setValue)
        self.工作线程.扫描完成.connect(self.扫描完成)
        self.工作线程.start()

    def 扫描完成(self, 垃圾文件: List):
        """扫描完成"""
        self.当前垃圾列表 = 垃圾文件
        self.扫描按钮.setEnabled(True)
        self.进度条.setVisible(False)

        if 垃圾文件:
            self.清理按钮.setEnabled(True)
            self.统计标签.setText(f"找到 {len(垃圾文件)} 个垃圾文件")

            # 使用定时器延迟更新UI，避免阻塞
            QTimer.singleShot(100, self.延迟更新UI)
        else:
            self.统计标签.setText("未找到垃圾文件")
            QMessageBox.information(self, "提示", "系统中未找到垃圾文件！")

    def 延迟更新UI(self):
        """延迟更新UI，避免阻塞"""
        self.更新类型树()
        self.更新垃圾表格()

    def 更新类型树(self):
        """更新类型树"""
        # 按类型分组
        类型分组 = {}
        总大小 = 0

        for 垃圾 in self.当前垃圾列表:
            if 垃圾.类型 not in 类型分组:
                类型分组[垃圾.类型] = []
            类型分组[垃圾.类型].append(垃圾)
            总大小 += 垃圾.大小

        # 创建树项
        for 类型, 垃圾列表 in 类型分组.items():
            类型大小 = sum(g.大小 for g in 垃圾列表)
            项文本 = f"{类型} ({len(垃圾列表)}项, {self.清理器.格式化大小(类型大小)})"

            类型项 = QTreeWidgetItem(self.类型树)
            类型项.setText(0, 项文本)
            类型项.setData(0, Qt.UserRole, 类型)
            类型项.setCheckState(0, Qt.Checked)

            # 添加子项
            for 垃圾 in 垃圾列表[:10]:  # 只显示前10个作为示例
                子项 = QTreeWidgetItem(类型项)
                子项.setText(0, f"  {垃圾.描述[:50]}...")
                子项.setData(0, Qt.UserRole, 垃圾)
                子项.setCheckState(0, Qt.Checked)

            if len(垃圾列表) > 10:
                更多项 = QTreeWidgetItem(类型项)
                更多项.setText(0, f"  ... 还有 {len(垃圾列表) - 10} 项")

        # 添加总统计
        总项 = QTreeWidgetItem(self.类型树)
        总项.setText(0, f"总计: {len(self.当前垃圾列表)} 项, {self.清理器.格式化大小(总大小)}")
        总项.setData(0, Qt.UserRole, 'TOTAL')
        总项.setCheckState(0, Qt.Checked)

        # 展开所有项
        self.类型树.expandAll()

    def 更新垃圾表格(self):
        """更新垃圾表格"""
        显示列表 = self.获取显示垃圾列表()

        # 如果数据太多，使用虚拟加载（只显示前200行）
        最大显示行数 = 200
        if len(显示列表) > 最大显示行数:
            self.垃圾表格.setRowCount(最大显示行数)
            # 添加提示行
            self.垃圾表格.setRowCount(最大显示行数 + 1)
            提示项 = QTableWidgetItem(f"... 还有 {len(显示列表) - 最大显示行数} 行未显示")
            提示项.setTextAlignment(Qt.AlignCenter)
            self.垃圾表格.setItem(最大显示行数, 0, 提示项)
            self.垃圾表格.setSpan(最大显示行数, 0, 1, 5)  # 合并5列
            显示列表 = 显示列表[:最大显示行数]
        else:
            self.垃圾表格.setRowCount(len(显示列表))

        for 行号, 垃圾 in enumerate(显示列表):
            # 选择复选框
            复选框 = QCheckBox()
            复选框.setChecked(垃圾.是否选中)
            复选框.stateChanged.connect(lambda state, g=垃圾: self.垃圾项选择改变(g, state))
            self.垃圾表格.setCellWidget(行号, 0, 复选框)

            # 类型
            类型项 = QTableWidgetItem(垃圾.类型)
            类型项.setToolTip(垃圾.类型)
            self.垃圾表格.setItem(行号, 1, 类型项)

            # 文件名
            文件路径 = Path(垃圾.路径)
            文件名项 = QTableWidgetItem(文件路径.name)
            文件名项.setToolTip(垃圾.描述)
            self.垃圾表格.setItem(行号, 2, 文件名项)

            # 大小
            大小项 = QTableWidgetItem(self.清理器.格式化大小(垃圾.大小))
            大小项.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.垃圾表格.setItem(行号, 3, 大小项)

            # 路径
            路径项 = QTableWidgetItem(垃圾.路径[:100] + '...' if len(垃圾.路径) > 100 else 垃圾.路径)
            路径项.setToolTip(垃圾.路径)
            self.垃圾表格.setItem(行号, 4, 路径项)

    def 获取显示垃圾列表(self) -> List:
        """获取显示的垃圾列表"""
        if self.显示全选复选框.isChecked():
            return self.当前垃圾列表
        else:
            return [g for g in self.当前垃圾列表 if g.是否选中]

    def 垃圾项选择改变(self, 垃圾, 状态: int):
        """垃圾项选择改变"""
        垃圾.是否选中 = (状态 == Qt.Checked)
        self.更新统计信息()
        self.更新类型树状态()

    def 类型树点击(self, 项: QTreeWidgetItem, 列: int):
        """类型树点击"""
        类型 = 项.data(0, Qt.UserRole)

        if 类型 == 'TOTAL':
            # 显示所有垃圾
            self.更新垃圾表格()
        else:
            # 显示特定类型的垃圾
            类型垃圾 = [g for g in self.当前垃圾列表 if g.类型 == 类型]
            self.显示垃圾列表(类型垃圾)

    def 类型树项改变(self, 项: QTreeWidgetItem, 列: int):
        """类型树项改变"""
        类型 = 项.data(0, Qt.UserRole)
        选中状态 = 项.checkState(0) == Qt.Checked

        if 类型 == 'TOTAL':
            # 全选/取消全选
            for 垃圾 in self.当前垃圾列表:
                垃圾.是否选中 = 选中状态
        elif isinstance(类型, str):
            # 选择/取消选择特定类型的所有垃圾
            for 垃圾 in self.当前垃圾列表:
                if 垃圾.类型 == 类型:
                    垃圾.是否选中 = 选中状态

        self.更新垃圾表格()
        self.更新统计信息()

    def 更新类型树状态(self):
        """更新类型树状态"""
        # 计算每种类型的选中数量
        类型统计 = {}
        总选中数 = 0

        for 垃圾 in self.当前垃圾列表:
            if 垃圾.类型 not in 类型统计:
                类型统计[垃圾.类型] = {'总数': 0, '选中数': 0}
            类型统计[垃圾.类型]['总数'] += 1
            if 垃圾.是否选中:
                类型统计[垃圾.类型]['选中数'] += 1
                总选中数 += 1

        # 更新树项状态
        总项 = self.类型树.topLevelItem(self.类型树.topLevelCount() - 1)  # 最后一项是总计
        if 总项:
            总项.setCheckState(0, Qt.Checked if 总选中数 == len(self.当前垃圾列表) else
                             Qt.PartiallyChecked if 总选中数 > 0 else Qt.Unchecked)

    def 过滤垃圾列表(self):
        """过滤垃圾列表"""
        self.更新垃圾表格()

    def 全选(self):
        """全选"""
        for 垃圾 in self.当前垃圾列表:
            垃圾.是否选中 = True
        self.更新垃圾表格()
        self.更新类型树状态()
        self.更新统计信息()

    def 取消选择(self):
        """取消选择"""
        for 垃圾 in self.当前垃圾列表:
            垃圾.是否选中 = False
        self.更新垃圾表格()
        self.更新类型树状态()
        self.更新统计信息()

    def 更新统计信息(self):
        """更新统计信息"""
        选中列表 = [g for g in self.当前垃圾列表 if g.是否选中]
        选中大小 = sum(g.大小 for g in 选中列表)

        if self.当前垃圾列表:
            总大小 = sum(g.大小 for g in self.当前垃圾列表)
            self.统计标签.setText(
                f"总计: {len(self.当前垃圾列表)} 项, {self.清理器.格式化大小(总大小)} | "
                f"已选: {len(选中列表)} 项, {self.清理器.格式化大小(选中大小)}"
            )
        else:
            self.统计标签.setText("请先扫描垃圾文件")

    def 开始清理(self):
        """开始清理垃圾文件"""
        选中列表 = [g for g in self.当前垃圾列表 if g.是否选中]

        if not 选中列表:
            QMessageBox.warning(self, "警告", "请先选择要清理的垃圾文件！")
            return

        # 确认对话框
        选中大小 = sum(g.大小 for g in 选中列表)
        回复 = QMessageBox.question(
            self,
            "🔍 确认清理",
            f"确定要清理选中的 {len(选中列表)} 个垃圾文件吗？\n"
            f"释放空间: {self.清理器.格式化大小(选中大小)}\n\n"
            f"⚠️ 注意：此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if 回复 != QMessageBox.StandardButton.Yes:
            return

        # 开始清理
        self.扫描按钮.setEnabled(False)
        self.清理按钮.setEnabled(False)
        self.进度条.setVisible(True)
        self.进度条.setValue(0)
        self.统计标签.setText("正在清理垃圾文件...")

        # 创建工作线程
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
                self,
                "✓ 清理完成",
                f"成功清理 {结果['成功数']} 个文件\n"
                f"释放空间: {self.清理器.格式化大小(结果['清理大小'])}\n"
                f"失败: {结果['失败数']} 个"
            )

            # 重新扫描以更新列表
            self.开始扫描()
        else:
            QMessageBox.warning(
                self,
                "⚠️ 清理失败",
                "清理过程中出现错误，请检查文件权限"
            )

    def 清空回收站(self):
        """清空回收站"""
        回复 = QMessageBox.question(
            self,
            "🔍 确认清空",
            "确定要清空回收站吗？\n\n⚠️ 注意：此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if 回复 != QMessageBox.StandardButton.Yes:
            return

        # 清空回收站
        结果 = self.清理器.清空回收站()

        if 结果['成功']:
            QMessageBox.information(
                self,
                "✓ 完成",
                f"回收站已清空\n释放空间: {self.清理器.格式化大小(结果['清理大小'])}"
            )
        else:
            QMessageBox.warning(self, "⚠️ 警告", "清空回收站失败")

    def 刷新界面(self):
        """刷新界面"""
        if self.当前垃圾列表:
            self.更新统计信息()
        else:
            self.统计标签.setText("请先扫描垃圾文件")

    def 显示垃圾列表(self, 垃圾列表: List):
        """显示特定的垃圾列表"""
        self.当前垃圾列表 = 垃圾列表
        self.更新垃圾表格()
        self.更新统计信息()