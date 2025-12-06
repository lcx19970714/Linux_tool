"""
标签页组件
"""

from functools import partial
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QLabel, QComboBox,
    QMessageBox, QCheckBox, QGroupBox, QFrame, QApplication
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QClipboard, QFont, QColor


class 软件标签页(QWidget):
    """软件管理标签页 - 支持筛选、搜索和管理"""

    搜索请求 = Signal(str)
    刷新请求 = Signal()
    安装请求 = Signal(str)
    卸载请求 = Signal(str)
    获取未描述包名 = Signal()

    def __init__(self):
        super().__init__()
        self.工作线程 = None
        self.所有软件包 = []
        self.过滤后软件包 = []
        self.当前模式 = "已安装"  # "已安装" 或 "可用"
        self.包管理器 = None
        self.筛选状态 = {
            "显示系统包": False,
            "显示用户包": True,
            "显示依赖库": False,
            "只显示可删除": False
        }
        self.初始化界面()

    def 初始化界面(self):
        """初始化UI"""
        布局 = QVBoxLayout(self)

        # 筛选区域（仅在已安装模式下显示）
        self.筛选区域 = self.创建筛选区域()
        布局.addWidget(self.筛选区域)

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
        self.搜索框.setPlaceholderText("输入软件包名称、中文名或用途...")
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
        self.表格.setHorizontalHeaderLabels(["软件名", "类型", "用途说明", "重要性", "操作"])

        # 设置列宽度
        self.表格.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.表格.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.表格.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.表格.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.表格.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        # 设置行高自适应
        self.表格.verticalHeader().setDefaultSectionSize(50)
        self.表格.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # 设置表格属性
        self.表格.setAlternatingRowColors(True)
        self.表格.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.表格.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.表格.setSortingEnabled(True)

        布局.addWidget(self.表格)

        # 默认隐藏筛选区域
        self.筛选区域.setVisible(False)

    def 创建筛选区域(self):
        """创建筛选区域"""
        分组框 = QGroupBox("🔍 快速筛选")
        分组框.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        筛选布局 = QVBoxLayout(分组框)

        # 第一行筛选选项
        行1布局 = QHBoxLayout()

        # 创建复选框
        self.显示用户包框 = QCheckBox("🟢 用户软件")
        self.显示用户包框.setChecked(True)
        self.显示用户包框.stateChanged.connect(self.应用筛选)
        行1布局.addWidget(self.显示用户包框)

        self.显示系统包框 = QCheckBox("🔧 系统工具")
        self.显示系统包框.stateChanged.connect(self.应用筛选)
        行1布局.addWidget(self.显示系统包框)

        self.显示依赖库框 = QCheckBox("📦 依赖库")
        self.显示依赖库框.stateChanged.connect(self.应用筛选)
        行1布局.addWidget(self.显示依赖库框)

        行1布局.addStretch()
        筛选布局.addLayout(行1布局)

        # 第二行筛选选项
        行2布局 = QHBoxLayout()

        self.只显示可删除框 = QCheckBox("✅ 只显示可安全删除")
        self.只显示可删除框.stateChanged.connect(self.应用筛选)
        行2布局.addWidget(self.只显示可删除框)

        self.显示不可删除框 = QCheckBox("⚠️ 显示不可删除（高亮警告）")
        self.显示不可删除框.stateChanged.connect(self.应用筛选)
        行2布局.addWidget(self.显示不可删除框)

        # 清除筛选按钮
        清除按钮 = QPushButton("🔄 清除所有筛选")
        清除按钮.clicked.connect(self.清除筛选)
        行2布局.addWidget(清除按钮)

        行2布局.addStretch()
        筛选布局.addLayout(行2布局)

        # 提示文本
        提示标签 = QLabel("💡 提示：默认只显示用户安装的软件，避免误删系统组件")
        提示标签.setStyleSheet("color: #666; font-size: 12px;")
        筛选布局.addWidget(提示标签)

        return 分组框

    def 模式改变(self, 新模式):
        """模式改变时的处理"""
        self.当前模式 = 新模式
        self.搜索框.clear()

        if 新模式 == "可用":
            self.筛选区域.setVisible(False)
            self.搜索按钮.setVisible(True)
            self.搜索框.setPlaceholderText("输入软件包名称...")
            self.表格.setColumnCount(4)
            self.表格.setHorizontalHeaderLabels(["软件名", "版本", "状态", "操作"])
        else:
            self.筛选区域.setVisible(True)
            self.搜索按钮.setVisible(False)
            self.搜索框.setPlaceholderText("输入软件包名称、中文名或用途...")
            self.表格.setColumnCount(5)
            self.表格.setHorizontalHeaderLabels(["软件名", "类型", "用途说明", "重要性", "操作"])
            self.刷新按钮点击()

    def 搜索按钮点击(self):
        """搜索按钮点击"""
        关键词 = self.搜索框.text().strip()
        if 关键词:
            self.搜索请求.emit(关键词)

    def 搜索或过滤(self):
        """搜索或过滤"""
        if self.当前模式 == "已安装":
            self.应用筛选()
        # 可用模式下不自动搜索，需要点击搜索按钮

    def 应用筛选(self):
        """应用所有筛选条件"""
        if not self.所有软件包:
            return

        # 更新筛选状态
        self.筛选状态 = {
            "显示用户包": self.显示用户包框.isChecked(),
            "显示系统包": self.显示系统包框.isChecked(),
            "显示依赖库": self.显示依赖库框.isChecked(),
            "只显示可删除": self.只显示可删除框.isChecked(),
            "显示不可删除": self.显示不可删除框.isChecked()
        }

        # 应用筛选
        过滤结果 = self.筛选软件包(self.所有软件包)

        # 再应用搜索关键词
        关键词 = self.搜索框.text().lower()
        if 关键词:
            过滤结果 = [
                pkg for pkg in 过滤结果
                if 关键词 in pkg.名称.lower()
                or 关键词 in pkg.中文名.lower()
                or 关键词 in pkg.用途.lower()
            ]

        self.过滤后软件包 = 过滤结果
        self._更新表格显示(过滤结果)

    def _更新表格显示(self, 软件包列表):
        """更新表格显示（优化性能）"""
        self.表格.setRowCount(len(软件包列表))
        self.表格.setSortingEnabled(False)

        for 行号, 软件包 in enumerate(软件包列表):
            # 列0: 软件包名称
            名称项目 = QTableWidgetItem(软件包.名称)
            名称项目.setToolTip(f"完整名称: {软件包.名称}")
            self.表格.setItem(行号, 0, 名称项目)

            # 列1: 类型
            包类型 = self.判断包类型(软件包)
            类型图标 = self.获取类型图标(包类型)
            类型项目 = QTableWidgetItem(f"{类型图标} {包类型}")
            self.表格.setItem(行号, 1, 类型项目)

            # 列2: 用途说明
            中文名 = 软件包.中文名 if 软件包.中文名 else "未分类"
            用途 = 软件包.用途 if 软件包.用途 else "暂无说明"
            说明文本 = f"{中文名}\n{用途}"
            说明项目 = QTableWidgetItem(说明文本)
            说明项目.setToolTip(f"中文名: {中文名}\n用途: {用途}")
            self.表格.setItem(行号, 2, 说明项目)

            # 列3: 重要性
            重要性文本, 重要性颜色 = self.获取重要性显示(软件包)
            重要性项目 = QTableWidgetItem(重要性文本)
            if 重要性颜色:
                重要性项目.setBackground(重要性颜色)
            self.表格.setItem(行号, 3, 重要性项目)

            # 列4: 操作按钮
            按钮布局 = QHBoxLayout()
            按钮布局.setContentsMargins(2, 2, 2, 2)

            卸载按钮 = QPushButton("卸载")
            if 软件包.可删除 != "是":
                卸载按钮.setText("⚠️ 禁用")
                卸载按钮.setEnabled(False)
                卸载_button_style = """
                    QPushButton {
                        background-color: #f0f0f0;
                        color: #999;
                        border: 1px solid #ddd;
                    }
                    QPushButton:hover {
                        background-color: #e0e0e0;
                    }
                """
                卸载按钮.setStyleSheet(卸载_button_style)
            卸载按钮.clicked.connect(partial(self.确认卸载, 软件包))
            按钮布局.addWidget(卸载按钮)

            详情按钮 = QPushButton("详情")
            详情按钮.setMaximumWidth(50)
            详情按钮.clicked.connect(partial(self.显示软件详情, 软件包))
            按钮布局.addWidget(详情按钮)

            容器 = QWidget()
            容器.setLayout(按钮布局)
            self.表格.setCellWidget(行号, 4, 容器)

        # 重新启用排序
        self.表格.setSortingEnabled(True)

    def 筛选软件包(self, 软件包列表):
        """根据筛选条件过滤软件包"""
        结果 = []
        显示用户包 = self.显示用户包框.isChecked()
        显示系统包 = self.显示系统包框.isChecked()
        显示依赖库 = self.显示依赖库框.isChecked()
        只显示可删除 = self.只显示可删除框.isChecked()
        显示不可删除 = self.显示不可删除框.isChecked()

        for pkg in 软件包列表:
            # 判断软件包类型
            包类型 = self.判断包类型(pkg)

            # 根据类型筛选
            if 包类型 == "用户软件" and not 显示用户包:
                continue
            elif 包类型 == "系统工具" and not 显示系统包:
                continue
            elif 包类型 == "依赖库" and not 显示依赖库:
                continue

            # 可删除性筛选
            if 只显示可删除 and pkg.可删除 != "是":
                continue

            # 不可删除筛选
            if not 显示不可删除 and pkg.重要性 in ["关键", "高"] and pkg.可删除 != "是":
                continue

            结果.append(pkg)

        return 结果

    def 判断包类型(self, pkg):
        """判断软件包类型"""
        # 系统关键组件
        if pkg.重要性 in ["关键"] or not pkg.可删除:
            return "系统工具"

        # 依赖库（通常以lib、dev、devel等结尾）
        if any(pkg.名称.endswith(suffix) for suffix in ['-dev', '-devel', '-libs', '-lib', '-common']):
            return "依赖库"

        # 用户软件
        if pkg.中文名 or (pkg.用途 and "系统" not in pkg.用途):
            return "用户软件"

        # 默认归类为系统工具
        return "系统工具"

    def 清除筛选(self):
        """清除所有筛选条件"""
        self.显示用户包框.setChecked(True)
        self.显示系统包框.setChecked(False)
        self.显示依赖库框.setChecked(False)
        self.只显示可删除框.setChecked(False)
        self.显示不可删除框.setChecked(False)
        self.搜索框.clear()

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
        # 保存原始数据（只保存一次）
        if not hasattr(self, '_原始软件包列表'):
            self._原始软件包列表 = 软件包列表
        self.所有软件包 = self._原始软件包列表

        # 应用筛选
        self.应用筛选()

    def 获取类型图标(self, 包类型):
        """获取包类型图标"""
        图标映射 = {
            "用户软件": "🟢",
            "系统工具": "🔧",
            "依赖库": "📦"
        }
        return 图标映射.get(包类型, "❓")

    def 获取重要性显示(self, 软件包):
        """获取重要性显示文本和颜色"""
        if 软件包.重要性 == "关键":
            return "🔴 关键", QColor(255, 200, 200)
        elif 软件包.重要性 == "高":
            return "🟠 重要", QColor(255, 230, 200)
        elif 软件包.重要性 == "中":
            return "🔵 中等", QColor(200, 230, 255)
        elif 软件包.重要性 == "低":
            return "🟢 低", QColor(200, 255, 200)
        else:
            return "⚪ 未知", None

    def 确认卸载(self, 软件包):
        """确认卸载软件包"""
        if 软件包.可删除 != "是":
            QMessageBox.warning(
                self,
                "⚠️ 警告",
                f"软件包 {软件包.名称} 是系统关键组件，不能删除！\n\n"
                f"重要性: {软件包.重要性}\n"
                f"用途: {软件包.用途}"
            )
            return

        # 显示确认对话框
        回复 = QMessageBox.question(
            self,
            "🔍 确认卸载",
            f"确定要卸载以下软件包吗？\n\n"
            f"名称: {软件包.名称}\n"
            f"中文名: {软件包.中文名 or '无'}\n"
            f"用途: {软件包.用途 or '无'}\n\n"
            f"⚠️ 注意：卸载后可能影响其他软件的运行！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if 回复 == QMessageBox.StandardButton.Yes:
            self.卸载请求.emit(软件包.名称)

    def 显示软件详情(self, 软件包):
        """显示软件包详细信息"""
        详情文本 = f"""
        <h3>{软件包.名称}</h3>

        <p><b>中文名:</b> {软件包.中文名 or '未知'}</p>
        <p><b>版本:</b> {软件包.版本}</p>
        <p><b>类型:</b> {self.判断包类型(软件包)}</p>
        <p><b>重要性:</b> {软件包.重要性}</p>
        <p><b>可删除:</b> {'是' if 软件包.可删除 == '是' else '否'}</p>
        <p><b>用途:</b> {软件包.用途 or '暂无说明'}</p>

        <br><b>提示:</b>
        <ul>
            <li>用户软件: 用户自己安装的应用程序</li>
            <li>系统工具: 系统预装的工具和服务</li>
            <li>依赖库: 其他程序依赖的组件</li>
        </ul>
        """

        msg = QMessageBox()
        msg.setWindowTitle("软件包详情")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(详情文本)
        msg.exec()

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


