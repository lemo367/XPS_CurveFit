import sys
from PyQt5.QtWidgets import QMainWindow, QMenu, QApplication
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Matplotlibのグラフを作成
        fig = Figure()
        self.canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.plot([1, 2, 3], [4, 5, 6])

        # ウィンドウにグラフを追加
        self.setCentralWidget(self.canvas)

        # グラフに右クリックしたときのコンテキストメニューを作成
        self.context_menu = QMenu(self)
        self.context_menu.addAction("コンテキストメニュー項目1")
        self.context_menu.addAction("コンテキストメニュー項目2")

        # グラフにマウスイベントを追加
        self.canvas.mpl_connect('button_press_event', self.on_click)

    def on_click(self, event):
        if event.button == Qt.RightButton:
            # Matplotlib座標系からPyQt5ウィンドウ座標系に変換
            x, y = self.canvas.mapToParent(event.x, event.y)

            # ウィンドウ内でのマウス座標を取得
            pos = self.mapFromGlobal(self.cursor().pos())

            # コンテキストメニューを表示
            if pos.x() == x and pos.y() == y:
                self.context_menu.exec_(self.mapToGlobal(pos))

            print(x, y, pos)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())
