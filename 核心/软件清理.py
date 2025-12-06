"""
软件清理模块 - 清理软件相关的配置文件、缓存、桌面图标等
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict


class 软件清理:
    """清理软件相关文件"""
    
    # 常见的配置文件位置
    配置位置 = [
        '~/.config',           # 应用配置
        '~/.local/share',      # 应用数据
        '~/.cache',            # 缓存文件
        '~/.local/bin',        # 本地二进制
        '~/.local/lib',        # 本地库文件
        '~/.desktop',          # 桌面文件
        '~/Desktop',           # 桌面目录
        '~/.local/share/applications',  # 桌面快捷方式
        '~/.local/share/icons',         # 图标
        '~/.local/share/pixmaps',       # 像素图
    ]
    
    @classmethod
    def 搜索相关文件(cls, 软件包名: str) -> Dict[str, List[str]]:
        """搜索软件相关的文件和目录"""
        结果 = {
            '配置文件': [],
            '缓存文件': [],
            '桌面图标': [],
            '其他文件': []
        }
        
        # 转换软件包名为可能的目录名
        可能的名称 = [
            软件包名,
            软件包名.replace('-', '_'),
            软件包名.replace('_', '-'),
            软件包名.lower(),
            软件包名.upper(),
        ]
        
        for 位置 in cls.配置位置:
            展开路径 = Path(位置).expanduser()
            if not 展开路径.exists():
                continue
            
            try:
                for 项 in 展开路径.rglob('*'):
                    if not 项.is_file():
                        continue
                    
                    项名 = 项.name.lower()
                    
                    # 检查是否与软件包相关
                    for 名称 in 可能的名称:
                        if 名称.lower() in 项名:
                            文件路径 = str(项)
                            
                            # 分类
                            if '.config' in 文件路径:
                                结果['配置文件'].append(文件路径)
                            elif '.cache' in 文件路径:
                                结果['缓存文件'].append(文件路径)
                            elif '.desktop' in 文件路径 or 'applications' in 文件路径:
                                结果['桌面图标'].append(文件路径)
                            else:
                                结果['其他文件'].append(文件路径)
                            break
            except PermissionError:
                continue
            except Exception:
                continue
        
        return 结果
    
    @classmethod
    def 清理文件(cls, 文件列表: List[str]) -> Dict:
        """清理指定的文件"""
        成功 = []
        失败 = []
        
        for 文件路径 in 文件列表:
            try:
                路径对象 = Path(文件路径)
                if 路径对象.exists():
                    if 路径对象.is_file():
                        路径对象.unlink()
                    elif 路径对象.is_dir():
                        import shutil
                        shutil.rmtree(路径对象)
                    成功.append(文件路径)
            except Exception as e:
                失败.append(f"{文件路径}: {str(e)}")
        
        return {
            '成功': 成功,
            '失败': 失败
        }
    
    @classmethod
    def 清理软件(cls, 软件包名: str) -> Dict:
        """完整清理软件相关文件"""
        相关文件 = cls.搜索相关文件(软件包名)
        
        # 收集所有文件
        所有文件 = []
        for 文件列表 in 相关文件.values():
            所有文件.extend(文件列表)
        
        if not 所有文件:
            return {
                '成功': True,
                '消息': '✓ 没有找到相关的配置文件',
                '清理数量': 0
            }
        
        # 清理文件
        清理结果 = cls.清理文件(所有文件)
        
        成功数 = len(清理结果['成功'])
        失败数 = len(清理结果['失败'])
        
        消息 = f"✓ 清理完成\n"
        消息 += f"  配置文件: {len(相关文件['配置文件'])} 个\n"
        消息 += f"  缓存文件: {len(相关文件['缓存文件'])} 个\n"
        消息 += f"  桌面图标: {len(相关文件['桌面图标'])} 个\n"
        消息 += f"  其他文件: {len(相关文件['其他文件'])} 个\n"
        消息 += f"  成功删除: {成功数} 个"
        
        if 失败数 > 0:
            消息 += f"\n  删除失败: {失败数} 个"
        
        return {
            '成功': True,
            '消息': 消息,
            '清理数量': 成功数,
            '相关文件': 相关文件
        }

