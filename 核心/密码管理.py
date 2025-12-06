"""
密码管理模块 - 处理 sudo 密码的保存和使用
"""

import json
import subprocess
from pathlib import Path
from cryptography.fernet import Fernet


class 密码管理:
    """管理 sudo 密码"""
    
    配置目录 = Path.home() / '.config' / 'linux_package_manager'
    密钥文件 = 配置目录 / '.key'
    密码文件 = 配置目录 / '.pwd'
    
    @classmethod
    def 初始化(cls):
        """初始化密钥"""
        cls.配置目录.mkdir(parents=True, exist_ok=True)
        
        if not cls.密钥文件.exists():
            密钥 = Fernet.generate_key()
            cls.密钥文件.write_bytes(密钥)
    
    @classmethod
    def 获取密钥(cls):
        """获取密钥"""
        cls.初始化()
        return cls.密钥文件.read_bytes()
    
    @classmethod
    def 保存密码(cls, 密码: str):
        """保存密码（加密）"""
        cls.初始化()
        密钥 = cls.获取密钥()
        cipher = Fernet(密钥)
        加密密码 = cipher.encrypt(密码.encode())
        cls.密码文件.write_bytes(加密密码)
    
    @classmethod
    def 读取密码(cls) -> str:
        """读取密码（解密）"""
        if not cls.密码文件.exists():
            return None
        
        try:
            密钥 = cls.获取密钥()
            cipher = Fernet(密钥)
            加密密码 = cls.密码文件.read_bytes()
            密码 = cipher.decrypt(加密密码).decode()
            return 密码
        except Exception:
            return None
    
    @classmethod
    def 清除密码(cls):
        """清除保存的密码"""
        if cls.密码文件.exists():
            cls.密码文件.unlink()
    
    @classmethod
    def 验证密码(cls, 密码: str) -> bool:
        """验证密码是否正确"""
        try:
            结果 = subprocess.run(
                ['sudo', '-S', 'true'],
                input=密码 + '\n',
                capture_output=True,
                text=True,
                timeout=5
            )
            return 结果.returncode == 0
        except Exception:
            return False
    
    @classmethod
    def 执行命令(cls, 命令列表: list, 密码: str = None) -> subprocess.CompletedProcess:
        """使用 sudo 执行命令"""
        if 密码 is None:
            密码 = cls.读取密码()
        
        if 密码 is None:
            raise ValueError("没有保存的密码，请先输入密码")
        
        try:
            结果 = subprocess.run(
                ['sudo', '-S'] + 命令列表,
                input=密码 + '\n',
                capture_output=True,
                text=True,
                timeout=60
            )
            return 结果
        except subprocess.TimeoutExpired:
            raise TimeoutError("命令执行超时")
        except Exception as e:
            raise Exception(f"执行命令失败: {str(e)}")

