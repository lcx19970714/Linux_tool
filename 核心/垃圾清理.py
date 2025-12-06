"""
系统垃圾清理模块
"""

import shutil
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class 垃圾项:
    """垃圾文件项"""
    类型: str
    路径: str
    大小: int
    描述: str
    是否选中: bool = True


# 垃圾文件位置配置
垃圾位置配置 = {
    '用户缓存': [
        '~/.cache/*',
        '~/Cache/*',
    ],
    '临时文件': [
        '/tmp/*',
        '/var/tmp/*',
    ],
    '系统日志': [
        '~/.local/share/Trash/files/*',
        '~/.local/share/Trash/info/*',
    ],
    '软件包缓存': [
        '/var/cache/apt/archives/*.deb',
        '/var/cache/apt/archives/partial/*',
    ],
    '缩略图缓存': [
        '~/.cache/thumbnails/*',
    ],
    '其他垃圾': [
        '~/.local/share/recently-used.xbel',
        '~/.npm/_cacache/*',
        '~/.pip/cache/*',
    ],
}

# 关键路径前缀（不可删除）
关键路径前缀 = ('/usr', '/lib', '/bin', '/sbin', '/etc', '/boot/vmlinuz', '/boot/grub', '/proc', '/sys', '/dev')

# 关键文件名（不可删除）
关键文件名集合 = {'kernel', 'initrd', 'grub.cfg', 'fstab', 'passwd', 'shadow', 'group', 'sudoers', 'hosts', 'hostname'}


def 格式化大小(大小字节: int) -> str:
    """格式化文件大小"""
    if 大小字节 == 0:
        return "0 B"
    单位 = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    大小 = float(大小字节)
    while 大小 >= 1024 and i < len(单位) - 1:
        大小 /= 1024
        i += 1
    return f"{大小:.2f} {单位[i]}"


def 计算路径大小(路径: Path, 最大深度: int = 3) -> int:
    """计算文件或目录大小"""
    try:
        if 路径.is_file():
            return 路径.stat().st_size
        if not 路径.is_dir():
            return 0
    except (PermissionError, OSError):
        return 0

    总大小 = 0
    待处理 = [(路径, 0)]

    while 待处理:
        当前路径, 深度 = 待处理.pop()
        if 深度 > 最大深度:
            continue
        try:
            for 子项 in 当前路径.iterdir():
                try:
                    if 子项.is_file():
                        总大小 += 子项.stat().st_size
                    elif 子项.is_dir():
                        待处理.append((子项, 深度 + 1))
                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError):
            continue

    return 总大小


def 是否关键文件(文件路径: Path) -> bool:
    """检查是否为关键文件"""
    文件字符串 = str(文件路径)
    for 前缀 in 关键路径前缀:
        if 文件字符串.startswith(前缀):
            return True
    return 文件路径.name in 关键文件名集合


def 生成描述(类型: str, 文件路径: Path) -> str:
    """生成垃圾项描述"""
    基础描述 = {
        '用户缓存': '应用程序缓存文件',
        '临时文件': '临时文件',
        '系统日志': '系统日志文件',
        '软件包缓存': '软件包下载缓存',
        '缩略图缓存': '图片缩略图缓存',
        '其他垃圾': '其他垃圾文件'
    }
    return 基础描述.get(类型, '垃圾文件')


class 垃圾清理器:
    """系统垃圾清理器"""

    def __init__(self):
        self._已取消 = False

    def 取消扫描(self):
        """取消扫描"""
        self._已取消 = True

    def 扫描垃圾文件(self, 进度回调=None, 文件回调=None) -> list:
        """扫描垃圾文件"""
        self._已取消 = False
        结果列表 = []
        已见路径 = set()

        # 构建扫描任务列表
        任务列表 = []
        for 类型, 位置列表 in 垃圾位置配置.items():
            for 位置模式 in 位置列表:
                任务列表.append((类型, 位置模式))

        任务总数 = len(任务列表)

        for 索引, (类型, 位置模式) in enumerate(任务列表):
            if self._已取消:
                break

            if 进度回调:
                进度回调(int((索引 + 1) * 100 / 任务总数))

            # 展开路径
            展开路径 = Path(位置模式).expanduser()
            路径字符串 = str(展开路径)

            # 处理通配符
            if '*' in 路径字符串:
                父目录 = 展开路径.parent
                模式 = 展开路径.name
                if not 父目录.exists():
                    continue
                try:
                    匹配文件列表 = list(父目录.glob(模式))[:100]
                except (PermissionError, OSError):
                    continue
            else:
                匹配文件列表 = [展开路径] if 展开路径.exists() else []

            # 处理匹配的文件
            for 文件路径 in 匹配文件列表:
                if self._已取消:
                    break

                路径字符串 = str(文件路径)
                if 路径字符串 in 已见路径:
                    continue

                if not 文件路径.exists():
                    continue

                if 是否关键文件(文件路径):
                    continue

                大小 = 计算路径大小(文件路径)
                if 大小 <= 0:
                    continue

                已见路径.add(路径字符串)
                垃圾 = 垃圾项(
                    类型=类型,
                    路径=路径字符串,
                    大小=大小,
                    描述=生成描述(类型, 文件路径)
                )
                结果列表.append(垃圾)

                if 文件回调:
                    文件回调(垃圾)

        return 结果列表

    def 清理选中的垃圾(self, 垃圾列表: list, 进度回调=None) -> dict:
        """清理选中的垃圾文件"""
        选中列表 = [g for g in 垃圾列表 if g.是否选中]
        成功数 = 0
        失败数 = 0
        清理大小 = 0
        总数 = len(选中列表)

        for 索引, 垃圾 in enumerate(选中列表):
            if 进度回调:
                进度回调(int((索引 + 1) * 100 / max(总数, 1)))

            文件路径 = Path(垃圾.路径)
            try:
                if not 文件路径.exists():
                    continue
                清理大小 += 垃圾.大小
                if 文件路径.is_file():
                    文件路径.unlink()
                elif 文件路径.is_dir():
                    shutil.rmtree(文件路径)
                成功数 += 1
            except (PermissionError, OSError):
                失败数 += 1

        return {
            '成功': 成功数 > 0,
            '成功数': 成功数,
            '失败数': 失败数,
            '清理大小': 清理大小,
        }

    def 清空回收站(self) -> dict:
        """清空回收站"""
        回收站路径列表 = [
            Path.home() / '.local' / 'share' / 'Trash',
            Path.home() / '.Trash',
        ]

        清理大小 = 0
        成功 = False

        for 回收站 in 回收站路径列表:
            if not 回收站.exists():
                continue
            try:
                清理大小 += 计算路径大小(回收站)
                shutil.rmtree(回收站)
                回收站.mkdir(parents=True, exist_ok=True)
                成功 = True
            except (PermissionError, OSError):
                continue

        return {
            '成功': 成功,
            '清理大小': 清理大小,
        }

    def 格式化大小(self, 大小字节: int) -> str:
        """格式化文件大小（兼容旧接口）"""
        return 格式化大小(大小字节)
