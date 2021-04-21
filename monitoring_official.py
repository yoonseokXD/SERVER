import sys, socket, threading, util, os, random, string, time, math, pickle
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import QTimer, QTime, Qt, QSize, QThread, pyqtSignal
from datetime import datetime
from mylogger import logger
from QLABEL2 import QLabel_alterada
from db.database import Database
from db.models import TDEVICE, TCODE, TSENSESET, ADCSENSORDATA, CTSENSORDATA
from functools import partial
from config import Config as Config
from monitoring_detail import MonitoringDetailUI
from multiprocessing import process, Queue, Pipe


sem = threading.Semaphore(1)
form_class = uic.loadUiType("./ui/1_monitoring.ui")[0]
form_class_new_widget = uic.loadUiType("./ui/1_monitoring_widget.ui")[0]



def clearLayout(layout):
    if layout is not None:
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                clearLayout(child.layout())


class NewTabWidget(QWidget, form_class_new_widget):
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.parent = parent


class MonitoringUI(QWidget, form_class):
    style_widget1 = "border:2px solid rgb(19, 51, 77);\nbackground-color:rgb(2,16,36);\ncolor:white;\nborder-radius: 5px;\npadding:3 3 3 3;\n\n"
    style_title1 = "border:0px solid rgb(19, 51, 77);\nbackground-color:rgb(2,43,90);\ncolor:white;\nborder-radius: 0px;\npadding:3 3 3 3;\nmargin:5 5 5 5;\n\n"
    style_title2 = "border:0px solid rgb(19, 51, 77);\nbackground-color:rgb(20, 99, 122);\ncolor:white;\nborder-radius: 0px;\npadding:3 3 3 3;\nmargin:5 5 5 5;\n\n"

    style_value = "border:0px solid rgb(19, 51, 77);\nbackground-color:rgb(2,16,36);\ncolor:white;\nborder-radius: 0px;\npadding:3 3 3 3;\nfont-size: 28px;\n"
    style_time = "border:0px solid rgb(19, 51, 77);\nbackground-color:rgb(2,16,36);\ncolor:white;\nborder-radius: 0px;\npadding:3 3 3 3;\n\n"
    style_page = "border:2px solid white;\nbackground-color:rgb(2,16,36);\ncolor:white;\nborder-radius: 0px;\n\n\n"
    style_page_active = "border:2px solid white;\nbackground-color:rgb(19, 51, 77);\ncolor:white;\nborder-radius: 0px;\n\n\n"
    config = Config()
        

    detail_ui = None

    def __del__(self):
        logger.info("monitoring.py 종료")

    def __init__(self, parent):
        super().__init__()
        self.setupUi(self)
        self.parent = parent
        
        self.db_session = Database.getSession()
        self.device_info = self.db_session.query(TDEVICE).limit(1)[0]
        logger.info("device info (DB) : {}".format(self.device_info.__dict__))

        # tab control
        self.tabWidget.clear()

        # ui updater thread

        self.updater = UpdateMonitoringUIThread()
        self.updater.update_signal.connect(self.updateDisplay)
        self.updater.start()

        # 설정 form 생성
        device_count = int(self.device_info.S_DRAIN_QUANTITY)
        ad_per_count = int(self.config.getSensorCountPerDevice())

        logger.info("device count : {}".format(device_count))
        self.current_page = 1
        #for AD_NUMBER in range(1, math.ceil(device_count / ad_per_count) + 1):  # loop1 (AD생성)
        for AD_NUMBER in range(1, device_count+ 1):  # loop1 (AD생성)
            avail_list = self.getAvailabeCountADBoardList(AD_NUMBER)
            total_page = int((len(avail_list) - 1) / 6) + 1
            logger.info("avail_list : adnum={}/total_page={}".format(AD_NUMBER, avail_list))
            logger.info("total page : adnum={}/avail_list={}".format(AD_NUMBER, total_page))

            new_tab = NewTabWidget(self)
            clearLayout(new_tab.findChild(QGridLayout, 'gridLayout'))

            #if (device_count > ad_per_count):
            if (device_count >= 2):
                # tab으로  생성
                logger.info("신규 AD탭 생성 : {}".format(AD_NUMBER))
                self.tabWidget.addTab(new_tab, "AD" + str(AD_NUMBER))
            else:
                # tab 삭제 후 메인레이아웃에 추가
                self.tabWidget.setParent(None)
                self.main_layout.addWidget(new_tab)

            start_index = (self.current_page - 1) * 6
            seq = 1
            logger.info("start_index : adnum={}/start_index={}".format(AD_NUMBER, start_index))
            for data in avail_list[start_index:start_index + 6]:
                self.addNewWidget(new_tab, AD_NUMBER, data, seq)
                seq = seq + 1
                logger.info("설정 form 생성 완료 : {}".format(data))

            self.makePage(new_tab, total_page, AD_NUMBER)

    def makePage(self, parent, total_page, ad_num):
        clearLayout(parent.findChild(QHBoxLayout, 'pageLayout'))

        for page in range(1, total_page + 1):
            new_page_label = QLabel_alterada(self.tab)
            new_page_label.setText(str(page))
            new_page_label.setMinimumSize(QSize(35, 35))
            new_page_label.setMaximumSize(QSize(40, 40))
            if (str(self.current_page) == str(page)):
                new_page_label.setStyleSheet(self.style_page_active)
            else:
                new_page_label.setStyleSheet(self.style_page)
            new_page_label.setAlignment(Qt.AlignCenter)
            new_page_label.setObjectName("page_{}_{}".format(str(ad_num), page))
            logger.info("page event :{}".format(page))

            new_page_label.mouseReleaseEvent = partial(self.move_page, parent=parent, page_num=page)

            parent.pageLayout.addWidget(new_page_label)

    def getAvailabeCountADBoardList(self, ad_num):
        db_sensor_set = self.db_session.query(TSENSESET).filter(
            TSENSESET.ID_AD_NUM == str(ad_num) and TSENSESET.ID_DEVICE == self.device_info.ID_DEVICE).limit(1)[0]

        result = []

        for i in range(1, 16 + 1):
            title = getattr(db_sensor_set, 'S_DEVICE{}_CD'.format(str(i).zfill(2)))
            yn = getattr(db_sensor_set, 'S_DEVICE{}_YN'.format(str(i).zfill(2)))
            if (yn == 'Y'):
                result.append({"sensor_id": i, "title": title})

        return result;

    def move_page(self, event, parent, page_num):
        self.current_page = page_num;

        logger.info("move page :{}".format(page_num))
        logger.info(
            "tab count= {} / current tab index={}".format(self.tabWidget.count(), self.tabWidget.currentIndex()))
        if (self.tabWidget.count() >= 2 or self.tabWidget.count() >= 0):
            clearLayout(parent.findChild(QGridLayout, 'gridLayout'))
            if (self.tabWidget.count() >= 2):
                AD_NUMBER = self.tabWidget.currentIndex() + 1
            else:
                AD_NUMBER = '1'
                
            avail_list = self.getAvailabeCountADBoardList(AD_NUMBER)
            total_page = int((len(avail_list) - 1) / 6) + 1
            logger.info("avail_list : adnum={}/total_page={}".format(AD_NUMBER, avail_list))
            logger.info("total page : adnum={}/avail_list={}".format(AD_NUMBER, total_page))

            start_index = (page_num - 1) * 6
            seq = 1
            logger.info("start_index : adnum={}/start_index={}".format(AD_NUMBER, start_index))
            for data in avail_list[start_index:start_index + 6]:
                self.addNewWidget(parent, AD_NUMBER, data, seq)
                seq = seq + 1
                logger.info("설정 form 생성 완료 : {}".format(data))

            self.makePage(parent, total_page, AD_NUMBER)

    def addNewWidget(self, parent, ad_number, sensor_data_map, seq):
        y_pos = (seq % 3)
        if (y_pos == 0):
            y_pos = 3
        y_pos = y_pos - 1
        x_pos = math.floor((seq - 1) / 3)

        logger.info("widget 생성 : seq={}, x={}, y={}".format(seq, x_pos, y_pos))
        new_widget = QWidget(self.tab)
        new_widget.setStyleSheet(self.style_widget1)
        new_widget.setObjectName("grid1_1")

        vlayout = QVBoxLayout(new_widget)

        label_title = QLabel_alterada(new_widget)
        label_title.setObjectName("title")
        label_title.setAlignment(Qt.AlignCenter)
        label_title.setText("{}(CH{})".format(sensor_data_map['title'], sensor_data_map['sensor_id']))

        if (y_pos % 2 == 0):
            label_title.setStyleSheet(self.style_title1)
        else:
            label_title.setStyleSheet(self.style_title2)

        vlayout.addWidget(label_title)

        label_value = QLabel_alterada(new_widget)
        label_value.setObjectName("value_{}_{}".format(ad_number, "CH" + str(sensor_data_map['sensor_id']).zfill(2)))
        label_value.setAlignment(Qt.AlignCenter)
        logger.info("title:|{}|".format(sensor_data_map['title'][:2]))
        if (sensor_data_map['title'][:2] == '차압'):
            label_value.setText("- mmH2O")
        if (sensor_data_map['title'][:2] == '온도'):
            label_value.setText("- °C")
        if (sensor_data_map['title'][:2] == 'pH'):
            label_value.setText("- pH")
        if (sensor_data_map['title'][:2] == '방지'):
            label_value.setText("- A")
        if (sensor_data_map['title'][:2] == '배출'):
            label_value.setText("- A")
        label_value.setStyleSheet(self.style_value)
        vlayout.addWidget(label_value)

        label_time = QLabel_alterada(new_widget)
        label_time.setObjectName("time_{}_{}".format(ad_number, "CH" + str(sensor_data_map['sensor_id']).zfill(2)))
        label_time.setAlignment(Qt.AlignCenter)
        label_time.setText("-")
        label_time.setStyleSheet(self.style_time)
        vlayout.addWidget(label_time)

        # new_widget.mouseReleaseEvent=self.showDetailPage
        # new_widget.mouseReleaseEvent = lambda event, sensor_id : self.showDetailPage(event, sensor_id)
        #new_widget.mouseReleaseEvent = partial(self.showDetailPage, ad_number=ad_number,
        #                       sensor_id_=sensor_data_map['sensor_id'])

        parent.gridLayout.addWidget(new_widget, x_pos, y_pos)

    def showDetailPage(self, event, ad_number, sensor_id_):
        logger.info("show detail page : ad_number={}/sensor_id_={}".format(ad_number, sensor_id_))

        if (self.detail_ui != None):
            self.detail_ui.deleteLater()
            self.detail_ui.destroy()

        self.detail_ui = MonitoringDetailUI(self, ad_number, sensor_id_)
        self.parent.main_stackedWidget.addWidget(self.detail_ui)
        self.parent.main_stackedWidget.setCurrentWidget(self.detail_ui)

    def updateDisplay(self, datas):
        logger.info("update graph : {}".format(datas))
        # value_{}_{} / time_{}_{}
        for data in datas:
            
            keyCh = data[1]
            valueStr = float(datas[data][0])
            
            datestr = datas[data][1]
            
            # logger.info("find obj : value_{}_{}".format(data[0], data[1]))
            objValue = self.findChild(QLabel, "value_{}_{}".format(data[0], data[1]))
            #logger.info("objValue:{}".format(objValue))

            if (objValue):
                unit = string_to_unit(objValue.text())
                #logger.info("unit:|{}|".format(unit))

                #차압, PH일 경우 계산해서 출력
                if(unit=='pH'):
                    valueStr = util.convertToPH(valueStr)
                if(unit=='mmH2O'):
                    valueStr = util.convertToPressure(valueStr)
                if(unit=='°C' and keyCh=='CH03'):
                    valueStr = util.convertToT(valueStr)

                objValue.setText(str(round(valueStr, 2)) + " " + unit)
                
            objDate = self.findChild(QLabel, "time_{}_{}".format(data[0], data[1]))
            if (objDate):
                objDate.setText(time.strftime('%Y-%m-%d %H:%M:%S')) #######################datetime형식변경해야함.


def string_to_unit(data):
    a = ''.join([n for n in data if (not n.isdigit())])
    result =  a.replace("-", '').replace('.', '').replace(" ", "")
    if( result == 'mmHO'):
        return "mmH2O"
    else:
        return result
        



class UpdateMonitoringUIThread(QThread):
    update_signal = pyqtSignal(object)

    def __init__(self):
        QThread.__init__(self)
        self.db_session = Database.getSession()

    def __del__(self):
        logger.info("monitoring 쓰레드 종료")

    def run(self):
      
        while (True):
            try :
                with open("data.pkl", 'rb') as f :
                    rawdata = pickle.load(f)
                    data_d = rawdata
                print(rawdata, type(rawdata))
                str_datas = data_d.split(':')
                print(str_datas, type(str_datas))
                result = {(str_datas[1] , 'CH01') : [str_datas[3] , str_datas[9]],
                                (str_datas[1] , 'CH02') : [str_datas[4] , str_datas[9]],
                                (str_datas[1] , 'CH03') : [str_datas[5] , str_datas[9]],
                                (str_datas[1] , 'CH04') : [str_datas[6] , str_datas[9]],
                                (str_datas[1] , 'CH05') : [str_datas[7] , str_datas[9]],
                                (str_datas[1] , 'CH06') : [str_datas[8] , str_datas[9]]
                                }
                print(result)
                self.update_signal.emit(result)
            except IndexError :
                pass
            
            time.sleep(0.5)


if __name__ == "__main__":
    q = Queue()
    monitoring_conn, serv_conn = Pipe()
    app = QApplication(sys.argv)
    mainWindow = MonitoringUI(None)
    mainWindow.show()
    app.exec_()

