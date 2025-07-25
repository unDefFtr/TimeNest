#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TimeNest 主应用入口
一个功能强大的跨平台课程表管理工具
"""

import sys
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTranslator, QLocale
from PyQt6.QtGui import QIcon

# 添加当前目录到 Python 路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from core.app_manager import AppManager
    from ui.system_tray import SystemTray, SystemTrayManager
    from ui.tray_features import TrayFeatureManager
    from ui.tray_status_monitor import TrayStatusManager
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有依赖已正确安装")
    sys.exit(1)


def setup_logging():
    """
    设置日志系统
    """
    # 创建日志目录
    log_dir = Path.home() / '.timenest' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 配置日志处理器
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_dir / 'timenest.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 设置第三方库的日志级别
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    return logging.getLogger('TimeNest')


def setup_application():
    """
    设置 QApplication
    """
    # 设置应用属性
    QApplication.setApplicationName('TimeNest')
    QApplication.setApplicationVersion('1.0.0')
    QApplication.setOrganizationName('TimeNest Team')
    QApplication.setOrganizationDomain('timenest.org')
    
    # 创建应用实例
    app = QApplication(sys.argv)
    
    # 设置应用图标
    icon_path = Path(__file__).parent / 'resources' / 'icons' / 'app.png'
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # 设置高DPI支持 (PyQt6 中高DPI缩放默认启用)
    try:
        # PyQt6 中只需要设置高DPI像素图
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # 如果属性不存在，说明是更新版本的PyQt6，可以忽略
        pass
    
    # 设置样式
    app.setStyle('Fusion')  # 使用 Fusion 样式以获得更好的跨平台一致性
    
    return app


def check_dependencies():
    """
    检查必要的依赖
    """
    missing_deps = []
    
    # 检查核心依赖
    try:
        import PyQt6
    except ImportError:
        missing_deps.append('PyQt6')
    
    try:
        import yaml
    except ImportError:
        missing_deps.append('PyYAML')
    
    try:
        import pandas
    except ImportError:
        missing_deps.append('pandas')
    
    if missing_deps:
        error_msg = f"缺少必要的依赖包:\n\n{', '.join(missing_deps)}\n\n请运行以下命令安装:\npip install {' '.join(missing_deps)}"
        print(error_msg)
        
        # 尝试显示图形化错误消息
        try:
            app = QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "TimeNest - 依赖错误",
                error_msg
            )
        except:
            pass
        
        return False
    
    return True


def create_directories():
    """
    创建必要的目录结构
    """
    base_dir = Path.home() / '.timenest'
    directories = [
        base_dir,
        base_dir / 'config',
        base_dir / 'schedules',
        base_dir / 'logs',
        base_dir / 'cache',
        base_dir / 'backups',
        base_dir / 'themes',
        base_dir / 'sounds',
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def _show_message(title: str, message: str):
    """显示信息对话框"""
    try:
        QMessageBox.information(None, f"TimeNest - {title}", message)
    except Exception as e:
        print(f"{title}: {message} (错误: {e})")


def create_tray_system(app_manager, logger):
    """创建完整的托盘系统"""
    try:
        # 检查系统托盘支持
        from PyQt6.QtWidgets import QSystemTrayIcon
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.error("系统托盘不可用")
            return None

        # 创建托盘管理器
        tray_manager = SystemTrayManager(
            floating_manager=app_manager.floating_manager
        )

        # 创建功能管理器
        feature_manager = TrayFeatureManager()

        # 创建状态监控器
        status_monitor = TrayStatusManager()

        # 设置信号连接
        setup_tray_connections(tray_manager, feature_manager, status_monitor, app_manager, logger)

        # 启动状态监控
        status_monitor.start_monitoring()

        logger.info("托盘系统组件创建完成")

        return {
            'tray_manager': tray_manager,
            'feature_manager': feature_manager,
            'status_monitor': status_monitor
        }

    except Exception as e:
        logger.error(f"创建托盘系统失败: {e}")
        return None


def setup_tray_connections(tray_manager, feature_manager, status_monitor, app_manager, logger):
    """设置托盘系统信号连接"""
    try:
        # 托盘管理器信号连接
        tray_manager.floating_toggled.connect(lambda visible: toggle_floating_widget(app_manager, visible, logger))
        tray_manager.floating_settings_requested.connect(feature_manager.show_floating_settings)
        tray_manager.schedule_module_requested.connect(feature_manager.show_schedule_management)
        tray_manager.settings_module_requested.connect(feature_manager.show_app_settings)
        tray_manager.plugins_module_requested.connect(feature_manager.show_plugin_marketplace)
        tray_manager.time_calibration_requested.connect(feature_manager.show_time_calibration)

        # 状态监控器信号连接
        status_monitor.alert_triggered.connect(lambda alert_type, message: handle_system_alert(app_manager, alert_type, message, logger))
        status_monitor.status_changed.connect(lambda status_type, status_data: update_tray_status(tray_manager, status_monitor, status_type, status_data))

        # 功能管理器信号连接
        feature_manager.notification_sent.connect(lambda title, message: send_tray_notification(app_manager, title, message, logger))

        logger.info("托盘系统信号连接完成")

    except Exception as e:
        logger.error(f"设置托盘信号连接失败: {e}")


def toggle_floating_widget(app_manager, visible, logger):
    """切换浮窗显示状态"""
    try:
        if app_manager.floating_manager:
            if visible:
                app_manager.floating_manager.show_widget()
            else:
                app_manager.floating_manager.hide_widget()
            logger.debug(f"浮窗状态切换: {visible}")
        else:
            logger.warning("浮窗管理器不可用")
    except Exception as e:
        logger.error(f"切换浮窗状态失败: {e}")


def handle_system_alert(app_manager, alert_type, message, logger):
    """处理系统警告"""
    try:
        # 发送通知
        if app_manager.notification_manager:
            app_manager.notification_manager.send_notification(
                title="系统警告",
                message=message,
                notification_type="warning",
                duration=5000
            )

        logger.warning(f"系统警告 [{alert_type}]: {message}")

    except Exception as e:
        logger.error(f"处理系统警告失败: {e}")


def update_tray_status(tray_manager, status_monitor, status_type, status_data):
    """更新托盘状态显示"""
    try:
        if status_type == 'system':
            # 更新托盘提示文本
            summary = status_monitor.get_status_summary()
            tray_manager.set_tooltip(f"TimeNest - {summary}")
    except Exception as e:
        pass  # 静默处理状态更新错误


def send_tray_notification(app_manager, title, message, logger):
    """发送托盘通知"""
    try:
        if app_manager.notification_manager:
            app_manager.notification_manager.send_notification(
                title=title,
                message=message,
                notification_type="info"
            )
    except Exception as e:
        logger.error(f"发送托盘通知失败: {e}")


def cleanup_tray_system(tray_system, logger):
    """清理托盘系统"""
    try:
        if 'status_monitor' in tray_system:
            tray_system['status_monitor'].cleanup()

        if 'feature_manager' in tray_system:
            tray_system['feature_manager'].cleanup()

        if 'tray_manager' in tray_system:
            tray_system['tray_manager'].cleanup()

        logger.info("托盘系统清理完成")

    except Exception as e:
        logger.error(f"清理托盘系统失败: {e}")

def main():
    """
    主函数
    """
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 创建必要目录
    create_directories()
    
    # 设置日志
    logger = setup_logging()
    logger.info("TimeNest 启动中...")
    
    try:
        # 创建应用
        app = setup_application()
        
        # 创建应用管理器
        app_manager = AppManager()
        
        # 初始化应用管理器
        if not app_manager.initialize():
            logger.error("应用管理器初始化失败")
            QMessageBox.critical(
                None,
                "TimeNest - 初始化错误",
                "应用初始化失败，请检查配置文件和权限设置。"
            )
            sys.exit(1)
        
        # 创建完整的托盘系统
        tray_system = create_tray_system(app_manager, logger)
        if not tray_system:
            logger.error("托盘系统创建失败")
            QMessageBox.critical(
                None,
                "TimeNest - 托盘错误",
                "系统托盘不可用或创建失败。"
            )
            sys.exit(1)

        # 连接退出信号
        tray_system['tray_manager'].quit_requested.connect(app.quit)
        logger.info("托盘系统初始化完成")

        # 设置应用退出策略 - 关闭最后一个窗口时不退出程序
        app.setQuitOnLastWindowClosed(False)

        # 启动智能浮窗系统
        floating_visible = False
        if app_manager.floating_manager:
            # 自动创建并显示智能浮窗
            if app_manager.floating_manager.create_widget():
                app_manager.floating_manager.show_widget()
                floating_visible = True
                logger.info("智能浮窗启动成功")
            else:
                logger.warning("智能浮窗启动失败")

        # 更新托盘状态
        if tray_system and floating_visible:
            tray_system['tray_manager'].update_floating_status(floating_visible)

        logger.info("系统托盘图标显示成功")

        logger.info("TimeNest 静默启动完成")
        
        # 运行应用
        exit_code = app.exec()
        
        # 清理资源
        logger.info("TimeNest 正在关闭...")

        # 清理托盘系统
        if tray_system:
            cleanup_tray_system(tray_system, logger)

        # 清理应用管理器
        app_manager.cleanup()
        logger.info("TimeNest 已关闭")
        
        sys.exit(exit_code)
        
    except Exception as e:
        logger.critical(f"启动失败: {e}", exc_info=True)
        
        try:
            QMessageBox.critical(
                None,
                "TimeNest - 启动错误",
                f"应用启动失败:\n\n{str(e)}\n\n请查看日志文件获取详细信息。"
            )
        except:
            print(f"启动失败: {e}")
        
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())