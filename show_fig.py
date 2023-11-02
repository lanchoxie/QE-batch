import sys
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QSizePolicy, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

fig_in=sys.argv[1]
size_x=int(sys.argv[2])
size_y=int(sys.argv[3])

class ScatterPlotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, size_x*100, size_y*100)
        # 设置窗口标题
        self.setWindowTitle("Scatter Plot Viewer")

        # 创建一个主窗口部件
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)

        # 创建一个垂直布局
        layout = QVBoxLayout(main_widget)

        # 创建一个标签用于显示图像
        self.image_label = QLabel(self)
        layout.addWidget(self.image_label)

        # 调整图像标签的大小策略，以自适应图像大小
        #self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        #self.image_label.setScaledContents(True)

        # 加载并显示图像
        self.load_image(fig_in)

    def load_image(self, image_path):
        #将图像等比放大100倍
        pixmap = QPixmap(image_path)
        pixmap = pixmap.scaled(size_x * 100, size_y * 100, aspectRatioMode=Qt.KeepAspectRatio)
        self.image_label.setPixmap(pixmap)

def main():
    windows = []
    app = QApplication(sys.argv)
    window = ScatterPlotApp()
    window.show()
    windows.append(window)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

