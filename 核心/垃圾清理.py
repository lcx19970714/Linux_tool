"""
系统垃圾清理模块
清理临时文件、缓存、日志、回收站等垃圾文件
"""

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class 垃圾项:
    """垃圾文件项"""
    类型: str
    路径: str
    大小: int  # 字节
    描述: str
    是否选中: bool = True


class 垃圾清理器:
    """系统垃圾清理器"""

    # 常见的垃圾文件位置
    垃圾位置 = {
        '用户缓存': [
            '~/.cache/*',
            '~/.cache/**/*',
            '~/Cache/*',
            '~/.cache/mozilla/*',
            '~/.cache/google-chrome/*',
            '~/.cache/chromium/*',
            '~/.cache/vlc/*',
        ],
        '临时文件': [
            '/tmp/*',
            '/var/tmp/*',
            '/tmp/.X*',
            '/tmp/tmp.*',
            '~/.cache/tmp/*',
            '~/.cache/yay/*',
            '~/.cache/pacman/*',
        ],
        '系统日志': [
            '~/.local/share/Trash/files/*',
            '~/.local/share/Trash/info/*',
            '~/.local/share/Trash/metadata/*',
            '~/.cache/gnome-software/*',
            '~/.cache/software-center/*',
        ],
        '软件包缓存': [
            '/var/cache/apt/archives/*.deb',
            '/var/cache/apt/archives/partial/*',
            '/var/cache/yum/*',
            '/var/cache/dnf/*',
            '/var/cache/pacman/pkg/*',
            '~/.cache/apt/*',
            '~/.cache/snap/*',
        ],
        '旧内核文件': [
            '/boot/vmlinuz-*',
            '/boot/initrd.img-*',
            '/boot/config-*',
            '/boot/System.map-*',
        ],
        '缩略图缓存': [
            '~/.cache/thumbnails/*',
            '~/.cache/thumbnails/normal/*',
            '~/.cache/thumbnails/large/*',
            '~/.cache/thumbnails/fail/*',
        ],
        '其他垃圾': [
            '~/.local/share/recently-used.xbel',
            '~/.local/share/gvfs-metadata/*',
            '~/.local/share/Trash/*',
            '~/.lesshst',
            '~/.python_history',
            '~/.npm/_cacache/*',
            '~/.pip/cache/*',
            '~/.gradle/caches/*',
            '~/.m2/repository/*',
        ],
    }

    def __init__(self):
        self.扫描结果 = []
        self.扫描状态 = False

    def 计算文件大小(self, 路径: Path) -> int:
        """计算文件或目录大小"""
        try:
            if 路径.is_file():
                return 路径.stat().st_size
            elif 路径.is_dir():
                # 优化：限制递归深度，避免扫描过深
                总大小 = 0
                最大深度 = 3  # 限制递归深度

                def 递归计算(当前路径: Path, 当前深度: int):
                    nonlocal 总大小
                    if 当前深度 > 最大深度:
                        return

                    try:
                        for 子项 in 当前路径.iterdir():
                            try:
                                if 子项.is_file():
                                    总大小 += 子项.stat().st_size
                                elif 子项.is_dir():
                                    递归计算(子项, 当前深度 + 1)
                            except (PermissionError, OSError):
                                continue
                    except (PermissionError, OSError):
                        pass

                递归计算(路径, 0)
                return 总大小
        except (PermissionError, OSError):
            pass
        return 0

    def 格式化大小(self, 大小字节: int) -> str:
        """格式化文件大小"""
        if 大小字节 == 0:
            return "0 B"

        单位 = ['B', 'KB', 'MB', 'GB', 'TB']
        i = 0
        while 大小字节 >= 1024 and i < len(单位) - 1:
            大小字节 /= 1024
            i += 1

        return f"{大小字节:.2f} {单位[i]}"

    def 扫描垃圾文件(self, 进度回调=None, 文件回调=None) -> List[垃圾项]:
        """扫描垃圾文件"""
        self.扫描结果 = []
        self.扫描状态 = True

        # 先统计所有位置模式
        位置模式列表 = []
        for 类型, 位置列表 in self.垃圾位置.items():
            for 位置模式 in 位置列表:
                位置模式列表.append((类型, 位置模式))

        位置模式总数 = len(位置模式列表)
        当前模式进度 = 0

        # 第一阶段：扫描位置模式
        for 类型, 位置模式 in 位置模式列表:
            if not self.扫描状态:  # 如果扫描被取消
                return self.扫描结果

            # 更新模式扫描进度（0-50%）
            当前模式进度 += 1
            if 进度回调:
                进度回调(int(当前模式进度 * 50 / 位置模式总数))

            try:
                展开路径 = Path(位置模式).expanduser()

                # 如果包含通配符，使用glob
                if '*' in 位置模式 or '**' in 位置模式:
                    # 处理相对路径中的通配符
                    if str(展开路径).startswith('~'):
                        展开路径 = Path(str(展开路径).replace('~', str(Path.home()), 1))

                    路径部分 = 展开路径.parent
                    模式 = 展开路径.name

                    if not 路径部分.exists():
                        continue

                    # 限制通配符匹配数量，避免过多文件
                    try:
                        匹配文件 = list(路径部分.glob(模式))
                        # 处理**通配符，但限制深度
                        if '**' in 位置模式:
                            # 限制递归深度为2
                            for 根路径 in 路径部分.rglob('*'):
                                if 根路径.is_dir():
                                    for 文件 in 根路径.glob(模式.split('/')[-1]):
                                        匹配文件.append(文件)
                    except Exception:
                        continue

                    # 限制每个模式最多匹配100个文件
                    匹配文件 = 匹配文件[:100]
                else:
                    匹配文件 = [展开路径] if 展开路径.exists() else []

                # 扫描文件并实时处理
                for 文件路径 in 匹配文件:
                    if not self.扫描状态:
                        return self.扫描结果

                    try:
                        if 文件路径.exists() and not self.是否关键文件(文件路径):
                            大小 = self.计算文件大小(文件路径)
                            if 大小 > 0:
                                垃圾 = 垃圾项(
                                    类型=类型,
                                    路径=str(文件路径),
                                    大小=大小,
                                    描述=self.生成描述(类型, 文件路径)
                                )
                                self.扫描结果.append(垃圾)
                                # 实时回调
                                if 文件回调:
                                    文件回调(垃圾)
                    except (PermissionError, OSError):
                        continue

            except Exception as e:
                print(f"扫描 {位置模式} 时出错: {e}")
                continue

        # 去重（相同路径可能被多次扫描）
        去重结果 = []
        已见路径 = set()
        for 垃圾 in self.扫描结果:
            if 垃圾.路径 not in 已见路径:
                去重结果.append(垃圾)
                已见路径.add(垃圾.路径)

        self.扫描结果 = 去重结果

        # 扫描完成，进度到100%
        if 进度回调:
            进度回调(100)

        return self.扫描结果

    def 是否关键文件(self, 文件路径: Path) -> bool:
        """检查是否为关键文件"""
        关键路径 = [
            '/usr', '/lib', '/bin', '/sbin', '/etc', '/boot/vmlinuz',
            '/boot/grub', '/proc', '/sys', '/dev'
        ]

        文件字符串 = str(文件路径)
        for 路径 in 关键路径:
            if 文件字符串.startswith(路径):
                return True

        # 检查关键文件名
        关键文件名 = [
            'kernel', 'initrd', 'grub.cfg', 'fstab', 'passwd', 'shadow',
            'group', 'sudoers', 'hosts', 'hostname'
        ]

        if 文件路径.name in 关键文件名:
            return True

        return False

    def 生成描述(self, 类型: str, 文件路径: Path) -> str:
        """生成垃圾项描述"""
        基础描述 = {
            '用户缓存': '应用程序缓存文件',
            '临时文件': '临时文件',
            '系统日志': '系统日志文件',
            '软件包缓存': '软件包下载缓存',
            '旧内核文件': '旧的内核文件',
            '缩略图缓存': '图片缩略图缓存',
            '其他垃圾': '其他垃圾文件'
        }

        描述 = 基础描述.get(类型, '垃圾文件')

        # 添加具体信息
        if 文件路径.name.startswith('tmp'):
            描述 += f" ({文件路径.name})"
        elif 'cache' in 文件路径.name.lower():
            应用名 = 文件路径.parent.name if 文件路径.parent.name != 'cache' else '未知应用'
            if 应用名 and 应用名 != 'cache':
                描述 += f" ({应用名})"

        return 描述

    def 按类型分组(self, 垃圾列表: List[垃圾项]) -> Dict[str, Tuple[int, List[垃圾项]]]:
        """按类型分组垃圾文件"""
        分组 = {}

        for 垃圾 in 垃圾列表:
            if 垃圾.类型 not in 分组:
                分组[垃圾.类型] = [0, []]  # [总大小, 垃圾列表]

            分组[垃圾.类型][0] += 垃圾.大小
            分组[垃圾.类型][1].append(垃圾)

        return 分组

    def 清理选中的垃圾(self, 垃圾列表: List[垃圾项], 进度回调=None) -> Dict:
        """清理选中的垃圾文件"""
        成功文件 = []
        失败文件 = []
        总大小 = 0
        总数 = len([g for g in 垃圾列表 if g.是否选中])
        当前进度 = 0

        for 垃圾 in 垃圾列表:
            if not 垃圾.是否选中:
                continue

            # 更新进度
            当前进度 += 1
            if 进度回调:
                进度回调(int(当前进度 * 100 / 总数))

            try:
                文件路径 = Path(垃圾.路径)
                if 文件路径.exists():
                    # 记录大小
                    总大小 += 垃圾.大小

                    # 删除文件
                    if 文件路径.is_file():
                        文件路径.unlink()
                    elif 文件路径.is_dir():
                        shutil.rmtree(文件路径)

                    成功文件.append(垃圾.路径)

            except (PermissionError, OSError) as e:
                失败文件.append(f"{垃圾.路径}: {str(e)}")
            except Exception as e:
                失败文件.append(f"{垃圾.路径}: {str(e)}")

        # 返回清理结果
        结果 = {
            '成功': True if 成功文件 else False,
            '成功数': len(成功文件),
            '失败数': len(失败文件),
            '清理大小': 总大小,
            '成功文件': 成功文件,
            '失败文件': 失败文件
        }

        return 结果

    def 取消扫描(self):
        """取消扫描"""
        self.扫描状态 = False

    def 清空回收站(self) -> Dict:
        """清空回收站"""
        回收站路径 = [
            Path.home() / '.local' / 'share' / 'Trash',
            Path.home() / '.Trash',
        ]

        成功 = 0
        失败 = 0
        总大小 = 0

        for 回收站 in 回收站路径:
            if 回收站.exists():
                try:
                    # 计算大小
                    for 项 in 回收站.rglob('*'):
                        if 项.is_file():
                            总大小 += 项.stat().st_size

                    # 删除回收站内容
                    shutil.rmtree(回收站)
                    # 重新创建目录
                    回收站.mkdir(parents=True, exist_ok=True)
                    成功 += 1
                except Exception:
                    失败 += 1

        return {
            '成功': 成功 > 0,
            '清理大小': 总大小,
            '消息': f'清空回收站完成 (成功: {成功}, 失败: {失败})'
        }

    def 获取系统信息(self) -> Dict:
        """获取系统垃圾信息"""
        信息 = {
            '总垃圾大小': 0,
            '垃圾项数量': 0,
            '类型统计': {}
        }

        if self.扫描结果:
            分组 = self.按类型分组(self.扫描结果)

            for 类型, (大小, 列表) in 分组.items():
                信息['类型统计'][类型] = {
                    '大小': 大小,
                    '数量': len(列表),
                    '格式化大小': self.格式化大小(大小)
                }

            信息['总垃圾大小'] = sum(g.大小 for g in self.扫描结果)
            信息['垃圾项数量'] = len(self.扫描结果)

        return 信息