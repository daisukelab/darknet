# Cookpad1 contest result viewer
#

import os, sys, re, copy
import operator, math
import cv2, numpy as np
from collections import OrderedDict

splitter = re.compile('[, \t\n\r:]+')

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
    def __init__(self):
        pass
    def drawOnImage(self, image, color):
        cv2.rectangle(image, (self.x, self.y),
                      (self.x + self.w, self.y + self.h), color, 2)
        cv2.putText(image, self.prob, (self.x + 3, self.y + self.h - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color,
                    thickness=2, lineType=cvw.LINE_AA)
        print self.prob, self.x, self.y, self.w, self.h
    def readText(self, line):
        xs = splitter.split(line)
        self.imagename = xs[0].strip()
        self.cls = 0
        self.prob = xs[1].strip()
        self.x = int(float(xs[2]))
        self.y = int(float(xs[3]))
        self.w = int(float(xs[4])) - self.x + 1
        self.h = int(float(xs[5])) - self.y + 1

## viewer model
def loadList(listfile):
    with open(listfile) as f:
        rawlines = f.read().splitlines()
    f.close()
    labellist = OrderedDict()
    for l in rawlines:
        label = Label()
        label.readText(l)
        if labellist.has_key(label.imagename):
            labellist[label.imagename].append(label)
        else:
            labellist[label.imagename] = [label]
    return labellist

class Model:
    def __init__(self, listfile):
        self.cur = 0
        self.listfile = listfile
    def load(self):
        self.labels = loadList(self.listfile)
        self.loadImage()
    def curLabel(self):
        return self.labels.items()[self.cur][1]
    def curFile(self):
        return self.curLabel()[0].imagename
    def loadImage(self):
        image = cv2.imread(self.curFile())
        if image is None or image.shape[0] == 0:
            print 'Failed to load: ', self.curFile()
        self.image = image
        return image
    def getImage(self):
        self.loadImage()
        self.dispImage = copy.copy(self.image)
        # bounding rectangle & label
        for l in self.curLabel():
            l.drawOnImage(self.dispImage, (0, 0, 255))
        # filename
        #cv2.putText(self.dispImage, self.curFile(), (5, self.dispImage.shape[0] - 12),
        #            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150,255,0),
        #            thickness=1, lineType=cvw.LINE_AA)
        return self.dispImage, self.curFile()
    def nextImage(self):
        self.cur += 1
        if len(self.labels) <= self.cur:
            self.cur = 0
        self.loadImage()
    def prevImage(self):
        self.cur -= 1
        if self.cur < 0:
            self.cur = len(self.labels) - 1
        self.loadImage()
    def savePreview(self):
        p = os.path.split(self.curFile())
        filename = './preview-' + p[1]
        cv2.imwrite(filename, self.dispImage)
        print 'Saved ' + filename

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
        cv2.imshow('Preview', img)
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
