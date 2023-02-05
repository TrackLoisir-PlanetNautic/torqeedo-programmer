# importing libraries
from PyQt5.QtWidgets import *
from PyQt5 import QtGui
import sys
import requests
import json

#base_url = "https://app.trackloisirs.com/api"
base_url = "http://localhost:8080/api"

# creating a class
# that inherits the QDialog class
class Window(QDialog):

	# constructor
	def __init__(self):
		super(Window, self).__init__()

		# setting window title
		self.setWindowTitle("TorqeedoProgrammer")

		# setting geometry to the window
		self.setGeometry(100, 100, 500, 300)

		# calling the method that create the form
		self.createConnexionForm()
	

	def createConnexionForm(self):

		# creating a group box
		self.connexionGroupBox = QGroupBox("Connexion")

		# creating a line edit for email connexion
		self.emailLineEdit = QLineEdit()
		self.emailLineEdit.setText("thomas.trackloisir@gmail.com") 
		#self.emailLineEdit.setFixedSize(350,40)

		# creating a line edit for password connexion
		self.passwordLineEdit = QLineEdit()
		self.passwordLineEdit.setEchoMode(QLineEdit.Password)
		#self.passwordLineEdit.setFixedSize(350,40)

		# creating a form layout
		self.loginLayout = QFormLayout()

		# adding rows
		# for email and adding input text
		self.loginLayout.addRow(QLabel("Email"), self.emailLineEdit)

		# for password and adding input text
		self.loginLayout.addRow(QLabel("Password"), self.passwordLineEdit)

		# setting layout
		self.connexionGroupBox.setLayout(self.loginLayout)

		# creating a dialog button for ok and cancel
		self.connexionButtonBox = QDialogButtonBox(QDialogButtonBox.Ok)

		# adding action when form is accepted
		self.connexionButtonBox.accepted.connect(self.connectToWebsite)

		# adding action when form is rejected
		self.connexionButtonBox.rejected.connect(self.reject)

		# creating a vertical layout
		self.mainLayout = QVBoxLayout()

		# adding form group box to the layout
		self.mainLayout.addWidget(self.connexionGroupBox)

		# adding button box to the layout
		self.mainLayout.addWidget(self.connexionButtonBox)

		# setting lay out
		self.setLayout(self.mainLayout)

	def connectToWebsite(self):
		
		
		#method to connect to the website
		url = base_url + '/frontend/account/login'
		params = {'email': self.emailLineEdit.text(), 'password': self.passwordLineEdit.text(), 'remember': 'true'}

		res = requests.post(url, json = params)
		if(res.status_code != 200):
			if(hasattr(self, 'connexionError')):
				self.connexionError.setText("Connexion au site internet impossible")
			else:
				self.connexionError = QLabel("Connexion au site internet impossible")
				self.loginLayout.addRow(self.connexionError)
			return
		res = res.json()

		if(res['status'] == 200):
			self.user = res['user']
			self.accessToken = res['accessToken']
			self.createSelectTorqeedoIdForm() #go to the next form if success
		else:
			if(hasattr(self, 'connexionError')):
				self.connexionError.setText(res['message'])
			else:
				self.connexionError = QLabel(res['message'])
				self.loginLayout.addRow(self.connexionError)

	# form to select the torqeedo id
	def createSelectTorqeedoIdForm(self):
		self.torqeedoIdList = []
		# creating a group box
		self.selectTorqeedoIdGroupBox = QGroupBox("Select Torqeedo ID")

		# creating combo box to select degree
		self.torqeedoIdComboBox = QComboBox()

		# adding items to the combo box
		self.torqeedoIdComboBox.addItems(self.torqeedoIdList)

		# creating a form layout
		self.selectTorqeedoIdLayout = QFormLayout()

		# adding rows
		# for name and adding input text

		refreshBtn = QPushButton()
		refreshBtn.setText("Refresh")
		refreshBtn.move(64,32)
		refreshBtn.clicked.connect(self.getTorqeedoList)

		self.selectTorqeedoIdLayout.addRow(refreshBtn)

		self.selectTorqeedoIdLayout.addRow(QLabel("TorqeedoId"), self.torqeedoIdComboBox)

		# setting layout
		self.selectTorqeedoIdGroupBox.setLayout(self.selectTorqeedoIdLayout)

		# creating a dialog button for ok and cancel
		self.selectTorqeedoIdButtonBox = QDialogButtonBox(QDialogButtonBox.Ok)

		# adding action when form is accepted
		self.selectTorqeedoIdButtonBox.accepted.connect(self.selectTorqeedoId)

		# adding action when form is rejected
		self.selectTorqeedoIdButtonBox.rejected.connect(self.backToLogin)

		self.mainLayout.removeWidget(self.connexionGroupBox)
		self.connexionGroupBox.deleteLater()
		self.connexionGroupBox = None

		self.mainLayout.removeWidget(self.connexionButtonBox)
		self.connexionButtonBox.deleteLater()
		self.connexionButtonBox = None


		self.serialConnectionLayout = QVBoxLayout()


		#self.mainLayout.setLayout(self.serialConnectionLayout)

		# adding form group box to the layout
		self.mainLayout.addWidget(self.selectTorqeedoIdGroupBox)

		# adding button box to the layout
		self.mainLayout.addWidget(self.selectTorqeedoIdButtonBox)

		self.getTorqeedoList()

	def getTorqeedoList(self):
		#request to get the torqeedo id list
		url = base_url + '/backend/pythonProgrammer/getTorqeedoControllersList'
		headers={'authorization': 'Bearer ' + self.accessToken}	
		res = requests.get(url, headers = headers, timeout=5)
		res = res.json()
		print(headers)

		if(res['status'] == 200):
			self.torqeedoIdList = res['data']
		else:
			if(hasattr(self, 'getTorqeedoIdError')):
				self.getTorqeedoIdError.setText(res['message'])
			else:
				self.getTorqeedoIdError = QLabel(res['message'])
				self.selectTorqeedoIdLayout.addRow(self.getTorqeedoIdError)
		self.torqeedoIdComboBox.clear()
		print(self.torqeedoIdList)
		self.torqeedoIdComboBox.addItems([item["kingwoId"] for item in self.torqeedoIdList])

	# method to change page after torqeedo Id is selected
	def selectTorqeedoId(self):

		# printing the form information
		self.torqCtrlId = self.torqeedoIdComboBox.currentText()
		print("troqeedo Id : {0}".format(self.torqCtrlId))

		self.createActivateESP32SignatureForm()

	# method to go back to the login form
	def backToLogin(self):
		self.mainLayout.removeWidget(self.selectTorqeedoIdGroupBox)
		self.selectTorqeedoIdGroupBox.deleteLater()
		self.selectTorqeedoIdGroupBox = None

		self.mainLayout.removeWidget(self.selectTorqeedoIdButtonBox)
		self.selectTorqeedoIdButtonBox.deleteLater()
		self.selectTorqeedoIdButtonBox = None
		self.createConnexionForm(self)
		
	
	# form to show the ESP32 signature
	def createActivateESP32SignatureForm(self):

		# creating a group box
		self.activateESP32SignatureGroupBox = QGroupBox("activateESP32Signature")

		# creating a line edit for email connexion
		# creating a form layout
		self.publicKeySignLayout = QFormLayout()
		refreshBtn = QPushButton()
		refreshBtn.setText("Refresh")
		refreshBtn.move(64,32)
		refreshBtn.clicked.connect(self.getESP32Signature)

		self.publicKeySignLayout.addRow(refreshBtn)
		# adding rows
		# for name and adding input text
		self.publicKeySignLine = QLabel("Chargement...")
		self.publicKeySignLayout.addRow(QLabel("Public key sign :"), self.publicKeySignLine)

		# setting layout
		self.activateESP32SignatureGroupBox.setLayout(self.publicKeySignLayout)

		# creating a dialog button for ok and cancel
		self.activateESP32SignatureButtonBox = QDialogButtonBox(QDialogButtonBox.Ok)

		# adding action when form is accepted
		self.activateESP32SignatureButtonBox.accepted.connect(self.activateESP32Signature)

		# adding action when form is rejected
		self.activateESP32SignatureButtonBox.rejected.connect(self.backToSelectTorqeedoIdForm)

		self.mainLayout.removeWidget(self.selectTorqeedoIdGroupBox)
		self.selectTorqeedoIdGroupBox.deleteLater()
		self.selectTorqeedoIdGroupBox = None

		self.mainLayout.removeWidget(self.selectTorqeedoIdButtonBox)
		self.selectTorqeedoIdButtonBox.deleteLater()
		self.selectTorqeedoIdButtonBox = None

		# adding form group box to the layout
		self.mainLayout.addWidget(self.activateESP32SignatureGroupBox)

		# adding button box to the layout
		self.mainLayout.addWidget(self.activateESP32SignatureButtonBox)

		self.getESP32Signature()

	def getESP32Signature(self):
		url = base_url + '/backend/pythonProgrammer/getHashSigningKey'
		headers={'authorization': 'access_token ' + self.accessToken, 'torqctrlid': self.torqCtrlId}	
		res = requests.get(url, headers, timeout=5)

		res = res.json()
		if(res['status'] == 200):
			self.torqeedoHashKey_base64 = res['hashkey_b64']
		else:
			if(hasattr(self, 'getESP32SignatureError')):
				self.getESP32SignatureError.setText(res['message'])
			else:
				self.getESP32SignatureError = QLabel(res['message'])
				self.publicKeySignLayout.addRow(self.getESP32SignatureError)
		self.publicKeySignLine.setText(self.torqeedoHashKey_base64)

		# get info method called when form is accepted

	def backToSelectTorqeedoIdForm(self):
		self.mainLayout.removeWidget(self.activateESP32SignatureGroupBox)
		self.activateESP32SignatureGroupBox.deleteLater()
		self.activateESP32SignatureGroupBox = None

		self.mainLayout.removeWidget(self.activateESP32SignatureButtonBox)
		self.activateESP32SignatureButtonBox.deleteLater()
		self.activateESP32SignatureButtonBox = None
		self.createSelectTorqeedoIdForm(self)
	
	# form to activate the ESP32 signature
	def activateESP32Signature(self):

		# printing the "public key sign
		print("public key sign : {0}".format(self.publicKeySignLine.text()))

		self.publicKeySignLayout.addRow(QLabel("Waiting Activation ESP32 Signature..."))
		#Thomas: here you can call the method that activate the ESP32 signature
		#at this point torqeedId is in variable self.torqeedoIdComboBox.currentText()
		#publicKeySign is in variable self.publicKeySignLine.text()
		#TODO: call the method that activate the ESP32 signature
		#when call back is received, call the part to upload the firmware



# main method
if __name__ == '__main__':

	# create pyqt5 app
	app = QApplication(sys.argv)
	app.setStyleSheet("QWidget{font-size:20px;}")

	# create the instance of our Window
	window = Window()

	# showing the window
	window.show()

	# start the app
	sys.exit(app.exec())
