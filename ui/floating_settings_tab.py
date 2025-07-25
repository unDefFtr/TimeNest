#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TimeNest 浮窗设置标签页
集成到现有 SettingsDialog 的浮窗配置界面
"""

import logging
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QSlider, QSpinBox, QCheckBox, QComboBox, QPushButton,
    QListWidget, QListWidgetItem, QColorDialog, QMessageBox,
    QFrame, QSplitter, QTextEdit, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from ui.floating_widget import FloatingWidget


class FloatingSettingsTab(QWidget):
    """
    浮窗设置标签页

    提供浮窗的完整配置界面，包括：
    - 外观设置（尺寸、透明度、圆角等）
    - 显示内容（模块管理、排序）
    - 行为设置（快捷键、专注模式等）
    """

    # 信号定义
    settings_changed = pyqtSignal(dict)  # 设置变化信号
    preview_requested = pyqtSignal(dict)  # 预览请求信号

    def __init__(self, parent=None):
        """
        初始化浮窗设置标签页

        Args:
            parent: 父窗口
        """
        super().__init__(parent)

        # 设置日志
        self.logger = logging.getLogger(f'{__name__}.FloatingSettingsTab')

        # 预览相关
        self.preview_widget: Optional[FloatingWidget] = None
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._apply_preview)

        # 初始化UI
        self._init_ui()
        self._connect_signals()

        self.logger.info("浮窗设置标签页初始化完成")

    def _init_ui(self) -> None:
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 创建分组
        appearance_group = self._create_appearance_group()
        content_group = self._create_content_group()
        behavior_group = self._create_behavior_group()

        layout.addWidget(appearance_group)
        layout.addWidget(content_group)
        layout.addWidget(behavior_group)
        layout.addStretch()

    def _create_appearance_group(self) -> QGroupBox:
        """创建外观设置分组"""
        group = QGroupBox("外观设置")
        layout = QGridLayout(group)

        # 尺寸设置
        layout.addWidget(QLabel("宽度:"), 0, 0)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(200, 800)
        self.width_spin.setValue(400)
        self.width_spin.setSuffix(" px")
        layout.addWidget(self.width_spin, 0, 1)

        layout.addWidget(QLabel("高度:"), 0, 2)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(40, 120)
        self.height_spin.setValue(60)
        self.height_spin.setSuffix(" px")
        layout.addWidget(self.height_spin, 0, 3)

        # 透明度设置
        layout.addWidget(QLabel("透明度:"), 1, 0)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setValue(85)
        layout.addWidget(self.opacity_slider, 1, 1, 1, 2)

        self.opacity_label = QLabel("85%")
        layout.addWidget(self.opacity_label, 1, 3)

        # 圆角设置
        layout.addWidget(QLabel("圆角:"), 2, 0)
        self.radius_slider = QSlider(Qt.Orientation.Horizontal)
        self.radius_slider.setRange(10, 50)
        self.radius_slider.setValue(30)
        layout.addWidget(self.radius_slider, 2, 1, 1, 2)

        self.radius_label = QLabel("30px")
        layout.addWidget(self.radius_label, 2, 3)

        # 字体大小
        layout.addWidget(QLabel("字体大小:"), 3, 0)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 18)
        self.font_size_spin.setValue(12)
        self.font_size_spin.setSuffix(" px")
        layout.addWidget(self.font_size_spin, 3, 1)

        # 颜色设置
        layout.addWidget(QLabel("背景色:"), 3, 2)
        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setFixedSize(50, 25)
        self.bg_color_btn.setStyleSheet("background-color: #323232; border: 1px solid #666;")
        self.bg_color_btn.clicked.connect(self._choose_bg_color)
        layout.addWidget(self.bg_color_btn, 3, 3)

        # 位置设置
        layout.addWidget(QLabel("位置:"), 4, 0)
        position_layout = QHBoxLayout()

        self.position_group = QButtonGroup()
        self.pos_top_center = QRadioButton("顶部居中")
        self.pos_top_left = QRadioButton("顶部左侧")
        self.pos_top_right = QRadioButton("顶部右侧")
        self.pos_custom = QRadioButton("自定义")

        self.pos_top_center.setChecked(True)

        self.position_group.addButton(self.pos_top_center, 0)
        self.position_group.addButton(self.pos_top_left, 1)
        self.position_group.addButton(self.pos_top_right, 2)
        self.position_group.addButton(self.pos_custom, 3)

        position_layout.addWidget(self.pos_top_center)
        position_layout.addWidget(self.pos_top_left)
        position_layout.addWidget(self.pos_top_right)
        position_layout.addWidget(self.pos_custom)
        position_layout.addStretch()

        layout.addLayout(position_layout, 4, 1, 1, 3)

        # 预览按钮
        self.preview_btn = QPushButton("实时预览")
        self.preview_btn.setCheckable(True)
        layout.addWidget(self.preview_btn, 5, 0, 1, 4)

        return group

    def _create_content_group(self) -> QGroupBox:
        """创建显示内容分组"""
        group = QGroupBox("显示内容")
        layout = QVBoxLayout(group)

        # 模块管理
        module_layout = QHBoxLayout()

        # 可用模块列表
        available_layout = QVBoxLayout()
        available_layout.addWidget(QLabel("可用模块:"))
        self.available_modules_list = QListWidget()
        self._populate_available_modules()
        available_layout.addWidget(self.available_modules_list)

        # 控制按钮
        buttons_layout = QVBoxLayout()
        buttons_layout.addStretch()

        self.add_module_btn = QPushButton("添加 →")
        self.remove_module_btn = QPushButton("← 移除")
        self.move_up_btn = QPushButton("↑ 上移")
        self.move_down_btn = QPushButton("↓ 下移")

        buttons_layout.addWidget(self.add_module_btn)
        buttons_layout.addWidget(self.remove_module_btn)
        buttons_layout.addWidget(self.move_up_btn)
        buttons_layout.addWidget(self.move_down_btn)
        buttons_layout.addStretch()

        # 已启用模块列表
        enabled_layout = QVBoxLayout()
        enabled_layout.addWidget(QLabel("已启用模块:"))
        self.enabled_modules_list = QListWidget()
        enabled_layout.addWidget(self.enabled_modules_list)

        module_layout.addLayout(available_layout)
        module_layout.addLayout(buttons_layout)
        module_layout.addLayout(enabled_layout)

        layout.addLayout(module_layout)

        # 模块设置
        module_settings_layout = QHBoxLayout()

        module_settings_layout.addWidget(QLabel("更新间隔:"))
        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setRange(1, 300)
        self.update_interval_spin.setValue(5)
        self.update_interval_spin.setSuffix(" 秒")
        module_settings_layout.addWidget(self.update_interval_spin)

        module_settings_layout.addStretch()

        self.auto_hide_check = QCheckBox("无内容时自动隐藏模块")
        module_settings_layout.addWidget(self.auto_hide_check)

        layout.addLayout(module_settings_layout)

        return group

    def _create_behavior_group(self) -> QGroupBox:
        """创建行为设置分组"""
        group = QGroupBox("行为设置")
        layout = QGridLayout(group)

        # 快捷键设置
        layout.addWidget(QLabel("显示/隐藏快捷键:"), 0, 0)
        self.toggle_shortcut_edit = QLabel("Ctrl+Shift+F")
        self.toggle_shortcut_edit.setStyleSheet("border: 1px solid #ccc; padding: 5px;")
        layout.addWidget(self.toggle_shortcut_edit, 0, 1)

        layout.addWidget(QLabel("鼠标穿透快捷键:"), 0, 2)
        self.transparent_shortcut_edit = QLabel("Ctrl+Shift+T")
        self.transparent_shortcut_edit.setStyleSheet("border: 1px solid #ccc; padding: 5px;")
        layout.addWidget(self.transparent_shortcut_edit, 0, 3)

        # 行为选项
        self.always_on_top_check = QCheckBox("总是置顶")
        self.always_on_top_check.setChecked(True)
        layout.addWidget(self.always_on_top_check, 1, 0, 1, 2)

        self.auto_hide_check = QCheckBox("无活动时自动隐藏")
        layout.addWidget(self.auto_hide_check, 1, 2, 1, 2)

        # 专注模式
        layout.addWidget(QLabel("专注模式:"), 2, 0)
        self.focus_mode_combo = QComboBox()
        self.focus_mode_combo.addItems(["禁用", "手动", "定时"])
        layout.addWidget(self.focus_mode_combo, 2, 1)

        layout.addWidget(QLabel("专注时长:"), 2, 2)
        self.focus_duration_spin = QSpinBox()
        self.focus_duration_spin.setRange(5, 180)
        self.focus_duration_spin.setValue(25)
        self.focus_duration_spin.setSuffix(" 分钟")
        layout.addWidget(self.focus_duration_spin, 2, 3)

        # 动画设置
        self.enable_animations_check = QCheckBox("启用动画效果")
        self.enable_animations_check.setChecked(True)
        layout.addWidget(self.enable_animations_check, 3, 0, 1, 2)

        layout.addWidget(QLabel("动画时长:"), 3, 2)
        self.animation_duration_spin = QSpinBox()
        self.animation_duration_spin.setRange(100, 1000)
        self.animation_duration_spin.setValue(300)
        self.animation_duration_spin.setSuffix(" ms")
        layout.addWidget(self.animation_duration_spin, 3, 3)

        return group

    def _populate_available_modules(self) -> None:
        """填充可用模块列表"""
        modules = [
            ("time", "时间模块", "显示当前时间"),
            ("schedule", "课程模块", "显示当前和下节课程"),
            ("weather", "天气模块", "显示天气信息"),
            ("countdown", "倒计时模块", "显示重要事件倒计时"),
            ("system", "系统状态模块", "显示CPU和内存使用率")
        ]

        for module_id, name, description in modules:
            item = QListWidgetItem(f"{name}\n{description}")
            item.setData(Qt.ItemDataRole.UserRole, module_id)
            self.available_modules_list.addItem(item)

    def _connect_signals(self) -> None:
        """连接信号和槽"""
        # 外观设置信号
        self.width_spin.valueChanged.connect(self._on_setting_changed)
        self.height_spin.valueChanged.connect(self._on_setting_changed)
        self.opacity_slider.valueChanged.connect(self._update_opacity_label)
        self.opacity_slider.valueChanged.connect(self._on_setting_changed)
        self.radius_slider.valueChanged.connect(self._update_radius_label)
        self.radius_slider.valueChanged.connect(self._on_setting_changed)
        self.font_size_spin.valueChanged.connect(self._on_setting_changed)
        self.position_group.buttonClicked.connect(self._on_setting_changed)

        # 预览按钮
        self.preview_btn.toggled.connect(self._toggle_preview)

        # 模块管理信号
        self.add_module_btn.clicked.connect(self._add_module)
        self.remove_module_btn.clicked.connect(self._remove_module)
        self.move_up_btn.clicked.connect(self._move_module_up)
        self.move_down_btn.clicked.connect(self._move_module_down)

        # 行为设置信号
        self.always_on_top_check.toggled.connect(self._on_setting_changed)
        self.auto_hide_check.toggled.connect(self._on_setting_changed)
        self.focus_mode_combo.currentTextChanged.connect(self._on_setting_changed)
        self.focus_duration_spin.valueChanged.connect(self._on_setting_changed)
        self.enable_animations_check.toggled.connect(self._on_setting_changed)
        self.animation_duration_spin.valueChanged.connect(self._on_setting_changed)

    def _update_opacity_label(self) -> None:
        """更新透明度标签"""
        value = self.opacity_slider.value()
        self.opacity_label.setText(f"{value}%")

    def _update_radius_label(self) -> None:
        """更新圆角标签"""
        value = self.radius_slider.value()
        self.radius_label.setText(f"{value}px")

    def _choose_bg_color(self) -> None:
        """选择背景颜色"""
        color = QColorDialog.getColor(QColor("#323232"), self, "选择背景颜色")
        if color.isValid():
            self.bg_color_btn.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #666;"
            )
            self._on_setting_changed()

    def _on_setting_changed(self) -> None:
        """设置变化处理"""
        if self.preview_btn.isChecked():
            # 延迟应用预览，避免频繁更新
            self.preview_timer.start(500)

        # 发送设置变化信号
        config = self.get_config()
        self.settings_changed.emit(config)

    def _toggle_preview(self, enabled: bool) -> None:
        """切换预览模式"""
        if enabled:
            self._create_preview_widget()
        else:
            self._destroy_preview_widget()

    def _create_preview_widget(self) -> None:
        """创建预览浮窗"""
        try:
            if self.preview_widget is None:
                self.preview_widget = FloatingWidget()
                self._apply_preview()
                self.preview_widget.show()
                self.logger.debug("创建预览浮窗")
        except Exception as e:
            self.logger.error(f"创建预览浮窗失败: {e}")

    def _destroy_preview_widget(self) -> None:
        """销毁预览浮窗"""
        try:
            if self.preview_widget:
                self.preview_widget.close()
                self.preview_widget = None
                self.logger.debug("销毁预览浮窗")
        except Exception as e:
            self.logger.error(f"销毁预览浮窗失败: {e}")

    def _apply_preview(self) -> None:
        """应用预览设置"""
        try:
            if self.preview_widget:
                config = self.get_config()
                self.preview_widget.update_config(config)
                self.preview_requested.emit(config)
        except Exception as e:
            self.logger.error(f"应用预览设置失败: {e}")

    def _add_module(self) -> None:
        """添加模块到已启用列表"""
        try:
            current_item = self.available_modules_list.currentItem()
            if current_item:
                module_id = current_item.data(Qt.ItemDataRole.UserRole)
                module_name = current_item.text().split('\n')[0]

                # 检查是否已存在
                for i in range(self.enabled_modules_list.count()):
                    item = self.enabled_modules_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == module_id:
                        QMessageBox.information(self, "提示", "该模块已添加")
                        return

                # 添加到已启用列表
                new_item = QListWidgetItem(module_name)
                new_item.setData(Qt.ItemDataRole.UserRole, module_id)
                new_item.setCheckState(Qt.CheckState.Checked)
                self.enabled_modules_list.addItem(new_item)

                self._on_setting_changed()
                self.logger.debug(f"添加模块: {module_name}")

        except Exception as e:
            self.logger.error(f"添加模块失败: {e}")

    def _remove_module(self) -> None:
        """从已启用列表移除模块"""
        try:
            current_row = self.enabled_modules_list.currentRow()
            if current_row >= 0:
                item = self.enabled_modules_list.takeItem(current_row)
                if item:
                    module_name = item.text()
                    self._on_setting_changed()
                    self.logger.debug(f"移除模块: {module_name}")
        except Exception as e:
            self.logger.error(f"移除模块失败: {e}")

    def _move_module_up(self) -> None:
        """上移模块"""
        try:
            current_row = self.enabled_modules_list.currentRow()
            if current_row > 0:
                item = self.enabled_modules_list.takeItem(current_row)
                self.enabled_modules_list.insertItem(current_row - 1, item)
                self.enabled_modules_list.setCurrentRow(current_row - 1)
                self._on_setting_changed()
        except Exception as e:
            self.logger.error(f"上移模块失败: {e}")

    def _move_module_down(self) -> None:
        """下移模块"""
        try:
            current_row = self.enabled_modules_list.currentRow()
            if current_row < self.enabled_modules_list.count() - 1:
                item = self.enabled_modules_list.takeItem(current_row)
                self.enabled_modules_list.insertItem(current_row + 1, item)
                self.enabled_modules_list.setCurrentRow(current_row + 1)
                self._on_setting_changed()
        except Exception as e:
            self.logger.error(f"下移模块失败: {e}")

    def get_config(self) -> Dict[str, Any]:
        """
        获取当前配置

        Returns:
            配置字典
        """
        try:
            # 获取背景颜色
            bg_color_style = self.bg_color_btn.styleSheet()
            bg_color = "#323232"  # 默认值
            if "background-color:" in bg_color_style:
                start = bg_color_style.find("background-color:") + len("background-color:")
                end = bg_color_style.find(";", start)
                if end > start:
                    bg_color = bg_color_style[start:end].strip()

            # 获取位置设置
            position_mode = self.position_group.checkedId()
            position_names = ["top_center", "top_left", "top_right", "custom"]
            position = position_names[position_mode] if 0 <= position_mode < len(position_names) else "top_center"

            # 获取已启用模块
            enabled_modules = []
            for i in range(self.enabled_modules_list.count()):
                item = self.enabled_modules_list.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    module_id = item.data(Qt.ItemDataRole.UserRole)
                    enabled_modules.append(module_id)

            config = {
                # 外观设置
                'width': self.width_spin.value(),
                'height': self.height_spin.value(),
                'opacity': self.opacity_slider.value() / 100.0,
                'radius': self.radius_slider.value(),
                'font_size': self.font_size_spin.value(),
                'bg_color': bg_color,
                'position': position,

                # 显示内容
                'enabled_modules': enabled_modules,
                'update_interval': self.update_interval_spin.value(),
                'auto_hide_empty': self.auto_hide_check.isChecked(),

                # 行为设置
                'always_on_top': self.always_on_top_check.isChecked(),
                'auto_hide': self.auto_hide_check.isChecked(),
                'focus_mode': self.focus_mode_combo.currentText(),
                'focus_duration': self.focus_duration_spin.value(),
                'enable_animations': self.enable_animations_check.isChecked(),
                'animation_duration': self.animation_duration_spin.value()
            }

            return config

        except Exception as e:
            self.logger.error(f"获取配置失败: {e}")
            return {}

    def set_config(self, config: Dict[str, Any]) -> None:
        """
        设置配置

        Args:
            config: 配置字典
        """
        try:
            # 阻止信号触发
            self.blockSignals(True)

            # 外观设置
            self.width_spin.setValue(config.get('width', 400))
            self.height_spin.setValue(config.get('height', 60))
            self.opacity_slider.setValue(int(config.get('opacity', 0.85) * 100))
            self.radius_slider.setValue(config.get('radius', 30))
            self.font_size_spin.setValue(config.get('font_size', 12))

            # 背景颜色
            bg_color = config.get('bg_color', '#323232')
            self.bg_color_btn.setStyleSheet(f"background-color: {bg_color}; border: 1px solid #666;")

            # 位置设置
            position = config.get('position', 'top_center')
            position_map = {
                'top_center': 0,
                'top_left': 1,
                'top_right': 2,
                'custom': 3
            }
            if position in position_map:
                button = self.position_group.button(position_map[position])
                if button:
                    button.setChecked(True)

            # 显示内容
            enabled_modules = config.get('enabled_modules', ['time', 'schedule'])
            self._load_enabled_modules(enabled_modules)

            self.update_interval_spin.setValue(config.get('update_interval', 5))
            self.auto_hide_check.setChecked(config.get('auto_hide_empty', False))

            # 行为设置
            self.always_on_top_check.setChecked(config.get('always_on_top', True))
            self.auto_hide_check.setChecked(config.get('auto_hide', False))

            focus_mode = config.get('focus_mode', '禁用')
            index = self.focus_mode_combo.findText(focus_mode)
            if index >= 0:
                self.focus_mode_combo.setCurrentIndex(index)

            self.focus_duration_spin.setValue(config.get('focus_duration', 25))
            self.enable_animations_check.setChecked(config.get('enable_animations', True))
            self.animation_duration_spin.setValue(config.get('animation_duration', 300))

            # 更新标签
            self._update_opacity_label()
            self._update_radius_label()

            # 恢复信号
            self.blockSignals(False)

            self.logger.debug("设置配置完成")

        except Exception as e:
            self.logger.error(f"设置配置失败: {e}")
            self.blockSignals(False)

    def _load_enabled_modules(self, enabled_modules: List[str]) -> None:
        """加载已启用模块列表"""
        try:
            self.enabled_modules_list.clear()

            # 模块信息映射
            module_info = {
                'time': '时间模块',
                'schedule': '课程模块',
                'weather': '天气模块',
                'countdown': '倒计时模块',
                'system': '系统状态模块'
            }

            for module_id in enabled_modules:
                if module_id in module_info:
                    item = QListWidgetItem(module_info[module_id])
                    item.setData(Qt.ItemDataRole.UserRole, module_id)
                    item.setCheckState(Qt.CheckState.Checked)
                    self.enabled_modules_list.addItem(item)

        except Exception as e:
            self.logger.error(f"加载已启用模块失败: {e}")

    def closeEvent(self, event) -> None:
        """关闭事件处理"""
        self._destroy_preview_widget()
        super().closeEvent(event)
