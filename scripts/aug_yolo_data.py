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

import os, sys, re, copy
import operator, math
import cv2, numpy as np

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
    def __init__(self, imagename):
        self.imagename = imagename
    def drawOnImage(self, image, color):
        cv2.rectangle(image, (self.x, self.y),
                      (self.x + self.w, self.y + self.h), color, 2)
        cv2.putText(image, str(self.cls), (self.x + 3, self.y + self.h - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color,
                    thickness=2, lineType=cvw.LINE_AA)
        print self.cls, self.x, self.y, self.w, self.h
    def readText(self, line):
        xs = splitter.split(line)
        self.cls = int(xs[0].strip())
        self.x = float(xs[1].strip())
        self.y = float(xs[2].strip())
        self.w = float(xs[3].strip())
        self.h = float(xs[4].strip())
    def flip(self):
        self.y = 1.0 - self.y
        return self
    def flop(self):
        self.x = 1.0 - self.x
        return self
    def __str__(self):
        return '%d %f %f %f %f\n' % (self.cls, self.x, self.y, self.w, self.h)

def saveLavelsWithPrefix(labels, prefix):
    labelfile = labels[0].imagename.replace('images/', 'labels/'+prefix).replace('.jpg', '.txt')
    with open(labelfile, 'w') as f:
        for label in labels:
            f.write(str(label))
        f.close()
    return labelfile

def loadLabels(imagefile, shape):
    labelfile = imagefile.replace('images/', 'labels/').replace('.jpg', '.txt')
    with open(labelfile) as f:
        rawlines = f.read().splitlines()
    f.close()
    labels = []
    for l in rawlines:
        xs = splitter.split(l)
        label = Label(imagefile)
        label.readText(l)
        labels.append(label)
    return labels

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
    def load(self):
        self.images = loadImageList(self.imagelist)
        self.loadImage()
    def curFile(self):
        return self.images[self.cur]
    def loadImage(self):
        image = cv2.imread(self.curFile())
        if image is None or image.shape[0] == 0:
            print 'Failed to load: ', self.curFile()
        self.labels = loadLabels(self.curFile(), image.shape)
        self.image = image
    def augment(self, xmag, ymag, flip=False, flop=False, invert=False):
        #result = cv2.resize(self.image, (xmag, ymag))
        augimage = self.image.copy()
        auglabels = copy.deepcopy(self.labels)
        if flip:
            augimage = cv2.flip(augimage, 0)
            auglabels = [l.flip() for l in auglabels]
        if flop:
            augimage = cv2.flip(augimage, 1)
            auglabels = [l.flop() for l in auglabels]
        if invert:
            augimage = (255 - augimage)
        self.augimage = augimage
        self.auglabels = auglabels
    def nextImage(self):
        self.cur += 1
        if len(self.images) <= self.cur:
            self.cur = 0
        self.loadImage()
    def prevImage(self):
        self.cur -= 1
        if self.cur < 0:
            self.cur = len(self.images) - 1
        self.loadImage()
    def saveAugmented(self, prefix):
        imagefile = self.curFile().replace('images/', 'images/'+prefix)
        cv2.imwrite(imagefile, self.augimage)
        labelfile = saveLavelsWithPrefix(self.auglabels, prefix)
        print 'Saved ' + imagefile + ' & ' + labelfile
    def __len__(self):
        return len(self.images)

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print "usage: python %s label-file" % (sys.argv[0])
        # IMPLEMENT ME loading label name file
        exit(-1)

    model = Model(sys.argv[1])
    model.load()
    for i in range(len(model)):
        model.loadImage()
        model.augment(1.0, 1.0, flip=True, flop=False, invert=False)
        model.saveAugmented('1fxx')
        model.augment(1.0, 1.0, flip=False, flop=True, invert=False)
        model.saveAugmented('2xfx')
        model.augment(1.0, 1.0, flip=True, flop=True, invert=False)
        model.saveAugmented('3ffx')
        model.augment(1.0, 1.0, flip=False, flop=False, invert=True)
        model.saveAugmented('4xxi')
        model.augment(1.0, 1.0, flip=True, flop=False, invert=True)
        model.saveAugmented('5fxi')
        model.augment(1.0, 1.0, flip=False, flop=True, invert=True)
        model.saveAugmented('6xfi')
        model.augment(1.0, 1.0, flip=True, flop=True, invert=True)
        model.saveAugmented('7ffi')
        model.nextImage()

    print 'done...'
