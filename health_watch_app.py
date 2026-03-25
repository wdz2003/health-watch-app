"""
健康监测手表APP - 优化版
功能：实时显示心率、血氧、步数、电子围栏状态，支持ESP8266通信
"""

import json
import threading
import time
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.config import Config
from kivy.properties import StringProperty, NumericProperty

# 设置窗口大小（调试用，手机上会全屏）
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')


class HealthWatchApp(App):
    """健康监测主应用类"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ESP8266连接配置
        self.esp_ip = "192.168.4.1"
        self.esp_port = 8888
        self.connected = False
        self.data_thread = None
        self.running = True

        # 实时数据
        self.realtime_data = {
            'heart_rate': 75,
            'blood_oxygen': 98,
            'steps': 0,
            'lat': 39.9042,
            'lon': 116.4074,
            'distance': 0.0,
            'fence_status': '正常'
        }

        # 设置参数
        self.settings = {
            'heart_rate_threshold': 120,  # 心率阈值
            'blood_oxygen_threshold': 90,  # 血氧阈值
            'medication_time': '08:00',  # 吃药时间
            'fence_lat': 39.9042,  # 围栏中心纬度
            'fence_lon': 116.4074,  # 围栏中心经度
            'fence_radius': 100  # 围栏半径（米）
        }

    def build(self):
        """构建UI界面"""
        Window.clearcolor = (0.95, 0.97, 1.0, 1)  # 淡蓝色背景

        # 主布局
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=15)

        # 顶部标题栏
        title_box = self.create_header_box()
        main_layout.add_widget(title_box)

        # 连接状态指示
        self.connection_label = Label(
            text='● 未连接',
            font_size=14,
            size_hint_y=None,
            height=30,
            color=(0.8, 0.2, 0.2, 1),
            halign='center',
            markup=True
        )
        main_layout.add_widget(self.connection_label)

        # 创建内容区域（可滚动）
        scroll = ScrollView(size_hint_y=None, height=480)
        content_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=12, padding=5)
        content_layout.bind(minimum_height=content_layout.setter('height'))

        # 实时数据区域
        data_label = Label(
            text='📊 实时数据',
            font_size=16,
            bold=True,
            size_hint_y=None,
            height=35,
            color=(0.2, 0.3, 0.5, 1),
            halign='left'
        )
        content_layout.add_widget(data_label)

        # 数据卡片网格 (2x2)
        self.data_grid = GridLayout(cols=2, size_hint_y=None, height=200, spacing=10, padding=5)
        self.data_grid.bind(minimum_height=self.data_grid.setter('height'))

        # 心率显示卡片
        self.heart_card = self.create_data_card('心率', '75', 'bpm', (0.23, 0.51, 0.96, 1))
        self.data_grid.add_widget(self.heart_card)

        # 血氧显示卡片
        self.blood_card = self.create_data_card('血氧', '98', '%', (0.13, 0.77, 0.37, 1))
        self.data_grid.add_widget(self.blood_card)

        # 步数显示卡片
        self.steps_card = self.create_data_card('步数', '0', '步', (0.98, 0.65, 0.14, 1))
        self.data_grid.add_widget(self.steps_card)

        # 围栏状态卡片
        self.fence_card = self.create_data_card('电子围栏', '正常', '', (0.16, 0.80, 0.68, 1))
        self.data_grid.add_widget(self.fence_card)

        content_layout.add_widget(self.data_grid)

        # 位置信息区域
        location_box = self.create_location_box()
        content_layout.add_widget(location_box)

        # 设置区域
        settings_label = Label(
            text='⚙️ 参数设置',
            font_size=16,
            bold=True,
            size_hint_y=None,
            height=35,
            color=(0.2, 0.3, 0.5, 1),
            halign='left'
        )
        content_layout.add_widget(settings_label)

        # 设置输入区域
        self.settings_layout = self.create_settings_layout()
        content_layout.add_widget(self.settings_layout)

        # 电子围栏设置按钮
        fence_button = Button(
            text='📍 设置电子围栏',
            size_hint_y=None,
            height=45,
            background_color=(0.3, 0.5, 0.9, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        fence_button.bind(on_press=self.show_fence_settings)
        content_layout.add_widget(fence_button)

        # 按钮区域
        button_box = BoxLayout(size_hint_y=None, height=50, spacing=10, padding=5)

        # 连接/断开按钮
        self.connect_button = Button(
            text='📡 连接ESP8266',
            size_hint_x=0.5,
            background_color=(0.2, 0.7, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        self.connect_button.bind(on_press=self.toggle_connection)
        button_box.add_widget(self.connect_button)

        # 保存设置按钮
        save_button = Button(
            text='💾 保存设置',
            size_hint_x=0.5,
            background_color=(0.2, 0.4, 0.9, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        save_button.bind(on_press=self.save_settings)
        button_box.add_widget(save_button)

        content_layout.add_widget(button_box)

        # 添加滚动视图
        scroll.add_widget(content_layout)
        main_layout.add_widget(scroll)

        # 底部信息
        self.footer_label = Label(
            text=f'最后更新: {datetime.now().strftime("%H:%M:%S")}',
            font_size=10,
            size_hint_y=None,
            height=25,
            color=(0.6, 0.6, 0.6, 1)
        )
        main_layout.add_widget(self.footer_label)

        # 启动数据更新定时器
        Clock.schedule_interval(self.update_ui, 1.0)

        return main_layout

    def create_header_box(self):
        """创建顶部标题栏"""
        box = BoxLayout(size_hint_y=None, height=50, padding=10)
        
        with box.canvas.before:
            Color(0.1, 0.2, 0.4, 1)
            rect = RoundedRectangle(pos=box.pos, size=box.size, radius=[15, 15, 15, 15])
            box.bind(pos=rect.setter('pos'), size=rect.setter('size'))
        
        title = Label(
            text='健康监测手表',
            font_size=22,
            bold=True,
            color=(1, 1, 1, 1)
        )
        box.add_widget(title)
        return box

    def create_data_card(self, title, value, unit, bg_color):
        """创建数据卡片"""
        card = BoxLayout(orientation='vertical', padding=12, spacing=5)
        
        with card.canvas.before:
            Color(bg_color[0], bg_color[1], bg_color[2], 1)
            rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[12, 12, 12, 12])
            card.bind(pos=rect.setter('pos'), size=rect.setter('size'))
        
        # 标题
        title_label = Label(
            text=title,
            font_size=13,
            size_hint_y=None,
            height=20,
            color=(1, 1, 1, 0.9)
        )
        card.add_widget(title_label)
        
        # 数值
        value_label = Label(
            text=value,
            font_size=28,
            size_hint_y=None,
            height=40,
            bold=True,
            color=(1, 1, 1, 1)
        )
        card.add_widget(value_label)
        
        # 单位
        if unit:
            unit_label = Label(
                text=unit,
                font_size=12,
                size_hint_y=None,
                height=20,
                color=(1, 1, 1, 0.8)
            )
            card.add_widget(unit_label)
        
        return card

    def create_location_box(self):
        """创建位置信息区域"""
        box = BoxLayout(orientation='vertical', size_hint_y=None, height=90, spacing=5, padding=10)
        
        with box.canvas.before:
            Color(0.9, 0.9, 0.95, 1)
            rect = RoundedRectangle(pos=box.pos, size=box.size, radius=[10, 10, 10, 10])
            box.bind(pos=rect.setter('pos'), size=rect.setter('size'))
        
        # 纬度
        self.lat_label = Label(
            text=f'📍 纬度: {self.realtime_data["lat"]:.6f}',
            font_size=12,
            size_hint_y=None,
            height=25,
            halign='left',
            color=(0.3, 0.3, 0.4, 1),
            text_size=(None, None)
        )
        box.add_widget(self.lat_label)
        
        # 经度
        self.lon_label = Label(
            text=f'📍 经度: {self.realtime_data["lon"]:.6f}',
            font_size=12,
            size_hint_y=None,
            height=25,
            halign='left',
            color=(0.3, 0.3, 0.4, 1)
        )
        box.add_widget(self.lon_label)
        
        # 距离
        self.distance_label = Label(
            text=f'📏 距离中心: {self.realtime_data["distance"]:.1f} 米',
            font_size=12,
            size_hint_y=None,
            height=25,
            halign='left',
            color=(0.3, 0.3, 0.4, 1)
        )
        box.add_widget(self.distance_label)
        
        return box

    def create_settings_layout(self):
        """创建设置布局"""
        layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8, padding=10)
        
        with layout.canvas.before:
            Color(0.98, 0.98, 1.0, 1)
            rect = RoundedRectangle(pos=layout.pos, size=layout.size, radius=[10, 10, 10, 10])
            layout.bind(pos=rect.setter('pos'), size=rect.setter('size'))
        
        # 心率阈值
        hr_box = BoxLayout(size_hint_y=None, height=40)
        hr_box.add_widget(Label(text='❤️ 心率阈值:', size_hint_x=0.4, color=(0.3, 0.3, 0.4, 1), font_size=13))
        self.hr_input = TextInput(
            text='120',
            size_hint_x=0.6,
            input_filter='int',
            font_size=13,
            background_color=(0.95, 0.95, 0.97, 1),
            foreground_color=(0.2, 0.2, 0.3, 1)
        )
        hr_box.add_widget(self.hr_input)
        layout.add_widget(hr_box)
        
        # 血氧阈值
        bo_box = BoxLayout(size_hint_y=None, height=40)
        bo_box.add_widget(Label(text='💧 血氧阈值:', size_hint_x=0.4, color=(0.3, 0.3, 0.4, 1), font_size=13))
        self.bo_input = TextInput(
            text='90',
            size_hint_x=0.6,
            input_filter='int',
            font_size=13,
            background_color=(0.95, 0.95, 0.97, 1),
            foreground_color=(0.2, 0.2, 0.3, 1)
        )
        bo_box.add_widget(self.bo_input)
        layout.add_widget(bo_box)
        
        # 吃药时间
        med_box = BoxLayout(size_hint_y=None, height=40)
        med_box.add_widget(Label(text='💊 吃药时间:', size_hint_x=0.4, color=(0.3, 0.3, 0.4, 1), font_size=13))
        self.med_input = TextInput(
            text='08:00',
            size_hint_x=0.6,
            font_size=13,
            background_color=(0.95, 0.95, 0.97, 1),
            foreground_color=(0.2, 0.2, 0.3, 1)
        )
        med_box.add_widget(self.med_input)
        layout.add_widget(med_box)
        
        return layout

    def show_fence_settings(self, instance):
        """显示电子围栏设置弹窗"""
        popup_layout = BoxLayout(orientation='vertical', spacing=15, padding=20)

        # 标题
        title = Label(text='📍 电子围栏设置', font_size=20, bold=True, color=(0.2, 0.3, 0.5, 1))
        popup_layout.add_widget(title)

        # 纬度
        lat_box = BoxLayout(size_hint_y=None, height=45)
        lat_box.add_widget(Label(text='中心纬度:', size_hint_x=0.3, font_size=14))
        self.fence_lat_input = TextInput(
            text=str(self.settings['fence_lat']),
            size_hint_x=0.7,
            font_size=14,
            multiline=False
        )
        lat_box.add_widget(self.fence_lat_input)
        popup_layout.add_widget(lat_box)

        # 经度
        lon_box = BoxLayout(size_hint_y=None, height=45)
        lon_box.add_widget(Label(text='中心经度:', size_hint_x=0.3, font_size=14))
        self.fence_lon_input = TextInput(
            text=str(self.settings['fence_lon']),
            size_hint_x=0.7,
            font_size=14,
            multiline=False
        )
        lon_box.add_widget(self.fence_lon_input)
        popup_layout.add_widget(lon_box)

        # 半径
        radius_box = BoxLayout(size_hint_y=None, height=45)
        radius_box.add_widget(Label(text='半径(米):', size_hint_x=0.3, font_size=14))
        self.fence_radius_input = TextInput(
            text=str(self.settings['fence_radius']),
            size_hint_x=0.7,
            font_size=14,
            input_filter='int',
            multiline=False
        )
        radius_box.add_widget(self.fence_radius_input)
        popup_layout.add_widget(radius_box)

        # 按钮
        button_box = BoxLayout(size_hint_y=None, height=50, spacing=10)
        confirm_button = Button(
            text='✓ 确认',
            background_color=(0.2, 0.7, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        confirm_button.bind(on_press=self.save_fence_settings)
        cancel_button = Button(
            text='✕ 取消',
            background_color=(0.8, 0.2, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=14
        )
        cancel_button.bind(on_press=lambda x: self.fence_popup.dismiss())
        button_box.add_widget(confirm_button)
        button_box.add_widget(cancel_button)
        popup_layout.add_widget(button_box)

        self.fence_popup = Popup(
            title='',
            content=popup_layout,
            size_hint=(0.85, 0.55),
            background_color=(0.95, 0.95, 0.97, 1)
        )
        self.fence_popup.open()

    def save_fence_settings(self, instance):
        """保存电子围栏设置"""
        try:
            self.settings['fence_lat'] = float(self.fence_lat_input.text)
            self.settings['fence_lon'] = float(self.fence_lon_input.text)
            self.settings['fence_radius'] = float(self.fence_radius_input.text)
            self.fence_popup.dismiss()
            self.show_message('✓ 保存成功', '电子围栏设置已保存\n请点击"保存设置"下发到设备')
        except ValueError:
            self.show_message('✗ 错误', '请输入有效的数值')

    def toggle_connection(self, instance):
        """切换ESP8266连接状态"""
        if not self.connected:
            self.connect_to_esp()
        else:
            self.disconnect_from_esp()

    def connect_to_esp(self):
        """连接到ESP8266"""
        try:
            # 这里实现实际的连接逻辑
            self.connected = True
            self.connection_label.text = '● 已连接'
            self.connection_label.color = (0.2, 0.7, 0.3, 1)
            self.connect_button.text = '📡 断开连接'
            self.connect_button.background_color = (0.8, 0.2, 0.2, 1)

            # 启动数据接收线程
            self.data_thread = threading.Thread(target=self.receive_data)
            self.data_thread.daemon = True
            self.data_thread.start()

            self.show_message('✓ 连接成功', f'已连接到 {self.esp_ip}:{self.esp_port}')
        except Exception as e:
            self.show_message('✗ 连接失败', str(e))

    def disconnect_from_esp(self):
        """断开ESP8266连接"""
        self.connected = False
        self.running = False
        self.connection_label.text = '● 未连接'
        self.connection_label.color = (0.8, 0.2, 0.2, 1)
        self.connect_button.text = '📡 连接ESP8266'
        self.connect_button.background_color = (0.2, 0.7, 0.3, 1)

    def receive_data(self):
        """接收ESP8266数据的线程"""
        import socket

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.esp_ip, self.esp_port))

            while self.running and self.connected:
                try:
                    data = sock.recv(1024)
                    if data:
                        data_str = data.decode('utf-8')
                        self.parse_sensor_data(data_str)
                except socket.timeout:
                    continue
                except:
                    break

            sock.close()
        except Exception as e:
            print(f"接收数据错误: {e}")

    def parse_sensor_data(self, data_str):
        """解析传感器数据"""
        try:
            # 解析JSON格式的数据
            data = json.loads(data_str)

            # 更新实时数据
            if 'heart_rate' in data:
                self.realtime_data['heart_rate'] = int(data['heart_rate'])
            if 'blood_oxygen' in data:
                self.realtime_data['blood_oxygen'] = int(data['blood_oxygen'])
            if 'steps' in data:
                self.realtime_data['steps'] = int(data['steps'])
            if 'lat' in data:
                self.realtime_data['lat'] = float(data['lat'])
            if 'lon' in data:
                self.realtime_data['lon'] = float(data['lon'])
            if 'distance' in data:
                self.realtime_data['distance'] = float(data['distance'])
            if 'fence_status' in data:
                self.realtime_data['fence_status'] = data['fence_status']

        except json.JSONDecodeError:
            print("数据格式错误")

    def save_settings(self, instance):
        """保存设置到ESP8266"""
        try:
            # 更新设置
            self.settings['heart_rate_threshold'] = int(self.hr_input.text)
            self.settings['blood_oxygen_threshold'] = int(self.bo_input.text)
            self.settings['medication_time'] = self.med_input.text

            # 打包成JSON
            settings_json = json.dumps(self.settings, ensure_ascii=False)

            # 发送到ESP8266
            self.send_to_esp(settings_json)

            self.show_message('✓ 保存成功', '配置参数已下发到ESP8266')
        except ValueError:
            self.show_message('✗ 错误', '请输入有效的数值')

    def send_to_esp(self, data):
        """发送数据到ESP8266"""
        import socket

        try:
            if self.connected:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((self.esp_ip, self.esp_port))
                sock.send(data.encode('utf-8'))
                sock.close()
        except Exception as e:
            print(f"发送数据错误: {e}")

    def update_ui(self, dt):
        """更新UI显示"""
        # 更新心率
        hr = self.realtime_data['heart_rate']
        hr_text = str(hr)
        if hr > self.settings['heart_rate_threshold']:
            hr_color = (0.9, 0.2, 0.2, 1)  # 红色警告
        else:
            hr_color = (0.23, 0.51, 0.96, 1)

        # 更新血氧
        bo = self.realtime_data['blood_oxygen']
        bo_text = str(bo)
        if bo < self.settings['blood_oxygen_threshold']:
            bo_color = (0.9, 0.2, 0.2, 1)  # 红色警告
        else:
            bo_color = (0.13, 0.77, 0.37, 1)

        # 更新围栏状态
        fence_status = self.realtime_data['fence_status']
        fence_text = fence_status
        if fence_status == '越界':
            fence_color = (0.9, 0.2, 0.2, 1)  # 红色警告
        else:
            fence_color = (0.16, 0.80, 0.68, 1)

        # 更新卡片颜色和数值
        self.heart_card.children[1].text = hr_text
        self.update_card_color(self.heart_card, hr_color)

        self.blood_card.children[1].text = bo_text
        self.update_card_color(self.blood_card, bo_color)

        self.steps_card.children[1].text = str(self.realtime_data['steps'])

        self.fence_card.children[1].text = fence_text
        self.update_card_color(self.fence_card, fence_color)

        # 更新GPS信息
        self.lat_label.text = f'📍 纬度: {self.realtime_data["lat"]:.6f}'
        self.lon_label.text = f'📍 经度: {self.realtime_data["lon"]:.6f}'
        self.distance_label.text = f'📏 距离中心: {self.realtime_data["distance"]:.1f} 米'

        # 更新底部时间
        self.footer_label.text = f'最后更新: {datetime.now().strftime("%H:%M:%S")}'

    def update_card_color(self, card, color):
        """更新卡片背景颜色"""
        # 清除旧的画布指令
        card.canvas.before.clear()
        
        # 添加新的颜色和圆角矩形
        with card.canvas.before:
            Color(color[0], color[1], color[2], 1)
            rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[12, 12, 12, 12])
            card.bind(pos=rect.setter('pos'), size=rect.setter('size'))

    def show_message(self, title, message):
        """显示消息弹窗"""
        content = Label(text=message, font_size=16, color=(0.2, 0.2, 0.3, 1))
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.8, 0.25),
            background_color=(0.95, 0.95, 0.97, 1)
        )
        popup.open()

    def on_stop(self):
        """应用退出时清理资源"""
        self.running = False
        self.disconnect_from_esp()


if __name__ == '__main__':
    HealthWatchApp().run()
