
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from interface import Ui_Form

class MyMainForm(QMainWindow, Ui_Form):
    def __init__(self, parent=None):
        super(MyMainForm, self).__init__(parent)
        self.setupUi(self)


if __name__ == "__main__":
    #固定的，PyQt程序都需要QApplication对象。sys.argv是命令行参数列表，确保程序可以双击运行
    app = QApplication(sys.argv)
    #初始化
    myWin = MyMainForm()
    #将窗口控件显示在屏幕上
    myWin.show()
    #程序运行，sys.exit方法确保程序完整退出。
    sys.exit(app.exec())