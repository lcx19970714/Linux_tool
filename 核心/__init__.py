"""核心业务逻辑模块"""

from .数据模型 import 软件包, 进程
from .包管理器 import 包管理器
from .进程管理 import 进程管理器
from .进程说明 import 获取进程说明

__all__ = ['软件包', '进程', '包管理器', '进程管理器', '获取进程说明']

