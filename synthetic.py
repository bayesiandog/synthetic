from ultralytics import YOLO
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2 as cv

#from IPython.display import Images
import torch, torchvision
import matplotlib.pyplot as plt



def getROI(image, poly):
    image_array = np.array(image)
    # Black image except roi
    mask = np.ones_like(image_array, dtype=np.uint8) * 255
    cv.fillPoly(mask, poly, (0, 0, 0))
    resultWhite = cv.bitwise_or(image_array, mask)
    
    new_mask = np.zeros_like(image)
    cv.fillPoly(new_mask, poly, (255, 255, 255))
    resultBlack = cv.bitwise_and(resultWhite, new_mask)
    #cv.imshow("Black image except roi", resultBlack)
    #cv.imshow("White image except roi", resultWhite)
    #cv.waitKey(0)
    return resultWhite, resultBlack

def moveROI(pixels, resultWhite):    
    white = np.ones_like(image_array, dtype=np.uint8) * 255
    white[:, pixels:] = resultWhite[:, :-pixels]
    return white

def duplicate(image, poly, pixels):
    poly[:, :, 0] += pixels
    cv.fillPoly(image, [poly], (255, 255, 255))
    final = cv.bitwise_and(image, moved)
    cv.imshow("Translated ROI", final)
    cv.waitKey(0)

# Load the trained model
models = YOLO('yolov8n-seg.pt')

# Detect objects in an image
image = cv.imread('aaaa.jpg')
height, width, channels  = image.shape
print(height, width)
rimage = cv.resize(image, (640, 640), interpolation=cv.INTER_AREA)

# Make predictions on the image
result = models.predict(image, conf=0.9)
for r in result:
    im_array = r.plot()  # plot a BGR numpy array of predictions

    #print(r.masks)
    boxes = r.boxes
    
    classes = boxes.cls
    
    dClasses = torch.unique(classes)

    detection_counts = {r.names[dClass.item()]: (classes == dClass).sum() for dClass in dClasses}
    detections = '\n'.join(f"{count} {class_name}s" for class_name, count in detection_counts.items())
    
    boxes = r.boxes.xyxy

    xy = np.array(r.masks.xy, dtype=int)
    
    image_array = np.array(image)
    resultWhite, resultBlack = getROI(image, xy)
    moved = moveROI(100, resultWhite)
    duplicate(image, xy, 100)
    
    new_boxes = [] #= torch.empty(1, 4, dtype = torch.float16)
    #print(r.boxes)
    nms = torchvision.ops.nms(boxes, r.boxes.conf, 0.9)
    #print(nms)

    imaged = Image.fromarray(cv.cvtColor(image, cv.COLOR_BGR2RGB))

    draw = ImageDraw.Draw(imaged)
    
    croppeds = []
    font = ImageFont.load_default()
    font = font.font_variant(size=70)
    for i in range(0, len(boxes)):
        if i in nms: 
            new_boxes.append(boxes[i])
            y1 = int(torch.round(boxes[i][1]))
            y2 = int(torch.round(boxes[i][3]))
            x1 = int(torch.round(boxes[i][0]))
            x2 = int(torch.round(boxes[i][2]))
            print(i, y1, y2, x1, x2)
            draw.rectangle([x1, y1, x2, y2], outline="red", width=10)
            draw.text((x1, y1-85), f"{r.names[classes[i].item()]}", align='left', font=font, fill='red')
            
            cropped = image[y1:y2, x1:x2]
            croppeds.append(cropped)

    for i, crop in enumerate(croppeds):
        if i==2:
            cv.imshow(f"New Crop {i}", crop)
            cv.imwrite(f"{i}.jpg", crop)
            #cv.waitKey(0)
            print(i, y1, y2, x1, x2)
            height, width, _ = crop.shape
            print(height, width)
            new_x1 = x1 + 100
            new_x2 = x2 + 100
            image[y1:y2, new_x1:new_x2] = crop
            cv.imshow(f"Duplicate {i}", image)
            
            cv.waitKey(0)
