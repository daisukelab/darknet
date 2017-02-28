# Result no trimmer
# Feb-23, 2017. Free software. @daisukelab
#

from collections import OrderedDict
import sys, re, os, cv2, numpy as np

splitter = re.compile('[, \t\n\r:]+')

####
def isDigit(x):
    try:
        tmp = float(x)
        return True
    except ValueError:
        return False

def doesMasterLineNotMatch(elems):
    if len(elems) != 6 or not isDigit(elems[1]):
        print ' this is not digit: ' + elems[1]
        return True
    return False


####
def calcOverlapRatio(xa1, ya1, xa2, ya2, xb1, yb1, xb2, yb2):
    c = max(0.0, min(xa2, xb2) - max(xa1, xb1)) * max(0.0, min(ya2, yb2) - max(ya1, yb1))
    a = abs(xa2 - xa1) * float(abs(ya2 - ya1))
    b = abs(xb2 - xb1) * float(abs(yb2 - yb1))
    SIZEMAX = 1920 * 1920 # just set enough size
    a = np.clip(a, 1.0, SIZEMAX)
    b = np.clip(b, 1.0, SIZEMAX)
    return max((c / a),  (c / b))

class Entry:
    def __init__(self, elems, loadingDefault=False):
        self.pathbody = elems[0] + ('' if loadingDefault else '.jpg')
        self.prob = float(elems[1])
        self.x1 = float(elems[2])
        self.y1 = float(elems[3])
        self.x2 = float(elems[4])
        self.y2 = float(elems[5])
    def __str__(self):
        return '%s,%f,%d,%d,%d,%d' % (self.pathbody, self.prob,
                                      int(self.x1 + 0.5), int(self.y1 + 0.5),
                                      int(self.x2 + 0.5), int(self.y2 + 0.5))
    def isNotOverlappedBy(self, entries):
        threshOverlap = 0.5
        threshUncertain = 0.5
        if not entries:
            return True
        for another in entries:
            r = calcOverlapRatio(self.x1, self.y1, self.x2, self.y2,
                                 another.x1, another.y1, another.x2, another.y2)
            if threshOverlap < r and \
               self.prob < threshUncertain and \
               self.prob < another.prob:
                # only if it overlaps, and uncertain enough, and there's other more certain one(s).
                return False
        return True
####
def loadDefault(deffile):
    with open(deffile) as f:
        lines = f.read().splitlines()
    f.close()
    defaults = OrderedDict()
    for line in lines:
        elems = splitter.split(line)
        defaults[elems[0]] = [Entry(elems, True)]
    return defaults

def insertMissingDefaults(deffiles, results):
    for deffile in deffiles:
        defs = loadDefault(deffile)
        for key in defs:
            if key in results:
                continue
            results[key] = defs[key]

####
def sortEntries(entries):
    tuped = [(entry.prob, entry) for entry in entries]
    tuped.sort(key=lambda tup: tup[0], reverse=True)
    return [tup[1] for tup in tuped]

def writeEntries(f, entries):
    # trim overlapped
    slimmed = sortEntries(entries)[:15]
    # write result
    for e in slimmed:
        f.write(str(e) + '\n')
        print str(e)

# main
if len(sys.argv) <= 2:
    exit('usage: python this-scripy.py input-result.txt default-result1.csv default-result2.csv ...')
infile = sys.argv[1]
deffiles = sys.argv[2:]

# load original list
with open(infile) as f:
    lines = f.read().splitlines()
f.close()

# covert list
fileEntries = OrderedDict()
for line in lines:
    # validate line
    elems = splitter.split(line)
    if doesMasterLineNotMatch(elems):
        print 'error: ' + line
        exit(-1)
    # put all data for a source image into a set
    e = Entry(elems)
    if fileEntries.has_key(e.pathbody):
        fileEntries[e.pathbody].append(e)
    else:
        fileEntries[e.pathbody] = [e]
    #print e.pathbody #, label

# insert default for all fileEntries found nothing
insertMissingDefaults(deffiles, fileEntries)

# write result
with open('cookpad1_result.csv', 'w') as f:
    for pathbody in fileEntries:
        writeEntries(f, fileEntries[pathbody])
f.close()

'''
---Sample input results: validate_recall_xxxx.txt, 63 lines---
test_0 0.861443 5.157532 17.462372 634.270813 466.046234
test_1 0.123307 24.503761 23.212318 254.821564 187.873718
test_2 0.744720 0.000000 2.598419 234.535980 366.983978
test_3 0.931955 0.000000 1.997185 280.000000 175.992554
test_4 0.767533 1.766724 232.392365 406.763031 599.495117
test_5 0.214676 6.604706 14.886627 232.480316 304.529358
test_6 0.896154 40.060760 0.000000 939.587524 664.000000
test_7 0.996398 0.000000 125.098572 471.135376 590.660217
test_8 0.964665 109.071991 40.378479 905.476685 675.748535
test_9 0.929376 8.649750 152.553223 959.745972 734.147400
test_10 0.742484 2.252579 246.848022 481.681213 722.755371
test_11 0.915968 0.452515 50.338402 243.284012 283.303833
test_12 0.642164 8.832169 59.844452 405.579773 776.537109
test_13 0.752084 8.783371 6.641251 377.292175 288.000000
test_14 0.938709 14.092499 29.356567 1000.000000 726.489014
test_15 0.829400 7.772491 0.000000 300.000000 219.043732
test_16 0.993152 0.000000 0.000000 994.238647 806.000000
test_16 0.121502 111.019745 491.411438 879.843262 800.252136
test_17 0.684070 21.491669 4.991821 618.791138 404.686584
test_18 0.143911 192.210632 0.109024 952.431702 401.254150
test_18 0.994611 64.070618 0.000000 987.283752 750.000000
test_18 0.131874 151.372345 452.339050 844.193359 749.353210
test_19 0.877752 0.000000 58.925842 984.278198 1308.090820
test_20 0.986579 112.156281 0.000000 1000.000000 727.471191
test_20 0.171699 174.690918 314.741974 977.985474 668.830688
test_21 0.875000 0.000000 11.960693 973.981812 713.907288
test_22 0.962824 0.000000 0.000000 1000.000000 789.000000
test_23 0.882648 0.000000 6.159607 1000.000000 725.117188
test_24 0.942468 0.000000 154.766083 608.750122 862.985962
test_25 0.937145 16.089600 1.902039 800.000000 471.831940
test_25 0.131189 55.451416 212.117340 763.375061 480.000000
test_26 0.109911 2.968170 0.000000 758.391113 639.328491
test_26 0.997955 0.000000 261.184784 764.000000 753.198242
test_27 0.770847 0.000000 11.330582 567.835571 454.358826
test_28 0.120073 204.019714 0.227509 946.144592 293.973999
test_28 0.932373 187.379730 22.923798 961.161499 624.772949
test_28 0.219685 386.104980 33.953400 1000.000000 702.746582
test_29 0.854695 37.724548 0.000000 944.333923 557.559204
test_30 0.887621 4.213776 0.000000 384.000000 287.492737
test_31 0.994176 0.000000 4.606216 280.000000 278.749451
test_31 0.112049 17.945274 171.850632 263.379974 277.546326
test_32 0.722579 15.235748 185.542847 750.000000 961.541626
test_33 0.687176 4.763077 12.526718 265.893005 197.777084
test_34 0.909964 63.415192 34.621735 955.585083 709.681519
test_35 0.375364 26.780502 149.759583 480.598938 711.887512
test_36 0.138998 15.204987 10.145477 624.825928 247.724823
test_36 0.991698 0.000000 0.000000 640.000000 480.000000
test_37 0.558633 14.951057 7.191216 266.589020 204.876526
test_38 0.972708 17.941605 41.825699 305.232239 465.160645
test_38 0.120476 41.685997 252.221298 289.945740 474.551758
test_39 0.910682 24.388855 31.900574 980.638794 1201.293701
test_40 0.913658 5.244354 14.005295 640.000000 460.302063
test_41 0.974499 0.000000 15.138031 497.339783 707.291870
test_42 0.975482 80.237381 33.470001 366.182556 303.274139
test_43 0.598804 11.271469 10.309334 261.226868 198.342865
test_44 0.764129 0.000000 71.565552 463.031860 788.174988
test_45 0.442368 5.082016 0.000000 229.043259 276.192291
test_46 0.977542 6.031525 26.214844 389.244080 282.760864
test_47 0.910265 10.165955 16.491882 637.358643 621.291443
test_48 0.117285 0.000000 42.159485 126.176300 103.542938
test_48 0.939348 11.200081 23.686092 169.217468 119.254639
test_49 0.922866 0.000000 0.000000 872.108032 745.782654
--------------------------
---Sample output results: cookpad1_results.csv, 50 lines---
test_0.jpg,1,5,17,634,466
test_1.jpg,1,25,23,255,188
test_2.jpg,1,0,3,235,367
test_3.jpg,1,0,2,280,176
test_4.jpg,1,2,232,407,599
test_5.jpg,1,7,15,232,305
test_6.jpg,1,40,0,940,664
test_7.jpg,1,0,125,471,591
test_8.jpg,1,109,40,905,676
test_9.jpg,1,9,153,960,734
test_10.jpg,1,2,247,482,723
test_11.jpg,1,0,50,243,283
test_12.jpg,1,9,60,406,777
test_13.jpg,1,9,7,377,288
test_14.jpg,1,14,29,1000,726
test_15.jpg,1,8,0,300,219
test_16.jpg,1,0,0,994,806
test_17.jpg,1,21,5,619,405
test_18.jpg,1,64,0,987,750
test_19.jpg,1,0,59,984,1308
test_20.jpg,1,112,0,1000,727
test_21.jpg,1,0,12,974,714
test_22.jpg,1,0,0,1000,789
test_23.jpg,1,0,6,1000,725
test_24.jpg,1,0,155,609,863
test_25.jpg,1,16,2,800,472
test_26.jpg,1,0,261,764,753
test_27.jpg,1,0,11,568,454
test_28.jpg,1,187,23,961,625
test_29.jpg,1,38,0,944,558
test_30.jpg,1,4,0,384,287
test_31.jpg,1,0,5,280,279
test_32.jpg,1,15,186,750,962
test_33.jpg,1,5,13,266,198
test_34.jpg,1,63,35,956,710
test_35.jpg,1,27,150,481,712
test_36.jpg,1,0,0,640,480
test_37.jpg,1,15,7,267,205
test_38.jpg,1,18,42,305,465
test_39.jpg,1,24,32,981,1201
test_40.jpg,1,5,14,640,460
test_41.jpg,1,0,15,497,707
test_42.jpg,1,80,33,366,303
test_43.jpg,1,11,10,261,198
test_44.jpg,1,0,72,463,788
test_45.jpg,1,5,0,229,276
test_46.jpg,1,6,26,389,283
test_47.jpg,1,10,16,637,621
test_48.jpg,1,11,24,169,119
test_49.jpg,1,0,0,872,746
--------------------------
'''
