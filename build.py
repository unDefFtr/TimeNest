#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TimeNest 本地构建脚本
使用 Nuitka 将 TimeNest 打包为可执行文件

用法:
    python build.py [选项]

选项:
    --platform {windows,macos,linux,auto}  目标平台 (默认: auto)
    --onefile                              生成单文件可执行程序 (默认)
    --standalone                           生成独立目录
    --debug                                启用调试模式
    --output-dir DIR                       输出目录 (默认: dist)
    --version VERSION                      版本号
    --clean                                清理之前的构建
    --help                                 显示帮助信息
"""

import os
import sys
import argparse
import platform
import shutil
import subprocess
from pathlib import Path


def get_platform():
    """获取当前平台"""
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system == 'darwin':
        return 'macos'
    elif system == 'linux':
        return 'linux'
    else:
        raise ValueError(f"不支持的平台: {system}")


def check_dependencies():
    """检查构建依赖"""
    print("🔍 检查构建依赖...")
    
    # 检查 Python 版本
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要 Python 3.8 或更高版本")
        sys.exit(1)
    
    # 检查 Nuitka
    try:
        import nuitka
        print(f"✅ Nuitka: {nuitka.__version__}")
    except ImportError:
        print("❌ 错误: 未安装 Nuitka")
        print("请运行: pip install nuitka>=1.8.0")
        sys.exit(1)
    
    # 检查项目依赖
    try:
        import PyQt6
        print(f"✅ PyQt6: {PyQt6.QtCore.PYQT_VERSION_STR}")
    except ImportError:
        print("❌ 错误: 未安装 PyQt6")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)
    
    print("✅ 所有依赖检查通过")


def clean_build_dir(output_dir):
    """清理构建目录"""
    if output_dir.exists():
        print(f"🧹 清理构建目录: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def get_nuitka_args(args, platform_name, output_dir):
    """生成 Nuitka 构建参数"""
    project_root = Path.cwd()
    
    # 基础参数
    nuitka_args = [
        'python', '-m', 'nuitka',
        '--assume-yes-for-downloads',
        '--enable-plugin=pyqt6',
    ]
    
    # 构建模式
    if args.standalone:
        nuitka_args.append('--standalone')
    else:
        nuitka_args.append('--onefile')
    
    # 调试模式
    if args.debug:
        nuitka_args.extend([
            '--debug',
            '--enable-console',
        ])
    
    # 平台特定参数
    if platform_name == 'windows':
        if not args.debug:
            nuitka_args.append('--windows-console-mode=disable')
        
        # Windows 图标
        icon_path = project_root / 'resources' / 'icons' / 'tray_icon.png'
        if icon_path.exists():
            nuitka_args.append(f'--windows-icon-from-ico={icon_path}')
    
    elif platform_name == 'macos':
        nuitka_args.append('--macos-create-app-bundle')
        
        # macOS 图标
        icon_path = project_root / 'resources' / 'icons' / 'tray_icon.png'
        if icon_path.exists():
            nuitka_args.append(f'--macos-app-icon={icon_path}')
    
    elif platform_name == 'linux':
        # Linux 图标
        icon_path = project_root / 'resources' / 'icons' / 'tray_icon.png'
        if icon_path.exists():
            nuitka_args.append(f'--linux-icon={icon_path}')
    
    # 包含资源文件
    resources_dir = project_root / 'resources'
    if resources_dir.exists():
        nuitka_args.append(f'--include-data-dir={resources_dir}=resources')
    
    # 包含 Python 包
    packages = ['core', 'ui', 'components', 'models', 'utils', 'sdk']
    for package in packages:
        package_path = project_root / package
        if package_path.exists():
            nuitka_args.append(f'--include-package={package}')
    
    # 输出文件名
    version = args.version or 'dev'
    if platform_name == 'windows':
        output_name = f'TimeNest-{version}-Windows-x64.exe'
    elif platform_name == 'macos':
        output_name = f'TimeNest-{version}-macOS-x64'
    else:  # linux
        output_name = f'TimeNest-{version}-Linux-x64'
    
    nuitka_args.append(f'--output-filename={output_name}')
    
    # 输出目录
    nuitka_args.append(f'--output-dir={output_dir}')
    
    # 主文件
    nuitka_args.append('main.py')
    
    return nuitka_args


def build_executable(args):
    """构建可执行文件"""
    # 确定平台
    if args.platform == 'auto':
        platform_name = get_platform()
    else:
        platform_name = args.platform
    
    print(f"🏗️  开始构建 TimeNest ({platform_name})")
    
    # 检查依赖
    check_dependencies()
    
    # 准备输出目录
    output_dir = Path(args.output_dir)
    if args.clean:
        clean_build_dir(output_dir)
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成 Nuitka 参数
    nuitka_args = get_nuitka_args(args, platform_name, output_dir)
    
    print(f"📦 构建命令: {' '.join(nuitka_args)}")
    print("⏳ 开始编译（这可能需要几分钟）...")
    
    # 执行构建
    try:
        result = subprocess.run(nuitka_args, check=True, capture_output=True, text=True)
        print("✅ 构建成功!")
        
        # 显示构建产物
        print(f"\n📁 构建产物位于: {output_dir}")
        if output_dir.exists():
            for item in output_dir.iterdir():
                if item.is_file():
                    size = item.stat().st_size / (1024 * 1024)  # MB
                    print(f"  📄 {item.name} ({size:.1f} MB)")
                elif item.is_dir():
                    print(f"  📁 {item.name}/")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        if e.stdout:
            print(f"标准输出:\n{e.stdout}")
        if e.stderr:
            print(f"错误输出:\n{e.stderr}")
        return False
    except KeyboardInterrupt:
        print("\n⚠️  构建被用户中断")
        return False
    except Exception as e:
        print(f"❌ 构建过程中发生错误: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='TimeNest 本地构建脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python build.py                          # 自动检测平台，生成单文件
  python build.py --platform windows       # 为 Windows 构建
  python build.py --standalone              # 生成独立目录
  python build.py --debug                   # 启用调试模式
  python build.py --version v1.0.0         # 指定版本号
  python build.py --clean                   # 清理后构建
        """
    )
    
    parser.add_argument(
        '--platform',
        choices=['windows', 'macos', 'linux', 'auto'],
        default='auto',
        help='目标平台 (默认: auto)'
    )
    
    parser.add_argument(
        '--onefile',
        action='store_true',
        default=True,
        help='生成单文件可执行程序 (默认)'
    )
    
    parser.add_argument(
        '--standalone',
        action='store_true',
        help='生成独立目录'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    parser.add_argument(
        '--output-dir',
        default='dist',
        help='输出目录 (默认: dist)'
    )
    
    parser.add_argument(
        '--version',
        help='版本号'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='清理之前的构建'
    )
    
    args = parser.parse_args()
    
    # 显示横幅
    print("")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                    TimeNest 构建工具                        ║")
    print("║                  使用 Nuitka 编译打包                       ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print("")
    
    # 执行构建
    success = build_executable(args)
    
    if success:
        print("\n🎉 构建完成! 您可以在输出目录中找到可执行文件。")
        print("\n💡 提示:")
        print("  - 首次运行可能需要较长时间进行初始化")
        print("  - 如遇到安全警告，请在系统设置中允许运行")
        print("  - 可以使用 --debug 选项生成带调试信息的版本")
        sys.exit(0)
    else:
        print("\n💥 构建失败! 请检查错误信息并重试。")
        print("\n🔧 故障排除:")
        print("  1. 确保已安装所有依赖: pip install -r requirements.txt")
        print("  2. 确保已安装 Nuitka: pip install nuitka>=1.8.0")
        print("  3. 检查 Python 版本是否 >= 3.8")
        print("  4. 在 Windows 上可能需要安装 Visual Studio Build Tools")
        sys.exit(1)


if __name__ == '__main__':
    main()