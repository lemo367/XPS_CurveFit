import sys
import re
from PyQt5.QtWidgets import (QMainWindow, QTextEdit, 
    QAction, QFileDialog, QApplication)
import pandas as pd


# テキストフォーム中心の画面のためQMainWindowを継承する
class Example(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()


    def initUI(self):      

        self.textEdit = QTextEdit()
        self.setCentralWidget(self.textEdit)
        self.statusBar()

        # メニューバーのアイコン設定
        openFile = QAction('Open', self)
        # ショートカット設定
        openFile.setShortcut('Ctrl+O')
        # ステータスバー設定
        openFile.setStatusTip('Open new File')
        openFile.triggered.connect(self.DataReshape)

        # メニューバー作成
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)       

        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('File dialog')
        self.show()


    def DataReshape(self):
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

            Dict_DF = {} #分割したテキストデータをDataframeとして読み込み、管理する辞書
            for i in range(len(Div_DataFilePath)):
                with open(Div_DataFilePath[i], mode = 'w') as f:
                    f.write(Dict_Data[SpectraName[i]])

                dataset = pd.read_csv(Div_DataFilePath[i], header = 3, delimiter = '\t') #分割したテキストデータをDataframeとして読み込み
                Dict_DF[SpectraName[i]] = dataset #辞書に読み込んだDataframeを追加
            #------------ファイル分割処理--------------

        else:
            Dict_DF = {}
            dataset = pd.read_csv(fname[0], header = 3, delimiter = '\t')
            Dict_DF[SpectraName[i]] = dataset

    def fileDialog(self):
        # 第二引数はダイアログのタイトル、第三引数は表示するパス
            fPath = QFileDialog.getOpenFileName(self, 'Open file', '/home')

        # fname[0]は選択したファイルのパス（ファイル名を含む）
            if fPath[0]:
                dataset = pd.read_csv(fPath[0], header = 3, delimiter = r"\t")
                self.textEdit.setText(str(dataset))        

if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())