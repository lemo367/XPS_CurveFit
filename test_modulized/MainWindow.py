import sys
from PyQt5.QtWidgets import(
    QMainWindow, QAction, QFileDialog, QApplication, QMdiArea, QMdiSubWindow, QLabel,
    QComboBox, QPushButton, QWidget, QDoubleSpinBox, QCheckBox, QVBoxLayout, QHBoxLayout, QMenu, QTextEdit)
import pandas as pd
import Fit_XPSSpectra as fXPS

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

        XPS_DataLoad = QAction('Open File', self)
        XPS_DataLoad.setStatusTip('Load XPS Data. Currently supports Kratos XPS data.')
        XPS_DataLoad.triggered.connect(self.XPS_DataReshape)

        XRD_PoleFigure = QAction("Pole Figure", self)
        XRD_PoleFigure.setStatusTip("Plot pole figure")

        #toolBarに表示する項目の定義
        fileMenu = toolbar.addMenu('&File') #fileに関するツール
        fileMenu.addAction(openFile)

        Menu_XPS = toolbar.addMenu("&XPS") #XPS解析に使用するツール, fittingに関するものを実装予定
        Menu_XPS.addAction(XPS_DataLoad)
        Menu_XPS.addAction(XPS_PeakFit)

        Menu_XRD = toolbar.addMenu("&XRD") #XRDのプロットに関するツールを実装予定, 一番は極点図, omega-2thetaは汎用プロット機能が実装できればそれでよい
        Menu_XRD.addAction(XRD_PoleFigure)

        self.setGeometry(0, 0, 1280, 800) #Main Windowのサイズ, (x, y, width, height)
        self.setWindowTitle('Main Window') #Main Windowのタイトル
        self.show() #Main Windowの表示

    def fileDialog(self):
        # 第二引数はダイアログのタイトル、第三引数は表示するパス
        fPath = QFileDialog.getOpenFileName(self, 'Open file', '/home', '*csv')

        # fname[0]は選択したファイルのパス（ファイル名を含む）
        if fPath[0]:
            dataset = pd.read_csv(fPath[0], header = 32)

    #XPSのデータを読み込むメソッド, 複数のデータの分割にも対応
    def XPS_DataReshape(self):
        loader = fXPS.FileLoader()
        loader.XPS_DataReshape()

    #XPSのfittingに際して使用する各種windowの表示を行うメソッド
    def show_XPSpanel(self):
        XPS = fXPS.XPS_FittingPanels()
        self.mdi.addSubWindow(XPS.PlotPanel)
        XPS.PlotPanel.show()
        self.mdi.addSubWindow(XPS.DataPanel)
        XPS.DataPanel.show()
        self.mdi.addSubWindow(XPS.FitPanel)
        XPS.FitPanel.show()
#-----------END class Main Window------------------


#実行部
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())