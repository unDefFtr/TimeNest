# TimeNest 构建指南

本文档介绍如何使用 Nuitka 将 TimeNest 打包为跨平台的可执行文件。

## 📋 目录

- [自动化构建（GitHub Actions）](#自动化构建github-actions)
- [本地构建](#本地构建)
- [构建要求](#构建要求)
- [故障排除](#故障排除)
- [高级配置](#高级配置)

## 🤖 自动化构建（GitHub Actions）

### 触发方式

我们的 GitHub Workflow 支持三种触发方式：

#### 1. 标签推送（推荐用于正式发布）

```bash
# 创建并推送标签
git tag v1.0.0
git push origin v1.0.0
```

这将自动构建所有平台的可执行文件并创建 GitHub Release。

#### 2. 手动触发

1. 访问 GitHub 仓库的 Actions 页面
2. 选择 "Build and Release" workflow
3. 点击 "Run workflow"
4. 可选择指定版本号（如 `v1.0.0`）

#### 3. Pull Request 触发

向 `main` 或 `develop` 分支提交 PR 时会自动触发构建测试。

### 构建产物

自动化构建会生成以下文件：

- **Windows**: `TimeNest-{version}-Windows-x64.exe`
- **macOS**: `TimeNest-{version}-macOS-x64.dmg` 或 `TimeNest-{version}-macOS-x64`
- **Linux**: `TimeNest-{version}-Linux-x64`

### 下载构建产物

#### 从 GitHub Release 下载（标签触发）

1. 访问 [Releases 页面](https://github.com/your-username/TimeNest/releases)
2. 选择对应版本
3. 下载适合您平台的文件

#### 从 Actions Artifacts 下载（手动触发或 PR）

1. 访问 GitHub 仓库的 Actions 页面
2. 选择对应的 workflow run
3. 在 "Artifacts" 部分下载对应平台的文件

## 🔨 本地构建

### 快速开始

```bash
# 1. 安装构建依赖
pip install nuitka>=1.8.0
pip install -r requirements.txt

# 2. 运行构建脚本
python build.py

# 3. 查看构建产物
ls dist/
```

### 构建选项

```bash
# 基础用法
python build.py                          # 自动检测平台，生成单文件
python build.py --help                   # 查看所有选项

# 平台选择
python build.py --platform windows       # 为 Windows 构建
python build.py --platform macos         # 为 macOS 构建
python build.py --platform linux         # 为 Linux 构建

# 构建模式
python build.py --onefile                # 单文件模式（默认）
python build.py --standalone              # 独立目录模式

# 调试和开发
python build.py --debug                   # 启用调试模式
python build.py --clean                   # 清理后构建

# 版本和输出
python build.py --version v1.0.0         # 指定版本号
python build.py --output-dir build       # 指定输出目录
```

### 构建模式说明

#### 单文件模式（推荐）

- **优点**: 分发简单，只有一个可执行文件
- **缺点**: 首次启动较慢，文件较大
- **适用**: 最终用户分发

```bash
python build.py --onefile
```

#### 独立目录模式

- **优点**: 启动速度快，便于调试
- **缺点**: 文件较多，分发复杂
- **适用**: 开发测试

```bash
python build.py --standalone
```

## 📋 构建要求

### 系统要求

| 平台 | 最低版本 | 推荐版本 |
|------|----------|----------|
| **Windows** | Windows 10 | Windows 11 |
| **macOS** | macOS 10.14 | macOS 12+ |
| **Linux** | Ubuntu 18.04 | Ubuntu 20.04+ |

### 软件依赖

#### 通用依赖

```bash
# Python 环境
Python >= 3.8

# 构建工具
nuitka >= 1.8.0
ordered-set
zstandard

# 项目依赖
pip install -r requirements.txt
```

#### Windows 特定依赖

```bash
# Visual Studio Build Tools（必需）
# 下载地址: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# 或使用 Chocolatey 安装
choco install visualstudio2022buildtools --package-parameters "--add Microsoft.VisualStudio.Workload.VCTools"
```

#### macOS 特定依赖

```bash
# Xcode Command Line Tools
xcode-select --install

# 创建 DMG 包（可选）
brew install create-dmg
```

#### Linux 特定依赖

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
  build-essential \
  libgl1-mesa-glx \
  libglib2.0-0 \
  libxkbcommon-x11-0 \
  libxcb-icccm4 \
  libxcb-image0 \
  libxcb-keysyms1 \
  libxcb-randr0 \
  libxcb-render-util0 \
  libxcb-xinerama0 \
  libxcb-xfixes0 \
  libegl1-mesa \
  libxcb-cursor0

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install qt6-qtbase-devel

# Arch Linux
sudo pacman -S base-devel qt6-base
```

## 🔧 故障排除

### 常见问题

#### 1. Nuitka 安装失败

```bash
# 错误: Microsoft Visual C++ 14.0 is required
# 解决: 安装 Visual Studio Build Tools

# Windows
choco install visualstudio2022buildtools

# 或手动下载安装
# https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

#### 2. PyQt6 相关错误

```bash
# 错误: No module named 'PyQt6'
# 解决: 重新安装 PyQt6

pip uninstall PyQt6
pip install PyQt6>=6.6.0
```

#### 3. 资源文件缺失

```bash
# 错误: 找不到图标或资源文件
# 解决: 检查资源文件路径

# 确保以下目录存在
ls resources/icons/
ls resources/sounds/  # 如果有音频文件
```

#### 4. Linux 上的 Qt 库问题

```bash
# 错误: qt.qpa.plugin: Could not load the Qt platform plugin "xcb"
# 解决: 安装 Qt 相关库

sudo apt-get install libxcb-xinerama0
# 或
export QT_DEBUG_PLUGINS=1  # 查看详细错误信息
```

#### 5. macOS 代码签名问题

```bash
# 错误: "TimeNest" cannot be opened because the developer cannot be verified
# 解决: 允许运行未签名应用

# 方法1: 系统偏好设置 > 安全性与隐私 > 通用 > 仍要打开
# 方法2: 命令行移除隔离属性
sudo xattr -rd com.apple.quarantine TimeNest.app
```

### 调试技巧

#### 1. 启用详细输出

```bash
# 构建时查看详细信息
python build.py --debug

# 或直接使用 Nuitka
python -m nuitka --show-progress --show-memory main.py
```

#### 2. 检查依赖

```bash
# 检查 Python 环境
python --version
python -c "import PyQt6; print('PyQt6 OK')"

# 检查 Nuitka
python -m nuitka --version

# 检查项目依赖
python check_dependencies.py
```

#### 3. 分步构建

```bash
# 1. 先生成独立目录
python build.py --standalone

# 2. 测试运行
cd dist/main.dist/
./main  # Linux/macOS
# 或
main.exe  # Windows

# 3. 如果正常，再生成单文件
python build.py --onefile
```

## ⚙️ 高级配置

### 自定义 Nuitka 参数

如需更精细的控制，可以直接使用 Nuitka 命令：

```bash
# 基础命令
python -m nuitka \
  --standalone \
  --enable-plugin=pyqt6 \
  --include-data-dir=resources=resources \
  --include-package=core \
  --include-package=ui \
  --include-package=components \
  --include-package=models \
  --include-package=utils \
  --include-package=sdk \
  main.py

# Windows 特定
python -m nuitka \
  --onefile \
  --windows-console-mode=disable \
  --windows-icon-from-ico=resources/icons/tray_icon.png \
  --enable-plugin=pyqt6 \
  main.py

# macOS 特定
python -m nuitka \
  --standalone \
  --macos-create-app-bundle \
  --macos-app-icon=resources/icons/tray_icon.png \
  --enable-plugin=pyqt6 \
  main.py

# Linux 特定
python -m nuitka \
  --onefile \
  --linux-icon=resources/icons/tray_icon.png \
  --enable-plugin=pyqt6 \
  main.py
```

### 优化选项

```bash
# 性能优化
--lto=yes                    # 链接时优化
--jobs=4                     # 并行编译
--python-flag=no_docstrings  # 移除文档字符串

# 大小优化
--remove-output              # 移除中间文件
--no-pyi-file               # 不生成 .pyi 文件

# 调试选项
--debug                      # 调试模式
--show-progress             # 显示进度
--show-memory               # 显示内存使用
--verbose                   # 详细输出
```

### 排除不需要的模块

```bash
# 排除测试模块
--nofollow-import-to=tests
--nofollow-import-to=pytest

# 排除开发工具
--nofollow-import-to=black
--nofollow-import-to=flake8
--nofollow-import-to=mypy
```

## 📦 分发建议

### 文件命名规范

```
TimeNest-{version}-{platform}-{arch}.{ext}

示例:
- TimeNest-v1.0.0-Windows-x64.exe
- TimeNest-v1.0.0-macOS-x64.dmg
- TimeNest-v1.0.0-Linux-x64
```

### 发布检查清单

- [ ] 所有平台构建成功
- [ ] 可执行文件能正常启动
- [ ] 核心功能测试通过
- [ ] 资源文件正确包含
- [ ] 版本信息正确显示
- [ ] 文件大小合理（< 100MB）
- [ ] 创建 Release Notes
- [ ] 更新下载链接

### 用户安装说明

为用户提供清晰的安装说明：

```markdown
## 安装说明

### Windows
1. 下载 `TimeNest-*-Windows-x64.exe`
2. 双击运行（可能需要允许运行未知应用）
3. 首次启动需要等待初始化

### macOS
1. 下载 `TimeNest-*-macOS-x64.dmg`
2. 双击挂载 DMG 文件
3. 拖拽 TimeNest.app 到应用程序文件夹
4. 右键点击应用 > 打开（首次运行）

### Linux
1. 下载 `TimeNest-*-Linux-x64`
2. 添加执行权限：`chmod +x TimeNest-*-Linux-x64`
3. 运行：`./TimeNest-*-Linux-x64`
```

## 🤝 贡献

如果您在构建过程中遇到问题或有改进建议，欢迎：

1. [提交 Issue](https://github.com/your-username/TimeNest/issues)
2. [发起 Discussion](https://github.com/your-username/TimeNest/discussions)
3. 提交 Pull Request 改进构建脚本

## 📄 许可证

本构建系统遵循与 TimeNest 项目相同的 MIT 许可证。