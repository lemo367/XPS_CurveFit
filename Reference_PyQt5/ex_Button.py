import sys
from PyQt5.QtWidgets import (
    QVBoxLayout, QPushButton, QApplication, QWidget
)


class MainWindow(QWidget):
    def __init__(self, n_buttons):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        for k in range(n_buttons):
            button = QPushButton(f"Button {k}")
            button.index = k
            button.clicked.connect(self.on_change)
            layout.addWidget(button)

    def on_change(self):
        button = self.sender()
        print( button.text() )
        print( button.index )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow(16)
    w.show()
    app.exit(app.exec_())