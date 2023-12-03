import os
import sys
import cv2 as cv
import numpy as np
from PyQt5.QtWidgets import QApplication, QTabWidget, QLabel, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QFileDialog, QScrollArea, QShortcut
from PyQt5.QtGui import QImage, QPixmap, QKeySequence
from PyQt5.QtCore import Qt, pyqtSignal, QObject


class WorkerSignals(QObject):
    connected = pyqtSignal(int)


class Synthesis(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.signals = WorkerSignals()
        self.img_ctr = 0
        self.setWindowTitle("Dataset Augmentation")
        self.setGeometry(100, 100, 2500, 1800)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        #self.tab_widget = QTabWidget(self)
        #self.layout.addWidget(self.tab_widget)

        self.image_label = QLabel(self)
        self.layout.addWidget(self.image_label)
        self.show_logo("aa.jpg")

        self.button = QPushButton('Choose dataset folder', self)
        self.button.clicked.connect(self.on_button_click)
        self.layout.addWidget(self.button)
        
        

    def on_button_click(self):
        options = QFileDialog.Options()
        self.folder_path = QFileDialog.getExistingDirectory(self, "Choose dataset folder", options=options)
        if self.folder_path:
            print("Selected Folder:", self.folder_path)
        file_list = os.listdir(self.folder_path)
        
        self.image_names = []
        self.image_paths = []
        # Iterate through the files and print their names
        for file_name in file_list:
            if file_name.lower().endswith(".jpg"):
                image_path = os.path.join(self.folder_path, file_name)
                self.image_paths.append(image_path)
                image_namesjpg = [os.path.basename(file_name)]
                self.image_names.append((image_namesjpg[0].split(".jpg"))[0])
        
        self.show_image(self.img_ctr)

    def show_logo(self, image_path):
        image = cv.imread(image_path)
        image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        height, width, channel = image.shape
        
        q_image = QImage(image.data, width, height, 3 * width, QImage.Format_RGB888)
        pixmap = QPixmap(q_image)
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignCenter)
    
    def show_image(self, counter):
        self.image = cv.imread(f'{self.image_paths[counter]}', cv.IMREAD_COLOR)
        
        self.height, self.width, self.channel = self.image.shape
        self.bytes_per_line = 3 * self.width
        q_image = QImage(self.image.data, self.width, self.height, self.bytes_per_line, QImage.Format_BGR888)
    
        pixmap = QPixmap.fromImage(q_image)
        self.image_label.setPixmap(pixmap)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    synthesis = Synthesis()
    synthesis.show()
    sys.exit(app.exec_())
