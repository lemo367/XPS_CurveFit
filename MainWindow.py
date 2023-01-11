import sys
import re
from PyQt5.QtWidgets import (
    QMainWindow, QAction, QFileDialog, QApplication, QMdiArea, QMdiSubWindow, QLabel,
    QComboBox, QPushButton, QWidget, QDoubleSpinBox, QCheckBox, QVBoxLayout)
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import numpy as np

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

        self.setGeometry(0, 0, 960, 720) #Main Windowのサイズ, (x, y, width, height)
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
        loader = FileLoader()
        loader.XPS_DataReshape()

    #XPSのfittingに際して使用する各種windowの表示を行うメソッド
    def show_XPSpanel(self):
        self.XPS = XPS_FittingPanels()
        self.mdi.addSubWindow(self.XPS.PlotPanel)
        self.XPS.PlotPanel.show()
        self.mdi.addSubWindow(self.XPS.DataPanel)
        self.XPS.DataPanel.show()
        self.mdi.addSubWindow(self.XPS.FitPanel)
        self.XPS.FitPanel.show()
#-----------END class Main Window------------------


#----------データの読み込みに関するクラス-----------
class FileLoader(QWidget):
    XPS_Dict_DF = {} #分割したXPSテキストデータをDataframeとして読み込み、管理する辞書

    def __init__(self) -> None:
        super().__init__()
    
    #XPSのデータを読み込むメソッド, 複数のデータの分割にも対応
    def XPS_DataReshape(self):
        # 第二引数はダイアログのタイトル、第三引数は表示するパス
        fname = QFileDialog.getOpenFileName(self, 'Open file', '/home')

        # fname[0]は選択したファイルのパス（ファイル名を含む）
        if fname[0]:
            # ファイル読み込み
            f = open(fname[0], 'r')
            # テキストエディタにファイル内容書き込み
            with f:
                self.data = f.read()
        
            LO_Dataset = [i.span() for i in re.finditer('Dataset', self.data)] #Location of 'Dataset'
            LO_colon = [i.start() for i in re.finditer(':', self.data)] #Location of ':' (colon)
            len_Data = len(self.data) #Length of data as nomber of characters
            SpectraName = [self.data[LO_Dataset[i][1]+1 : LO_colon[i]] for i in range(len(LO_colon))] #Spectra name List
        
            if len(LO_Dataset) != 1:
                #--------ファイル分割処理---------
                Dict_Data = {} #分割したテキストデータを管理する辞書
                for i in range(len(LO_Dataset)):
                    if i+1 < len(LO_Dataset):
                        Div_data = self.data[LO_Dataset[i][0] : LO_Dataset[i+1][0]]

                    elif i+1 == len(LO_Dataset):
                        Div_data = self.data[LO_Dataset[i][0] : len_Data]
            
                    Dict_Data[SpectraName[i]] = Div_data #辞書に分割したテキストデータを追加

                LO_SlashinPath = fname[0].rfind('/')
                PrefixDir = fname[0][0 : LO_SlashinPath]
                Div_DataFilePath = [f'{PrefixDir}/{i}.txt' for i in SpectraName] #分割したテキストデータのファイルパスのリスト

                for i in range(len(Div_DataFilePath)):
                    with open(Div_DataFilePath[i], mode = 'w') as f:
                        f.write(Dict_Data[SpectraName[i]])

                    dataset = pd.read_csv(Div_DataFilePath[i], header = 3, delimiter = '\t') #分割したテキストデータをDataframeとして読み込み
                    self.XPS_Dict_DF[SpectraName[i]] = dataset #辞書に読み込んだDataframeを追加
            #------------ファイル分割処理--------------

            else:
                dataset = pd.read_csv(fname[0], header = 3, delimiter = '\t')
                self.XPS_Dict_DF[SpectraName[0]] = dataset


#XPSのfittingに際して使用するwindow類の定義クラス
class XPS_FittingPanels(QWidget):
    gco = None

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        fileloader = FileLoader()
        SpectraName = list(fileloader.XPS_Dict_DF.keys())

        #---------Setting for Fit Panel---------
        self.FitPanel = QMdiSubWindow()
        self.FitPanel.setWindowTitle("Fitting Panel")
        self.FitPanel.setFixedWidth(950)
        self.FitPanel.setFixedHeight(350)

        #コンボボックスの生成
        self.combo_SpectraName = QComboBox(self.FitPanel)
        self.combo_SpectraName.move(10, 30)
        self.combo_SpectraName.setFixedWidth(200)
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
        self.combo_DataName = QComboBox(self.DataPanel)
        self.combo_DataName.move(120, 43)
        self.combo_DataName.setFixedWidth(120)
        self.combo_DataName.activated.connect(self.activated)
        self.combo_DataName.currentTextChanged.connect(self.text_changed)
        self.combo_DataName.currentIndexChanged.connect(self.index_changed)
        for i in SpectraName:
            self.combo_DataName.addItem(f'{i}')
        self.Label_DataName = QLabel('Choose spectra', self.DataPanel)
        self.Label_DataName.move(20, 40)

        BGSubstractionMethod = ['Shirley', 'Linear']
        self.combo_BGsubs = QComboBox(self.DataPanel)
        self.combo_BGsubs.move(30, 250)
        self.combo_BGsubs.setFixedWidth(120)
        for i in BGSubstractionMethod:
            self.combo_BGsubs.addItem(i)

        #スピンボックスの生成
        for i in range(0, 2, 1):
            self.spinDPP = QDoubleSpinBox(self.DataPanel) # DPP : Data Preparation Panel
            self.spinDPP.setGeometry(10+140*i , 130, 130, 30)
        self.LabelRange = QLabel('Fitting range (start, end)', self.DataPanel)
        self.LabelRange.setGeometry(65, 105, 150, 20)
        
        #ボタンの生成
        ButtonName_Data = ['Draw Graph', 'Make Processed Wave', 'Substract']
        for i in range(len(ButtonName_Data)):
            self.Button_Data = QPushButton(ButtonName_Data[i], self.DataPanel)
            self.Button_Data.index = ButtonName_Data[i]
            self.Button_Data.clicked.connect(self.XPSPlot_DPP)

            if i == 0:
                self.Button_Data.move(10+(90*i), 160)

            elif i == 1:
                self.Button_Data.move(10+(90*i), 160)
                self.Button_Data.setFixedWidth(180)

            else:
                self.Button_Data.move(145, 248)

        #各種ラベル
        self.Label_BGmethod = QLabel('<p><font size="3">Choose substraction method of background</font></p>', self.DataPanel)
        self.Label_BGmethod.move(10, 220)
        self.Label_BGmethod.setFixedWidth(270)
        #---------Setting for Data Panel----------

        #---------Setting for Plot Panel----------
        self.PlotPanel = QMdiSubWindow()
        self.PlotPanel.setWindowTitle("Graph")
        self.PlotPanel.setGeometry(250, 250, 500, 500)
        
        config = {
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.major.width": 1.0,
            "ytick.major.width": 1.0,
            "xtick.minor.width": 1.0,
            "ytick.minor.width": 1.0,
            "xtick.major.size": 5.0,
            "ytick.major.size": 5.0,
            "xtick.minor.size": 3.0,
            "ytick.minor.size": 3.0,
            "font.family": "Arial",
            "font.size": 12
        }
        plt.rcParams.update(config)

        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.spines["top"].set_visible(False) #プロット外周部の黒枠削除
        self.ax.spines["right"].set_visible(False) #プロット外周部の黒枠削除
        self.ax.set_xlabel(xlabel = 'Binding Energy (eV)', fontsize = 14)
        self.ax.invert_xaxis()
        self.ax.set_ylabel(ylabel = 'Intensity (a. u.)', fontsize = 14)
        self.ax.minorticks_on()

        self.canvas = FigureCanvasQTAgg(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self.PlotPanel)
        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.toolbar)        
        self.layout.addWidget(self.canvas)
        
        self.widget = QWidget()
        self.widget.setLayout(self.layout)
        self.PlotPanel.setWidget(self.widget)

        self.Fit_s = self.ax.plot(0, 0, 'v', picker = 10)
        self.Fit_e = self.ax.plot(1, 0, '^', picker = 10)

        self.fig.canvas.mpl_connect('motion_notify_event', self.motion)
        self.fig.canvas.mpl_connect('pick_event', self.onpick)
        self.fig.canvas.mpl_connect('button_release_event', self.release)

        self.canvas.draw()
        #---------Setting for Plot Panel------------

    def XPSPlot_DPP(self):
        Button = self.sender()
        loader = FileLoader()

        if Button.text() == 'Draw Graph' and loader.XPS_Dict_DF != {}:
            DataKey = self.combo_DataName.currentText()
            BindingEnergy = loader.XPS_Dict_DF[DataKey]['Binding Energy(eV)']
            Intensity = loader.XPS_Dict_DF[DataKey]['Intensity(cps)']

            self.ax.cla()
            self.ax.set_xlabel(xlabel = 'Binding Energy (eV)', fontsize = 14)
            self.ax.invert_xaxis()
            self.ax.set_ylabel(ylabel = 'Intensity (a. u.)', fontsize = 14)
            self.ax.minorticks_on()
            self.ax.set_yticks([])
            
            self.Fit_s = self.ax.plot(BindingEnergy[0], Intensity[0], 'v', c = 'red', picker = 10)
            self.Fit_e = self.ax.plot(BindingEnergy[len(BindingEnergy)-1], Intensity[len(Intensity)-1], '^', c = 'orange', picker = 10)
            self.ax.plot(loader.XPS_Dict_DF[DataKey]['Binding Energy(eV)'], loader.XPS_Dict_DF[DataKey]['Intensity(cps)'])
            self.canvas.draw()
            print(DataKey)
            print(Button.text())

        elif Button.text() == 'Make Processed Wave' and loader.XPS_Dict_DF != {}:
            DataKey = self.combo_DataName.currentText()
            BindingEnergy = loader.XPS_Dict_DF[DataKey]['Binding Energy(eV)']
            Intensity = loader.XPS_Dict_DF[DataKey]['Intensity(cps)']
            
            FitStart = self.Fit_s[0].get_xydata()[0][0]
            FitEnd = self.Fit_e[0].get_xydata()[0][0]
            list_idxSE = [np.abs(np.array(BindingEnergy) - FitStart).argmin(), np.abs(np.array(BindingEnergy) - FitEnd).argmin()] #[Start, End]の順で格納、FitStartおよびEndと最も近い値のindexをDataFrameから取得する
            
            df_processed = pd.DataFrame({'Binding Energy(eV)': np.array(BindingEnergy[list_idxSE[0]:list_idxSE[1]]), 'Intensity(cps)': np.array(Intensity[list_idxSE[0]:list_idxSE[1]])})
            loader.XPS_Dict_DF[f'{DataKey}_proc'] = df_processed
            
            self.combo_DataName.clear()
            SpectraName = list(loader.XPS_Dict_DF.keys())
            for i in SpectraName:
                self.combo_DataName.addItem(f'{i}')
            print(loader.XPS_Dict_DF)

        else:
            return

    def motion(self, event):
        if self.gco == None:
            return
        x = event.xdata
        y = event.ydata
        self.gco.set_data(x,y)
        self.canvas.draw()

    def onpick(self, event):
        self.gco = event.artist

    def release(self, event):
        self.gco = None

    def activated(Self, index):
        print("Activated index:", index)

    def text_changed(self, s):
        print("Text changed:", s)

    def index_changed(self, index):
        print("Index changed", index)


#実行部
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())