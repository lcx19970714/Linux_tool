"""
应用配置管理模块
"""

import json
from pathlib import Path


class 配置:
    """应用配置管理"""
    
    配置目录 = Path.home() / '.config' / 'linux_package_manager'
    配置文件 = 配置目录 / 'config.json'
    
    默认配置 = {
        '窗口宽度': 1000,
        '窗口高度': 600,
        '搜索限制': 20,
        '已安装限制': 50,
        '自动刷新': False,
        '刷新间隔': 300,
        '主题': 'light',
    }
    
    def __init__(self):
        self.配置数据 = self.加载配置()
    
    @classmethod
    def 确保配置目录(cls):
        """确保配置目录存在"""
        cls.配置目录.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def 加载配置(cls):
        """加载配置"""
        cls.确保配置目录()
        
        if cls.配置文件.exists():
            try:
                with open(cls.配置文件, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置失败: {e}，使用默认配置")
                return cls.默认配置.copy()
        
        return cls.默认配置.copy()
    
    def 保存配置(self):
        """保存配置"""
        self.确保配置目录()
        try:
            with open(self.配置文件, 'w', encoding='utf-8') as f:
                json.dump(self.配置数据, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def 获取(self, 键, 默认值=None):
        """获取配置值"""
        return self.配置数据.get(键, 默认值)
    
    def 设置(self, 键, 值):
        """设置配置值"""
        self.配置数据[键] = 值
        self.保存配置()
    
    def 获取全部(self):
        """获取所有配置"""
        return self.配置数据.copy()


# 全局配置实例
配置 = 配置()

