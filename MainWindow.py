import sys
from PyQt5.QtWidgets import (
    QMainWindow, QAction, QFileDialog, QApplication, QMdiArea, QMdiSubWindow, QLabel,
    QComboBox, QPushButton, QWidget, QDoubleSpinBox, QCheckBox, QVBoxLayout)
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure



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

        self.setGeometry(0, 0, 1600, 800) #Main Windowのサイズ, (x, y, width, height)
        self.setWindowTitle('Main Window') #Main Windowのタイトル
        self.show() #Main Windowの表示


    def fileDialog(self):
        # 第二引数はダイアログのタイトル、第三引数は表示するパス
        fPath = QFileDialog.getOpenFileName(self, 'Open file', '/home', '*csv')

        # fname[0]は選択したファイルのパス（ファイル名を含む）
        if fPath[0]:
            dataset = pd.read_csv(fPath[0], header = 32)

    #XPSのfittingに際して使用する各種windowの表示を行うメソッド
    def show_XPSpanel(self):
        self.XPS = XPS_FittingPanels()
        self.mdi.addSubWindow(self.XPS.FitPanel)
        self.mdi.addSubWindow(self.XPS.DataPanel)
        self.mdi.addSubWindow(self.XPS.PlotPanel)
        self.XPS.FitPanel.show()
        self.XPS.DataPanel.show()
        self.XPS.PlotPanel.show()
#-----------END class Main Window------------------


#XPSのfittingに際して使用するwindow類の定義クラス
class XPS_FittingPanels(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        #---------Setting for Fit Panel---------
        self.FitPanel = QMdiSubWindow()
        self.FitPanel.setWindowTitle("Fitting Panel")
        self.FitPanel.setFixedWidth(950)
        self.FitPanel.setFixedHeight(350)

        #コンボボックスの生成
        self.combo_SpectraName = QComboBox(self.FitPanel)
        self.combo_SpectraName.move(10, 30)
        self.combo_SpectraName.setFixedWidth(200)
        SpectraName = [1, 2, 3]
        for i in SpectraName:
            self.combo_SpectraName.addItem(f"{i}") #ループでリストの中身をコンボボックスの表示値に

        ReltMethod = ['Method 1', 'Method 2']
        self.combo_HowRelative = QComboBox(self.FitPanel)
        self.combo_HowRelative.move(395, 305)
        for i in ReltMethod:
            self.combo_HowRelative.addItem(f'{i}')

        AbsANDRel = ['Absol.', 'Relat.']
        self.Abs_Rel = QComboBox(self.FitPanel)
        self.Abs_Rel.move(255, 305)
        for i in AbsANDRel:
            self.Abs_Rel.addItem(f'{i}')

        #スピンボックスの生成
        for i in range(0, 36, 1):
            self.spinBOX = QDoubleSpinBox(self.FitPanel)
            if i <= 5:
                self.spinBOX.move(70+(140*i), 80)
                self.spinBOX.index = f"B.E. {i+1}"
            
            elif 6 <= i <= 11:
                self.spinBOX.move(70+(140*(i-6)), 110)
                self.spinBOX.index = f"Int. {i-5}"

            elif 12 <= i <= 17:
                self.spinBOX.move(70+(140*(i-12)), 140)
                self.spinBOX.index = f"W_gau. {i-11}"

            elif 18 <= i <= 23:
                self.spinBOX.move(70+(140*(i-18)), 170)
                self.spinBOX.index = f"Gamma {i-17}"

            elif 24 <= i <= 29:
                self.spinBOX.move(70+(140*(i-24)), 200)
                self.spinBOX.index = f"S.O.S. {i-23}"

            elif 30 <= i <= 35:
                self.spinBOX.move(70+(140*(i-30)), 230)
                self.spinBOX.index = f"B.R. {i-29}"

        for i in range(0, 2, 1):
            self.BGspinBOX = QDoubleSpinBox(self.FitPanel)
            self.BGspinBOX.move(70, 275+30*i)
            self.BGspinBOX.index = f'B.G. {i}'

        #チェックボックスの生成
        for i in range(0, 36, 1):
            self.CheckBox = QCheckBox(self.FitPanel)
            if i <= 5:
                self.CheckBox.move(180+(140*i), 80)
                self.CheckBox.index = f"Check_B.E. {i+1}"
            
            elif 6 <= i <= 11:
                self.CheckBox.move(180+(140*(i-6)), 110)
                self.CheckBox.index = f"Check_Int. {i-5}"

            elif 12 <= i <= 17:
                self.CheckBox.move(180+(140*(i-12)), 140)
                self.CheckBox.index = f"Check_W_gau. {i-11}"

            elif 18 <= i <= 23:
                self.CheckBox.move(180+(140*(i-18)), 170)
                self.CheckBox.index = f"Check_Gamma {i-17}"

            elif 24 <= i <= 29:
                self.CheckBox.move(180+(140*(i-24)), 200)
                self.CheckBox.index = f"Check_S.O.S. {i-23}"

            elif 30 <= i <= 35:
                self.CheckBox.move(180+(140*(i-30)), 230)
                self.CheckBox.index = f"Check_B.R. {i-29}"

        for i in range(0, 2, 1):
            self.BGcheckBOX = QCheckBox(self.FitPanel)
            self.BGcheckBOX.move(180, 275+30*i)
            self.BGcheckBOX.index = f'Check_B.G. {i}'


        #各種ラベルの定義
        ParamName = ['B.E.', 'Int.', 'Wid_G', 'gamma', 'S.O.S.', 'B.R.']
        for i in range(len(ParamName)):
            self.Label_Param = QLabel(ParamName[i], self.FitPanel)
            self.Label_Param.move(20, 30*i+80)

        No_composition = [f'Comp. {i}' for i in range(1, 7, 1)]
        for i in range(len(No_composition)):
            self.Label_comp = QLabel(No_composition[i], self.FitPanel)
            self.Label_comp.move(90+(140*i), 55)

        for i in range(0, 6, 1):
            self.Label_hold = QLabel('Hold', self.FitPanel)
            self.Label_hold.move(175+(140*i), 55)

        Tips = ['B.E. value: Absolute/Relative', 'Method 1: All B.E. values are relative to Comp. 1', 'Method 2: Relative values are Comp. 2 (to Comp. 1), Comp. 4 (to Comp. 3)...']
        for i in range(len(Tips)):
            self.Label_Tips = QLabel(f'<p><font size="2.5">{Tips[i]}</font></p>', self.FitPanel)
            if i < 1:
                self.Label_Tips.move(240, 285)
                self.Label_Tips.setFixedWidth(130)
            else:
                self.Label_Tips.move(500, 300+15*(i-1))
                self.Label_Tips.setFixedWidth(335)

        BGCoeff = ['Slope', 'Intercept']
        for i in range(len(BGCoeff)):
            self.Label_BGCoeff = QLabel(BGCoeff[i], self.FitPanel)
            self.Label_BGCoeff.move(10, 275+30*i)

        #ボタンの生成
        ButtonName_Fit = ['Open Graph', 'Check', 'Fit']
        for i in range(len(ButtonName_Fit)):
            self.Button_Fit = QPushButton(ButtonName_Fit[i], self.FitPanel)
            self.Button_Fit.move(250+(90*i), 30)
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
        RangeX = [] #Dataの横軸に関する量、またはDataFrameの列名などが入る予定
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

        BGSubstractionMethod = ['Shirley', 'Linear']
        self.combo_BGsubs = QComboBox(self.DataPanel)
        self.combo_BGsubs.move(20, 180)
        for i in BGSubstractionMethod:
            self.combo_BGsubs.addItem(i)

        #ボタンの生成
        ButtonName_Data = ['Draw Graph', 'Make Processed Wave', 'Substract']
        for i in range(len(ButtonName_Data)):
            self.Button_Data = QPushButton(ButtonName_Data[i], self.DataPanel)
            self.Button_Data.index = ButtonName_Data[i]

            if i == 0:
                self.Button_Data.move(20+(90*i), 110)

            elif i == 1:
                self.Button_Data.move(20+(90*i), 110)
                self.Button_Data.setFixedWidth(180)

            else:
                self.Button_Data.move(110, 180)

        #各種ラベル
        self.Label_BGmethod = QLabel('<p><font size="3">Choose substraction method of background</font></p>', self.DataPanel)
        self.Label_BGmethod.move(10, 160)
        self.Label_BGmethod.setFixedWidth(270)
        #---------Setting for Data Panel----------

        #---------Setting for Plot Panel----------
        self.PlotPanel = QMdiSubWindow()
        self.PlotPanel.setWindowTitle("Graph")
        self.PlotPanel.setGeometry(250, 250, 500, 500)
        
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self.PlotPanel)
        
        
        #---------Setting for Plot Panel------------

        



#実行部
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())