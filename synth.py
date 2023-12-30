import os
import random
import sys
import cv2 as cv
import numpy as np
from PyQt5.QtWidgets import QApplication, QTabWidget, QLabel, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QFileDialog, QScrollArea, QShortcut
from PyQt5.QtGui import QImage, QPixmap, QKeySequence
from PyQt5.QtCore import Qt, pyqtSignal, QObject


class Poly:
  def __init__(self, poly=None, name=None, age=None, anotation=None, nump=None):
    self.name = name
    self.age = age
    self.anotation = anotation
    if nump==0:
        self.poly = np.array([poly], dtype=np.int32)        
    else:
        self.poly = poly

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
        self.showMaximized()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        #self.tab_widget = QTabWidget(self)
        #self.layout.addWidget(self.tab_widget)
        
        self.button = QPushButton('Choose dataset folder', self)
        self.button.clicked.connect(self.on_button_click)
        self.layout.addWidget(self.button)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        self.image_label = QLabel()
        self.scroll_area.setWidget(self.image_label)
        
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.show_logo("aa.jpg")

        self.anotation = QTextEdit()
        self.anotation.setPlaceholderText("Enter class and press save.")
        self.anotation.setFixedSize(100, 100)
        self.layout.addWidget(self.anotation)
        self.anotation.hide()

        # Add a button to save anotations
        self.save_button = QPushButton("Save")
        #self.save_button.clicked.connect(self.save)
        self.layout.addWidget(self.save_button)
        self.save_button.hide()

        # Add a button to iterate through images in file
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.iterate_images)
        self.layout.addWidget(self.next_button)
        self.next_button.hide()

         # Set up mouse events
        self.image_label.mousePressEvent = self.mouse_click
        self.image_label.mouseReleaseEvent = self.mouse_release
        self.image_label.mouseMoveEvent = self.mouse_move
        
        
    def on_button_click(self):
        self.button.hide()
        options = QFileDialog.Options()
        self.folder_path = QFileDialog.getExistingDirectory(self, "Choose dataset folder", options=options)
        if self.folder_path:
            #print("Selected Folder:", self.folder_path)
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
        if event.button() == Qt.LeftButton:
            xp = event.x()
            yp = event.y()
            self.polygon.append((xp,yp))
            cv.circle(self.imageCopy, (xp, yp), radius=2, color=(255, 255, 0), thickness=-1)  # Thickness=-1 for filled circle
            q_image = QImage(self.imageCopy.data, self.width, self.height, self.bytes_per_line, QImage.Format_BGR888)
            pixmap = QPixmap.fromImage(q_image)
            self.image_label.setPixmap(pixmap)            
    
    def mouse_move(self, event):
        if event.buttons() & Qt.LeftButton:  # Check if the left button is pressed
            xp = event.x()
            yp = event.y()
            self.polygon.append((xp, yp))  # Add the moved point to the list            
            cv.circle(self.imageCopy, (xp, yp), radius=2, color=(255, 255, 0), thickness=-1)  # Thickness=-1 for filled circle
            q_image = QImage(self.imageCopy.data, self.width, self.height, self.bytes_per_line, QImage.Format_BGR888)
            pixmap = QPixmap.fromImage(q_image)
            self.image_label.setPixmap(pixmap)

    def mouse_release(self, event):
        if event.button() == Qt.LeftButton:
            xp = event.x()
            yp = event.y()
            self.polygon.append((xp, yp))
            anotation = self.anotation.toPlainText().strip()
            self.objects.append(Poly(self.polygon, anotation=anotation, nump=0))
            maxX, maxY, minX, minY = self.get_boundaries(self.objects[self.objCounter].poly)
            
            cv.rectangle(self.imageCopy, (minX, minY), (maxX, maxY), (255, 0, 0), 2)
            # TODO Store the boundaries in YOLO format for training
            q_image = QImage(self.imageCopy.data, self.width, self.height, self.bytes_per_line, QImage.Format_BGR888)
            pixmap = QPixmap.fromImage(q_image)
            self.image_label.setPixmap(pixmap)
            self.polygon = []            
            self.file_path = f"{self.image_paths[self.img_ctr].split('.jpg')[0]}"
            self.file_path += ".txt"
            self.anotate(self.objects[self.objCounter], self.file_path, 1)
            self.objCounter += 1

    def anotate(self, polyObj, file_path, original):
        maxX, maxY, minX, minY = self.get_boundaries(polyObj.poly)
        anotation = polyObj.anotation
        b = next((object_class for object_class, name in d_classes.items() if name == anotation), None)

        if b==None:
            return
        if not os.path.exists(file_path):
            open(file_path, 'x')
        #else:
        #    print(f"{file_path} already exists.")

        object_class_id = b[0]
        x_center = (abs(maxX - minX) / 2) + minX
        y_center = (abs(maxY - minY) / 2) + minY
        x_center /= self.width
        y_center /= self.height
        
        width = abs(maxX - minX) / self.width  
        height = abs(maxY - minY) / self.height 
        # Format the YOLO line for this object
        yolo_line = f"{object_class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n"
        if original:
            self.original_anotation += yolo_line
            
        with open (file_path,'a') as self.f:
            self.f.write(yolo_line)
            self.f.close()

    def add_original_anotation(self, file_path):
        with open (file_path,'a') as self.f:
            self.f.write(self.original_anotation)
            self.f.close()
            
    def iterate_images(self):
        self.augment()
        self.img_ctr += 1
        if self.img_ctr < len(self.image_paths):
            self.show_image(self.img_ctr)
        else:
            self.show_logo("aa.jpg")
            self.next_button.hide()

    def change_image(self, image, type):
        image_array = np.array(image)
        image_hsv = cv.cvtColor(image_array, cv.COLOR_BGR2HSV)
        image_hsv[:, :, 1] += 300
        image_hsv = np.clip(image_hsv, 0, 255)
        image = cv.cvtColor(image_hsv, cv.COLOR_HSV2BGR)
        return image

    def augment(self):
        for imageInd in range(5):
            self.created_objects_cnt = 0
            self.image = self.original_image
            self.image = self.change_image(self.image, imageInd)
            original_image_array = np.array(self.original_image)
            self.polygon = np.array([self.polygon], dtype=np.int32)
            height, width, color = original_image_array.shape
            for obj in self.objects:
                axis = random.randint(0, 1)
                flip = random.randint(0, 1)
                dir = random.randint(0, 1)
                poly = obj.poly
                if flip:
                    poly = np.array([[[width - x, y]  for x, y in row] for row in obj.poly])            
                
                maxX, maxY, minX, minY = self.get_boundaries(poly)                
                if (maxX > (width/2)) or (maxY > (height / 2)):
                    dir = 1

                if axis==0:
                    if (width - maxX) < (maxX - minX):
                        disp = random.randint(width - maxX, maxX - minX)
                    else:
                        disp = random.randint(maxX - minX, width - maxX)
                        if (width - maxX) > minX:
                            disp = minX
                else:
                    if (height - maxY) < (maxY - minY):
                        disp = random.randint(height - maxY, maxY - minY)
                    else:
                        disp = random.randint(maxY - minY, height - maxY)
                        if (height - maxY) > minY:
                            disp = minY
                        
                col, i = self.check_overlap(poly, disp, axis, dir)
                if col==-1:
                    image_array = np.array(self.image)
                    roi = self.getROI(image_array, poly, flip)
                    moved = self.moveROI(image_array, disp, roi, axis, dir)
                    self.image, poly = self.duplicate(image_array, poly, disp, moved, axis,dir)
                    self.created_objects.append(Poly(poly, anotation=obj.anotation, nump=1))
                    self.file_path = f"{self.image_paths[self.img_ctr].split('.jpg')[0]}"
                    self.file_path += f"{imageInd}.txt"            
                    self.anotate(self.created_objects[self.created_objects_cnt], self.file_path, 0)
                    self.created_objects_cnt += 1
                else:
                    print(f"{i} collision")
                    continue
            self.created_objects = []
            self.file_path = f"{self.image_paths[self.img_ctr].split('.jpg')[0]}"
            self.file_path += f"{imageInd}.jpg"
            cv.imwrite(self.file_path, self.image)
            self.file_path = f"{self.image_paths[self.img_ctr].split('.jpg')[0]}"
            self.file_path += f"{imageInd}.txt"
            self.add_original_anotation(self.file_path)
            
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
        self.imageCopy = self.image.copy()        
        self.height, self.width, self.channel = self.image.shape
        label_size = self.image_label.size()
        
        if (self.height < label_size.height()) or self.width < label_size.width():
            self.imageCopy = cv.resize(self.imageCopy, (label_size.width(), label_size.height()))
            self.image = cv.resize(self.image, (label_size.width(), label_size.height()))
        self.original_image = self.image.copy()
        self.height, self.width, self.channel = self.imageCopy.shape
        self.bytes_per_line = 3 * self.width
        q_image = QImage(self.imageCopy.data, self.width, self.height, self.bytes_per_line, QImage.Format_BGR888)
    
        pixmap = QPixmap.fromImage(q_image)
        self.image_label.setPixmap(pixmap)
        self.objects = []
        self.created_objects = []
        self.objCounter = 0
        self.polygon = []
        self.original_anotation = ""
        self.next_button.show()
        self.anotation.show()

    def get_boundaries(self, poly):
        maxX = np.max(poly[:, :, 0])
        maxY = np.max(poly[:, :, 1])
        minX = np.min(poly[:, :, 0])
        minY = np.min(poly[:, :, 1])
        return maxX, maxY, minX, minY

    def check_overlap(self, poly, disp, axis, dir):
        col = -1
        index = -1
        polyc = np.copy(poly)
        if dir==0:
            polyc[:, :, axis] += disp
        else:
            polyc[:, :, axis] -= disp
        pmaxX, pmaxY, pminX, pminY = self.get_boundaries(polyc)
        for i, obj in enumerate(self.objects):
            maxX, maxY, minX, minY = self.get_boundaries(obj.poly)
            xRange = range(minX, maxX)
            yRange = range(minY, maxY)
            if ((pminX in xRange) or (pmaxX in xRange)) and ((pminY in yRange) or (pmaxY in yRange)):
                col = 1
                index = i
            #print("col", col, i)
        
        for i, obj in enumerate(self.created_objects):
            maxX, maxY, minX, minY = self.get_boundaries(obj.poly)
            xRange = range(minX, maxX)
            yRange = range(minY, maxY)
            if ((pminX in xRange) or (pmaxX in xRange)) and ((pminY in yRange) or (pmaxY in yRange)):
                col = 1
                index = i
            #print("col in created", col, i)
        return col, index

    def normalize(self, value, min_val, max_val):
        return (value - min_val) / (max_val - min_val)

    def getROI(self, image_array, poly, flip):
        '''
        image_hsv = cv.cvtColor(image_array, cv.COLOR_BGR2HSV)
        image_hsv[:, :, 1] += 300
        image_hsv = np.clip(image_hsv, 0, 255)
        image_array = cv.cvtColor(image_hsv, cv.COLOR_HSV2BGR)
        '''
        if flip:
            image_array = cv.flip(image_array, 1)
        mask = np.ones_like(image_array, dtype=np.uint8) * 255
        #maxX, maxY, minX, minY = self.get_boundaries(poly)
        #height, widths, color = image_array.shape
        #width = maxX - minX
        #middle = minX + width / 2
        #shift = np.array([[[maxX - int(width * (self.normalize(x, minX, maxX))), y]  for x, y in row] for row in poly])        
        #shift = poly + [(maxX - minX), 0]
        
        cv.fillPoly(mask, poly, (0, 0, 0))
        resultWhite = cv.bitwise_or(image_array, mask)
        return resultWhite

    def moveROI(self, image_array, pixels, resultWhite, axis, dir):
        white = np.ones_like(image_array, dtype=np.uint8) * 255
        if axis==0:
            if dir==0:
                white[:, pixels:] = resultWhite[:, :-pixels]
            else:
                white[:, :-pixels] = resultWhite[:, pixels:]
        else:
            if dir==0:
                white[pixels:, :] = resultWhite[:-pixels, :]
            else:
                white[:-pixels, :] = resultWhite[pixels:, :]
        return white

    def duplicate(self, image_array, poly, pixels, moved, axis, dir):
        polyc = np.copy(poly)
        
        if dir==0:
            polyc[:, :, axis] += pixels
        else:
            polyc[:, :, axis] -= pixels
        
        cv.fillPoly(image_array, [polyc], (255, 255, 255))
        final = cv.bitwise_and(image_array, moved)
        return final, polyc

if __name__ == '__main__':
    d_classes = {
        "0": "mr",
        "1": "nc",
        "2": "wf"
    }
    app = QApplication(sys.argv)
    synthesis = Synthesis()
    synthesis.show()
    sys.exit(app.exec_())
