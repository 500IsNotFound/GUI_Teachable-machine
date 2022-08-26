from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from threading import *

from PyQt5.QtTest import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


from PyQt5 import uic

import time
import sys
import cv2
import os
import shutil



webDriver = "C:/Users/KimJuYeop/Desktop/chromedriver.exe"
progressColorList = ["#E67701", "#D84C6F", "#794AEF", "#1967D2"]
progressBackCList = ["#FFECE2", "#FFE9EC", "#F1F0FF", "#D2E3FC"]


main_class = uic.loadUiType("Main.ui")[0]
classifier_class = uic.loadUiType("classifier.ui")[0]
predprogress_class = uic.loadUiType("PredProgress.ui")[0]
webcam_class = uic.loadUiType("webcam.ui")[0]


class Main(QMainWindow, main_class):
    def __init__(self):
        super(Main, self).__init__()
        self.setupUi(self)
        self.CIndex = 0
        self.classDataDict = {}
        self.trainTrig = 0
        self.cnt = 0
        self.classPredList = []
        if not os.path.exists("temp"):
            os.mkdir("temp")
        elif os.path.exists("temp"):
            shutil.rmtree("temp")
            os.mkdir("temp")

        logoShadow = QGraphicsDropShadowEffect()
        logoShadow.setBlurRadius(5)
        logoShadow.setColor(QColor("gray"))
        logoShadow.setOffset(1,2)
        for i in range(2):
            self.AddAClass()

        self.TMLogo.setGraphicsEffect(logoShadow)
        self.classifierBtnAdd.clicked.connect(self.AddAClass)
        self.learningBtnStart.clicked.connect(self.TeachableLearning)
        self.pvBtnUpload.clicked.connect(self.PredFileUpload)
        self.pvCBox.currentIndexChanged.connect(self.ShowWcBtn)
        self.SetPreviewUi(0)
        self.timer = QTimer()

        self.show()

    def PredFileUpload(self, pvImg = ""):
        if not pvImg:
            pvImg = list(QFileDialog().getOpenFileName(self, "선택", ".", "*.jpg *.png"))[0]

            pvPixmap = QPixmap(pvImg)
            self.pvImgLabel.setPixmap(pvPixmap)
            self.pvImgLabel.setScaledContents(True)
            self.pvImgLabel.show()

        self.previewInput.send_keys(os.path.abspath(pvImg))

        for i in range(self.CIndex):
            shadowPredValue = self.expand_shadow_element(self.predShowTrig[i].find_element_by_tag_name("tm-bar-graph"))
            self.classPredList[i].SetEachValue(int(shadowPredValue.find_element_by_tag_name("#container #value-label").text[:-1]))


    def ShowWcBtn(self):

        preview = self.shadowBody.find_elements_by_tag_name(".column.vcenter-sticky")[1]

        if self.pvCBox.currentText() == "File":
            self.pvBtnUpload.show()
            self.pvImgLabel.show()
            self.pvwebcamLabel.hide()
            self.timer.stop()


        else:
            self.pvBtnUpload.hide()
            self.pvImgLabel.hide()
            self.pvwebcamLabel.show()
            self.StartWCPred()


    def StartWCPred(self):
        global cap
        if cap == 0:
            cap = cv2.VideoCapture(0)

        self.timer.timeout.connect(self.PredCapture)
        self.timer.start(1000./24)

    def PredCapture(self):
        self.state, self.cam = cap.read()
        img = QImage(self.cam, self.cam.shape[1], self.cam.shape[0], QImage.Format_BGR888)
        pix = QPixmap.fromImage(img)
        self.pvwebcamLabel.setPixmap(pix)

        cv2.imwrite(str(self.cnt) + ".jpg", self.cam)
        self.PredFileUpload(str(self.cnt) + ".jpg")
        os.remove(str(self.cnt)+".jpg")
        self.cnt+=1




    def AddAClass(self):
        self.classifierList.addWidget(Classifier(self.CIndex, self.classDataDict))
        self.CIndex+=1

    def ThreadLearningStart(self):
        t = Thread(target = self.TeachableLearning())
        t.start()


    def TeachableLearning(self):
        for i in self.classDataDict:
            try:
                self.classDataDict[i][1]
            except:
                return print("안돼용")
        # global cap
        # cap = 0

        options = Options()
        options.add_experimental_option('prefs', {"profile.default_content_setting_values.media_stream_camera": 1})
        # options.add_argument("--headless")
        self.browser = webdriver.Chrome(webDriver, options = options)
        html = self.browser.page_source

        TMurl = 'https://teachablemachine.withgoogle.com/train/image'
        self.browser.get(TMurl)

        time.sleep(2)
        root1 = self.browser.find_element_by_id("tmApp")
        self.shadowBody = self.expand_shadow_element(root1)
        shadowPreview = self.shadowBody.find_elements_by_tag_name(".column.vcenter-sticky")[1]
        preview = shadowPreview.find_element_by_tag_name(".column-stretch-container #run")
        selectMethod = self.expand_shadow_element(preview.find_element_by_tag_name("tm-file-sample-input"))
        self.previewInput = selectMethod.find_element_by_tag_name("div #file-input")


        columnScroll = self.shadowBody.find_element_by_class_name("column.scroll")
        if self.CIndex > 2:
            for i in range(self.CIndex-2):
                shadowAddBtn = self.expand_shadow_element(columnScroll.find_element_by_tag_name("tm-classifier-list")).find_element_by_tag_name("#train-holder .add-classes")
                self.browser.execute_script("arguments[0].click();",shadowAddBtn)

        for i in range(self.CIndex):
            time.sleep(2)
            ClassList = columnScroll.find_elements_by_tag_name("tm-classifier-list>*")[i]

            uploaderContents = ClassList.find_element_by_tag_name("tm-file-sample-input")
            shadowInput = self.expand_shadow_element(uploaderContents)

            inputTry = shadowInput.find_element_by_tag_name("div #file-input")
            self.browser.execute_script("arguments[0].style.display = 'block';",inputTry)
            inputTry.send_keys("\n".join(self.classDataDict[i][1]))
            shadowList = self.expand_shadow_element(ClassList)
            print(shadowList.find_element_by_tag_name("#container .samples-label").text)
            while(shadowList.find_element_by_tag_name("#container .samples-label").text != str(len(self.classDataDict[i][1])) + " Image Samples"):
                time.sleep(1)
        shadowDivTrain = self.expand_shadow_element(self.shadowBody.find_element_by_tag_name(".column.vcenter-sticky .panel"))
        shadowBtnDiv = self.expand_shadow_element(shadowDivTrain.find_element_by_tag_name(".train-section.container #train-btn"))

        time.sleep(3)
        shadowBtn = shadowBtnDiv.find_element_by_tag_name("#container tm-button")
        self.browser.execute_script("arguments[0].click();", shadowBtn)

        self.learningBtnStart.setText("Model Trained")



        self.ShowWcBtn()
        self.SetPreviewUi(1)




    def SetPreviewUi(self, trig):
        if not trig:
            self.pvAlert.show()
            self.pvCBox.hide()
            self.pvBtnUpload.hide()
            self.pvImgLabel.hide()
            self.pvwebcamLabel.hide()

            self.previewFrame.setMaximumHeight(210)
            self.previewFrame.setMinimumHeight(210)
            self.previewFrame.move(910, 360 - (self.previewFrame.height()) // 2)


        elif trig:
            self.pvAlert.hide()
            self.pvCBox.show()

            self.previewFrame.setMinimumHeight(600)
            self.previewFrame.move(910, 360 - (self.previewFrame.height()) // 2)

            shadowPred = self.shadowBody.find_elements_by_tag_name(".column.vcenter-sticky")[1]
            preview = self.expand_shadow_element(shadowPred.find_element_by_tag_name(".column-stretch-container #run"))
            predDivList = preview.find_element_by_tag_name("#run-panel .section.no-border .sub-label")
            self.predShowTrig = []
            self.classPredList = []
            self.progressLayout = QVBoxLayout()
            while not self.predShowTrig:
                time.sleep(0.5)
                self.predShowTrig = predDivList.find_elements_by_tag_name(".bar-graph-holder")

            for i in range(self.CIndex):
                EachPred = PredProgress()
                EachPred.SetEachCName(self.classDataDict[i][0].GetClassName())
                self.classPredList.append(EachPred)
                self.progressLayout.addWidget(EachPred)
                self.classPredList[i].SetEachColor(i)

            self.progressFrame.setLayout(self.progressLayout)
            self.progressFrame.setMinimumHeight(self.CIndex*60)
            self.progressFrame.setMaximumHeight(self.CIndex*60)

    def expand_shadow_element(self, element):
        shadow_root = self.browser.execute_script('return arguments[0].shadowRoot', element)
        return shadow_root

    def closeEvent(self,QCloseEvent):
        global cap
        cap.release()

        try:self.browser.close()
        except:""


class Classifier(QWidget, classifier_class):
    def __init__(self, index, dataDict):
        super(Classifier, self).__init__()
        self.setupUi(self)
        self.classifierIndex.setText("Class" + str(index + 1))
        self.uploadBtnFile.clicked.connect(self.UploadObject)
        self.uploadBtnWebcam.clicked.connect(self.UploadWebcam)
        self.objectList = []

        self.index = index
        self.dataDict = dataDict
        logoShadow = QGraphicsDropShadowEffect()
        logoShadow.setBlurRadius(5)
        logoShadow.setColor(QColor("gray"))
        logoShadow.setOffset(1,2)
        self.classifierIndex.textChanged.connect(self.ChangeNameWidth)
        self.classifierFrame.setGraphicsEffect(logoShadow)
        self.ChangeNameWidth()
        self.dataDict[self.index] = [self]


    def GetClassName(self):
        return self.classifierIndex.text()

    def ChangeNameWidth(self):
        self.classifierIndex.setFixedWidth(len(self.classifierIndex.text()) * 14 + 30)


    def UploadObject(self, cap = [], method = 0):
        if method == 1:
            self.objectList = cap
        else:
            self.objectList = list(QFileDialog().getOpenFileNames(self, "선택", ".", "*.jpg *.png"))[0]
        objectShowFrame = QFrame()
        objectShowLayout = QHBoxLayout()

        self.objectShowFrame.unsetLayoutDirection()
        self.objectShowFrame.setLayout(objectShowLayout)
        for i in self.objectList:
            imgLabel = QLabel()
            imgLabel.setMinimumHeight(58)
            imgLabel.setMaximumHeight(58)
            imgLabel.setMinimumWidth(58)
            imgLabel.setMaximumWidth(58)
            imgPixmap= QPixmap(i)
            imgLabel.setPixmap(imgPixmap)
            imgLabel.setScaledContents(True)
            objectShowLayout.addWidget(imgLabel)
        objectShowFrame.setLayout(objectShowLayout)
        self.objectShowFrame.setWidget(objectShowFrame)
        self.dataDict[self.index].append(self.GetLearningData())

    def UploadWebcam(self):
        self.wc = Webcam(self.index, self)

    def GetLearningData(self):
        return self.objectList

class Webcam(QMainWindow, webcam_class):
    def __init__(self, idx, classifier):
        super(Webcam, self).__init__()
        self.setupUi(self)
        self.index = idx
        if not os.path.exists("temp/" + str(self.index)):
            os.mkdir("temp/" + str(self.index))
        self.webcamAlert.hide()
        self.webcamLoad.show()
        self.show()
        self.webcamAlert.hide()
        self.fps = 24
        self.sens = 300
        self.classifier = classifier
        self.timer = QTimer()
        while not cap:
            QTest.qWait(100)

        if cap.isOpened():
            self.frame.hide()
            self.StartCapture()
        else:
            self.webcamAlert.show()
            self.webcamLoad.hide()

        self.cnt = 0


    def StartCapture(self):
        global cap
        if cap == 0:
            cap = cv2.VideoCapture(0)

        self.timer.timeout.connect(self.Capture)
        self.timer.start(1000./self.fps)

    def Capture(self):
        self.state, self.cam = cap.read()
        img = QImage(self.cam, self.cam.shape[1], self.cam.shape[0], QImage.Format_BGR888)
        pix = QPixmap.fromImage(img)
        self.webcamLabel.setPixmap(pix)

        if self.webcamBtnRecord.isDown():
            writePath = "temp/" + str(self.index) + "/" + str(self.cnt // 2) + ".jpg"
            if not self.cnt%2:
                cv2.imwrite(writePath, self.cam)
            self.cnt+=1
            webcamLabel = QLabel()
            webcamLabel.setScaledContents(True)
            webcamPix = QPixmap(writePath)
            webcamLabel.setPixmap(webcamPix)
            webcamLabel.setMinimumHeight(80)
            webcamLabel.setMaximumHeight(80)
            webcamLabel.setMinimumWidth(80)
            webcamLabel.setMaximumWidth(80)
            self.webcamLayout.addWidget(webcamLabel)


    def closeEvent(self, QCloseEvent):
        tempath = os.path.abspath("temp/"+str(self.index)) + "\\"
        listdir = os.listdir("temp/" + str(self.index))
        abslistdir = [tempath+x for x in listdir]
        self.classifier.UploadObject(abslistdir, 1)
        try:
            self.timer.stop()
        except:
            ""

class PredProgress(QWidget, predprogress_class):
    def __init__(self):
        super(PredProgress, self).__init__()
        self.setupUi(self)


    def SetEachValue(self, value):
        self.progressBar.setValue(value)

    def SetEachColor(self, index):
        self.progressBar.setStyleSheet("QProgressBar::chunk {background-color: "+ progressColorList[index%4] +";border-radius: 5px;}"
                                        "QProgressBar{border-radius: 5px; background-color: "+ progressBackCList[index%4] +"}")
        self.predCName.setStyleSheet("font-style:  normal; color: rgb(75, 75, 75); font-size: 20px; font-weight: 500; color: "+progressColorList[index%4])

    def SetEachCName(self, cname):
        self.predCName.setText(cname)


def LoadVideo():
    global cap
    cap = 0
    cap = cv2.VideoCapture(0)
    return

if __name__ == "__main__":
    t = Thread(target=LoadVideo)
    t.start()
    app = QApplication(sys.argv)
    myWindow = Main()
    myWindow.show()
    app.exec_()