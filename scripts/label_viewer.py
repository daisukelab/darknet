# Label Viewer
#
# This viewer
# - Handles file/folder structure below:
#   images/file1.jpg
#   images/file2.jpg
#   ...
#   labels/file1.txt
#   labels/file2.txt
#   ...
# - Reads a file that contains list of image files to view.
# - Label file format is yolo's as below:
#   label x y w h
#   * x y are center of image in [0.0, 1.0]
#   * w h are size in [0.0, 1.0]
# 

import os, sys, re
import operator, math
import cv2, numpy as np

splitter = re.compile('[, \t\n\r:]+')
_W = 800
_H = 800

def fitToRect(image):
    w = image.shape[1]
    h = image.shape[0]
    wph = float(w) / h
    _WpH = float(_W) / _H
    print wph, _WpH
    if _WpH < wph: # portrait
        w = _W
        h = int(_H / wph)
        x = 0
        y = int((_H - h) / 2)
    else:
        w = int(_W * wph)
        h = _H
        x = int((_W - w) / 2)
        y = 0
    print image.shape, x, y, w, h
    frame = np.zeros((_H, _W, 3), dtype=np.uint8)
    frame[y:y+h, x:x+w] = cv2.resize(image, (w, h))
    return frame

## opencv to wrap
class opencv_wrapper:
    def __init__(self):
        self.isCV3 = self.isOpenCV3()
        self.FILLED = self.FILLED()
        self.LINE_AA = self.LINE_AA()
        self.CAP_PROP_FRAME_WIDTH = self.CAP_PROP_FRAME_WIDTH()
        self.CAP_PROP_FRAME_HEIGHT = self.CAP_PROP_FRAME_HEIGHT()
    def isOpenCV3(self):
        return cv2.__version__[0] == '3'
    def CAP_PROP_FRAME_WIDTH(self):
        if self.isCV3:
            return cv2.CAP_PROP_FRAME_WIDTH
        else:
            return cv2.cv.CV_CAP_PROP_FRAME_WIDTH
    def CAP_PROP_FRAME_HEIGHT(self):
        if self.isCV3:
            return cv2.CAP_PROP_FRAME_HEIGHT
        else:
            return cv2.cv.CV_CAP_PROP_FRAME_HEIGHT
    def FILLED(self):
        if self.isCV3:
            return cv2.FILLED
        else:
            return cv2.cv.CV_FILLED
    def LINE_AA(self):
        if self.isCV3:
            return cv2.LINE_AA
        else:
            return cv2.cv.CV_AA
    def calcOpticalFlowFarneback(self, prev, gray, a, b, c, d, e, f, g):
        if self.isCV3:
            return cv2.calcOpticalFlowFarneback(prev, gray, None,
                                                a, b, c, d, e, f, g)
        else:
            return cv2.calcOpticalFlowFarneback(prev, gray,
                                                a, b, c, d, e, f, g)

cvw = opencv_wrapper()

## label
class Label:
    def __init__(self, imgename):
        self.imgename = imgename
    def drawOnImage(self, image, color, index):
        cv2.rectangle(image, (self.x, self.y),
                      (self.x + self.w, self.y + self.h), color, 2)
        cv2.putText(image, str(self.cls), (self.x + 3, self.y + self.h - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color,
                    thickness=2, lineType=cvw.LINE_AA)
        cv2.putText(image, str(index), (self.x + 3, self.y + 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color,
                    thickness=2, lineType=cvw.LINE_AA)
        print 'test: ' + str(self), '=>', self.x, self.y, self.w, self.h
    def readText(self, line, W, H):
        xs = splitter.split(line)
        self.cls = int(xs[0].strip())
        r = [float(xs[i].strip()) for i in range(1,5)]
        self.x = int((r[0] - r[2]/2) * W)
        self.y = int((r[1] - r[3]/2) * H)
        self.w = int((r[2]) * W)
        self.h = int((r[3]) * H)
        self.orgLine = line
    def setClass(self, cls):
        self.cls = cls
    def __str__(self):
        xs = splitter.split(self.orgLine)
        xs[0] = str(self.cls)
        return ' '.join(xs)

def makeLabelfile(imagefile):
    return imagefile.replace('images/', 'labels/').replace('.jpg', '.txt')
def loadLabels(imagefile, shape):
    labelfile = makeLabelfile(imagefile)
    with open(labelfile) as f:
        rawlines = f.read().splitlines()
    f.close()
    labels = []
    for l in rawlines:
        xs = splitter.split(l)
        label = Label(xs[0].strip())
        label.readText(l, shape[1], shape[0])
        labels.append(label)
    return labels
def saveLabels(imagefile, labels):
    labelfile = makeLabelfile(imagefile)
    with open(labelfile, 'w') as f:
        for l in labels:
            f.write(str(l) + '\n')
    f.close()

## viewer model
def loadImageList(imagelist):
    with open(imagelist) as f:
        imagelist = f.read().splitlines()
    f.close()
    return imagelist

class Model:
    def __init__(self, imagelist):
        self.labels = []
        self.images = []
        self.cur = 0
        self.imagelist = imagelist
        self.edited = False
    def load(self):
        self.images = loadImageList(self.imagelist)
        self.loadImage()
    def curFile(self):
        return self.images[self.cur]
    def loadImage(self):
        '''load image and labels'''
        image = cv2.imread(self.curFile())
        if image is None or image.shape[0] == 0:
            print 'Failed to load: ', self.curFile()
        self.labels = loadLabels(self.curFile(), image.shape)
        self.curLabel = 0
        self.image = image
        self.edited = False
        return image
    def saveLabels(self):
        # save labels before loading
        if not self.edited:
            return
        saveLabels(self.curFile(), self.labels)
    def setNextClass(self, cls):
        self.labels[self.curLabel].setClass(cls)
        self.curLabel = self.curLabel + 1 \
                        if self.curLabel < len(self.labels) - 1 else 0
        self.edited = True
    def getImage(self):
        #self.image = self.loadImage()
        self.dispImage = self.image.copy()
        # bounding rectangle & label
        for i in range(len(self.labels)):
            self.labels[i].drawOnImage(self.dispImage, (0, 0, 255), i)
        # filename
        #cv2.putText(self.dispImage, self.curFile(), (5, self.dispImage.shape[0] - 12),
        #            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150,255,0),
        #            thickness=1, lineType=cvw.LINE_AA)
        return self.dispImage, self.curFile()
    def nextImage(self):
        self.saveLabels()
        self.cur += 1
        if len(self.images) <= self.cur:
            self.cur = 0
        self.loadImage()
    def prevImage(self):
        self.saveLabels()
        self.cur -= 1
        if self.cur < 0:
            self.cur = len(self.images) - 1
        self.loadImage()
    def savePreview(self):
        p = os.path.split(self.curFile())
        filename = './preview-' + p[1]
        cv2.imwrite(filename, self.dispImage)
        print 'Saved ' + filename
    def __del__(self):
        self.saveLabels()

## viewer controller
mouse_drawing = False
mouse_ix, mouse_iy = -1, -1
mouse_controller = None
def callOnMouse(event, x, y, flags, param):
    global mouse_drawing, mouse_ix, mouse_iy, mouse_model
    #print event, x, y, flags, param
    mouse_controller.onMouse(event, x, y, flags, param)
    mouse_controller.update()

class ViewController:
    def __init__(self, model):
        global mouse_controller
        self.model = model
        mouse_controller = self
        cv2.namedWindow('Preview')
        cv2.setMouseCallback('Preview', callOnMouse)
    def onMouse(self, event, x, y, flags, param):
        pass
    def onKey(self, c):
        result = True
        if c == ord(' '):
            self.model.nextImage()
        elif c == ord('b'):
            self.model.prevImage()
        elif c == ord('s'):
            self.model.savePreview()
        elif c == ord('q'):
            result = False
        elif ord('0') <= c and c <= ord('9'):
            self.model.setNextClass(c - ord('0'))
        elif c == 27: # ESC
            result = False
        elif c == 82: # UP
            self.model.prevImage()
        elif c == 84: # DOWN
            self.model.nextImage()
        elif c == 83: # RIGHT
            self.model.nextImage()
        elif c == 81: # LEFT
            self.model.prevImage()
        else:
            print c
        if result == False:
            return False
        self.update()
        return True
    def update(self):
        img, imagefilename = self.model.getImage()
        cv2.imshow('Preview', fitToRect(img))
        cv2.setWindowTitle('Preview', imagefilename)
    def loop(self):
        keepLooping = True
        while keepLooping:
            self.update()
            key = cv2.waitKey(0) & 0xff
            keepLooping = self.onKey(key)
        
if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print "usage: python %s label-file" % (sys.argv[0])
        # IMPLEMENT ME loading label name file
        exit(-1)

    print '''Yolo dataset image-label viewer
Legends:
 ' '  next image
 'b'  prev image
 's'  save preview image
 'q' or ESC  quit
'''
    model = Model(sys.argv[1])
    viewctrlr = ViewController(model)
    model.load()
    viewctrlr.loop()
    print 'exit...'
