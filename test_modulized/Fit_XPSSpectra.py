import sys
import re
from PyQt5.QtWidgets import(
    QApplication, QFileDialog, QMdiSubWindow, QLabel, QComboBox, QPushButton, QWidget,
    QDoubleSpinBox, QCheckBox, QVBoxLayout, QHBoxLayout, QMenu, QTextEdit)
from PyQt5.QtCore import QPoint
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.cm as cm
from matplotlib.lines import Line2D
import numpy as np
from scipy import integrate, optimize
import scipy.special
import itertools

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

                LO_SlashinPath = fname[0].rfind('/') #ファイルパスの最後の'/'の位置
                PrefixDir = fname[0][0 : LO_SlashinPath] #ファイルパスの最後の'/'の前までの文字列
                Div_DataFilePath = [f'{PrefixDir}/{i}.txt' for i in SpectraName] #分割したテキストデータのファイルパスのリスト

                for i in range(len(Div_DataFilePath)):
                    with open(Div_DataFilePath[i], mode = 'w') as f: #分割したテキストデータをファイルに書き込み
                        f.write(Dict_Data[SpectraName[i]]) #辞書から分割したテキストデータを取り出し、ファイルに書き込み

                    dataset = pd.read_csv(Div_DataFilePath[i], header = 3, delimiter = '\t') #分割したテキストデータをDataframeとして読み込み
                    self.XPS_Dict_DF[SpectraName[i]] = dataset #辞書に読み込んだDataframeを追加
            #------------ファイル分割処理--------------

            else: #ファイル分割がない場合
                dataset = pd.read_csv(fname[0], header = 3, delimiter = '\t')
                self.XPS_Dict_DF[SpectraName[0]] = dataset


#XPSのfittingに際して使用するwindow類の定義クラス
class XPS_FittingPanels(QWidget):
    gco = None

    ParamName = ['B.E.', 'Int.', 'Wid_G', 'gamma', 'S.O.S.', 'B.R.']
    Dict_FitComps = {} #Fittingに使用する各コンポーネントのパラメータを管理する辞書
    Dict_CheckState = {} #Fittingに使用する各コンポーネントのチェックボックスの状態を管理する辞書, パラメータの拘束状態を反映する
    BindIndex = [] #Fittingに使用するパラメータが拘束されている場合、そのインデックスを格納するリスト
    guess_init = [] #Fittingに使用するパラメータの初期値を格納するリスト
    FitParams = [] #Fitting後のパラメータを格納するリスト
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
        self.listSpin1 = []
        self.listSpin2 = []
        self.listSpin3 = []
        self.listSpin4 = []
        self.listSpin5 = []
        self.listSpin6 = []
        for i in range(0, 36, 1):
            self.spinBOX = QDoubleSpinBox(self.FitPanel)
            self.spinBOX.valueChanged.connect(self.getFitParams)
            self.spinBOX.setDecimals(3)

            if i <= 5:
                self.spinBOX.move(70+(140*i), 80)
                self.spinBOX.index = f"B.E. {i+1}"
                self.spinBOX.setRange(0, 1500)
                self.spinBOX.setSingleStep(0.5)
                
                if (i+1)%6 == 1:
                    self.listSpin1.append(self.spinBOX)

                elif (i+1)%6 == 2:
                    self.listSpin2.append(self.spinBOX)

                elif (i+1)%6 == 3:
                    self.listSpin3.append(self.spinBOX)
                
                elif (i+1)%6 == 4:
                    self.listSpin4.append(self.spinBOX)

                elif (i+1)%6 == 5:
                    self.listSpin5.append(self.spinBOX)

                elif (i+1)%6 == 0:
                    self.listSpin6.append(self.spinBOX)

            elif 6 <= i <= 11:
                self.spinBOX.move(70+(140*(i-6)), 110)
                self.spinBOX.index = f"Int. {i-5}"
                self.spinBOX.setRange(0, 2000000)
                self.spinBOX.setSingleStep(100)

                if (i+1)%6 == 1:
                    self.listSpin1.append(self.spinBOX)

                elif (i+1)%6 == 2:
                    self.listSpin2.append(self.spinBOX)

                elif (i+1)%6 == 3:
                    self.listSpin3.append(self.spinBOX)
                
                elif (i+1)%6 == 4:
                    self.listSpin4.append(self.spinBOX)

                elif (i+1)%6 == 5:
                    self.listSpin5.append(self.spinBOX)

                elif (i+1)%6 == 0:
                    self.listSpin6.append(self.spinBOX)

            elif 12 <= i <= 17:
                self.spinBOX.move(70+(140*(i-12)), 140)
                self.spinBOX.index = f"W_gau. {i-11}"
                self.spinBOX.setRange(0, 1000)
                self.spinBOX.setSingleStep(0.1)

                if (i+1)%6 == 1:
                    self.listSpin1.append(self.spinBOX)

                elif (i+1)%6 == 2:
                    self.listSpin2.append(self.spinBOX)

                elif (i+1)%6 == 3:
                    self.listSpin3.append(self.spinBOX)
                
                elif (i+1)%6 == 4:
                    self.listSpin4.append(self.spinBOX)

                elif (i+1)%6 == 5:
                    self.listSpin5.append(self.spinBOX)

                elif (i+1)%6 == 0:
                    self.listSpin6.append(self.spinBOX)

            elif 18 <= i <= 23:
                self.spinBOX.move(70+(140*(i-18)), 170)
                self.spinBOX.index = f"Gamma {i-17}"
                self.spinBOX.setRange(0, 1000)
                self.spinBOX.setSingleStep(0.05)

                if (i+1)%6 == 1:
                    self.listSpin1.append(self.spinBOX)

                elif (i+1)%6 == 2:
                    self.listSpin2.append(self.spinBOX)

                elif (i+1)%6 == 3:
                    self.listSpin3.append(self.spinBOX)
                
                elif (i+1)%6 == 4:
                    self.listSpin4.append(self.spinBOX)

                elif (i+1)%6 == 5:
                    self.listSpin5.append(self.spinBOX)

                elif (i+1)%6 == 0:
                    self.listSpin6.append(self.spinBOX)

            elif 24 <= i <= 29:
                self.spinBOX.move(70+(140*(i-24)), 200)
                self.spinBOX.index = f"S.O.S. {i-23}"
                self.spinBOX.setRange(0, 100)
                self.spinBOX.setSingleStep(0.1)

                if (i+1)%6 == 1:
                    self.listSpin1.append(self.spinBOX)

                elif (i+1)%6 == 2:
                    self.listSpin2.append(self.spinBOX)

                elif (i+1)%6 == 3:
                    self.listSpin3.append(self.spinBOX)
                
                elif (i+1)%6 == 4:
                    self.listSpin4.append(self.spinBOX)

                elif (i+1)%6 == 5:
                    self.listSpin5.append(self.spinBOX)

                elif (i+1)%6 == 0:
                    self.listSpin6.append(self.spinBOX)

            elif 30 <= i <= 35:
                self.spinBOX.move(70+(140*(i-30)), 230)
                self.spinBOX.index = f"B.R. {i-29}"
                self.spinBOX.setRange(0, 1)
                self.spinBOX.setSingleStep(0.02)

                if (i+1)%6 == 1:
                    self.listSpin1.append(self.spinBOX)

                elif (i+1)%6 == 2:
                    self.listSpin2.append(self.spinBOX)

                elif (i+1)%6 == 3:
                    self.listSpin3.append(self.spinBOX)
                
                elif (i+1)%6 == 4:
                    self.listSpin4.append(self.spinBOX)

                elif (i+1)%6 == 5:
                    self.listSpin5.append(self.spinBOX)

                elif (i+1)%6 == 0:
                    self.listSpin6.append(self.spinBOX)

        #スピンボックスへの値の反映が後々やりやすくなるように辞書でリストを管理
        self.dictSpinBoxList = {'listSpin1': self.listSpin1, 'listSpin2': self.listSpin2, 'listSpin3': self.listSpin3, 'listSpin4': self.listSpin4, 'listSpin5': self.listSpin5, 'listSpin6': self.listSpin6}

        #for i in range(0, 2, 1):
        #    self.BGspinBOX = QDoubleSpinBox(self.FitPanel)
        #    self.BGspinBOX.move(70, 275+30*i)
        #    self.BGspinBOX.index = f'B.G. {i}'

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

        #for i in range(0, 2, 1):
        #    self.BGcheckBOX = QCheckBox(self.FitPanel)
        #    self.BGcheckBOX.move(180, 275+30*i)
        #    self.BGcheckBOX.index = f'Check_B.G. {i}'


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

        #BGCoeff = ['Slope', 'Intercept']
        #for i in range(len(BGCoeff)):
        #    self.Label_BGCoeff = QLabel(BGCoeff[i], self.FitPanel)
        #    self.Label_BGCoeff.move(10, 275+30*i)

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

        BGSubtractionMethod = ['Shirley', 'Linear']
        self.combo_BGsubs = QComboBox(self.DataPanel)
        self.combo_BGsubs.move(30, 250)
        self.combo_BGsubs.setFixedWidth(120)
        for i in BGSubtractionMethod:
            self.combo_BGsubs.addItem(i)

        #スピンボックスの生成
        for i in range(0, 2, 1):
            self.spinDPP = QDoubleSpinBox(self.DataPanel) # DPP : Data Preparation Panel
            self.spinDPP.setGeometry(10+140*i , 130, 130, 30)
        self.LabelRange = QLabel('Fitting range (start, end)', self.DataPanel)
        self.LabelRange.setGeometry(65, 105, 150, 20)
        
        #ボタンの生成
        ButtonName_Data = ['Draw Graph', 'Make Processed Wave', 'Subtract']
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
        self.Label_BGmethod = QLabel('<p><font size="3">Choose subtraction method of background</font></p>', self.DataPanel)
        self.Label_BGmethod.move(10, 220)
        self.Label_BGmethod.setFixedWidth(270)
        #---------Setting for Data Panel----------

        #---------Setting for Plot Panel----------
        self.PlotPanel = QMdiSubWindow()
        self.PlotPanel.setWindowTitle("Graph")
        self.PlotPanel.setGeometry(400, 400, 600, 600)
        
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
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.toolbar)
        
        self.widget = QWidget()
        self.widget.setLayout(self.layout)
        self.PlotPanel.setWidget(self.widget)

        self.Fit_s = self.ax.plot(0, 0, 'v', picker = 10)
        self.Fit_e = self.ax.plot(1, 0, '^', picker = 10)

        self.cmenu = QMenu(self.PlotPanel)
        annotation = self.cmenu.addAction('add annotation')
        annotation.triggered.connect(self.MakeAnnotation)

        self.canvas.mpl_connect('motion_notify_event', self.motion) #----------------------------------------------
        self.canvas.mpl_connect('pick_event', self.onpick)          #グラフキャンバス上でのカーソルアクション定義
        self.canvas.mpl_connect('button_release_event', self.release) #---------------------------------------------
        self.canvas.mpl_connect('button_press_event', self.onclick)

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

        elif Button.text() == 'Subtract' and loader.XPS_Dict_DF != {}:
            SubMethod = self.combo_BGsubs.currentText() #SubMethod: Subtraction Method, バックグラウンドを引く方法

            if SubMethod == 'Shirley' and '_proc' in DataKey: #Shirleyバックグラウンドを引く場合
                f_x = Intensity #f_x: function of x, Intensityをf_xとして扱う
                x = BindingEnergy #x: x-axis, BindingEnergyをxとして扱う
                B_init = f_x[-1] #最初のバックグラウンド
                k = f_x[0] - B_init #k: constant, f_xの最初の値から最後の値を引いたもの
                count = 1 #count: counter, while文のループ回数をカウントする
                
                while count == 1: 
                    g_x = f_x - B_init #g_x: g(x), f_xからB_initを引いたもの
                    SpectraArea_init = np.abs(integrate.trapz(g_x, x)) #SpectraArea_init: Spectra Area Initial, スペクトル全面積の初期値
                    Q = np.array([np.abs(integrate.trapz(g_x[i: -1], x[i : -1])) for i in range(len(x))]) #Q: スペクトルの各部分面積の配列
                    count = count +1

                while count == 2:
                    B_x = k*Q/SpectraArea_init + B_init #B_x: B(x), k*Q/SpectraArea_init + B_init, Shirlyバックグラウンドの式
                    g_x = f_x - B_x #g_x: g(x), f_xからB_xを引いたもの, 1回目のループのB_initがB_xに変わっただけ
                    SpectraArea = np.abs(integrate.trapz(g_x, x)) #SpectraArea: Spectra Area, スペクトル全面積
                    Q = np.array([np.abs(integrate.trapz(g_x[i: -1], x[i : -1])) for i in range(len(x))]) #Q: スペクトルの各部分面積の配列, g_xの中身が違うだけ
                    Resid_Area = SpectraArea - SpectraArea_init #Resid_Area: Residual Area, 前回ループとスペクトル全面積を比較して変化があるかどうかを判定する
                    count = count +1

                while count > 2 and Resid_Area != 0: #Resid_Areaが0になるまでループを続ける
                    SpectraArea_p = SpectraArea #SpectraArea_p: Spectra Area Previous, 前回ループのスペクトル全面積
                    B_x = k*Q/SpectraArea_p + B_init #B_x: B(x), SpectraArea_pに変わっただけ
                    g_x = f_x - B_x
                    SpectraArea = np.abs(integrate.trapz(g_x, x)) #SpectraArea: Spectra Area, スペクトル全面積, SpectraArea_pと違う値になる(直前のループで得られた値を更新する)
                    Q = np.array([np.abs(integrate.trapz(g_x[i: -1], x[i : -1])) for i in range(len(x))])
                    Resid_Area = SpectraArea - SpectraArea_p #Resid_Area: Residual Area, 前回ループとスペクトル全面積を比較して変化があるかどうかを判定する
                    count = count +1

                if count == 3 and Resid_Area == 0: #ループ3回目でResid_Areaが0になった場合
                    B_x = k*Q/SpectraArea + B_init
                
                Intensity_BG = Intensity-B_x #Intensity_BG: Intensity Background Subtracted, Intensityからバックグラウンドを引いたもの
                loader.XPS_Dict_DF[f'{DataKey}']['IntensityBG'] = Intensity_BG #辞書に新たにIntensityBGというキーを作成し, その中にIntensity_BGを格納する
                loader.XPS_Dict_DF[f'{DataKey}']['Background'] = B_x #辞書に新たにBackgroundというキーを作成し, その中にB_xを格納する
                BackGround = self.ax.plot(x, B_x)
                Signal_sub = self.ax.plot(x, Intensity_BG)
                self.canvas.draw()

            elif SubMethod == 'Linear' and '_proc' in DataKey: #線形(1次関数)バックグラウンドを引く場合
                x_1, y_1 = BindingEnergy[0], Intensity[0] #x_1, y_1: x-axis, y-axis, 範囲制限したBindingEnergyとIntensityの最初の値
                x_2, y_2 = BindingEnergy[-1], Intensity[-1] #x_2, y_2: x-axis, y-axis, 範囲制限したBindingEnergyとIntensityの最後の値
                matrix_coef = np.array([[x_1, 1], [x_2, 1]]) #matrix_coef: matrix coefficient, 2x2の行列
                matrix_y = np.array([y_1, y_2]) #matrix_y: matrix y, 2x1の行列
                Slope_Intercept = np.linalg.solve(matrix_coef, matrix_y) #Slope_Intercept: Slope and Intercept, 2x1の行列
                a, b = Slope_Intercept[0], Slope_Intercept[1] #a, b: Slope and Intercept, 1次関数の傾きと切片
                B_x = a*BindingEnergy+b #B_x: B(x), 1次関数の式

                Intensity_BG = Intensity-B_x
                loader.XPS_Dict_DF[f'{DataKey}']['IntensityBG'] = Intensity_BG
                loader.XPS_Dict_DF[f'{DataKey}']['Background'] = B_x
                BackGround = self.ax.plot(BindingEnergy, B_x)
                Signal_sub = self.ax.plot(BindingEnergy, Intensity_BG)
                self.canvas.draw()

            self.combo_SpectraName.clear() #コンボボックスの中身をクリアする
            SpectraName = list(loader.XPS_Dict_DF.keys()) #SpectraName: Spectra Name, XPSのデータが格納されている辞書のキーをリストに変換する
            for i in SpectraName:
                if '_proc' in i: #_procが含まれているキーのみをコンボボックスに追加する
                    self.combo_SpectraName.addItem(f'{i}')

                else:
                    continue
            
            else:
                return

    def XPSFit_FP(self):
        Button = self.sender() #Button: sender()で押されたボタンの情報を取得する
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
            guess_init = [] #guess_init: guess initial, パラメータの初期値を格納するリスト, クラス変数とは別なので注意

            for i in range(len(self.Dict_FitComps)):
                FitComps = self.Dict_FitComps[f'Comp. {i+1}'] #FitComps: Fitting Components, 各Voigt関数の番号をキーに辞書からパラメータを取り出す, リストに格納
                
                if all([FitComps[f'{j}'] == 0 for j in self.ParamName]): #あるVoigt関数のパラメータがすべて0の場合
                    continue

                else:
                    guess_init.append([FitComps[f'{j}'] for j in self.ParamName]) #あるVoigt関数のパラメータがすべて0でない場合、パラメータをリストに格納する
            
            if guess_init != []:
                self.ax.cla()
                self.ax.set_xlabel(xlabel = 'Binding Energy (eV)', fontsize = 14)
                self.ax.invert_xaxis()
                self.ax.set_ylabel(ylabel = 'Intensity (a. u.)', fontsize = 14)
                self.ax.minorticks_on()

                Spectrum = self.ax.plot(BindingEnergy, IntensityBG) #Spectrum: 生データ

                Voight_ini = function.Voigt(BindingEnergy, *guess_init)[0] #Voight_ini: Voight initial, パラメータ初期値を用いて生成したVoigt関数, 0番目は各voigt関数が成分ごとに格納されている
                for n, i in enumerate(Voight_ini):
                    #FuncCheck_fill: パラメータ初期値で生成したVoigt関数のグラフを描画
                    FuncCheck_fill = self.ax.fill_between(BindingEnergy, i, np.zeros_like(BindingEnergy), lw = 1.5, facecolor = 'none', hatch = '////', alpha = 1, edgecolor = cm.rainbow(n/len(Voight_ini)))

                self.canvas.draw()

        elif Button.text() == 'Fit' and '_proc' in DataKey:
            limitation = [0, 1, np.inf] #limitation: limitation of fitting, フィッティングパラメータの範囲制限値を格納
            self.guess_init.clear()
            self.BindIndex.clear()

            for i in range(len(self.Dict_FitComps)):
                FitComps = self.Dict_FitComps[f'Comp. {i+1}'] #FitComps: Fitting Components, 各Voigt関数の番号をキーに辞書からパラメータを取り出す, リストに格納
                BindParams = self.Dict_CheckState[f'Comp. {i+1}'] #BindParams: Binding Parameters, 各Voigt関数の番号をキーに辞書からパラメータのバインド状態を取り出す, リストに格納
                
                if all([FitComps[f'{key}'] == 0 for key in self.ParamName]): #あるVoigt関数のパラメータがすべて0の場合
                    continue

                else:
                    innerList = [] #一時的にパラメータを格納するリスト
                    for j in range(len(self.ParamName)):
                        if BindParams[self.ParamName[j]] == False:
                            innerList.append(FitComps[self.ParamName[j]]) #パラメータのバインド状態がFalseの場合、パラメータをリストに格納する

                        elif BindParams[self.ParamName[j]] == True:
                            self.BindIndex.append([i, j]) #パラメータのバインド状態がTrueの場合、パラメータのインデックスをリストに格納する, あとでパラメータの挿入に使う

                    self.guess_init.append(innerList) #すべてのパラメータをリストに格納する

            if self.guess_init != []:
                #以下パラメータの種別によって制限範囲を変え、上限下限を格納したtuple(=constraint)を作成
                minimum = [] #各パラメータの下限値を格納するリスト
                maximum = [] #各パラメータの上限値を格納するリスト
                for i in range(len(self.guess_init)):
                    BindParams = self.Dict_CheckState[f'Comp. {i+1}']

                    for j in range(len(self.ParamName)):
                        if BindParams[self.ParamName[j]] == True:
                            continue

                        elif BindParams[self.ParamName[j]] == False and self.ParamName[j] != 'B.R.': #B.R.以外のパラメータの場合
                            minimum.append(limitation[0]) #下限値は0
                            maximum.append(limitation[2]) #上限値は無限大

                        elif BindParams[self.ParamName[j]] == False and self.ParamName[j] == 'B.R.': #B.R.の場合
                            minimum.append(limitation[0]) #下限値は0
                            maximum.append(limitation[1]) #上限値は1

                constraint = (tuple(minimum), tuple(maximum)) #constraint: フィッティングパラメータの範囲制限値を格納
                
                #フィッティングを実行
                popt, _ = optimize.curve_fit(function.Voigt, BindingEnergy, IntensityBG, p0 = list(itertools.chain.from_iterable(self.guess_init)), bounds = constraint, maxfev = 50000)

                self.FitParams.clear()
                for i in range(0, int((len(popt)+len(self.BindIndex))/6), 1):
                    p = popt.tolist() #フィッティングパラメータが格納されているtupleをリストに変換
                    
                    for j in self.BindIndex:
                        s = j[0] #s: index of fitting components, Voigt関数の番号
                        t = j[1] #t: index of fitting parameters, パラメータの番号
                        st = 6*s + t #st: 拘束されたパラメータの挿入位置

                        p.insert(st, self.Dict_FitComps[f'Comp. {s+1}'][self.ParamName[t]]) #拘束されたパラメータを挿入

                    q = p[6*i : 6*(i+1)] #q: 6個ごとにパラメータを取り出しリストに格納, 各Voigt関数のパラメータに分ける
                    self.FitParams.append(q) # フィッティング結果をn*6リストの形で保存, nはVoigt関数の数

                self.ax.cla()
                self.ax.set_xlabel(xlabel = 'Binding Energy (eV)', fontsize = 14)
                self.ax.invert_xaxis()
                self.ax.set_ylabel(ylabel = 'Intensity (a. u.)', fontsize = 14)
                self.ax.minorticks_on()

                Voight_comp = function.Voigt(BindingEnergy, *self.FitParams)[0]
                for n, i in enumerate(Voight_comp):
                    #FitComp_fill: Fitting Components Fill, パラメータ最適化後のVoigt関数を書く成分ごとにプロット
                    FitComp_fill = self.ax.fill_between(BindingEnergy, i, np.zeros_like(BindingEnergy), lw = 1.5, facecolor = 'none', hatch = '////', alpha = 1, edgecolor = cm.rainbow(n/len(Voight_comp)))

                Fit = function.Voigt(BindingEnergy, *self.FitParams)[1] #フィッティング結果のVoigt関数の和, 1つの関数・曲線として得られる
                PeakArea = function.Voigt(BindingEnergy, *self.FitParams)[2] #各Voigt関数のピーク面積

                Experiment = self.ax.scatter(BindingEnergy, IntensityBG, s = 35, facecolors = 'none', edgecolors = 'black') #実験データ, 中空の円でプロット
                Spectram_Fit = self.ax.plot(BindingEnergy, Fit, c = 'red', lw = 1.5) #フィッティング結果のVoigt関数の和, 1つの関数・曲線としてプロット

                self.canvas.draw()
                
                print(self.FitParams) #フィッティング結果のパラメータを表示

                N_func = len(self.FitParams) #Voigt関数の数
                for i in range(N_func):
                    if f'listSpin{i+1}' in self.dictSpinBoxList.keys():
                        BE = self.dictSpinBoxList[f'listSpin{i+1}'][0]
                        Intensity = self.dictSpinBoxList[f'listSpin{i+1}'][1]
                        Wid_G = self.dictSpinBoxList[f'listSpin{i+1}'][2]
                        Wid_L = self.dictSpinBoxList[f'listSpin{i+1}'][3]
                        SOS = self.dictSpinBoxList[f'listSpin{i+1}'][4]
                        BR = self.dictSpinBoxList[f'listSpin{i+1}'][5]

                        BE.setValue(self.FitParams[i][0])
                        Intensity.setValue(self.FitParams[i][1])
                        Wid_G.setValue(self.FitParams[i][2])
                        Wid_L.setValue(self.FitParams[i][3])
                        SOS.setValue(self.FitParams[i][4])
                        BR.setValue(self.FitParams[i][5])

                for i in range(len(PeakArea)):
                    print(PeakArea[i]) #各Voigt関数のピーク面積を表示
                    if i%2 == 1: #ピーク面積の比を表示
                        print(PeakArea[i]/PeakArea[i-1])

        elif Button.text() == 'add BG' and self.FitParams != []: #差し引いたバックグラウンドを戻す
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

            Experiment = self.ax.scatter(BindingEnergy, Iex_withBG, s = 35, facecolors = 'none', edgecolors = 'black') # experimental data with Background
            Spectram_Fit = self.ax.plot(BindingEnergy, Ifit_withBG, c = 'red', lw = 1.5) # fitting curve with Background
            BG = self.ax.plot(BindingEnergy, Background, c = 'black', lw = 1) # Background

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
    
    # fit panelのチェックボックスから値を取得するメソッド. チェックボックスにconnectされてる.
    def getCheckState(self):
        CheckBox = self.sender()
        Index = CheckBox.index

        for i in range(1, 7, 1):
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

    def motion(self, event):
        if self.gco == None:
            return
        x = event.xdata
        y = event.ydata
        self.gco.set_data(x,y)
        self.canvas.draw()

    def onpick(self, event):
        if isinstance(event.artist, Line2D):
            self.gco = event.artist

    def release(self, event):
        self.gco = None

    def onclick(self, event):
        if event.button == 3:
            canvas = event.canvas
            fig = canvas.figure
            canvas_width, canvas_height = fig.get_size_inches()*fig.dpi
            transform = fig.transFigure
            x, y = event.x, event.y
            g_pos = self.PlotPanel.mapToGlobal(self.PlotPanel.pos())
            x_global = g_pos.x() + x
            y_global = g_pos.y() - y + canvas_height

            location = QPoint()
            location.setX(int(x_global))
            location.setY(int(y_global))

            action = self.cmenu.exec_(location)

            print(x, y, g_pos, x_global, y_global)

    def MakeAnnotation(self, event):
        g_pos = self.PlotPanel.mapToGlobal(self.PlotPanel.pos())
        self.Widget_annotation = QWidget()
        self.Widget_annotation.setGeometry(g_pos.x(), g_pos.y(), 400, 300)
        self.Widget_annotation.setWindowTitle('add annotation')

        TextField = QTextEdit()
        TextField.setFixedSize(400, 150)
        ButtonName = ['Font', 'Color', 'Done']
        layout_button = QHBoxLayout()
        for i in range(len(ButtonName)):
            self.button_aanotation = QPushButton(ButtonName[i], self.Widget_annotation)
            layout_button.addWidget(self.button_aanotation)

        layout = QVBoxLayout()
        layout.addWidget(TextField)
        layout.addLayout(layout_button)
        self.Widget_annotation.setLayout(layout)

        self.Widget_annotation.show()


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

        if type(params[0]) is list: # tuple(list[])で入力した場合, 各voigt関数成分を独立に格納したlist[NDarray, NDarray, ...]と各成分の和(NDarray)を返す, グラフ描画ではこちらの処理になる
            N_func = len(params)
            
            list_y_V = [] # ピーク強度格納用リスト, voigt functionを成分ごとに格納する
            y_Vtotal = np.zeros_like(x) # ピーク強度格納用リスト, voigt functionの和を格納する
            list_A_Vw = [] # ピーク面積格納用リスト, 分裂がある場合は強度の大きいピークの方の面積用になる
            list_A_Vt = [] # ピーク面積格納用リスト, 分裂がある場合は強度の小さいピークの方の面積用になる
            for i in range(0, N_func, 1):    
                y_V = np.zeros_like(x) # 関数の初期化

                if AbsorRel == 'Absol.': # ピーク位置:Absol.(絶対位置指定)の場合
                    BE = params[i][0] # ピーク位置

                elif AbsorRel == 'Relat.' and RelMethod == 'Method 1': # ピーク位置:Relat.(相対位置指定)の場合, method1: 相対位置の基準は1つ目のピークの位置
                    if i == 0: # 1つ目のピークの場合, BEはそのまま
                        BE = params[i][0]

                    elif i > 0: # 2つ目以降のピークの場合, BEは1つ目のピークの位置に相対位置を足したもの
                        BE = params[0][0] + params[i][0]

                elif AbsorRel == 'Relat.' and RelMethod == 'Method 2': # ピーク位置:Relat.(相対位置指定)の場合, method2: 相対位置の基準は奇数番ピークの位置
                    if i%2 == 0: # 奇数番のピークの場合, BEはそのまま(Pythonのindexは0から始まるため)
                        BE = params[i][0]

                    elif i%2 == 1: # 偶数番のピークの場合, BEは奇数番のピークの位置に相対位置を足したもの
                        BE = params[i-1][0] + params[i][0]
                
                I = params[i][1] # ピーク強度
                W_G = params[i][2] # ガウシアン成分の幅
                gamma = params[i][3] # ガンマパラメータ. ローレンチアンの幅(比率)を決める
                SOS = params[i][4] # Spin-Orbit splitting. スピン軌道相互作用によるピーク分裂幅を決める
                BR = params[i][5] # Branch ratio. 方位量子数ごとに決まるピーク強度比. 例えば理想的にはp軌道なら1:2の強度比でピークが分裂する

                z = (x - BE + 1j*gamma)/(W_G * np.sqrt(2.0)) # 強度の大きいピークに対する複素変数の定義
                w = scipy.special.wofz(z) #Faddeeva function (強度の大きい方)
                s = (x - BE - SOS + 1j*gamma)/(W_G * np.sqrt(2.0)) # spin orbit couplingによる分裂ピーク表現用の複素変数の定義
                t = scipy.special.wofz(s) #Faddeeva function (強度の小きい方, spin orbit couplingによる分裂ピーク)
                
                V_w = I * (w.real)/(W_G * np.sqrt(2.0*np.pi)) #Faddeeva functionの実部を使用したvoight関数の定義
                Area_V_w = np.abs(integrate.trapz(V_w, x)) # ピークの面積を計算

                V_t = BR * I * (t.real)/(W_G * np.sqrt(2.0*np.pi)) #Faddeeva functionの実部を使用したvoight関数の定義, spin orbit couplingによる分裂ピーク
                Area_V_t = np.abs(integrate.trapz(V_t, x)) # ピークの面積を計算

                y_V = y_V + V_w + V_t # Voigt functionの成分保存
                y_Vtotal = y_Vtotal + V_w + V_t # Voigt functionの総和, 1つの関数としての表現

                list_y_V.append(y_V)
                list_A_Vw.append(Area_V_w)
                list_A_Vt.append(Area_V_t)

            return [list_y_V, y_Vtotal, list_A_Vw, list_A_Vt]


        elif type(params[0]) is not list: # tuple(parameters)の場合, 束縛されているパラメーターを後から取り込みVoigt functionを計算する
            counts = len(XPS_FP.BindIndex) # 束縛されているパラメーターの数

            N_func = int((len(params)+counts)/6) # voiht関数の数
            
            params_mod = list(params) # パラメーターをリストに変換
            for i in XPS_FP.BindIndex:
                s = i[0] # 束縛されているパラメーターの関数番号
                t = i[1] # 束縛されているパラメーターのパラメーター番号
                st = 6*s + t # 束縛されているパラメーターの挿入位置を計算

                params_mod.insert(st, XPS_FP.Dict_FitComps[f'Comp. {s+1}'][XPS_FP.ParamName[t]]) # 束縛されているパラメーターを挿入

            L_params = [] # ピークのパラメーターを格納するリスト
            y_V = np.zeros_like(x) # Voigt functionの総和を格納する配列, 1つの関数として表現(フィッティング結果そのもの)
            for i in range(0, N_func, 1):
                p = params_mod[6*i : 6*(i+1)] # ピークのパラメーターを取り出す
                L_params.append(p) # ピークのパラメーターをリストに格納

                if AbsorRel == 'Absol.': # ピーク位置:Absol.(絶対位置指定)の場合
                    BE = L_params[i][0] # ピーク位置

                elif AbsorRel == 'Relat.' and RelMethod == 'Method 1': # ピーク位置:Relat.(相対位置指定)の場合, method1: 相対位置の基準は1つ目のピークの位置
                    if i == 0: # 1つ目のピークの場合, ピーク位置はそのまま
                        BE = L_params[i][0]

                    elif i > 0: # 2つ目以降のピークの場合, ピーク位置は1つ目のピークの位置からの相対位置
                        BE = L_params[0][0] + L_params[i][0]

                elif AbsorRel == 'Relat.' and RelMethod == 'Method 2': # ピーク位置:Relat.(相対位置指定)の場合, method2: 相対位置の基準は奇数番ピークの位置
                    if i%2 == 0: # 奇数番のピークの場合, ピーク位置はそのまま(Pythonのインデックスは0から始まるため)
                        BE = L_params[i][0]

                    elif i%2 == 1: # 偶数番のピークの場合, ピーク位置は奇数番のピークの位置からの相対位置
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
    ex = XPS_FittingPanels()
    sys.exit(app.exec_())