import platform
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import QPixmap, QPainter, QPoint, QPaintEvent, QMouseEvent, QPen, QColor, QSize
from PyQt5.QtCore import Qt
from PyQt5.Qt import QWidget, QColor, QPixmap, QIcon, QSize, QCheckBox
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QPushButton, QSplitter, QComboBox, QLabel, QSpinBox, QFileDialog
import tensorflow as tf
from tensorflow.keras import models
from tensorflow.keras import layers
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
 
 
def main():
    app = QApplication(sys.argv)
 
    mainWidget = MainWidget() #新建一个主界面
    mainWidget.show()    #显示主界面
 
    exit(app.exec_()) #进入消息循环
 
 
class PaintBoard(QWidget):
 
    def __init__(self, Parent=None):
        '''
        Constructor
        '''
        super().__init__(Parent)
 
        self.__InitData()  # 先初始化数据，再初始化界面
        self.__InitView()
        self.setWindowTitle("画笔")
 
    def __InitData(self):
 
        self.__size = QSize(280, 280)
 
        # 新建QPixmap作为画板，尺寸为__size
        self.__board = QPixmap(self.__size)
        self.__board.fill(Qt.black)  # 用黑色填充画板
 
        self.__IsEmpty = True  # 默认为空画板
 
        self.__lastPos = QPoint(0, 0)  # 上一次鼠标位置
        self.__currentPos = QPoint(0, 0)  # 当前的鼠标位置
 
        self.__painter = QPainter()  # 新建绘图工具
 
        self.__thickness = 10  # 默认画笔粗细为10px
        self.__penColor = QColor("white")  # 设置默认画笔颜色为白色
 
    def __InitView(self):
        # 设置界面的尺寸为__size
        self.setFixedSize(self.__size)
 
    def Clear(self):
        # 清空画板
        self.__board.fill(Qt.black)
        self.update()
        self.__IsEmpty = True
 
 
    def IsEmpty(self):
        # 返回画板是否为空
        return self.__IsEmpty
 
    def GetContentAsQImage(self):
        # 获取画板内容（返回QImage）
        image = self.__board.toImage()
        return image
 
    def paintEvent(self, paintEvent):
        # 绘图事件
        # 绘图时必须使用QPainter的实例，此处为__painter
        # 绘图在begin()函数与end()函数间进行
        # begin(param)的参数要指定绘图设备，即把图画在哪里
        # drawPixmap用于绘制QPixmap类型的对象
        self.__painter.begin(self)
        # 0,0为绘图的左上角起点的坐标，__board即要绘制的图
        self.__painter.drawPixmap(0, 0, self.__board)
        self.__painter.end()
 
    def mousePressEvent(self, mouseEvent):
        # 鼠标按下时，获取鼠标的当前位置保存为上一次位置
        self.__currentPos = mouseEvent.pos()
        self.__lastPos = self.__currentPos
 
    def mouseMoveEvent(self, mouseEvent):
        # 鼠标移动时，更新当前位置，并在上一个位置和当前位置间画线
        self.__currentPos = mouseEvent.pos()
        self.__painter.begin(self.__board)
        self.__painter.setPen(QPen(self.__penColor, self.__thickness))  # 设置画笔颜色，粗细
        # 画线
        self.__painter.drawLine(self.__lastPos, self.__currentPos)
        self.__painter.end()
        self.__lastPos = self.__currentPos
 
        self.update()  # 更新显示
 
    def mouseReleaseEvent(self, mouseEvent):
        self.__IsEmpty = False  # 画板不再为空
 
 
class MainWidget(QWidget):
 
    def __init__(self, Parent=None):
        '''
        Constructor
        '''
        super().__init__(Parent)
 
        self.__InitData()  # 先初始化数据，再初始化界面
        self.__InitView()
 
    def __InitData(self):
        '''
                  初始化成员变量
        '''
        self.__paintBoard = PaintBoard(self)
 
    def __InitView(self):
        '''
                  初始化界面
        '''
        self.setFixedSize(550, 300)
        self.setWindowTitle("Predictive handwritten digits")
 
        # 新建一个水平布局作为本窗体的主布局
        main_layout = QHBoxLayout(self)
        # 设置主布局内边距以及控件间距为10px
        main_layout.setSpacing(10)
 
        # 在主界面左侧放置画板
        main_layout.addWidget(self.__paintBoard)
 
        # 新建垂直子布局用于放置按键
        sub_layout = QVBoxLayout()
 
        # 设置此子布局和内部控件的间距为10px
        sub_layout.setContentsMargins(10, 10, 10, 10)
 
        self.__btn_Clear = QPushButton("清空画板")
        self.__btn_Clear.setParent(self)  # 设置父对象为本界面
 
        # 将按键按下信号与画板清空函数相关联
        self.__btn_Clear.clicked.connect(self.__paintBoard.Clear)
        sub_layout.addWidget(self.__btn_Clear)
 
 
        self.__btn_Save = QPushButton("保存作品")
        self.__btn_Save.setParent(self)
        self.__btn_Save.clicked.connect(self.on_btn_Save_Clicked)
        sub_layout.addWidget(self.__btn_Save)
 
        self.__btn_Predict = QPushButton("预测")
        self.__btn_Predict.setParent(self)  # 设置父对象为本界面
        self.__btn_Predict.clicked.connect(self.Predict)
        sub_layout.addWidget(self.__btn_Predict)
 
        self.__btn_Quit = QPushButton("退出")
        self.__btn_Quit.setParent(self)  # 设置父对象为本界面
        self.__btn_Quit.clicked.connect(self.Quit)
        sub_layout.addWidget(self.__btn_Quit)
 
        self.__text_browser = QTextBrowser(self)
        self.__text_browser.setParent(self)
        sub_layout.addWidget(self.__text_browser)
 
        splitter = QSplitter(self)  # 占位符
        sub_layout.addWidget(splitter)
 
        main_layout.addLayout(sub_layout)  # 将子布局加入主布局
 
    def __fillColorList(self, comboBox):
 
        index_black = 0
        index = 0
        for color in self.__colorList:
            if color == "black":
                index_black = index
            index += 1
            pix = QPixmap(70, 20)
            pix.fill(QColor(color))
            comboBox.addItem(QIcon(pix), None)
            comboBox.setIconSize(QSize(70, 20))
            comboBox.setSizeAdjustPolicy(QComboBox.AdjustToContents)
 
        comboBox.setCurrentIndex(index_black)
 
    def on_PenColorChange(self):
        color_index = self.__comboBox_penColor.currentIndex()
        color_str = self.__colorList[color_index]
        self.__paintBoard.ChangePenColor(color_str)
 
    def on_PenThicknessChange(self):
        penThickness = self.__spinBox_penThickness.value()
        self.__paintBoard.ChangePenThickness(penThickness)
 
    def on_btn_Save_Clicked(self):
        image = self.__paintBoard.GetContentAsQImage()
        image.save('1.png')
 
    def Predict(self):
        # 调用模型
        newmodel = models.load_model('my_model.h5')
        # 读取图片
        # img = cv2.imread('1.png', 0)
        img = cv2.imread('1.png', 0)
        plt.imshow(img)
        # print(img.shape)
        img = cv2.resize(img, (28, 28))
 
        rows = img.shape[0]
        cols = img.shape[1]
        for i in range(rows):
            for j in range(cols):
                if (img[i, j] > 150):
                    img[i, j] = 255;
                else:
                    img[i, j] = 0;
 
        img = img.reshape(1, 28, 28, 1)
        img = img / 255  # 归一化
        # print(img.shape)
 
 
        predict = newmodel.predict(img)
        predict
        # print(predict)
        np.argmax(predict)
        # print("预测图像中的数字为：" + str(np.argmax(predict)))
        self.__text_browser.append("预测图像中的数字为：" + str(np.argmax(predict)))
        self.cursot = self.__text_browser.textCursor()
        self.__text_browser.moveCursor(self.cursot.End)
 
 
 
    def Quit(self):
        self.close()
 
 
if __name__ == '__main__':
    main()
 