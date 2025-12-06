"""
软件分析标签页 - 分析可清理的软件
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QLabel,
    QCheckBox, QMessageBox, QTreeWidget, QTreeWidgetItem, QSplitter,
    QGroupBox, QInputDialog, QLineEdit
)
from PySide6.QtCore import Signal, Qt, QThread
from PySide6.QtGui import QColor, QFont
from 核心.软件分析 import 软件分析器, 可清理软件, 格式化大小
from 核心.密码管理 import 密码管理


class 软件分析线程(QThread):
    """软件分析工作线程"""
    进度更新 = Signal(int, str)
    分析完成 = Signal(list)

    def __init__(self, 分析器: 软件分析器):
        super().__init__()
        self.分析器 = 分析器

    def run(self):
        结果 = self.分析器.分析全部(self.进度更新.emit)
        self.分析完成.emit(结果)

    def 取消(self):
        self.分析器.取消分析()
        self.quit()


class 软件分析标签页(QWidget):
    """软件分析标签页"""

    def __init__(self):
        super().__init__()
        self.分析器 = 软件分析器()
        self.软件列表 = []
        self.当前过滤类型 = None
        self.工作线程 = None
        self._正在更新 = False
        self.初始化界面()

    def 初始化界面(self):
        """初始化界面"""
        主布局 = QVBoxLayout(self)

        # 说明区域
        说明框 = QGroupBox("📊 软件分析说明")
        说明布局 = QVBoxLayout(说明框)
        说明文本 = QLabel(
            "分析系统中可清理的软件，包括：\n"
            "• 大型应用软件（>50MB）\n"
            "• Snap/Flatpak 应用\n"
            "• 旧版本内核\n"
            "• APT下载缓存\n"
            "• 孤立包（不再被依赖）\n"
            "• 重复类型软件（如多个浏览器）"
        )
        说明文本.setStyleSheet("color: #666;")
        说明布局.addWidget(说明文本)
        主布局.addWidget(说明框)

        # 操作栏
        操作布局 = QHBoxLayout()
        
        self.分析按钮 = QPushButton("🔍 开始分析")
        self.分析按钮.clicked.connect(self.开始分析)
        self.分析按钮.setStyleSheet("font-weight: bold; padding: 8px 16px;")
        操作布局.addWidget(self.分析按钮)

        self.清理按钮 = QPushButton("🗑️ 清理选中")
        self.清理按钮.setEnabled(False)
        self.清理按钮.clicked.connect(self.清理选中)
        操作布局.addWidget(self.清理按钮)

        操作布局.addStretch()

        self.统计标签 = QLabel("请点击「开始分析」扫描可清理的软件")
        self.统计标签.setStyleSheet("font-size: 13px;")
        操作布局.addWidget(self.统计标签)

        主布局.addLayout(操作布局)

        # 进度区域
        self.进度条 = QProgressBar()
        self.进度条.setVisible(False)
        主布局.addWidget(self.进度条)

        self.进度标签 = QLabel()
        self.进度标签.setVisible(False)
        主布局.addWidget(self.进度标签)

        # 分割器
        分割器 = QSplitter(Qt.Horizontal)

        # 左侧分类树
        左侧面板 = QWidget()
        左侧布局 = QVBoxLayout(左侧面板)
        左侧布局.setContentsMargins(0, 0, 0, 0)
        左侧布局.addWidget(QLabel("📁 软件分类"))

        self.分类树 = QTreeWidget()
        self.分类树.setHeaderLabel("类型")
        self.分类树.itemClicked.connect(self.分类树点击)
        self.分类树.itemChanged.connect(self.分类树勾选改变)
        左侧布局.addWidget(self.分类树)

        # 快捷操作
        快捷布局 = QHBoxLayout()
        全选按钮 = QPushButton("全选")
        全选按钮.clicked.connect(self.全选)
        快捷布局.addWidget(全选按钮)

        取消按钮 = QPushButton("取消")
        取消按钮.clicked.connect(self.取消选择)
        快捷布局.addWidget(取消按钮)
        左侧布局.addLayout(快捷布局)

        分割器.addWidget(左侧面板)

        # 右侧表格
        右侧面板 = QWidget()
        右侧布局 = QVBoxLayout(右侧面板)
        右侧布局.setContentsMargins(0, 0, 0, 0)
        右侧布局.addWidget(QLabel("📋 可清理软件列表"))

        self.软件表格 = QTableWidget()
        self.软件表格.setColumnCount(6)
        self.软件表格.setHorizontalHeaderLabels(["选择", "软件名称", "大小", "类型", "风险", "建议"])
        
        self.软件表格.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.软件表格.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.软件表格.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.软件表格.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.软件表格.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.软件表格.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        self.软件表格.setAlternatingRowColors(True)
        self.软件表格.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.软件表格.setSortingEnabled(True)
        右侧布局.addWidget(self.软件表格)

        分割器.addWidget(右侧面板)
        分割器.setStretchFactor(0, 1)
        分割器.setStretchFactor(1, 3)

        主布局.addWidget(分割器)

    def 开始分析(self):
        """开始分析"""
        self.分析按钮.setEnabled(False)
        self.清理按钮.setEnabled(False)
        self.进度条.setVisible(True)
        self.进度条.setValue(0)
        self.进度标签.setVisible(True)
        self.统计标签.setText("正在分析...")

        self.软件列表 = []
        self.当前过滤类型 = None
        self.分类树.clear()
        self.软件表格.setRowCount(0)

        self.工作线程 = 软件分析线程(self.分析器)
        self.工作线程.进度更新.connect(self.更新进度)
        self.工作线程.分析完成.connect(self.分析完成)
        self.工作线程.start()

    def 更新进度(self, 百分比: int, 描述: str):
        """更新进度"""
        self.进度条.setValue(百分比)
        self.进度标签.setText(描述)

    def 分析完成(self, 软件列表: list):
        """分析完成"""
        self.分析按钮.setEnabled(True)
        self.清理按钮.setEnabled(True)
        self.进度条.setVisible(False)
        self.进度标签.setVisible(False)

        self.软件列表 = 软件列表
        self.刷新分类树()
        self.刷新表格()
        self.更新统计()

    def 刷新分类树(self):
        """刷新分类树"""
        self._正在更新 = True
        self.分类树.clear()

        if not self.软件列表:
            self._正在更新 = False
            return

        # 按类型分组
        类型统计 = {}
        总大小 = 0

        for 软件 in self.软件列表:
            if 软件.类型 not in 类型统计:
                类型统计[软件.类型] = {'数量': 0, '大小': 0, '选中数': 0}
            类型统计[软件.类型]['数量'] += 1
            类型统计[软件.类型]['大小'] += 软件.大小
            if 软件.是否选中:
                类型统计[软件.类型]['选中数'] += 1
            总大小 += 软件.大小

        # 类型图标
        类型图标 = {
            'apt': '📦',
            'snap': '🔵',
            'flatpak': '📀',
            '内核': '🔧',
            '缓存': '📁',
            '孤立包': '🔗',
            '重复软件': '♊',
        }

        # 创建类型项
        for 类型, 统计 in sorted(类型统计.items(), key=lambda x: x[1]['大小'], reverse=True):
            图标 = 类型图标.get(类型, '📋')
            项文本 = f"{图标} {类型} ({统计['数量']}项, {格式化大小(统计['大小'])})"
            类型项 = QTreeWidgetItem(self.分类树)
            类型项.setText(0, 项文本)
            类型项.setData(0, Qt.UserRole, 类型)
            类型项.setFlags(类型项.flags() | Qt.ItemIsUserCheckable)

            if 统计['选中数'] == 统计['数量']:
                类型项.setCheckState(0, Qt.Checked)
            elif 统计['选中数'] > 0:
                类型项.setCheckState(0, Qt.PartiallyChecked)
            else:
                类型项.setCheckState(0, Qt.Unchecked)

        # 全部项
        总项 = QTreeWidgetItem(self.分类树)
        总选中 = sum(1 for s in self.软件列表 if s.是否选中)
        总项.setText(0, f"📊 全部 ({len(self.软件列表)}项, {格式化大小(总大小)})")
        总项.setData(0, Qt.UserRole, None)
        总项.setFlags(总项.flags() | Qt.ItemIsUserCheckable)

        if 总选中 == len(self.软件列表):
            总项.setCheckState(0, Qt.Checked)
        elif 总选中 > 0:
            总项.setCheckState(0, Qt.PartiallyChecked)
        else:
            总项.setCheckState(0, Qt.Unchecked)

        self.分类树.expandAll()
        self._正在更新 = False

    def 刷新表格(self):
        """刷新表格"""
        self._正在更新 = True
        self.软件表格.setRowCount(0)
        self.软件表格.setSortingEnabled(False)

        显示列表 = self.获取显示列表()

        for 软件 in 显示列表:
            self.添加表格行(软件)

        self.软件表格.setSortingEnabled(True)
        self._正在更新 = False

    def 获取显示列表(self) -> list:
        """获取要显示的列表"""
        if self.当前过滤类型 is None:
            return self.软件列表
        return [s for s in self.软件列表 if s.类型 == self.当前过滤类型]

    def 添加表格行(self, 软件: 可清理软件):
        """添加表格行"""
        行号 = self.软件表格.rowCount()
        self.软件表格.insertRow(行号)

        # 复选框
        复选框 = QCheckBox()
        复选框.setChecked(软件.是否选中)
        复选框.stateChanged.connect(lambda state, s=软件: self.表格复选框改变(s, state))
        self.软件表格.setCellWidget(行号, 0, 复选框)

        # 软件名称
        名称项 = QTableWidgetItem(软件.名称)
        名称项.setToolTip(f"删除命令: {软件.删除命令}")
        self.软件表格.setItem(行号, 1, 名称项)

        # 大小
        大小项 = QTableWidgetItem(格式化大小(软件.大小))
        大小项.setData(Qt.UserRole, 软件.大小)  # 用于排序
        大小项.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.软件表格.setItem(行号, 2, 大小项)

        # 类型
        self.软件表格.setItem(行号, 3, QTableWidgetItem(软件.类型))

        # 风险
        风险项 = QTableWidgetItem(软件.风险等级)
        if 软件.风险等级 == "高":
            风险项.setBackground(QColor(255, 200, 200))
        elif 软件.风险等级 == "中":
            风险项.setBackground(QColor(255, 230, 200))
        else:
            风险项.setBackground(QColor(200, 255, 200))
        self.软件表格.setItem(行号, 4, 风险项)

        # 建议
        建议项 = QTableWidgetItem(软件.建议)
        建议项.setToolTip(软件.描述)
        self.软件表格.setItem(行号, 5, 建议项)

    def 表格复选框改变(self, 软件: 可清理软件, 状态: int):
        """表格复选框状态改变"""
        if self._正在更新:
            return
        软件.是否选中 = (状态 == Qt.Checked)
        self.刷新分类树()
        self.更新统计()

    def 分类树点击(self, 项: QTreeWidgetItem, 列: int):
        """分类树点击"""
        类型 = 项.data(0, Qt.UserRole)
        self.当前过滤类型 = 类型
        self.刷新表格()

    def 分类树勾选改变(self, 项: QTreeWidgetItem, 列: int):
        """分类树勾选改变"""
        if self._正在更新:
            return

        类型 = 项.data(0, Qt.UserRole)
        选中 = 项.checkState(0) == Qt.Checked

        if 类型 is None:
            for 软件 in self.软件列表:
                软件.是否选中 = 选中
        else:
            for 软件 in self.软件列表:
                if 软件.类型 == 类型:
                    软件.是否选中 = 选中

        self.刷新表格()
        self.刷新分类树()
        self.更新统计()

    def 全选(self):
        """全选"""
        for 软件 in self.软件列表:
            软件.是否选中 = True
        self.刷新表格()
        self.刷新分类树()
        self.更新统计()

    def 取消选择(self):
        """取消选择"""
        for 软件 in self.软件列表:
            软件.是否选中 = False
        self.刷新表格()
        self.刷新分类树()
        self.更新统计()

    def 更新统计(self):
        """更新统计信息"""
        if not self.软件列表:
            self.统计标签.setText("请点击「开始分析」扫描可清理的软件")
            return

        总大小 = sum(s.大小 for s in self.软件列表)
        选中列表 = [s for s in self.软件列表 if s.是否选中]
        选中大小 = sum(s.大小 for s in 选中列表)

        self.统计标签.setText(
            f"共发现 {len(self.软件列表)} 项可清理 ({格式化大小(总大小)}) | "
            f"已选择 {len(选中列表)} 项 ({格式化大小(选中大小)})"
        )

    def 清理选中(self):
        """清理选中的软件"""
        选中列表 = [s for s in self.软件列表 if s.是否选中]

        if not 选中列表:
            QMessageBox.warning(self, "警告", "请先选择要清理的软件")
            return

        # 检查是否有高风险项
        高风险项 = [s for s in 选中列表 if s.风险等级 == "高"]
        if 高风险项:
            回复 = QMessageBox.warning(
                self, "⚠️ 高风险警告",
                f"您选中了 {len(高风险项)} 个高风险项:\n\n" +
                "\n".join(f"• {s.名称}" for s in 高风险项[:5]) +
                ("\n..." if len(高风险项) > 5 else "") +
                "\n\n这些项目删除后可能影响系统运行，确定要继续吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if 回复 != QMessageBox.StandardButton.Yes:
                return

        选中大小 = sum(s.大小 for s in 选中列表)
        回复 = QMessageBox.question(
            self, "确认清理",
            f"确定要清理以下 {len(选中列表)} 项吗？\n\n" +
            "\n".join(f"• {s.名称} ({格式化大小(s.大小)})" for s in 选中列表[:10]) +
            (f"\n... 还有 {len(选中列表) - 10} 项" if len(选中列表) > 10 else "") +
            f"\n\n预计释放空间: {格式化大小(选中大小)}\n\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if 回复 != QMessageBox.StandardButton.Yes:
            return

        # 获取密码
        密码 = 密码管理.读取密码()
        if not 密码:
            密码, 确认 = QInputDialog.getText(
                self, "需要密码",
                "部分操作需要管理员权限，请输入 sudo 密码:",
                QLineEdit.EchoMode.Password
            )
            if not 确认 or not 密码:
                return
            密码管理.保存密码(密码)

        # 执行清理
        成功数 = 0
        失败数 = 0
        清理大小 = 0

        for 软件 in 选中列表:
            def 获取密码():
                return 密码

            结果 = self.分析器.执行清理(软件, 获取密码)
            if 结果['成功']:
                成功数 += 1
                清理大小 += 软件.大小
            else:
                失败数 += 1

        # 显示结果
        QMessageBox.information(
            self, "清理完成",
            f"清理完成！\n\n"
            f"成功: {成功数} 项\n"
            f"失败: {失败数} 项\n"
            f"释放空间: {格式化大小(清理大小)}"
        )

        # 重新分析
        if 成功数 > 0:
            self.开始分析()
