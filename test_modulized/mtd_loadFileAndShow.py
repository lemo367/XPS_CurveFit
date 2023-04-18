import sys
from PyQt5.QtWidgets import(
    QMainWindow, QAction, QFileDialog, QApplication, QMdiArea, QMdiSubWindow, QLabel,
    QComboBox, QPushButton, QWidget, QDoubleSpinBox, QCheckBox, QVBoxLayout, QHBoxLayout, QMenu, QTextEdit)

class showFileData(QWidget):
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
                self.text.setText(data)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = showFileData()
    sys.exit(app.exec_())