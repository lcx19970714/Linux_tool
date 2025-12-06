"""
进程管理核心逻辑
"""

import subprocess
import psutil
from typing import List, Dict, Optional
from .数据模型 import 进程
from .密码管理 import 密码管理


class 进程管理器:
    """Linux进程管理器"""

    def __init__(self):
        """初始化进程管理器"""
        self.进程缓存 = []
        self.排序字段 = 'cpu使用率'
        self.排序倒序 = True
    
    def 获取所有进程(self, 排序字段: str = None, 倒序: bool = True) -> List[进程]:
        """
        获取所有运行中的进程
        
        Args:
            排序字段: 排序字段名 (cpu使用率, 内存使用率, pid, 名称)
            倒序: 是否倒序排列
        
        Returns:
            进程列表
        """
        进程列表 = []
        
        try:
            # 使用psutil获取所有进程
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 
                                            'memory_percent', 'memory_info', 'status', 
                                            'nice', 'cmdline', 'create_time']):
                try:
                    # 获取进程信息
                    信息 = proc.info
                    
                    # 计算内存使用量（MB）
                    内存字节 = 信息.get('memory_info').rss if 信息.get('memory_info') else 0
                    内存MB = 内存字节 / (1024 * 1024)
                    
                    # 格式化内存显示
                    if 内存MB >= 1024:
                        内存显示 = f"{内存MB / 1024:.1f} GB"
                    else:
                        内存显示 = f"{内存MB:.1f} MB"
                    
                    # 获取命令行
                    命令行列表 = 信息.get('cmdline', [])
                    命令行 = ' '.join(命令行列表) if 命令行列表 else 信息.get('name', '')
                    
                    # 格式化启动时间
                    创建时间 = 信息.get('create_time', 0)
                    if 创建时间:
                        from datetime import datetime
                        启动时间 = datetime.fromtimestamp(创建时间).strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        启动时间 = "未知"
                    
                    # 状态映射
                    状态映射 = {
                        'running': '运行中',
                        'sleeping': '睡眠',
                        'disk-sleep': '磁盘睡眠',
                        'stopped': '已停止',
                        'zombie': '僵尸',
                        'dead': '已死亡',
                        'tracing-stop': '跟踪停止',
                        'idle': '空闲'
                    }
                    状态 = 状态映射.get(信息.get('status', 'unknown'), '未知')
                    
                    # 创建进程对象
                    进程对象 = 进程(
                        pid=信息.get('pid', 0),
                        名称=信息.get('name', '未知'),
                        用户=信息.get('username', '未知'),
                        cpu使用率=round(信息.get('cpu_percent', 0.0), 1),
                        内存使用率=round(信息.get('memory_percent', 0.0), 1),
                        内存使用量=内存显示,
                        状态=状态,
                        优先级=信息.get('nice', 0),
                        命令行=命令行[:200],  # 限制长度
                        启动时间=启动时间
                    )
                    
                    进程列表.append(进程对象)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # 跳过无法访问的进程
                    continue
            
            # 排序
            if 排序字段:
                self.排序字段 = 排序字段
                self.排序倒序 = 倒序
            
            进程列表 = self._排序进程(进程列表, self.排序字段, self.排序倒序)
            
            # 更新缓存
            self.进程缓存 = 进程列表
            
            return 进程列表
            
        except Exception as e:
            print(f"获取进程列表失败: {e}")
            return []
    
    def _排序进程(self, 进程列表: List[进程], 字段: str, 倒序: bool) -> List[进程]:
        """排序进程列表"""
        排序映射 = {
            'cpu使用率': lambda p: p.cpu使用率,
            '内存使用率': lambda p: p.内存使用率,
            'pid': lambda p: p.pid,
            '名称': lambda p: p.名称.lower(),
            '用户': lambda p: p.用户.lower()
        }
        
        排序函数 = 排序映射.get(字段, lambda p: p.cpu使用率)
        return sorted(进程列表, key=排序函数, reverse=倒序)
    
    def 搜索进程(self, 关键词: str) -> List[进程]:
        """
        搜索进程

        Args:
            关键词: 搜索关键词（进程名、PID、用户名、命令行）

        Returns:
            匹配的进程列表
        """
        if not 关键词:
            return self.进程缓存

        关键词_小写 = 关键词.lower()
        结果 = []

        for proc in self.进程缓存:
            if (关键词_小写 in proc.名称.lower() or
                关键词_小写 in proc.用户.lower() or
                关键词_小写 in proc.命令行.lower() or
                关键词 == str(proc.pid)):
                结果.append(proc)

        return 结果

    def 终止进程(self, pid: int, 强制: bool = False, 密码: str = None) -> Dict:
        """
        终止进程

        Args:
            pid: 进程ID
            强制: 是否强制终止 (SIGKILL vs SIGTERM)
            密码: sudo密码（如果需要）

        Returns:
            操作结果字典
        """
        try:
            proc = psutil.Process(pid)
            进程名 = proc.name()

            # 检查是否需要sudo权限
            需要sudo = proc.username() != psutil.Process().username()

            if 需要sudo:
                # 需要sudo权限
                if not 密码:
                    if not 密码管理.读取密码():
                        return {'成功': False, '消息': '需要密码', '需要密码': True}
                    密码 = 密码管理.读取密码()

                # 验证密码
                if not 密码管理.验证密码(密码):
                    return {'成功': False, '消息': '❌ 密码错误'}

                密码管理.保存密码(密码)

                # 使用sudo终止进程
                信号 = '-9' if 强制 else '-15'
                命令 = ['kill', 信号, str(pid)]
                结果 = 密码管理.执行命令(命令)

                if 结果.returncode == 0:
                    return {'成功': True, '消息': f'✓ 进程 {进程名} (PID: {pid}) 已终止'}
                else:
                    return {'成功': False, '消息': f'❌ 终止失败: {结果.stderr}'}
            else:
                # 不需要sudo，直接终止
                if 强制:
                    proc.kill()  # SIGKILL
                else:
                    proc.terminate()  # SIGTERM

                # 等待进程结束
                try:
                    proc.wait(timeout=3)
                except psutil.TimeoutExpired:
                    pass

                return {'成功': True, '消息': f'✓ 进程 {进程名} (PID: {pid}) 已终止'}

        except psutil.NoSuchProcess:
            return {'成功': False, '消息': f'❌ 进程 {pid} 不存在'}
        except psutil.AccessDenied:
            return {'成功': False, '消息': f'❌ 权限不足，无法终止进程 {pid}', '需要密码': True}
        except ValueError as e:
            return {'成功': False, '消息': '需要密码', '需要密码': True}
        except Exception as e:
            return {'成功': False, '消息': f'❌ 终止进程失败: {str(e)}'}

    def 调整优先级(self, pid: int, 优先级: int, 密码: str = None) -> Dict:
        """
        调整进程优先级（nice值）

        Args:
            pid: 进程ID
            优先级: nice值 (-20到19，越小优先级越高)
            密码: sudo密码（降低nice值需要）

        Returns:
            操作结果字典
        """
        try:
            proc = psutil.Process(pid)
            进程名 = proc.name()
            当前优先级 = proc.nice()

            # 检查是否需要sudo（降低nice值需要root权限）
            需要sudo = 优先级 < 当前优先级

            if 需要sudo:
                if not 密码:
                    if not 密码管理.读取密码():
                        return {'成功': False, '消息': '需要密码', '需要密码': True}
                    密码 = 密码管理.读取密码()

                if not 密码管理.验证密码(密码):
                    return {'成功': False, '消息': '❌ 密码错误'}

                密码管理.保存密码(密码)

                # 使用renice命令
                命令 = ['renice', '-n', str(优先级), '-p', str(pid)]
                结果 = 密码管理.执行命令(命令)

                if 结果.returncode == 0:
                    return {'成功': True, '消息': f'✓ 进程 {进程名} (PID: {pid}) 优先级已调整为 {优先级}'}
                else:
                    return {'成功': False, '消息': f'❌ 调整失败: {结果.stderr}'}
            else:
                # 不需要sudo
                proc.nice(优先级)
                return {'成功': True, '消息': f'✓ 进程 {进程名} (PID: {pid}) 优先级已调整为 {优先级}'}

        except psutil.NoSuchProcess:
            return {'成功': False, '消息': f'❌ 进程 {pid} 不存在'}
        except psutil.AccessDenied:
            return {'成功': False, '消息': f'❌ 权限不足', '需要密码': True}
        except ValueError as e:
            return {'成功': False, '消息': '需要密码', '需要密码': True}
        except Exception as e:
            return {'成功': False, '消息': f'❌ 调整优先级失败: {str(e)}'}

    def 获取系统资源(self) -> Dict:
        """
        获取系统资源使用情况

        Returns:
            系统资源信息字典
        """
        try:
            # CPU使用率
            cpu使用率 = psutil.cpu_percent(interval=0.1)
            cpu核心数 = psutil.cpu_count()

            # 内存使用
            内存 = psutil.virtual_memory()
            内存使用率 = 内存.percent
            内存总量 = 内存.total / (1024 ** 3)  # GB
            内存已用 = 内存.used / (1024 ** 3)  # GB

            # 交换分区
            交换 = psutil.swap_memory()
            交换使用率 = 交换.percent

            # 系统负载
            负载 = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)

            return {
                'cpu使用率': cpu使用率,
                'cpu核心数': cpu核心数,
                '内存使用率': 内存使用率,
                '内存总量': f"{内存总量:.1f} GB",
                '内存已用': f"{内存已用:.1f} GB",
                '交换使用率': 交换使用率,
                '负载1分钟': round(负载[0], 2),
                '负载5分钟': round(负载[1], 2),
                '负载15分钟': round(负载[2], 2)
            }
        except Exception as e:
            print(f"获取系统资源失败: {e}")
            return {}

