import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QComboBox
from PyQt6.QtCore import QTimer
from interface import Ui_Form
from serial_handler import serialManager
baud_rates = [
    "1200", "2400", "4800", "9600", "19200", "38400",
    "57600", "115200", "230400", "460800", "921600", "1000000"
]
data_bits = ["8", "7", "6", "5"]
stop_bits = ["1", "1.5", "2"]
parity_check = ["None", "Odd", "Even"]

class MyMainForm(QMainWindow, Ui_Form):
    def __init__(self, parent=None):
        super(MyMainForm, self).__init__(parent)
        self.setupUi(self)
        # 给两个下拉框都绑定刷新串口列表的功能
        self.setup_serial_combobox(self.controlSerialBox)
        self.setup_serial_combobox(self.dataSerialBox)
        self.controlBaudBox.addItems(baud_rates)
        self.dataBaudBox.addItems(baud_rates)
        self.cfgDataBitBox.addItems(data_bits)
        self.cfgStopBitBox.addItems(stop_bits)
        self.cfgParityCheckBox.addItems(parity_check)
        self.controlBaudBox.setCurrentText("115200")
        self.dataBaudBox.setCurrentText("1000000")
        self.cfgDataBitBox.setCurrentText("8")
        self.cfgStopBitBox.setCurrentText("1")
        self.cfgParityCheckBox.setCurrentText("None")
        self.serial_manager = serialManager()
        self.connectButton.clicked.connect(self.toggle_serials)
        self.sendButton.clicked.connect(self.send_data_from_edit)
        self.sendClearButton.clicked.connect(self.edit_data_clear)
        self.terminalClearButton.clicked.connect(self.terminal_clear)
        self._history_buffer = bytearray()
        self.isHexShowBox.stateChanged.connect(self.toggle_hex_display)
        self.serial_manager.control_callback = self.control_data_received #注册回调
        self.serial_manager.data_callback = self.data_data_received
        self.terminalControlButton.setChecked(True)
        self._control_buffer = bytearray()
        self._data_buffer = bytearray()
        self.isControlSerial = True
        self.terminalControlButton.toggled.connect(lambda: self.dual_selection(self.terminalControlButton))
        self.terminalDataButton.toggled.connect(lambda: self.dual_selection(self.terminalDataButton))
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.flush_terminal)
        self.update_timer.start(50)
    def setup_serial_combobox(self, combobox: QComboBox):
        """初始化串口下拉框，使其点击时刷新列表"""
        combobox.showPopup = lambda cb=combobox: self.refresh_ports_and_show(cb)

    def refresh_ports_and_show(self, combobox: QComboBox):
        """刷新串口列表并展开下拉"""
        combobox.blockSignals(True)
        combobox.clear()
        combobox.addItem("请选择串口号", None)
        for port, desc in self.serial_manager.list_ports():
            combobox.addItem(f"{port} - {desc}", port)
        combobox.blockSignals(False)
        # 展开下拉
        QComboBox.showPopup(combobox)

    def selection_changed(self, combobox: QComboBox, index: int):
        port = combobox.itemData(index)
        if port:
            print(f"{combobox.objectName()} 选择的串口号：{port}")

    def toggle_serials(self):
        if not self.serial_manager.is_connected:
            control_port = self.controlSerialBox.currentData()
            data_port = self.dataSerialBox.currentData()
            control_baud = int(self.controlBaudBox.currentText())
            data_baud = int(self.dataBaudBox.currentText())
            if control_port and data_port:
                if self.serial_manager.connect(control_port, control_baud, data_port, data_baud):
                    self.connectButton.setText("断开串口")
                else:
                    self.connectButton.setText("连接失败")
            else:
                self.connectButton.setText("串口缺失")
        else:
            self.serial_manager.disconnect()
            self.connectButton.setText("连接串口")
    def control_data_received(self, data):
        self._control_buffer.extend(data)

    def data_data_received(self, data):
        self._data_buffer.extend(data)

    def dual_selection(self, btn):
        if btn.text() == self.terminalControlButton.text():
            if btn.isChecked() == True:
                print(btn.text() + " is selected")
                self.isControlSerial = True
        if btn.text() == self.terminalDataButton.text():
            if btn.isChecked() == True:
                print(btn.text() + " is selected")
                self.isControlSerial = False

    def flush_terminal(self):
        """定时器调用 → 批量更新 UI"""
        if self.isControlSerial and self._control_buffer:
            self._history_buffer.extend(self._control_buffer)
            if self.isHexShowBox.isChecked():
                text = " ".join(f"{b:02X}" for b in self._control_buffer)
            else:
                text = self._control_buffer.decode("utf-8", errors="replace")
            self.terminalBrowser.insertPlainText(text)
            self._control_buffer.clear()
        elif not self.isControlSerial and self._data_buffer:
            if self.isHexShowBox.isChecked():
                text = " ".join(f"{b:02X}" for b in self._data_buffer)
            else:
                text = self._data_buffer.decode("utf-8", errors="replace")
            self.terminalBrowser.insertPlainText(text)
            self._data_buffer.clear()

    def toggle_hex_display(self, state):
        """切换Hex/Text显示模式时，刷新整个历史"""
        self.terminalBrowser.clear()
        if not self._history_buffer:
            return

        if self.isHexShowBox.isChecked():
            text = " ".join(f"{b:02X}" for b in self._history_buffer)
        else:
            text = self._history_buffer.decode("utf-8", errors="replace")
        self.terminalBrowser.setPlainText(text)

    def terminal_clear(self):
        self.terminalBrowser.clear()
        self._history_buffer.clear()

    def send_data_from_edit(self):
        """点击按钮，把 sendEdit 的内容发到当前选择的串口"""
        text = self.sendEdit.toPlainText()  # 获取输入框内容（QTextEdit 用 toPlainText）
        if not text.strip():
            return  # 空内容就不发
        if self.isSendNewLineBox.isChecked():
            text += "\r\n"
        data = text.encode("utf-8", errors="replace")  # 转成字节
        if self.isControlSerial:
            self.serial_manager.send_control(data)
        else:
            self.serial_manager.send_data(data)

    def edit_data_clear(self):
        self.sendEdit.clear()

if __name__ == "__main__":
    #固定的，PyQt程序都需要QApplication对象。sys.argv是命令行参数列表，确保程序可以双击运行
    app = QApplication(sys.argv)
    #初始化
    myWin = MyMainForm()
    #将窗口控件显示在屏幕上
    myWin.show()
    #程序运行，sys.exit方法确保程序完整退出。
    sys.exit(app.exec())
