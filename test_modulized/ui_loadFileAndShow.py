import sys
from PyQt5.QtWidgets import(
    QMainWindow, QAction, QFileDialog, QApplication, QMdiArea, QMdiSubWindow, QLabel,
    QComboBox, QPushButton, QWidget, QDoubleSpinBox, QCheckBox, QVBoxLayout, QHBoxLayout, QMenu, QTextEdit)
import mtd_loadFileAndShow as mtd

#Definition of Main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.statusBar() #definition of statusBar at bottom of window

        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)

        #menuBarの表示
        menubar = self.menuBar()

        #menuBarのaction定義
        XPS = QAction("XPS", self)
        #XRD.setStatusTip("Plot XRD pattern, such as 2theta-omega, rocking curve, and pole figure, etc.")
        XPS.triggered.connect(self.showXPSdata)

        Menu_XRD = menubar.addMenu("&XPS")
        Menu_XRD.addAction(XPS)

        self.setGeometry(0, 0, 1280, 960) #Main Windowのサイズ, (x, y, width, height)
        self.setWindowTitle('main window') #Main Windowのタイトル
        self.show() #Main Windowの表示

    def showXPSdata(self):
        self.filedata = mtd.showFileData()
        self.mdi.addSubWindow(self.filedata.textWindow)
        self.filedata.textWindow.show()
        self.mdi.addSubWindow(self.filedata.controlPanel)
        self.filedata.controlPanel.show()

"""class showFileData(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.text = QTextEdit()
        self.text.setReadOnly(True)

        self.textWindow = QMdiSubWindow()
        self.textWindow.setWindowTitle("File Data")

        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.text)
        widget.setLayout(layout)
        self.textWindow.setWidget(widget)

        self.controlPanel = QMdiSubWindow()
        self.controlPanel.setWindowTitle("Control Panel")
        self.controlPanel.setFixedSize(200, 200)

        btnLoad = QPushButton("Browse", self.controlPanel)
        btnLoad.move(50, 100)
        btnLoad.clicked.connect(self.loadData)

    def loadData(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '/home')
        if fname[0]:
            with open(fname[0], 'r') as f:
                data = f.read()
                self.text.setText(data)"""

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindow()
    sys.exit(app.exec_())