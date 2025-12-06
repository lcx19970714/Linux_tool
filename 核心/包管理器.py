"""
包管理器核心逻辑
"""

import subprocess
import json
from typing import List, Dict, Optional
from pathlib import Path
from .数据模型 import 软件包
from .密码管理 import 密码管理
from .软件清理 import 软件清理


class 包管理器:
    """Linux包管理器基类"""

    def __init__(self):
        self.管理器类型 = None
        self.软件包描述 = {}
        self.已安装缓存 = None
        self.可用缓存 = None
        self.检测管理器()
        self.加载软件包描述()
    
    def 加载软件包描述(self):
        """加载软件包描述映射"""
        try:
            描述文件 = Path(__file__).parent / '软件包描述.json'
            if 描述文件.exists():
                with open(描述文件, 'r', encoding='utf-8') as f:
                    self.软件包描述 = json.load(f)
        except Exception as e:
            print(f"加载软件包描述失败: {e}")

    def 获取软件包信息(self, 软件包名: str) -> Dict:
        """获取软件包的详细信息"""
        if 软件包名 in self.软件包描述:
            return self.软件包描述[软件包名]

        # 返回默认信息
        return {
            '描述': '暂无说明',
            '用途': '未知',
            '可删除': True,
            '重要性': '未知'
        }

    def 检测管理器(self):
        """检测系统使用的包管理器"""
        管理器列表 = {
            'apt': 'apt --version',
            'yum': 'yum --version',
            'dnf': 'dnf --version',
            'pacman': 'pacman --version',
            'zypper': 'zypper --version'
        }

        for 管理器, 命令 in 管理器列表.items():
            try:
                subprocess.run(命令.split(), capture_output=True, check=True, timeout=2)
                self.管理器类型 = 管理器
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
    
    def 获取所有可用(self) -> List[软件包]:
        """获取所有可用软件包（使用缓存）"""
        if self.可用缓存 is not None:
            return self.可用缓存

        if not self.管理器类型:
            return []

        if self.管理器类型 == 'apt':
            self.可用缓存 = self._获取所有apt()
        elif self.管理器类型 in ['yum', 'dnf']:
            self.可用缓存 = self._获取所有yum()
        elif self.管理器类型 == 'pacman':
            self.可用缓存 = self._获取所有pacman()
        else:
            self.可用缓存 = []

        return self.可用缓存

    def 搜索(self, 关键词: str) -> List[软件包]:
        """搜索软件包（从缓存中搜索）"""
        if not self.管理器类型:
            return []

        # 先获取所有可用软件包
        所有软件包 = self.获取所有可用()

        # 在本地过滤
        关键词_小写 = 关键词.lower()
        结果 = [
            pkg for pkg in 所有软件包
            if 关键词_小写 in pkg.名称.lower()
            or 关键词_小写 in pkg.版本.lower()
            or 关键词_小写 in pkg.描述.lower()
        ]

        return 结果[:50]  # 返回前50个结果
    
    def _获取所有apt(self) -> List[软件包]:
        """APT获取所有可用软件包"""
        try:
            结果 = subprocess.run(
                ['apt', 'search', ''],
                capture_output=True, text=True, timeout=30
            )
            软件包列表 = []
            for 行 in 结果.stdout.split('\n'):
                if '/' in 行:
                    部分 = 行.split('/')
                    if len(部分) >= 2:
                        名称 = 部分[0].strip()
                        if 名称:
                            软件包列表.append(软件包(
                                名称=名称,
                                版本='',
                                状态='可用'
                            ))
            return 软件包列表
        except Exception as e:
            print(f"获取所有可用软件包失败: {e}")
            return []
    
    def _获取所有yum(self) -> List[软件包]:
        """YUM/DNF获取所有可用软件包"""
        try:
            命令 = 'dnf' if self.管理器类型 == 'dnf' else 'yum'
            结果 = subprocess.run(
                [命令, 'list', 'available'],
                capture_output=True, text=True, timeout=30
            )
            软件包列表 = []
            for 行 in 结果.stdout.split('\n')[1:]:
                if 行.strip() and ':' in 行:
                    部分 = 行.split()
                    if len(部分) >= 2:
                        名称 = 部分[0].strip()
                        版本 = 部分[1] if len(部分) > 1 else ''
                        if 名称:
                            软件包列表.append(软件包(
                                名称=名称,
                                版本=版本,
                                状态='可用'
                            ))
            return 软件包列表
        except Exception as e:
            print(f"获取所有可用软件包失败: {e}")
            return []
    
    def _获取所有pacman(self) -> List[软件包]:
        """Pacman获取所有可用软件包"""
        try:
            结果 = subprocess.run(
                ['pacman', '-Ss', ''],
                capture_output=True, text=True, timeout=30
            )
            软件包列表 = []
            for 行 in 结果.stdout.split('\n'):
                if '/' in 行:
                    部分 = 行.split()
                    if len(部分) >= 2:
                        名称 = 部分[0].split('/')[-1]
                        版本 = 部分[1] if len(部分) > 1 else ''
                        if 名称:
                            软件包列表.append(软件包(
                                名称=名称,
                                版本=版本,
                                状态='可用'
                            ))
            return 软件包列表
        except Exception as e:
            print(f"获取所有可用软件包失败: {e}")
            return []
    
    def 获取已安装(self, 使用缓存=False) -> List[软件包]:
        """获取已安装的软件包"""
        # 如果使用缓存且缓存存在，直接返回
        if 使用缓存 and self.已安装缓存 is not None:
            return self.已安装缓存

        if not self.管理器类型:
            return []

        if self.管理器类型 == 'apt':
            结果 = self._获取已安装apt()
        elif self.管理器类型 in ['yum', 'dnf']:
            结果 = self._获取已安装yum()
        elif self.管理器类型 == 'pacman':
            结果 = self._获取已安装pacman()
        else:
            结果 = []

        # 更新缓存
        self.已安装缓存 = 结果
        return 结果
    
    def _获取已安装apt(self) -> List[软件包]:
        """获取APT已安装包"""
        try:
            结果 = subprocess.run(
                ['dpkg', '-l'],
                capture_output=True, text=True, timeout=10
            )
            软件包列表 = []
            # 预加载所有软件包信息以加快查询速度
            软件包描述 = self.软件包描述
            默认信息 = {
                '中文名': '',
                '用途': '',
                '可删除': True,
                '重要性': '未知'
            }

            for 行 in 结果.stdout.split('\n'):
                if 行.startswith('ii'):
                    部分 = 行.split()
                    if len(部分) >= 4:
                        软件包名 = 部分[1]
                        # 直接从字典查询，避免函数调用开销
                        信息 = 软件包描述.get(软件包名, 默认信息)
                        软件包列表.append(软件包(
                            名称=软件包名,
                            版本=部分[2],
                            状态='已安装',
                            中文名=信息.get('中文名', ''),
                            用途=信息.get('用途', ''),
                            可删除='是' if 信息.get('可删除', True) else '否',
                            重要性=信息.get('重要性', '未知')
                        ))
            return 软件包列表
        except Exception as e:
            print(f"获取已安装包失败: {e}")
            return []
    
    def _获取已安装yum(self) -> List[软件包]:
        """获取YUM/DNF已安装包"""
        try:
            命令 = 'dnf' if self.管理器类型 == 'dnf' else 'yum'
            结果 = subprocess.run(
                [命令, 'list', 'installed'],
                capture_output=True, text=True, timeout=10
            )
            软件包列表 = []
            # 预加载所有软件包信息以加快查询速度
            软件包描述 = self.软件包描述
            默认信息 = {
                '中文名': '',
                '用途': '',
                '可删除': True,
                '重要性': '未知'
            }

            for 行 in 结果.stdout.split('\n')[1:]:
                if 行.strip():
                    部分 = 行.split()
                    if len(部分) >= 2:
                        软件包名 = 部分[0]
                        # 直接从字典查询，避免函数调用开销
                        信息 = 软件包描述.get(软件包名, 默认信息)
                        软件包列表.append(软件包(
                            名称=软件包名,
                            版本=部分[1],
                            状态='已安装',
                            中文名=信息.get('中文名', ''),
                            用途=信息.get('用途', ''),
                            可删除='是' if 信息.get('可删除', True) else '否',
                            重要性=信息.get('重要性', '未知')
                        ))
            return 软件包列表
        except Exception as e:
            print(f"获取已安装包失败: {e}")
            return []
    
    def _获取已安装pacman(self) -> List[软件包]:
        """获取Pacman已安装包"""
        try:
            结果 = subprocess.run(
                ['pacman', '-Q'],
                capture_output=True, text=True, timeout=10
            )
            软件包列表 = []
            # 预加载所有软件包信息以加快查询速度
            软件包描述 = self.软件包描述
            默认信息 = {
                '中文名': '',
                '用途': '',
                '可删除': True,
                '重要性': '未知'
            }

            for 行 in 结果.stdout.split('\n'):
                if 行.strip():
                    部分 = 行.split()
                    if len(部分) >= 2:
                        软件包名 = 部分[0]
                        # 直接从字典查询，避免函数调用开销
                        信息 = 软件包描述.get(软件包名, 默认信息)
                        软件包列表.append(软件包(
                            名称=软件包名,
                            版本=部分[1],
                            状态='已安装',
                            中文名=信息.get('中文名', ''),
                            用途=信息.get('用途', ''),
                            可删除='是' if 信息.get('可删除', True) else '否',
                            重要性=信息.get('重要性', '未知')
                        ))
            return 软件包列表
        except Exception as e:
            print(f"获取已安装包失败: {e}")
            return []
    
    def 安装(self, 软件包名: str) -> bool:
        """安装软件包"""
        if not self.管理器类型:
            return False
        
        try:
            if self.管理器类型 == 'apt':
                subprocess.run(['sudo', 'apt', 'install', '-y', 软件包名], check=True)
            elif self.管理器类型 == 'yum':
                subprocess.run(['sudo', 'yum', 'install', '-y', 软件包名], check=True)
            elif self.管理器类型 == 'dnf':
                subprocess.run(['sudo', 'dnf', 'install', '-y', 软件包名], check=True)
            elif self.管理器类型 == 'pacman':
                subprocess.run(['sudo', 'pacman', '-S', '--noconfirm', 软件包名], check=True)
            return True
        except Exception as e:
            print(f"安装失败: {e}")
            return False
    
    def 卸载(self, 软件包名: str, 密码: str = None) -> Dict:
        """卸载软件包，返回详细结果"""
        if not self.管理器类型:
            return {'成功': False, '消息': '未检测到包管理器'}

        # 检查软件包是否可删除
        信息 = self.获取软件包信息(软件包名)
        if not 信息.get('可删除', True):
            return {
                '成功': False,
                '消息': f'❌ {软件包名} 是系统关键软件包，不能删除！\n\n重要性: {信息.get("重要性", "未知")}\n说明: {信息.get("说明", "系统核心，绝对不能删除")}'
            }

        try:
            # 获取卸载命令
            if self.管理器类型 == 'apt':
                命令 = ['apt', 'remove', '-y', 软件包名]
            elif self.管理器类型 == 'yum':
                命令 = ['yum', 'remove', '-y', 软件包名]
            elif self.管理器类型 == 'dnf':
                命令 = ['dnf', 'remove', '-y', 软件包名]
            elif self.管理器类型 == 'pacman':
                命令 = ['pacman', '-R', '--noconfirm', 软件包名]
            else:
                return {'成功': False, '消息': '不支持的包管理器'}

            # 使用密码管理执行命令
            if 密码:
                # 验证并保存密码
                if not 密码管理.验证密码(密码):
                    return {'成功': False, '消息': '❌ 密码错误'}
                密码管理.保存密码(密码)

            结果 = 密码管理.执行命令(命令)

            if 结果.returncode == 0:
                # 卸载成功，清理相关文件
                清理结果 = 软件清理.清理软件(软件包名)

                消息 = f'✓ {软件包名} 卸载成功\n\n'
                消息 += '清理相关文件:\n'
                消息 += 清理结果['消息']

                return {'成功': True, '消息': 消息}
            else:
                错误信息 = 结果.stderr if 结果.stderr else 结果.stdout
                return {'成功': False, '消息': f'❌ 卸载失败:\n{错误信息[:200]}'}

        except ValueError as e:
            # 需要输入密码
            return {'成功': False, '消息': '需要密码', '需要密码': True}
        except subprocess.TimeoutExpired:
            return {'成功': False, '消息': '❌ 卸载超时（超过60秒）'}
        except Exception as e:
            return {'成功': False, '消息': f'❌ 卸载出错: {str(e)[:100]}'}

