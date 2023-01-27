import sys
import re
from PyQt5.QtWidgets import (
    QMainWindow, QAction, QFileDialog, QApplication, QMdiArea, QMdiSubWindow, QLabel,
    QComboBox, QPushButton, QWidget, QDoubleSpinBox, QCheckBox, QVBoxLayout)
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.cm as cm
import numpy as np
from scipy import integrate, optimize
import scipy.special
import itertools

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

    ParamName = ['B.E.', 'Int.', 'Wid_G', 'gamma', 'S.O.S.', 'B.R.']
    Dict_FitComps = {}
    Dict_CheckState = {}
    BindIndex = []
    guess_init = []
    FitParams = []
    AbsorRel = ''
    RelMethod = ''

    for i in range(1, 7, 1):
        Dict_FitComps[f'Comp. {i}'] = {f'{j}': 0 for j in ParamName}
        
        if i < 5:
            Dict_CheckState[f'Comp. {i}'] = {f'{j}': False for j in ParamName}
        
        else:
            Dict_CheckState[f'Comp. {i}'] = {f'{j}': True for j in ParamName}

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
        #for i in SpectraName:
        #    self.combo_SpectraName.addItem(f"{i}") #ループでリストの中身をコンボボックスの表示値に

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
            self.spinBOX.valueChanged.connect(self.getFitParams)
            self.spinBOX.setDecimals(3)

            if i <= 5:
                self.spinBOX.move(70+(140*i), 80)
                self.spinBOX.index = f"B.E. {i+1}"
                self.spinBOX.setRange(0, 1500)
                self.spinBOX.setSingleStep(0.5)

            elif 6 <= i <= 11:
                self.spinBOX.move(70+(140*(i-6)), 110)
                self.spinBOX.index = f"Int. {i-5}"
                self.spinBOX.setRange(0, 2000000)
                self.spinBOX.setSingleStep(100)

            elif 12 <= i <= 17:
                self.spinBOX.move(70+(140*(i-12)), 140)
                self.spinBOX.index = f"W_gau. {i-11}"
                self.spinBOX.setRange(0, 1000)
                self.spinBOX.setSingleStep(0.1)

            elif 18 <= i <= 23:
                self.spinBOX.move(70+(140*(i-18)), 170)
                self.spinBOX.index = f"Gamma {i-17}"
                self.spinBOX.setRange(0, 1000)
                self.spinBOX.setSingleStep(0.05)

            elif 24 <= i <= 29:
                self.spinBOX.move(70+(140*(i-24)), 200)
                self.spinBOX.index = f"S.O.S. {i-23}"
                self.spinBOX.setRange(0, 100)
                self.spinBOX.setSingleStep(0.1)

            elif 30 <= i <= 35:
                self.spinBOX.move(70+(140*(i-30)), 230)
                self.spinBOX.index = f"B.R. {i-29}"
                self.spinBOX.setRange(0, 1)
                self.spinBOX.setSingleStep(0.02)

        for i in range(0, 2, 1):
            self.BGspinBOX = QDoubleSpinBox(self.FitPanel)
            self.BGspinBOX.move(70, 275+30*i)
            self.BGspinBOX.index = f'B.G. {i}'

        #チェックボックスの生成
        for i in range(0, 36, 1):
            self.CheckBox = QCheckBox(self.FitPanel)
            self.CheckBox.stateChanged.connect(self.getCheckState)

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
                self.CheckBox.setChecked(True)

            elif 30 <= i <= 35:
                self.CheckBox.move(180+(140*(i-30)), 230)
                self.CheckBox.index = f"Check_B.R. {i-29}"
                self.CheckBox.setChecked(True)

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
        ButtonName_Fit = ['Open Graph', 'Check', 'Fit', 'add BG']
        for i in range(len(ButtonName_Fit)):
            self.Button_Fit = QPushButton(ButtonName_Fit[i], self.FitPanel)
            self.Button_Fit.move(250+(90*i), 30)
            self.Button_Fit.clicked.connect(self.XPSFit_FP)
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
        
        # グラフの初期設定値
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

        self.fig.canvas.mpl_connect('motion_notify_event', self.motion) #----------------------------------------------
        self.fig.canvas.mpl_connect('pick_event', self.onpick)          #グラフキャンバス上でのカーソルアクション定義
        self.fig.canvas.mpl_connect('button_release_event', self.release) #---------------------------------------------

        self.canvas.draw()
        #---------Setting for Plot Panel------------

    # Data Preparation Panelからデータをプロットおよびバックグラウンド処理するためのメソッド
    def XPSPlot_DPP(self):
        Button = self.sender()
        loader = FileLoader()

        DataKey = self.combo_DataName.currentText() #選択してるスペクトルの名前を格納
        if DataKey != '':
            BindingEnergy = np.array(loader.XPS_Dict_DF[DataKey]['Binding Energy(eV)']) # loader.XPS_Dict_DFはデータの読み込み時に作成したDataframeが格納されている辞書
            Intensity = np.array(loader.XPS_Dict_DF[DataKey]['Intensity(cps)'])

        if Button.text() == 'Draw Graph' and loader.XPS_Dict_DF != {}:
            self.ax.cla()
            self.ax.set_xlabel(xlabel = 'Binding Energy (eV)', fontsize = 14)
            self.ax.invert_xaxis()
            self.ax.set_ylabel(ylabel = 'Intensity (a. u.)', fontsize = 14)
            self.ax.minorticks_on()
            #self.ax.set_yticks([])
            
            self.Fit_s = self.ax.plot(BindingEnergy[0], Intensity[0], 'v', c = 'red', picker = 10) # fittingの範囲を切り出すためのドット
            self.Fit_e = self.ax.plot(BindingEnergy[-1], Intensity[-1], '^', c = 'orange', picker = 10) # 同上
            Spectrum = self.ax.plot(BindingEnergy, Intensity)
            self.canvas.draw()

        elif Button.text() == 'Make Processed Wave' and loader.XPS_Dict_DF != {}:
            FitStart = self.Fit_s[0].get_xydata()[0][0] # fittingの範囲を切り出すためのドットのx, y座標を取得
            FitEnd = self.Fit_e[0].get_xydata()[0][0]
            list_idxSE = [np.abs(BindingEnergy - FitStart).argmin(), np.abs(BindingEnergy - FitEnd).argmin()] #[Start, End]の順で格納、FitStartおよびEndと最も近い値のindexをDataFrameから取得する
            
            df_processed = pd.DataFrame({'Binding Energy(eV)': BindingEnergy[list_idxSE[0]:list_idxSE[1]], 'Intensity(cps)': Intensity[list_idxSE[0]:list_idxSE[1]]})
            loader.XPS_Dict_DF[f'{DataKey}_proc'] = df_processed # df_processedはfittingする範囲で切り出したデータが格納されている. それを全データが格納されている辞書へ新規に書き込む
            
            # 以下DPP上のコンボボックスの内容更新
            self.combo_DataName.clear()
            SpectraName = list(loader.XPS_Dict_DF.keys())
            for i in SpectraName:
                self.combo_DataName.addItem(f'{i}')


        elif Button.text() == 'Substract' and loader.XPS_Dict_DF != {}:
            SubMethod = self.combo_BGsubs.currentText()

            if SubMethod == 'Shirley' and '_proc' in DataKey:
                f_x = Intensity
                x = BindingEnergy
                B_init = f_x[-1]
                k = f_x[0] - B_init
                count = 1
                
                while count == 1:
                    g_x = f_x - B_init
                    SpectraArea_init = np.abs(integrate.trapz(g_x, x))
                    Q = np.array([np.abs(integrate.trapz(g_x[i: -1], x[i : -1])) for i in range(len(x))])
                    count = count +1

                while count == 2:
                    B_x = k*Q/SpectraArea_init + B_init
                    g_x = f_x - B_x
                    SpectraArea = np.abs(integrate.trapz(g_x, x))
                    Q = np.array([np.abs(integrate.trapz(g_x[i: -1], x[i : -1])) for i in range(len(x))])
                    Resid_Area = SpectraArea - SpectraArea_init
                    count = count +1

                while count > 2 and Resid_Area != 0:
                    SpectraArea_p = SpectraArea
                    B_x = k*Q/SpectraArea_p + B_init
                    g_x = f_x - B_x
                    SpectraArea = np.abs(integrate.trapz(g_x, x))
                    Q = np.array([np.abs(integrate.trapz(g_x[i: -1], x[i : -1])) for i in range(len(x))])
                    Resid_Area = SpectraArea - SpectraArea_p
                    count = count +1

                if count == 3 and Resid_Area == 0:
                    B_x = k*Q/SpectraArea + B_init
                
                Intensity_BG = Intensity-B_x
                loader.XPS_Dict_DF[f'{DataKey}']['IntensityBG'] = Intensity_BG
                loader.XPS_Dict_DF[f'{DataKey}']['Background'] = B_x
                BackGround = self.ax.plot(x, B_x)
                Signal_sub = self.ax.plot(x, Intensity_BG)
                self.canvas.draw()

                #print(loader.XPS_Dict_DF[f'{DataKey}']['Background'])
                #print(SpectraArea_p, SpectraArea, Resid_Area, count)

            elif SubMethod == 'Linear' and '_proc' in DataKey:
                x_1, y_1 = BindingEnergy[0], Intensity[0]
                x_2, y_2 = BindingEnergy[-1], Intensity[-1]
                matrix_coef = np.array([[x_1, 1], [x_2, 1]])
                matrix_y = np.array([y_1, y_2])
                Slope_Intercept = np.linalg.solve(matrix_coef, matrix_y)
                a, b = Slope_Intercept[0], Slope_Intercept[1]
                B_x = a*BindingEnergy+b

                Intensity_BG = Intensity-B_x
                loader.XPS_Dict_DF[f'{DataKey}']['IntensityBG'] = Intensity_BG
                loader.XPS_Dict_DF[f'{DataKey}']['Background'] = B_x
                BackGround = self.ax.plot(BindingEnergy, B_x)
                Signal_sub = self.ax.plot(BindingEnergy, Intensity_BG)
                self.canvas.draw()

                #print(loader.XPS_Dict_DF[f'{DataKey}']['Background'])
                #print(Slope_Intercept)

            self.combo_SpectraName.clear()
            SpectraName = list(loader.XPS_Dict_DF.keys())
            for i in SpectraName:
                if '_proc' in i:
                    self.combo_SpectraName.addItem(f'{i}')

                else:
                    continue
            
            else:
                return

    def XPSFit_FP(self):
        Button = self.sender()
        loader = FileLoader()
        function = FittingFunctions()

        XPS_FittingPanels.AbsorRel = self.Abs_Rel.currentText()
        XPS_FittingPanels.RelMethod = self.combo_HowRelative.currentText()

        DataKey =  self.combo_SpectraName.currentText()
        if DataKey != '':
            Dict_DF = loader.XPS_Dict_DF[DataKey] #XPSのデータが格納されている辞書、呼び出されるデータはDataFrame
            #list_DFindex = list(Dict_DF.columns)
            BindingEnergy = np.array(Dict_DF['Binding Energy(eV)'])
            IntensityBG = np.array(Dict_DF['IntensityBG'])
            Background = np.array(Dict_DF['Background'])

        if Button.text() == 'Open Graph' and '_proc' in DataKey:
            self.ax.cla()
            self.ax.set_xlabel(xlabel = 'Binding Energy (eV)', fontsize = 14)
            self.ax.invert_xaxis()
            self.ax.set_ylabel(ylabel = 'Intensity (a. u.)', fontsize = 14)
            self.ax.minorticks_on()

            Spectrum = self.ax.plot(BindingEnergy, IntensityBG)
            self.canvas.draw()
            #print(list_DFindex)

        elif Button.text() == 'Check' and '_proc' in DataKey:            
            guess_init = []

            for i in range(len(self.Dict_FitComps)):
                FitComps = self.Dict_FitComps[f'Comp. {i+1}']
                
                if all([FitComps[f'{j}'] == 0 for j in self.ParamName]):
                    continue

                else:
                    guess_init.append([FitComps[f'{j}'] for j in self.ParamName])
            
            if guess_init != []:
                self.ax.cla()
                self.ax.set_xlabel(xlabel = 'Binding Energy (eV)', fontsize = 14)
                self.ax.invert_xaxis()
                self.ax.set_ylabel(ylabel = 'Intensity (a. u.)', fontsize = 14)
                self.ax.minorticks_on()

                Spectrum = self.ax.plot(BindingEnergy, IntensityBG)

                Voight_ini = function.Voigt(BindingEnergy, *guess_init)[0]
                for n, i in enumerate(Voight_ini):
                    FuncCheck_fill = self.ax.fill_between(BindingEnergy, i, np.zeros_like(BindingEnergy), lw = 1.5, facecolor = 'none', hatch = '////', alpha = 1, edgecolor = cm.rainbow(n/len(Voight_ini)))
                
                self.canvas.draw()
            
                #print(Voight_ini)
                #print(self.AbsorRel, self.RelMethod)

        elif Button.text() == 'Fit' and '_proc' in DataKey:
            limitation = [0, 1, np.inf]
            self.guess_init.clear()
            self.BindIndex.clear()

            for i in range(len(self.Dict_FitComps)):
                FitComps = self.Dict_FitComps[f'Comp. {i+1}']
                BindParams = self.Dict_CheckState[f'Comp. {i+1}']
                
                if all([FitComps[f'{key}'] == 0 for key in self.ParamName]):
                    continue

                else:
                    innerList = []
                    for j in range(len(self.ParamName)):
                        if BindParams[self.ParamName[j]] == False:
                            innerList.append(FitComps[self.ParamName[j]])

                        elif BindParams[self.ParamName[j]] == True:
                            self.BindIndex.append([i, j])

                    self.guess_init.append(innerList)

            if self.guess_init != []:
                minimum = [] #各パラメータの下限値を格納するリスト
                maximum = [] #各パラメータの上限値を格納するリスト
                for i in range(len(self.guess_init)):
                    BindParams = self.Dict_CheckState[f'Comp. {i+1}']

                    for j in range(len(self.ParamName)):
                        if BindParams[self.ParamName[j]] == True:
                            continue

                        elif BindParams[self.ParamName[j]] == False and self.ParamName[j] != 'B.R.':
                            minimum.append(limitation[0])
                            maximum.append(limitation[2])

                        elif BindParams[self.ParamName[j]] == False and self.ParamName[j] == 'B.R.':
                            minimum.append(limitation[0])
                            maximum.append(limitation[1])

                constraint = (tuple(minimum), tuple(maximum))
                
                popt, _ = optimize.curve_fit(function.Voigt, BindingEnergy, IntensityBG, p0 = list(itertools.chain.from_iterable(self.guess_init)), bounds = constraint, maxfev = 50000)

                self.FitParams.clear()
                for i in range(0, int((len(popt)+len(self.BindIndex))/6), 1):
                    p = popt.tolist()
                    
                    for j in self.BindIndex:
                        s = j[0]
                        t = j[1]
                        st = 6*s + t

                        p.insert(st, self.Dict_FitComps[f'Comp. {s+1}'][self.ParamName[t]])

                    q = p[6*i : 6*(i+1)]
                    self.FitParams.append(q) # フィッティング結果をインスタンス変数へ保存

                self.ax.cla()
                self.ax.set_xlabel(xlabel = 'Binding Energy (eV)', fontsize = 14)
                self.ax.invert_xaxis()
                self.ax.set_ylabel(ylabel = 'Intensity (a. u.)', fontsize = 14)
                self.ax.minorticks_on()

                Voight_comp = function.Voigt(BindingEnergy, *self.FitParams)[0]
                for n, i in enumerate(Voight_comp):
                    FitComp_fill = self.ax.fill_between(BindingEnergy, i, np.zeros_like(BindingEnergy), lw = 1.5, facecolor = 'none', hatch = '////', alpha = 1, edgecolor = cm.rainbow(n/len(Voight_comp)))

                Fit = function.Voigt(BindingEnergy, *self.FitParams)[1]
                PeakArea = function.Voigt(BindingEnergy, *self.FitParams)[2]

                Experiment = self.ax.scatter(BindingEnergy, IntensityBG, s = 35, facecolors = 'none', edgecolors = 'black')
                Spectram_Fit = self.ax.plot(BindingEnergy, Fit, c = 'red', lw = 1.5)

                self.canvas.draw()
                print(self.FitParams)

                for i in range(len(PeakArea)):
                    print(PeakArea[i])
                    if i%2 == 1:
                        print(PeakArea[i]/PeakArea[i-1])
                #print(function.L_params)

        elif Button.text() == 'add BG' and self.FitParams != []:
            Iex_withBG = IntensityBG + Background # Intensity observed experimentally with Background
            Ifit_withBG = function.Voigt(BindingEnergy, *self.FitParams)[1] + Background # Intensity fitted by Voigt function with Background

            self.ax.cla()
            self.ax.set_xlabel(xlabel = 'Binding Energy (eV)', fontsize = 14)
            self.ax.invert_xaxis()
            self.ax.set_ylabel(ylabel = 'Intensity (a. u.)', fontsize = 14)
            self.ax.minorticks_on()
            self.ax.set_yticks([])

            Voight_comp = function.Voigt(BindingEnergy, *self.FitParams)[0] # The compositions of Voigt function after fitting
            for n, i in enumerate(Voight_comp):
                FitComp_fill = self.ax.fill_between(BindingEnergy, i, np.zeros_like(BindingEnergy), lw = 1.5, facecolor = 'none', hatch = '////', alpha = 1, edgecolor = cm.rainbow(n/len(Voight_comp)))

            Experiment = self.ax.scatter(BindingEnergy, Iex_withBG, s = 35, facecolors = 'none', edgecolors = 'black')
            Spectram_Fit = self.ax.plot(BindingEnergy, Ifit_withBG, c = 'red', lw = 1.5)
            BG = self.ax.plot(BindingEnergy, Background, c = 'black', lw = 1)

            self.canvas.draw()

    # fit panelのスピンボックスから値を取得するメソッド. スピンボックスにconnectされてる.
    def getFitParams(self):
        SpinBox = self.sender()
        Index = SpinBox.index

        for i in range(1, len(self.ParamName)+1, 1):
            if f'{i}' in Index:
                if 'B.E.' in Index:
                    self.Dict_FitComps[f'Comp. {i}']['B.E.'] = SpinBox.value()

                elif 'Int.' in Index:
                    self.Dict_FitComps[f'Comp. {i}']['Int.'] = SpinBox.value()

                elif 'W_gau.' in Index:
                    self.Dict_FitComps[f'Comp. {i}']['Wid_G'] = SpinBox.value()

                elif 'Gamma' in Index:
                    self.Dict_FitComps[f'Comp. {i}']['gamma'] = SpinBox.value()

                elif 'S.O.S.' in Index:
                    self.Dict_FitComps[f'Comp. {i}']['S.O.S.'] = SpinBox.value()

                elif 'B.R.' in Index:
                    self.Dict_FitComps[f'Comp. {i}']['B.R.'] = SpinBox.value()

            else:
                continue

        #print(Index)
        #print(self.Dict_FitComps)

    def getCheckState(self):
        CheckBox = self.sender()
        Index = CheckBox.index

        for i in range(1, len(self.ParamName)+1, 1):
            if f'{i}' in Index:
                if 'B.E.' in Index:
                    self.Dict_CheckState[f'Comp. {i}']['B.E.'] = CheckBox.isChecked()

                elif 'Int.' in Index:
                    self.Dict_CheckState[f'Comp. {i}']['Int.'] = CheckBox.isChecked()

                elif 'W_gau.' in Index:
                    self.Dict_CheckState[f'Comp. {i}']['Wid_G'] = CheckBox.isChecked()

                elif 'Gamma' in Index:
                    self.Dict_CheckState[f'Comp. {i}']['gamma'] = CheckBox.isChecked()

                elif 'S.O.S.' in Index:
                    self.Dict_CheckState[f'Comp. {i}']['S.O.S.'] = CheckBox.isChecked()

                elif 'B.R.' in Index:
                    self.Dict_CheckState[f'Comp. {i}']['B.R.'] = CheckBox.isChecked()

            else:
                continue

        #print(Index)
        #print(self.Dict_CheckState)

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


# Fittingに使用する各種モデル関数を定義するクラス. 現段階ではVoigt functionを実装. 今後関数を増やすことも検討
class FittingFunctions():

    def __init__(self) -> None:
        pass

    def Voigt(self, x, *params): # Voigt function, Faddeeva functionの実部を取ることで定義
        # pythonでは*付きの変数はtupleとして認識されるため、その中の1つ目の要素がlist型か否かで分岐処理.
        # tuple(list[])で入力した場合は各成分を独立に格納したlist[NDarray, NDarray, ...]と各成分の和(NDarray)を返す. tuple(not list, e.g., float)で入力した場合はすべての成分の和を格納したNDarrayを返す.
        XPS_FP = XPS_FittingPanels()
        AbsorRel = XPS_FP.AbsorRel
        RelMethod = XPS_FP.RelMethod

        if type(params[0]) is list:
            N_func = len(params)
            
            list_y_V = []
            list_A_Vw = []
            list_A_Vt = []
            y_Vtotal = np.zeros_like(x)
            for i in range(0, N_func, 1):    
                y_V = np.zeros_like(x)

                if AbsorRel == 'Absol.':
                    BE = params[i][0] # ピーク位置

                elif AbsorRel == 'Relat.' and RelMethod == 'Method 1':
                    if i == 0:
                        BE = params[i][0]

                    elif i > 0:
                        BE = params[0][0] + params[i][0]

                elif AbsorRel == 'Relat.' and RelMethod == 'Method 2':
                    if i%2 == 0:
                        BE = params[i][0]

                    elif i%2 == 1:
                        BE = params[i-1][0] + params[i][0]
                
                I = params[i][1] # ピーク強度
                W_G = params[i][2] # ガウシアン成分の幅
                gamma = params[i][3] # ガンマパラメータ. ローレンチアンの幅(比率)を決める
                SOS = params[i][4] # Spin-Orbit splitting. スピン軌道相互作用によるピーク分裂幅を決める
                BR = params[i][5] # Branch ratio. 方位量子数ごとに決まるピーク強度比. 例えば理想的にはp軌道なら1:2の強度比でピークが分裂する

                z = (x - BE + 1j*gamma)/(W_G * np.sqrt(2.0)) # 強度の大きいピークに対する複素変数の定義
                w = scipy.special.wofz(z) #Faddeeva function (強度の大きい方)
                s = (x - BE - SOS+ 1j*gamma)/(W_G * np.sqrt(2.0))
                t = scipy.special.wofz(s) #Faddeeva function (強度の小きい方)
                
                V_w = I * (w.real)/(W_G * np.sqrt(2.0*np.pi))
                Area_V_w = np.abs(integrate.trapz(V_w, x))

                V_t = BR * I * (t.real)/(W_G * np.sqrt(2.0*np.pi))
                Area_V_t = np.abs(integrate.trapz(V_t, x))

                y_V = y_V + V_w + V_t #Faddeeva functionを用いたvoight関数の定義
                y_Vtotal = y_Vtotal + V_w + V_t #Faddeeva functionを用いたvoight関数の定義

                list_y_V.append(y_V)
                list_A_Vw.append(Area_V_w)
                list_A_Vt.append(Area_V_t)

            return [list_y_V, y_Vtotal, list_A_Vw, list_A_Vt]


        elif type(params[0]) is not list:
            counts = len(XPS_FP.BindIndex)

            N_func = int((len(params)+counts)/6)
            
            params_mod = list(params)
            for i in XPS_FP.BindIndex:
                s = i[0]
                t = i[1]
                st = 6*s + t

                params_mod.insert(st, XPS_FP.Dict_FitComps[f'Comp. {s+1}'][XPS_FP.ParamName[t]])

            L_params = []
            y_V = np.zeros_like(x)
            for i in range(0, N_func, 1):
                p = params_mod[6*i : 6*(i+1)]
                L_params.append(p)

                if AbsorRel == 'Absol.':
                    BE = L_params[i][0] # ピーク位置

                elif AbsorRel == 'Relat.' and RelMethod == 'Method 1':
                    if i == 0:
                        BE = L_params[i][0]

                    elif i > 0:
                        BE = L_params[0][0] + L_params[i][0]

                elif AbsorRel == 'Relat.' and RelMethod == 'Method 2':
                    if i%2 == 0:
                        BE = L_params[i][0]

                    elif i%2 == 1:
                        BE = L_params[i-1][0] + L_params[i][0]

                I = L_params[i][1] # ピーク強度
                W_G = L_params[i][2] # ガウシアン成分の幅
                gamma = L_params[i][3] # ガンマパラメータ. ローレンチアンの幅(比率)を決める
                SOS = L_params[i][4] # Spin-Orbit splitting. スピン軌道相互作用によるピーク分裂幅を決める
                BR = L_params[i][5] # Branch ratio. 方位量子数ごとに決まるピーク強度比. 例えば理想的にはp軌道なら1:2の強度比でピークが分裂する 

                z = (x - BE + 1j*gamma)/(W_G * np.sqrt(2.0)) # 強度の大きいピークに対する複素変数の定義
                w = scipy.special.wofz(z) #Faddeeva function (強度の大きい方)
                V_w = I * (w.real)/(W_G * np.sqrt(2.0*np.pi))

                s = (x - BE - SOS+ 1j*gamma)/(W_G * np.sqrt(2.0))
                t = scipy.special.wofz(s) #Faddeeva function (強度の小きい方)
                V_t = BR * I * (t.real)/(W_G * np.sqrt(2.0*np.pi))

                y_V = y_V + V_w + V_t #Faddeeva functionを用いたvoight関数の定義
        
            return y_V


#実行部
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())