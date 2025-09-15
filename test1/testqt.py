
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from test1 import Ui_Form

class MyMainForm(QMainWindow, Ui_Form):
    def __init__(self, parent=None):
        super(MyMainForm, self).__init__(parent)
        self.setupUi(self)
        self.runButton.clicked.connect(self.display)
        self.exitButton.clicked.connect(self.close)
        self.backButton.clicked.connect(lambda: self.backpage())
        self.nextButton.clicked.connect(lambda: self.nextpage())
    def display(self):
        num1 = int(self.num1.text())
        num2 = int(self.num2.text())
        num3 = num1 + num2
        self.displayBrowser.setText(str(num1) + "+" + str(num2) + "=" + str(num3))
    def backpage(self):
        self.stackedWidget.setCurrentIndex(0)

    def nextpage(self):
        self.stackedWidget.setCurrentIndex(1)


if __name__ == "__main__":
    #固定的，PyQt程序都需要QApplication对象。sys.argv是命令行参数列表，确保程序可以双击运行
    app = QApplication(sys.argv)
    #初始化
    myWin = MyMainForm()
    #将窗口控件显示在屏幕上
    myWin.show()
    #程序运行，sys.exit方法确保程序完整退出。
    sys.exit(app.exec())