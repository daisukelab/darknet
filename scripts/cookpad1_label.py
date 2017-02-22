# Data converter for a contest: https://deepanalytics.jp/compe/31?tab=compedetail
# Feb-22, 2017. Free software. @daisukelab
#
# 1. Download files from contest web site: https://deepanalytics.jp/compe/31/download
#  dtc_sample_submit.csv
#  dtc_train_master.tsv
#  dtc_train_images_1/
#  dtc_train_images_2/
#  dtc_train_images_3/
#  dtc_train_images_4/
#  dtc_test_images_1/
#  dtc_test_images_2/
#
# 2. Put all the files in a folder. Then move to the folder.
# 3. Run this script.
#  $ python $YOUR_DARKNET-CPP_FOLDER/scripts/cookpad1_label.py
#
# Folder will have followings:
#  dtc_sample_submit.csv (no change)
#  dtc_train_master.tsv  (no change)
#  images/               (created)
#    test_0.jpg          (moved)
#      :
#    train_0.jpg         (moved)
#      :
#    train_19999.jpg     (moved)
#  labels/               (created)
#    test_0.txt          (created)
#      :
#    train_0.txt         (created)
#      :
#    train_19999.txt     (created)
#
# * All food objects will have class '0', just because no class specified for them.

import sys, re, os, cv2

splitter = re.compile('[ \t\n\r:]+')
fname_splitter = re.compile('[_\.]+')

def isDigit(x):
    try:
        tmp = int(x)
        return True
    except ValueError:
        return False

def getFolder(fname):
    #num_of_files_in_folder = 5000
    #elems = fname_splitter.split(fname)
    # file # = [0, 19999]
    #file_num = int(elems[1])
    # folder # = 0 to 3 for each 5000 files
    #folder_num = file_num / num_of_files_in_folder
    return 'images' # 'dtc_' + elems[0] + '_images_' + str(folder_num)

def getImageAttr(fname):
    folder = getFolder(fname)
    fullpath = folder + '/' + fname
    image = cv2.imread(fullpath) #, cv2.IMREAD_COLOR)
    if image.data == None:
        print 'Cannot load ' + fullpath
        exit(-2)
    height, width = image.shape[:2]
    return fullpath, height, width

def doesMasterLineNotMatch(elems):
    if len(elems) != 5 or not isDigit(elems[1]):
        print ' this is not digit: ' + elems[1]
        return True
    return False

def conv(elems):
    fullpath, H, W = getImageAttr(elems[0])
    cls = 0
    x = float(elems[1])
    y = float(elems[2])
    w = float(elems[3])
    h = float(elems[4])
    return fullpath, '%d %f %f %f %f\n' % (cls, (x + x+w)/2.0/W, (y + y+h)/2.0/H, w/W, h/H)

def writeLabel(imgpath, labels):
    txtpath = imgpath.replace('images/', 'labels/').replace('.jpg', '.txt')
    with open(txtpath, 'w') as f:
        for label in labels:
            f.write(label)
        f.close()

# main
if os.path.isdir('./dtc_test_images_1'):
    os.system('mkdir ./images')
    os.system('mv -n ./dtc_test_images_1/* ./images')
    os.system('mv -n ./dtc_test_images_2/* ./images')
    os.system('mv -n ./dtc_train_images_1/* ./images')
    os.system('mv -n ./dtc_train_images_2/* ./images')
    os.system('mv -n ./dtc_train_images_3/* ./images')
    os.system('mv -n ./dtc_train_images_4/* ./images')
    os.system('rmdir ./dtc_test_images_[1-4] ./dtc_train_images_[1-4]')

if not os.path.isdir('./labels'):
    os.system('mkdir ./labels')

# load original list
with open('./dtc_train_master.tsv') as f:
    lines = f.read().splitlines()
f.close()
del lines[0] # delete first title line

# covert list
conved = {}
for line in lines:
    # validate line
    elems = splitter.split(line)
    if doesMasterLineNotMatch(elems):
        print 'error: ' + line
        exit(-1)
    # convert data
    fullpath, label = conv(elems)
    if conved.has_key(fullpath):
        conved[fullpath].append(label)
    else:
        conved[fullpath] = [label]
    print fullpath #, label

# write result
for k, v in conved.items():
    writeLabel(k, v)
