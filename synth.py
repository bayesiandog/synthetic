import os
import sys
import cv2 as cv
import numpy as np
from PyQt5.QtWidgets import QApplication, QTabWidget, QLabel, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QFileDialog, QScrollArea, QShortcut
from PyQt5.QtGui import QImage, QPixmap, QKeySequence
from PyQt5.QtCore import Qt, pyqtSignal, QObject


class WorkerSignals(QObject):
    connected = pyqtSignal(int)


def getROI(image_array, poly):
    # Black image except roi
    
    print(poly)
    mask = np.ones_like(image_array, dtype=np.uint8) * 255
    cv.fillPoly(mask, poly, (0, 0, 0))
    resultWhite = cv.bitwise_or(image_array, mask)
    
    new_mask = np.zeros_like(image_array)
    cv.fillPoly(new_mask, poly, (255, 255, 255))
    resultBlack = cv.bitwise_and(resultWhite, new_mask)
    #cv.imshow("Black image except roi", resultBlack)
    #cv.imshow("White image except roi", resultWhite)
    #cv.waitKey(0)
    return resultWhite

def moveROI(image_array, pixels, resultWhite):    
    white = np.ones_like(image_array, dtype=np.uint8) * 255
    white[:, pixels:] = resultWhite[:, :-pixels]
    return white

def duplicate(image_array, poly, pixels, moved):
    poly[:, :, 0] += pixels
    cv.fillPoly(image_array, [poly], (255, 255, 255))
    final = cv.bitwise_and(image_array, moved)
    cv.imshow("Translated ROI", final)
    cv.waitKey(0)


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

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        self.image_label = QLabel()
        self.scroll_area.setWidget(self.image_label)
        
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.show_logo("aa.jpg")

        self.button = QPushButton('Choose dataset folder', self)
        self.button.clicked.connect(self.on_button_click)
        self.layout.addWidget(self.button)

         # Set up mouse events
        self.image_label.mousePressEvent = self.mouse_click
        self.image_label.mouseReleaseEvent = self.mouse_release
        self.image_label.mouseMoveEvent = self.mouse_move
        self.polygon = []
        
    def on_button_click(self):
        self.button.hide()
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
        else:
            self.button.show()

    def mouse_click(self, event):
        global xp, yp
        if event.button() == Qt.LeftButton:
            xp = event.x()
            yp = event.y()
            self.polygon.append((xp,yp))
            LB = f'{xp}, {yp}'
            cv.putText(self.image, LB, (xp, yp), cv.FONT_HERSHEY_PLAIN, 1, (255, 255, 0), 2)
            q_image = QImage(self.image.data, self.width, self.height, self.bytes_per_line, QImage.Format_BGR888)
            pixmap = QPixmap.fromImage(q_image)
            self.image_label.setPixmap(pixmap)            
    
    def mouse_move(self, event):
        global xp, yp
        if event.buttons() & Qt.LeftButton:  # Check if the left button is pressed
            xp = event.x()
            yp = event.y()
            self.polygon.append((xp, yp))  # Add the moved point to the list
            LB = f'{xp}, {yp}'
            #cv.putText(self.image, LB, (xp, yp), cv.FONT_HERSHEY_PLAIN, 1, (255, 255, 0), 2)
            cv.circle(self.image, (xp, yp), radius=2, color=(255, 255, 0), thickness=-1)  # Thickness=-1 for filled circle
            q_image = QImage(self.image.data, self.width, self.height, self.bytes_per_line, QImage.Format_BGR888)
            pixmap = QPixmap.fromImage(q_image)
            self.image_label.setPixmap(pixmap)

    def mouse_release(self, event):
        global x, y
        if event.button() == Qt.LeftButton:
            x = event.x()
            y = event.y()
            RB = f'{x}, {y}'
            #cv.putText(self.image, RB, (x, y), cv.FONT_HERSHEY_PLAIN, 1, (0, 255, 255), 2)
            cv.rectangle(self.image, (xp, yp), (x, y), (255, 0, 0), 2)
            q_image = QImage(self.image.data, self.width, self.height, self.bytes_per_line, QImage.Format_BGR888)
            pixmap = QPixmap.fromImage(q_image)
            self.image_label.setPixmap(pixmap)
            print(self.polygon)
            image_array = np.array(self.image)
            self.polygon = np.array([self.polygon], dtype=np.int32)
            roi = getROI(image_array, self.polygon)
            moved = moveROI(image_array, 100, roi)
            duplicate(image_array, self.polygon, 100, moved)

            #self.anotation.show()

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
        label_size = self.image_label.size()
        
        if (self.height < label_size.height()) or self.width < label_size.width(): 
            self.image = cv.resize(self.image, (label_size.width(), label_size.height()))

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
