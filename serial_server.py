import serial,time,threading, sqlalchemy
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLCDNumber, QDial, QVBoxLayout
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
''' 
serial parameter 
 <class serial.Serial>
port					   :: Device name or None.
baudrate (int) 			   :: Baud rate such as 9600 or 115200 etc.
bytesize 				   :: Number of data bits. Possible values: FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS
parity 					   :: Enable parity checking. Possible values: PARITY_NONE, PARITY_EVEN, PARITY_ODD PARITY_MARK, PARITY_SPACE
stopbits				   :: Number of stop bits. Possible values: STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO
timeout (float) 		   :: Set a read timeout value.
xonxoff (bool)			   :: Enable software flow control.
rtscts (bool)			   :: Enable hardware (RTS/CTS) flow control.
dsrdtr (bool)			   :: Enable hardware (DSR/DTR) flow control.
write_timeout (float) 	   :: Set a write timeout value.
inter_byte_timeout (float) :: Inter-character timeout, None to disable (default).
exclusive (bool)		   :: Set exclusive access mode (POSIX only). 
							  A port cannot be opened in exclusive access mode if it is already open in exclusive access mode.


'''
class Database():
	@staticmethod
	def getSession():
		engine = create_engine('mysql+mysqldb://root:root@localhost/sensor_dipo?charset=utf8', convert_unicode=True, echo=True)
		#engine = create_engine('mysql+mysqldb://root:qq123321!@192.168.31.251/sensor', convert_unicode=True, echo=True)
		db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
		return db_session

port = 'COM10'
baudrate = 115200
sr = serial.Serial(port , baudrate, timeout = 0.01)
datas = []
db_session = Database.getSession()
'''
class MainGUI(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)

		lcd1 = QLCDNumber(self)
		lcd2 = QLCDNumber(self)
		lcd3 = QLCDNumber(self)

		vbox = QVBoxLayout()
		vbox.addWidget(lcd1)
		vbox.addWidget(lcd2)
		vbox.addWidget(lcd3)
		self.setLayout(vbox)

		self.setGeometry(600,600,400,400)

class Main(MainGUI):
		signal = pyqtSignal()

'''

def serverThread():
	while(True):

		data = sr.readline().decode()
		data_s = data.split('.')
		if (data != '') :
			print(data)
			print(type(data))
			print(data_s)
			sql = '''
			INSERT INTO sensor_data(Pressure, Temp, HO) VALUES (%s,%s,%s)
			'''%(data_s[1],data_s[3],data_s[5])
			db_session.execute(sql)
			db_session.commit()
			print(data)
			print(data_s)
		if (data_s[-1] == "quit"):
			print('quit')
			break

ts = threading.Thread(target=serverThread())
ts.daemon(True)
ts.start()
'''
class MyApp(QWidget):

	def __init__(self):
		super().__init__()
		self.initUI()


	def initUI(self):
		lcd = QLCDNumber(self)
		lcd_1 = QLCDNumber(self)
		lcd_2 = QLCDNumber(self)
		dial = QDial(self)

		vbox = QVBoxLayout()
		vbox.addWidget(lcd)
		vbox.addWidget(lcd_1)
		vbox.addWidget(lcd_2)
		vbox.addWidget(dial)
		self.setLayout(vbox)

		dial.valueChanged.connect(lcd.display)


		self.setWindowTitle('Signal and Slot')
		self.setGeometry(600, 600, 400, 400)
		self.show()


if __name__ == "__main__":
	app = QApplication(sys.argv)
	mainWindow = MyApp(None)
	mainWindow.show()
	app.exec_()




class serialThread(QThread):
	threadEvent = QtCore.pyqtSignal(int)

	def __init__(self, parent=None):
		super().__init__()
		self.n = 0
		self.main = parent
		self.isRun = False

	def run(self):
		while self.isRun:
			print('Status :' + str(self.n))
			self.threadEvent.emit(self.n)
		
		self.n +=1
		self.sleep(1)

class Test(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)

		lcd1 = QLCDNumber(self)
		lcd2 = QLCDNumber(self)
		lcd3 = QLCDNumber(self)

		vbox = QVBoxLayout()
		vbox.addWidget(lcd1)
		vbox.addWidget(lcd2)
		vbox.addWidget(lcd3)
		self.setLayout(vbox)

		self.setGeometry(600,600,400,400)
		self.show()

		self.th = serialThread(self)
		self.th.threadEvent.connect(self.threadEventHandler)

		@pyqtSlot(int)
		def threadEventHandler(self, n):
			
			pass
if __name__ == "__main__":
	app = QApplication(sys.argv)
	mainWindow = Test(None)
	mainWindow.show()
	app.exec_()
	'''