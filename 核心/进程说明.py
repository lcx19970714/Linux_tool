"""
进程用途说明数据库
"""

# 常见进程的用途说明
进程说明数据库 = {
    # 系统核心
    'systemd': '系统和服务管理器',
    'init': '系统初始化进程',
    'kthreadd': '内核线程守护进程',
    'ksoftirqd': '内核软中断处理',
    'kworker': '内核工作队列',
    'migration': 'CPU迁移线程',
    'watchdog': '系统看门狗',
    'cpuhp': 'CPU热插拔',
    'kdevtmpfs': '设备文件系统',
    'netns': '网络命名空间',
    'khungtaskd': '检测挂起任务',
    'oom_reaper': '内存不足处理',
    'writeback': '磁盘写回',
    'kcompactd': '内存压缩',
    'ksmd': '内存去重',
    'khugepaged': '大页内存管理',
    'kswapd': '内存交换守护进程',
    'kintegrityd': '数据完整性检查',
    'kblockd': '块设备I/O',
    'blkcg_punt_bio': '块设备控制组',
    'tpm_dev_wq': 'TPM设备工作队列',
    'md': '软RAID管理',
    'edac-poller': '内存错误检测',
    'devfreq_wq': '设备频率调整',
    'kthrotld': 'I/O限流',
    'acpi_thermal_pm': 'ACPI温度管理',
    'scsi_eh': 'SCSI错误处理',
    'scsi_tmf': 'SCSI任务管理',
    'ipv6_addrconf': 'IPv6地址配置',
    'kstrp': '内核流解析器',
    
    # 桌面环境
    'gnome-shell': 'GNOME桌面环境',
    'gnome-session': 'GNOME会话管理',
    'gnome-settings-daemon': 'GNOME设置守护进程',
    'gsd-': 'GNOME设置守护进程',
    'nautilus': 'GNOME文件管理器',
    'gdm': 'GNOME显示管理器',
    'gdm3': 'GNOME显示管理器',
    'kde': 'KDE桌面环境',
    'plasma': 'KDE Plasma桌面',
    'kwin': 'KDE窗口管理器',
    'xfce': 'XFCE桌面环境',
    'xfwm4': 'XFCE窗口管理器',
    'mate': 'MATE桌面环境',
    'cinnamon': 'Cinnamon桌面环境',
    'lxde': 'LXDE桌面环境',
    
    # 显示服务
    'Xorg': 'X Window显示服务器',
    'X': 'X Window显示服务器',
    'wayland': 'Wayland显示服务器',
    'xwayland': 'X应用兼容层',
    
    # 网络
    'networkmanager': '网络连接管理',
    'wpa_supplicant': 'WiFi认证',
    'dhclient': 'DHCP客户端',
    'dhcpcd': 'DHCP客户端守护进程',
    'avahi-daemon': '本地网络服务发现',
    'dnsmasq': 'DNS和DHCP服务',
    'systemd-resolved': '系统DNS解析',
    'systemd-networkd': '系统网络管理',
    
    # 音频
    'pulseaudio': '音频服务器',
    'pipewire': '多媒体服务器',
    'wireplumber': 'PipeWire会话管理',
    'alsa': 'ALSA音频系统',
    
    # 蓝牙
    'bluetoothd': '蓝牙守护进程',
    'bluetooth': '蓝牙服务',
    
    # 打印
    'cupsd': '打印服务',
    'cups-browsed': '打印机发现服务',
    
    # 电源管理
    'upowerd': '电源管理守护进程',
    'thermald': '温度管理守护进程',
    'tlp': '笔记本电源优化',
    'laptop-mode': '笔记本省电模式',
    
    # 系统服务
    'systemd-journald': '系统日志服务',
    'systemd-logind': '登录管理',
    'systemd-udevd': '设备管理',
    'systemd-timesyncd': '时间同步',
    'rsyslogd': '系统日志守护进程',
    'cron': '定时任务调度',
    'crond': '定时任务守护进程',
    'atd': '一次性任务调度',
    'anacron': '非24小时运行系统的定时任务',
    'dbus-daemon': 'D-Bus消息总线',
    'dbus': 'D-Bus消息总线',
    'polkitd': '权限管理',
    'accounts-daemon': '用户账户管理',
    'udisksd': '磁盘管理服务',
    'colord': '色彩管理',
    'packagekitd': '软件包管理服务',
    'snapd': 'Snap软件包管理',
    'fwupd': '固件更新服务',
    
    # 安全
    'apparmor': 'AppArmor安全模块',
    'aa-': 'AppArmor相关',
    'firewalld': '防火墙守护进程',
    'ufw': '简易防火墙',
    'fail2ban': '入侵防护',
    'aide': '文件完整性检查',
    
    # 虚拟化
    'libvirtd': '虚拟化管理',
    'virtlogd': '虚拟机日志',
    'qemu': 'QEMU虚拟机',
    'kvm': 'KVM虚拟化',
    'vboxdrv': 'VirtualBox驱动',
    'VBoxClient': 'VirtualBox客户端',
    'vmware': 'VMware虚拟化',
    'docker': 'Docker容器',
    'dockerd': 'Docker守护进程',
    'containerd': '容器运行时',
    'podman': 'Podman容器',
    
    # 开发工具
    'python': 'Python解释器',
    'python3': 'Python 3解释器',
    'node': 'Node.js运行时',
    'java': 'Java虚拟机',
    'code': 'VS Code编辑器',
    'vim': 'Vim编辑器',
    'emacs': 'Emacs编辑器',
    'gedit': 'GNOME文本编辑器',
    'kate': 'KDE文本编辑器',
    
    # 浏览器
    'firefox': 'Firefox浏览器',
    'chrome': 'Chrome浏览器',
    'chromium': 'Chromium浏览器',
    'brave': 'Brave浏览器',
    'opera': 'Opera浏览器',
    'edge': 'Edge浏览器',
}


def 获取进程说明(进程名: str) -> str:
    """
    获取进程的用途说明
    
    Args:
        进程名: 进程名称
        
    Returns:
        进程用途说明，如果未知则返回空字符串
    """
    进程名小写 = 进程名.lower()
    
    # 精确匹配
    if 进程名小写 in 进程说明数据库:
        return 进程说明数据库[进程名小写]
    
    # 模糊匹配（前缀匹配）
    for 关键词, 说明 in 进程说明数据库.items():
        if 进程名小写.startswith(关键词):
            return 说明
    
    return ""

