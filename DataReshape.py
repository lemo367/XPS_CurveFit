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
            self.f = open(fname[0], 'r')
            # テキストエディタにファイル内容書き込み
            with self.f:
                self.data = self.f.read()
                #self.textEdit.setText(data)
        
        LO_Dataset = [i.span() for i in re.finditer('Dataset', self.data)] #Location of 'Dataset'
        LO_colon = [i.start() for i in re.finditer(':', self.data)] #Location of ':' (colon)
        len_Data = len(self.data) #Length of data as nomber of characters
        SpectraName = [self.data[LO_Dataset[i][1]+1 : LO_colon[i]] for i in range(len(LO_colon))]
        
        Dict_Data = {}
        for i in range(len(LO_Dataset)):
            if i+1 < len(LO_Dataset):
                Div_data = self.data[LO_Dataset[i][0] : LO_Dataset[i+1][0]]

            elif i+1 == len(LO_Dataset):
                Div_data = self.data[LO_Dataset[i][0] : len_Data]
            
            Dict_Data[SpectraName[i]] = Div_data

        LO_SlashinPath = fname[0].rfind('/')
        PrefixDir = fname[0][0 : LO_SlashinPath]
        Div_DataFilePath = [f'{PrefixDir}/{i}.txt' for i in SpectraName]

        Dict_DF = {}
        for i in range(len(Div_DataFilePath)):
            with open(Div_DataFilePath[i], mode = 'w') as f:
                f.write(Dict_Data[SpectraName[i]])

            dataset = pd.read_csv(Div_DataFilePath[i], header = 3, delimiter = "\t")
            Dict_DF[SpectraName[i]] = dataset

        print(Dict_DF[SpectraName[2]])

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