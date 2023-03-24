import sys
from PyQt5.QtWidgets import QMainWindow, QMenu, QApplication, QMdiArea, QMdiSubWindow, QWidget, QVBoxLayout
from PyQt5.QtCore import QPoint
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # MDIウィンドウを作成
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)
        self.setGeometry(800, 300, 800, 600)

        # グラフ用のQWidgetを作成
        graph_widget = QWidget()
        layout = QVBoxLayout(graph_widget)

        # Matplotlibのグラフを作成
        fig = Figure()
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.plot([1, 2, 3], [4, 5, 6])
        layout.addWidget(canvas)

        # グラフをMDIウィンドウに追加
        self.sub_window = QMdiSubWindow()
        self.sub_window.setWidget(graph_widget)
        self.mdi.addSubWindow(self.sub_window)
        self.sub_window.show()

        # グラフに右クリックしたときのコンテキストメニューを作成
        self.context_menu = QMenu(self)
        self.context_menu.addAction("コンテキストメニュー項目1")
        self.context_menu.addAction("コンテキストメニュー項目2")

        # グラフにマウスイベントを追加
        canvas.mpl_connect('button_press_event', self.on_click)

    def on_click(self, event):
        if event.button == 3:
            canvas =  event.canvas
            fig = canvas.figure
            canvas_width, canvas_height = fig.get_size_inches()*fig.dpi
            transform = fig.transFigure
            x, y = event.x, event.y
            g_pos = self.mapToGlobal(self.sub_window.pos())
            x_global = g_pos.x() + x
            y_global = g_pos.y() - y + canvas_height

            print(event, g_pos, x_global, y_global)

            location = QPoint()
            location.setX(int(x_global))
            location.setY(int(y_global))
            # コンテキストメニューを表示
            self.context_menu.exec_(location)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())
