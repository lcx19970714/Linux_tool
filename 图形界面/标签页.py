"""
标签页组件
"""

from functools import partial
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QLabel, QComboBox,
    QMessageBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QClipboard
from PySide6.QtWidgets import QApplication


class 软件标签页(QWidget):
    """统一的软件管理标签页 - 支持搜索、过滤和管理"""

    搜索请求 = Signal(str)
    刷新请求 = Signal()
    安装请求 = Signal(str)
    卸载请求 = Signal(str)
    获取未描述包名 = Signal()

    def __init__(self):
        super().__init__()
        self.工作线程 = None
        self.所有软件包 = []
        self.当前模式 = "已安装"  # "已安装" 或 "可用"
        self.包管理器 = None  # 将由主窗口设置
        self.初始化界面()

    def 初始化界面(self):
        """初始化UI"""
        布局 = QVBoxLayout(self)

        # 控制栏
        控制布局 = QHBoxLayout()

        # 模式选择
        控制布局.addWidget(QLabel("显示:"))
        self.模式选择 = QComboBox()
        self.模式选择.addItems(["已安装", "可用"])
        self.模式选择.currentTextChanged.connect(self.模式改变)
        控制布局.addWidget(self.模式选择)

        # 搜索框
        控制布局.addWidget(QLabel("搜索:"))
        self.搜索框 = QLineEdit()
        self.搜索框.setPlaceholderText("输入软件包名称...")
        self.搜索框.setMaximumWidth(300)
        self.搜索框.textChanged.connect(self.搜索或过滤)
        控制布局.addWidget(self.搜索框)

        # 搜索按钮（用于可用软件的搜索）
        self.搜索按钮 = QPushButton("搜索")
        self.搜索按钮.clicked.connect(self.搜索按钮点击)
        self.搜索按钮.setVisible(False)
        控制布局.addWidget(self.搜索按钮)

        # 刷新按钮
        刷新按钮 = QPushButton("刷新")
        刷新按钮.clicked.connect(self.刷新按钮点击)
        控制布局.addWidget(刷新按钮)

        # 复制未描述包名按钮
        self.复制未描述按钮 = QPushButton("📋 复制未描述包名")
        self.复制未描述按钮.clicked.connect(self.复制未描述包名)
        self.复制未描述按钮.setToolTip("复制所有在软件包描述.json中没有的包名到剪贴板")
        控制布局.addWidget(self.复制未描述按钮)

        控制布局.addStretch()
        布局.addLayout(控制布局)

        # 进度条
        self.进度条 = QProgressBar()
        self.进度条.setVisible(False)
        布局.addWidget(self.进度条)

        # 结果表格
        self.表格 = QTableWidget()
        self.表格.setColumnCount(5)
        self.表格.setHorizontalHeaderLabels(["软件名", "中文名/用途", "版本", "状态", "操作"])

        # 设置列宽度
        self.表格.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.表格.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.表格.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.表格.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.表格.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        # 设置行高自适应
        self.表格.verticalHeader().setDefaultSectionSize(60)
        self.表格.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # 设置表格属性
        self.表格.setAlternatingRowColors(True)
        self.表格.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        布局.addWidget(self.表格)

    def 模式改变(self, 新模式):
        """模式改变时的处理"""
        self.当前模式 = 新模式
        self.搜索框.clear()

        if 新模式 == "可用":
            self.搜索按钮.setVisible(True)
            self.搜索框.setPlaceholderText("输入软件包名称...")
            self.表格.setColumnCount(4)
            self.表格.setHorizontalHeaderLabels(["软件名", "版本", "状态", "操作"])
        else:
            self.搜索按钮.setVisible(False)
            self.搜索框.setPlaceholderText("按名称、中文名或用途搜索...")
            self.表格.setColumnCount(5)
            self.表格.setHorizontalHeaderLabels(["软件名", "中文名/用途", "版本", "可删除", "操作"])
            self.刷新按钮点击()

    def 搜索按钮点击(self):
        """搜索按钮点击"""
        关键词 = self.搜索框.text().strip()
        if 关键词:
            self.搜索请求.emit(关键词)

    def 搜索或过滤(self):
        """搜索或过滤"""
        if self.当前模式 == "已安装":
            self.过滤已安装()
        # 可用模式下不自动搜索，需要点击搜索按钮

    def 过滤已安装(self):
        """过滤已安装软件"""
        关键词 = self.搜索框.text().lower()
        self.表格.setRowCount(0)

        if not 关键词:
            self.显示已安装(self.所有软件包)
            return

        过滤结果 = [
            pkg for pkg in self.所有软件包
            if 关键词 in pkg.名称.lower()
            or 关键词 in pkg.中文名.lower()
            or 关键词 in pkg.用途.lower()
        ]
        self.显示已安装(过滤结果)

    def 刷新按钮点击(self):
        """刷新按钮点击"""
        self.刷新请求.emit()

    def 显示结果(self, 软件包列表):
        """显示搜索结果（可用软件）"""
        self.所有软件包 = 软件包列表
        self.表格.setRowCount(len(软件包列表))
        for 行号, 软件包 in enumerate(软件包列表):
            self.表格.setItem(行号, 0, QTableWidgetItem(软件包.名称))
            self.表格.setItem(行号, 1, QTableWidgetItem(软件包.版本))
            self.表格.setItem(行号, 2, QTableWidgetItem(软件包.状态))

            按钮 = QPushButton("安装")
            按钮.clicked.connect(partial(self.安装请求.emit, 软件包.名称))
            self.表格.setCellWidget(行号, 3, 按钮)

    def 显示已安装(self, 软件包列表):
        """显示已安装软件"""
        self.所有软件包 = 软件包列表
        self.表格.setRowCount(len(软件包列表))
        for 行号, 软件包 in enumerate(软件包列表):
            # 列0: 软件包名称
            self.表格.setItem(行号, 0, QTableWidgetItem(软件包.名称))

            # 列1: 中文名和用途（合并显示）
            中文名 = 软件包.中文名 if 软件包.中文名 else "未知"
            用途 = 软件包.用途 if 软件包.用途 else "暂无说明"
            合并文本 = f"{中文名}\n{用途}"
            项目 = QTableWidgetItem(合并文本)
            项目.setToolTip(f"中文名: {中文名}\n用途: {用途}")
            self.表格.setItem(行号, 1, 项目)

            # 列2: 版本
            self.表格.setItem(行号, 2, QTableWidgetItem(软件包.版本))

            # 列3: 可删除
            可删除文本 = "✓ 可删" if 软件包.可删除 == "是" else "✗ 不可"
            self.表格.setItem(行号, 3, QTableWidgetItem(可删除文本))

            # 列4: 卸载按钮
            按钮 = QPushButton("卸载")
            按钮.clicked.connect(partial(self.卸载请求.emit, 软件包.名称))
            self.表格.setCellWidget(行号, 4, 按钮)

    def 显示进度条(self):
        """显示进度条"""
        self.进度条.setVisible(True)
        self.进度条.setValue(0)

    def 隐藏进度条(self):
        """隐藏进度条"""
        self.进度条.setVisible(False)

    def 复制未描述包名(self):
        """复制所有未描述的包名到剪贴板"""
        if not self.包管理器:
            QMessageBox.warning(self, "警告", "包管理器未初始化")
            return

        # 获取所有已安装的软件包
        所有软件包 = self.包管理器.获取已安装()

        # 获取软件包描述字典
        软件包描述 = self.包管理器.软件包描述

        # 找出未描述的包名
        未描述包名 = []
        for pkg in 所有软件包:
            if pkg.名称 not in 软件包描述:
                未描述包名.append(pkg.名称)

        if not 未描述包名:
            QMessageBox.information(self, "提示", "所有软件包都已描述！")
            return

        # 复制到剪贴板
        文本 = '\n'.join(未描述包名)
        剪贴板 = QApplication.clipboard()
        剪贴板.setText(文本)

        # 显示成功消息
        QMessageBox.information(
            self,
            "✓ 复制成功",
            f"已复制 {len(未描述包名)} 个未描述的包名到剪贴板\n\n"
            f"前10个:\n" + '\n'.join(未描述包名[:10]) +
            (f"\n... 还有 {len(未描述包名) - 10} 个" if len(未描述包名) > 10 else "")
        )


