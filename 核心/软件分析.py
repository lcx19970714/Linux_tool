"""
软件分析模块 - 分析已安装软件，找出可删除的软件
"""

import subprocess
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from pathlib import Path


@dataclass
class 可清理软件:
    """可清理的软件项"""
    名称: str
    大小: int  # 字节
    类型: str  # apt/snap/flatpak/内核/缓存/孤立包
    描述: str
    建议: str  # 删除建议
    风险等级: str  # 低/中/高
    是否选中: bool = False
    删除命令: str = ""


def 格式化大小(字节数: int) -> str:
    """格式化文件大小"""
    if 字节数 == 0:
        return "0 B"
    单位 = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    大小 = float(字节数)
    while 大小 >= 1024 and i < len(单位) - 1:
        大小 /= 1024
        i += 1
    return f"{大小:.1f} {单位[i]}"


# 常见可删除软件分类
可删除软件分类 = {
    '浏览器': ['firefox', 'chromium', 'google-chrome', 'microsoft-edge', 'brave-browser', 'vivaldi', 'opera'],
    '办公套件': ['libreoffice', 'wps-office', 'onlyoffice'],
    '媒体播放器': ['rhythmbox', 'totem', 'vlc', 'audacious', 'celluloid'],
    '光盘刻录': ['brasero', 'k3b', 'xfburn'],
    '远程桌面': ['remmina', 'vinagre', 'krdc'],
    '扫描软件': ['simple-scan', 'xsane', 'skanlite'],
    '游戏相关': ['gnome-games', 'aisleriot', 'gnome-mines', 'gnome-sudoku', 'gnome-mahjongg', 'lutris', 'steam'],
    '聊天软件': ['wechat', 'bytedance-feishu', 'telegram', 'discord', 'slack'],
    '邮件客户端': ['thunderbird', 'evolution', 'geary'],
    '下载工具': ['transmission', 'qbittorrent', 'deluge'],
}


class 软件分析器:
    """软件分析器 - 分析系统中可清理的软件"""

    def __init__(self):
        self._已取消 = False
        self.当前内核 = self._获取当前内核版本()

    def 取消分析(self):
        """取消分析"""
        self._已取消 = True

    def _获取当前内核版本(self) -> str:
        """获取当前运行的内核版本"""
        try:
            结果 = subprocess.run(['uname', '-r'], capture_output=True, text=True, timeout=5)
            return 结果.stdout.strip().replace('-generic', '')
        except Exception:
            return ""

    def _执行命令(self, 命令: List[str], 超时: int = 30) -> Optional[str]:
        """执行命令并返回输出"""
        try:
            结果 = subprocess.run(命令, capture_output=True, text=True, timeout=超时)
            return 结果.stdout
        except Exception:
            return None

    def 分析全部(self, 进度回调: Callable[[int, str], None] = None) -> List[可清理软件]:
        """执行全面分析"""
        self._已取消 = False
        结果列表 = []
        
        分析任务 = [
            (self.分析大型apt包, "分析APT大型软件包..."),
            (self.分析snap包, "分析Snap软件包..."),
            (self.分析flatpak包, "分析Flatpak软件包..."),
            (self.分析旧内核, "分析旧内核..."),
            (self.分析apt缓存, "分析APT缓存..."),
            (self.分析孤立包, "分析孤立包..."),
            (self.分析重复软件, "分析重复软件..."),
        ]
        
        总数 = len(分析任务)
        for 索引, (任务函数, 描述) in enumerate(分析任务):
            if self._已取消:
                break
            
            if 进度回调:
                进度回调(int((索引 / 总数) * 100), 描述)
            
            try:
                结果列表.extend(任务函数())
            except Exception as e:
                print(f"分析任务失败: {描述}, 错误: {e}")
        
        if 进度回调:
            进度回调(100, "分析完成")
        
        # 按大小排序
        结果列表.sort(key=lambda x: x.大小, reverse=True)
        return 结果列表

    def 分析大型apt包(self, 最小大小MB: int = 50) -> List[可清理软件]:
        """分析大型APT软件包"""
        结果 = []
        最小字节 = 最小大小MB * 1024 * 1024
        
        输出 = self._执行命令([
            'dpkg-query', '-W', 
            '--showformat=${Installed-Size}\t${Package}\t${Status}\n'
        ])
        
        if not 输出:
            return 结果
        
        for 行 in 输出.strip().split('\n'):
            if self._已取消:
                break
            
            if 'install ok installed' not in 行:
                continue
            
            部分 = 行.split('\t')
            if len(部分) < 2:
                continue
            
            try:
                大小KB = int(部分[0])
                大小字节 = 大小KB * 1024
                包名 = 部分[1]
                
                if 大小字节 < 最小字节:
                    continue
                
                # 判断软件类型和建议
                类型标签, 建议, 风险 = self._分析包类型(包名)
                
                结果.append(可清理软件(
                    名称=包名,
                    大小=大小字节,
                    类型='apt',
                    描述=f"{类型标签} ({格式化大小(大小字节)})",
                    建议=建议,
                    风险等级=风险,
                    删除命令=f"sudo apt remove --purge {包名}"
                ))
            except (ValueError, IndexError):
                continue
        
        return 结果

    def _分析包类型(self, 包名: str) -> tuple:
        """分析软件包类型，返回(类型标签, 建议, 风险等级)"""
        包名小写 = 包名.lower()
        
        for 类型, 关键词列表 in 可删除软件分类.items():
            for 关键词 in 关键词列表:
                if 关键词 in 包名小写:
                    return (类型, f"可选的{类型}软件，不使用可删除", "低")
        
        # 系统关键包
        关键词 = ['linux-image', 'linux-headers', 'grub', 'systemd', 'kernel', 'base-']
        for 词 in 关键词:
            if 词 in 包名小写:
                return ("系统组件", "系统关键组件，谨慎删除", "高")
        
        # 开发相关
        if any(x in 包名小写 for x in ['-dev', '-devel', 'build-essential']):
            return ("开发工具", "开发依赖，不开发可删除", "中")
        
        # 库文件
        if 包名小写.startswith('lib'):
            return ("系统库", "可能被其他软件依赖", "中")
        
        return ("应用软件", "可根据使用情况决定", "低")

    def 分析snap包(self) -> List[可清理软件]:
        """分析Snap软件包"""
        结果 = []
        
        输出 = self._执行命令(['snap', 'list'])
        if not 输出:
            return 结果
        
        for 行 in 输出.strip().split('\n')[1:]:  # 跳过标题行
            if self._已取消:
                break
            
            部分 = 行.split()
            if len(部分) < 2:
                continue
            
            名称 = 部分[0]
            
            # 跳过系统核心snap
            if 名称 in ['bare', 'core', 'core18', 'core20', 'core22', 'snapd', 'gnome-3-28-1804', 'gtk-common-themes']:
                continue
            
            # 获取snap大小
            大小 = self._获取snap大小(名称)
            
            结果.append(可清理软件(
                名称=名称,
                大小=大小,
                类型='snap',
                描述=f"Snap应用 ({格式化大小(大小)})",
                建议="Snap应用，不使用可删除以节省空间",
                风险等级="低",
                删除命令=f"sudo snap remove {名称}"
            ))
        
        return 结果

    def _获取snap大小(self, 名称: str) -> int:
        """获取Snap包大小"""
        snap_path = Path(f"/snap/{名称}")
        if not snap_path.exists():
            return 0
        
        总大小 = 0
        try:
            for 文件 in snap_path.rglob('*'):
                if 文件.is_file():
                    try:
                        总大小 += 文件.stat().st_size
                    except (PermissionError, OSError):
                        pass
        except (PermissionError, OSError):
            pass
        
        return 总大小

    def 分析flatpak包(self) -> List[可清理软件]:
        """分析Flatpak软件包"""
        结果 = []
        
        输出 = self._执行命令(['flatpak', 'list', '--app', '--columns=name,application,size'])
        if not 输出:
            return 结果
        
        for 行 in 输出.strip().split('\n'):
            if self._已取消:
                break
            
            部分 = 行.split('\t')
            if len(部分) < 2:
                continue
            
            名称 = 部分[0]
            应用ID = 部分[1] if len(部分) > 1 else 名称
            
            # 解析大小
            大小 = 0
            if len(部分) > 2:
                大小文本 = 部分[2].strip()
                大小 = self._解析大小文本(大小文本)
            
            结果.append(可清理软件(
                名称=名称,
                大小=大小,
                类型='flatpak',
                描述=f"Flatpak应用 ({应用ID})",
                建议="Flatpak应用，不使用可删除",
                风险等级="低",
                删除命令=f"flatpak uninstall {应用ID}"
            ))
        
        return 结果

    def _解析大小文本(self, 文本: str) -> int:
        """解析大小文本为字节"""
        文本 = 文本.strip().upper()
        if not 文本:
            return 0
        
        单位映射 = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
        
        for 单位, 乘数 in 单位映射.items():
            if 单位 in 文本:
                try:
                    数值 = float(文本.replace(单位, '').strip())
                    return int(数值 * 乘数)
                except ValueError:
                    return 0
        
        return 0

    def 分析旧内核(self) -> List[可清理软件]:
        """分析旧内核"""
        结果 = []
        
        if not self.当前内核:
            return 结果
        
        输出 = self._执行命令(['dpkg', '-l'])
        if not 输出:
            return 结果
        
        已找到内核 = set()
        
        for 行 in 输出.strip().split('\n'):
            if self._已取消:
                break
            
            if not 行.startswith('ii'):
                continue
            
            部分 = 行.split()
            if len(部分) < 3:
                continue
            
            包名 = 部分[1]
            
            # 查找内核相关包
            if 'linux-image-' in 包名 or 'linux-modules-' in 包名 or 'linux-headers-' in 包名:
                # 排除当前内核
                if self.当前内核 in 包名:
                    continue
                
                # 排除meta包
                if 包名 in ['linux-image-generic', 'linux-headers-generic', 'linux-modules-extra-generic']:
                    continue
                
                # 提取版本号
                版本 = self._提取内核版本(包名)
                if not 版本 or 版本 in 已找到内核:
                    continue
                
                已找到内核.add(版本)
                
                # 获取大小
                大小输出 = self._执行命令([
                    'dpkg-query', '-W', '-f=${Installed-Size}', 包名
                ])
                大小 = int(大小输出.strip()) * 1024 if 大小输出 else 0
                
                结果.append(可清理软件(
                    名称=f"旧内核 {版本}",
                    大小=大小,
                    类型='内核',
                    描述=f"旧版本内核 (当前: {self.当前内核})",
                    建议="旧内核可安全删除，建议保留一个备用",
                    风险等级="中",
                    删除命令=f"sudo apt remove --purge linux-*-{版本}*"
                ))
        
        return 结果

    def _提取内核版本(self, 包名: str) -> str:
        """从包名中提取内核版本"""
        import re
        匹配 = re.search(r'(\d+\.\d+\.\d+-\d+)', 包名)
        return 匹配.group(1) if 匹配 else ""

    def 分析apt缓存(self) -> List[可清理软件]:
        """分析APT缓存"""
        结果 = []
        
        缓存路径 = Path('/var/cache/apt/archives')
        if not 缓存路径.exists():
            return 结果
        
        总大小 = 0
        文件数 = 0
        
        try:
            for 文件 in 缓存路径.glob('*.deb'):
                try:
                    总大小 += 文件.stat().st_size
                    文件数 += 1
                except (PermissionError, OSError):
                    pass
        except (PermissionError, OSError):
            pass
        
        if 总大小 > 0:
            结果.append(可清理软件(
                名称="APT下载缓存",
                大小=总大小,
                类型='缓存',
                描述=f"{文件数} 个deb包缓存",
                建议="可安全清理，不影响已安装软件",
                风险等级="低",
                删除命令="sudo apt clean"
            ))
        
        return 结果

    def 分析孤立包(self) -> List[可清理软件]:
        """分析孤立包（不再被依赖的包）"""
        结果 = []
        
        输出 = self._执行命令(['apt-get', 'autoremove', '--dry-run'])
        if not 输出:
            return 结果
        
        孤立包列表 = []
        for 行 in 输出.split('\n'):
            if 行.startswith('Remv '):
                包名 = 行.split()[1]
                孤立包列表.append(包名)
        
        if 孤立包列表:
            # 计算总大小
            总大小 = 0
            for 包名 in 孤立包列表[:50]:  # 限制数量避免太慢
                大小输出 = self._执行命令([
                    'dpkg-query', '-W', '-f=${Installed-Size}', 包名
                ])
                if 大小输出:
                    try:
                        总大小 += int(大小输出.strip()) * 1024
                    except ValueError:
                        pass
            
            结果.append(可清理软件(
                名称=f"孤立包 ({len(孤立包列表)}个)",
                大小=总大小,
                类型='孤立包',
                描述=f"不再被其他软件依赖的包: {', '.join(孤立包列表[:5])}{'...' if len(孤立包列表) > 5 else ''}",
                建议="可安全删除，这些包不再被任何软件依赖",
                风险等级="低",
                删除命令="sudo apt autoremove --purge"
            ))
        
        return 结果

    def 分析重复软件(self) -> List[可清理软件]:
        """分析重复类型的软件（如多个浏览器）"""
        结果 = []
        
        # 获取已安装的软件
        输出 = self._执行命令(['dpkg', '-l'])
        if not 输出:
            return 结果
        
        已安装包 = set()
        for 行 in 输出.split('\n'):
            if 行.startswith('ii'):
                部分 = 行.split()
                if len(部分) >= 2:
                    已安装包.add(部分[1].lower())
        
        # 检查每个分类中的重复软件
        重复检测 = {
            '浏览器': ['firefox', 'chromium-browser', 'google-chrome-stable', 'microsoft-edge-stable', 'brave-browser', 'vivaldi-stable'],
            '办公套件': ['libreoffice-core', 'wps-office'],
        }
        
        for 类型, 软件列表 in 重复检测.items():
            已安装 = [软件 for 软件 in 软件列表 if 软件 in 已安装包]
            
            if len(已安装) > 1:
                # 获取每个软件的大小
                for 软件 in 已安装[1:]:  # 保留第一个
                    大小输出 = self._执行命令([
                        'dpkg-query', '-W', '-f=${Installed-Size}', 软件
                    ])
                    大小 = int(大小输出.strip()) * 1024 if 大小输出 else 0
                    
                    结果.append(可清理软件(
                        名称=软件,
                        大小=大小,
                        类型='重复软件',
                        描述=f"重复的{类型} (已安装{len(已安装)}个)",
                        建议=f"您安装了多个{类型}，可以删除不常用的",
                        风险等级="低",
                        删除命令=f"sudo apt remove --purge {软件}"
                    ))
        
        return 结果

    def 执行清理(self, 软件: 可清理软件, 密码回调: Callable[[], str] = None) -> Dict:
        """执行清理操作"""
        if not 软件.删除命令:
            return {'成功': False, '消息': '没有删除命令'}
        
        try:
            # 对于需要sudo的命令，需要密码
            if 'sudo' in 软件.删除命令:
                if 密码回调:
                    密码 = 密码回调()
                    if not 密码:
                        return {'成功': False, '消息': '需要密码'}
                    
                    # 使用sudo执行
                    命令 = 软件.删除命令.replace('sudo ', '')
                    进程 = subprocess.Popen(
                        ['sudo', '-S'] + 命令.split(),
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = 进程.communicate(input=密码 + '\n', timeout=120)
                    
                    if 进程.returncode == 0:
                        return {'成功': True, '消息': f'成功删除 {软件.名称}'}
                    else:
                        return {'成功': False, '消息': f'删除失败: {stderr[:200]}'}
            else:
                结果 = subprocess.run(
                    软件.删除命令.split(),
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if 结果.returncode == 0:
                    return {'成功': True, '消息': f'成功删除 {软件.名称}'}
                else:
                    return {'成功': False, '消息': f'删除失败: {结果.stderr[:200]}'}
        except subprocess.TimeoutExpired:
            return {'成功': False, '消息': '操作超时'}
        except Exception as e:
            return {'成功': False, '消息': f'执行错误: {str(e)}'}
