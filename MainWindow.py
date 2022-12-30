import sys
from PyQt5.QtWidgets import (
    QMainWindow, QAction, QFileDialog, QApplication, QMdiArea, QMdiSubWindow, QLabel,
    QComboBox, QPushButton, QWidget)
import pandas as pd


#Definition of Main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.statusBar() #definition of statusBar at bottom of window

        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)

        #toolBarの表示
        toolbar = self.menuBar()

        #toolBarのaction定義
        openFile = QAction("Open", self) #ファイル読み込み
        openFile.setShortcut("Ctrl+O")
        openFile.setStatusTip('Open new File')
        openFile.triggered.connect(self.fileDialog) #クッリクした時の挙動をconnectで連結

        XPS_PeakFit = QAction("Peak Fitting", self)
        XPS_PeakFit.setStatusTip("Fit XPS spectra")
        XPS_PeakFit.triggered.connect(self.show_XPSpanel) #クッリクした時の挙動をconnectで連結

        XRD_PoleFigure = QAction("Pole Figure", self)
        XRD_PoleFigure.setStatusTip("Plot pole figure")

        #toolBarに表示する項目の定義
        fileMenu = toolbar.addMenu('&File') #fileに関するツール
        fileMenu.addAction(openFile)

        Menu_XPS = toolbar.addMenu("&XPS") #XPS解析に使用するツール, fittingに関するものを実装予定
        Menu_XPS.addAction(XPS_PeakFit)

        Menu_XRD = toolbar.addMenu("&XRD") #XRDのプロットに関するツールを実装予定, 一番は極点図, omega-2thetaは汎用プロット機能が実装できればそれでよい
        Menu_XRD.addAction(XRD_PoleFigure)

        self.setGeometry(0, 0, 1200, 800) #Main Windowのサイズ, (x, y, width, height)
        self.setWindowTitle('Main Window') #Main Windowのタイトル
        self.show() #Main Windowの表示


    def fileDialog(self):
        # 第二引数はダイアログのタイトル、第三引数は表示するパス
        fPath = QFileDialog.getOpenFileName(self, 'Open file', '/home', '*csv')

        # fname[0]は選択したファイルのパス（ファイル名を含む）
        if fPath[0]:
            dataset = pd.read_csv(fPath[0], header = 32)

    def show_XPSpanel(self):
        self.XPS = XPS_FittingPanel()
        self.mdi.addSubWindow(self.XPS.FitPanel)
        self.mdi.addSubWindow(self.XPS.DataPanel)
        self.XPS.FitPanel.show()
        self.XPS.DataPanel.show()


class XPS_FittingPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        #---------Setting for Fit Panel---------
        self.FitPanel = QMdiSubWindow()
        self.FitPanel.setWindowTitle("Fitting Panel")
        self.FitPanel.setFixedWidth(800)
        self.FitPanel.setFixedHeight(300)

        #コンボボックスの生成
        self.combo_SpectraName = QComboBox(self.FitPanel)
        self.combo_SpectraName.move(10, 30)
        self.combo_SpectraName.setFixedWidth(200)
        SpectraName = [1, 2, 3]
        for i in SpectraName:
            self.combo_SpectraName.addItem(f"{i}") #ループでリストの中身をコンボボックスの表示値に

        #ボタンの生成
        ButtonName = ['Open Graph', 'Check', 'Fit']
        for i in range(len(ButtonName)):
            self.Button = QPushButton(ButtonName[i], self.FitPanel)
            self.Button.move(250+(90*i), 30)
        #---------Setting for Fit Panel----------

        #---------Setting for Data Panel----------
        self.DataPanel = QMdiSubWindow()
        self.DataPanel.setWindowTitle("Data Preparation Panel")
        self.DataPanel.setFixedWidth(300)
        self.DataPanel.setFixedHeight(400)

        #コンボボックスの生成
        self.combo_DataX = QComboBox(self.DataPanel)
        self.combo_DataX.move(50, 50)
        self.combo_DataX.setFixedWidth(80)
        RangeX = []
        for i in RangeX:
            self.combo_DataX.addItem(f'{i}')
        self.Label_DataX = QLabel('X :', self.DataPanel)
        self.Label_DataX.move(20, 50)

        self.combo_DataY = QComboBox(self.DataPanel)
        self.combo_DataY.move(50, 80)
        self.combo_DataY.setFixedWidth(120)
        for i in SpectraName:
            self.combo_DataY.addItem(f'{i}')
        self.Label_DataY = QLabel('Y :', self.DataPanel)
        self.Label_DataY.move(20, 80)
        #---------Setting for Data Panel----------


#実行部
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
