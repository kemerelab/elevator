# Refer to the following link for PyQt documentation:
# http://pyqt.sourceforge.net/Docs/PyQt4/classes.html
# Written for AMIS-30543 driver.

'''
At an RPM of 60 and an input of 200 steps in mode 1/1, takes motor 1 second to complete task
At an RPM of 120 and an input of 200 steps in mode 1/2, takes motor 1 second to complete task
'''
import sys
import RNELBanner_rc
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QPalette
from serial import *
#imports for multithreading
import threading

import multiprocessing

import socket
import os
import signal
import RPi.GPIO as GPIO
##### imports for picamera
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
import numpy as np
from scipy.misc import imresize
##### end


try:
    arduino = Serial('/dev/ttyACM0', 115200, timeout = 0.5)
except:
    pass

try:
    arduinoservodoor = Serial('/dev/ttyACM1', 9600)
except:
    pass

class Ui_Form(QtGui.QWidget):
    def __init__(self):
        super(Ui_Form, self).__init__()
        self.currentPosition = 0
        self.level_position = {1:0, 2:1000, 3:2000}
        self.setupUi()
	

    def setupUi(self):


        #self.threadclass = level()
        #self.threadclass.start()
      
        #self.connect(self, QtCore.SIGNAL('LEVEL'), self.threadclass) 

        self.setWindowTitle("RNEL Elevator Controller")
        rowSpacer = QtGui.QSpacerItem(1, 20)
        columnSpacer = QtGui.QSpacerItem(50, 1)

        # Highlight input that is currently selected
        self.setFocusPolicy(QtCore.Qt.ClickFocus)

        # Create UI elements
        label_banner = QtGui.QLabel()
        label_banner.setText("")
        label_banner.setPixmap(QtGui.QPixmap(":/RNELicon/RNELBanner.png"))

        font = QtGui.QFont("Helvetica", 12, 75)
        font.setBold(True)
        label_motorState = QtGui.QLabel("Stepper Motor Parameters")
        label_motorState.setFont(font)

        label_speed = QtGui.QLabel("Speed (RPM):")
        label_steps = QtGui.QLabel("Steps:")
        label_direction = QtGui.QLabel("Direction:")
        label_mode = QtGui.QLabel("Mode:")
        label_torque = QtGui.QLabel("Torque:")
		
        label_percentPixels = QtGui.QLabel("Percent Pixel Difference: ") #LOOK HERE	
        label_percentPixels.setFont(font)

        self.percentPixels = QtGui.QLCDNumber(self) #LOOK HERE 
        self.percentPixels.setFont(font)
        palette = QPalette()
       # palette.setBrush(QtGui.QPalette.Light, QtCore.Qt.black)
        brush = QtGui.QBrush(QtGui.QColor(0,0,0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Dark, brush)
        self.percentPixels.setPalette(palette)

       
        
        self.threadclass = receiving()
        self.threadclass.start()
		
        self.connect(self.threadclass, QtCore.SIGNAL('PERCENTDIF'), self.updatePercentPixelLCD)

        
        
        self.percentPixels.display(0) # just so something is there
                

        self.lineEdit_speed = QtGui.QLineEdit()
        self.lineEdit_speed.setMaximumSize(QtCore.QSize(100, 30))
        self.lineEdit_speed.setText("0")
        self.lineEdit_steps = QtGui.QLineEdit()
        self.lineEdit_steps.setMaximumSize(QtCore.QSize(100, 30))
        self.lineEdit_steps.setText("0")
        self.comboBox_direction = QtGui.QComboBox()
        self.comboBox_direction.addItems(["Up", "Down"])
        self.comboBox_mode = QtGui.QComboBox()
        self.comboBox_mode.addItems(["1/1", "1/2", "1/4", "1/8", "1/16", "1/32", "1/64", "1/128"])
        self.comboBox_torque = QtGui.QComboBox()
        self.comboBox_torque.addItems(["10%", "20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%"])
        self.comboBox_torque.setCurrentIndex(4)

        

        self.preset_checkbox = QtGui.QCheckBox("Use preset elevator levels")
        self.preset_checkbox.setCheckState(False)
        self.preset_checkbox.setTristate(False)
        label_level = QtGui.QLabel("Level:")
        self.comboBox_level = QtGui.QComboBox()
        self.comboBox_level.addItems(["1", "2", "3"])
        self.comboBox_level.setEnabled(False)

       
       



        label_assign = QtGui.QLabel("Assign position to level?")
        self.btn_assign = QtGui.QPushButton("Assign")
        self.btn_assign.setEnabled(False)

        self.btn_run = QtGui.QPushButton("Run")
        self.progress_bar = QtGui.QProgressBar()

        label_history = QtGui.QLabel("Command History")
        label_history.setFont(font)
        self.command_history = QtGui.QPlainTextEdit()
        self.command_history.setMaximumSize(QtCore.QSize(1000, 500))
        self.command_history.setReadOnly(True)
        self.command_history.appendPlainText("Note: The speed will be scaled according to the microstepping mode.")
        self.command_history.appendPlainText("Note: The speed and steps inputs must be positive integers. Numbers that are not integers will be rounded down.")
        self.command_history.appendPlainText("")

        font = QtGui.QFont("Helvetica", 12)
        label_instructions = QtGui.QLabel("Please visit the following site for instructions:")
        label_instructions.setFont(font)

        label_website = QtGui.QLabel()
        label_website.setFont(font)
        label_website.setText("<a href=\"https://github.com/kemerelab/Elevator/\">Elevator Maze</a>")
        label_website.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse)
        label_website.setOpenExternalLinks(True)

        # Format UI elements
        formLayout = QtGui.QFormLayout()
        formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        formLayout.setLabelAlignment(QtCore.Qt.AlignLeft)
        formLayout.addRow(label_speed, self.lineEdit_speed)
        formLayout.addRow(label_steps, self.lineEdit_steps)
        formLayout.addRow(label_direction, self.comboBox_direction)
        formLayout.addRow(label_mode, self.comboBox_mode)
        formLayout.addRow(label_torque, self.comboBox_torque)
		
       

        formLayout2 = QtGui.QFormLayout()
        formLayout2.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        formLayout2.setLabelAlignment(QtCore.Qt.AlignLeft)
        formLayout2.addRow(label_level, self.comboBox_level)

        formLayout2.addRow(label_percentPixels, self.percentPixels) #LOOK HERE

        verticalLayout = QtGui.QVBoxLayout()
        verticalLayout.addWidget(self.preset_checkbox)
        verticalLayout.addLayout(formLayout2)
        verticalLayout.addStretch()
        verticalLayout.addWidget(label_assign)
        verticalLayout.addWidget(self.btn_assign, 0, QtCore.Qt.AlignHCenter)

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.addLayout(formLayout)
        horizontalLayout.addSpacerItem(columnSpacer)
        horizontalLayout.addLayout(verticalLayout)

        verticalLayout2 = QtGui.QVBoxLayout(self)
        verticalLayout2.setContentsMargins(30, 20, 30, 20)
        verticalLayout2.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        verticalLayout2.addWidget(label_banner, 0, QtCore.Qt.AlignHCenter)
        verticalLayout2.addSpacerItem(rowSpacer)
        verticalLayout2.addWidget(label_motorState)
        verticalLayout2.addLayout(horizontalLayout)
        verticalLayout2.addWidget(self.btn_run, 0, QtCore.Qt.AlignHCenter)
        verticalLayout2.addWidget(self.progress_bar)
        verticalLayout2.addSpacerItem(rowSpacer)
        formLayout3 = QtGui.QFormLayout()
        verticalLayout2.addLayout(formLayout3)


        formLayout3.addRow(label_percentPixels, self.percentPixels) #LOOK HERE
     
        verticalLayout2.addWidget(label_history)
        verticalLayout2.addWidget(self.command_history)
        verticalLayout2.addSpacerItem(rowSpacer)
        verticalLayout2.addWidget(label_instructions)
        verticalLayout2.addWidget(label_website)



        self.btn_run.clicked.connect(self.collectMotorData)
        self.preset_checkbox.stateChanged.connect(self.updateUI)
        self.comboBox_level.currentIndexChanged.connect(self.updateUI)
        self.btn_assign.clicked.connect(self.assignPosition)
        self.btn_assign.clicked.connect(self.updateUI)


    def updatePercentPixelLCD(self, val):
        self.percentPixels.display(val)



    def collectMotorData(self):
        minHeight, maxHeight = 0, 200000
        speed, speed_valid = QtCore.QString.toFloat(self.lineEdit_speed.text())
        torque = str(self.comboBox_torque.currentText()[0])

        # If preset levels are used, calculate steps and direction
        if self.preset_checkbox.checkState() == 0:
            steps, steps_valid = QtCore.QString.toFloat(self.lineEdit_steps.text())
            direction = str(self.comboBox_direction.currentText())
        if self.preset_checkbox.checkState() == 2:
            steps_valid = True
            steps, direction = self.level_calculations()

        if speed_valid == False or steps_valid == False:
            self.errorMessage(0)
        if speed == 0 and speed_valid == True:
            self.errorMessage(1)
        if speed > 150 or speed < 0:
            self.errorMessage(2)
            #self.level_position(2)
            speed = 0
            steps = 0
        speed = int(speed)
        if(speed != 0):
            if steps == 0 and steps_valid == True:
                if self.preset_checkbox.checkState() == 0:
                    self.errorMessage(3)
                if self.preset_checkbox.checkState() == 2:
                    self.errorMessage(6)
            if steps < 0:
                self.errorMessage(8)
                steps = 0
        steps = int(steps)

        # Do not step past the top and bottom of the maze
        if direction == "Up" and speed != 0:
            if steps > maxHeight - self.currentPosition:
                self.errorMessage(4)
                steps = maxHeight - self.currentPosition
            self.currentPosition += int(steps)
        if direction == "Down" and speed != 0:
            if steps > self.currentPosition - minHeight:
                self.errorMessage(5)
                steps = self.currentPosition - minHeight
            self.currentPosition -= int(steps)

        mode = int(self.comboBox_mode.currentText()[2:])
        
        speed = int(speed) * mode
        try:
            required_time = (steps * mode)/(speed * float(200./60))
        except:
            required_time = 0.0

        # Using a microstepping mode of 1/2, for example, halves the number of steps
        # Multiply the number of steps by the reciprocal of the mode
        # This will not affect position tracking as it occurs after position tracking
        self.steps = int(steps) * mode
        #print (mode)
        self.sendMotorData(str(speed), str(self.steps), str(mode), torque, direction, required_time)
        
    def sendMotorData(self, speed, steps, mode, torque, direction, required_time):
        self.btn_run.setEnabled(False)

        while len(speed) < 4:
            speed = "0" + speed

        while len(steps) < 8:
            steps = "0" + steps
        while len(mode) < 3:
            mode = "0" + mode

        data = 'x'+speed+'x'+steps+'x'+mode+'x'+torque+'x'+direction
        self.command_history.appendPlainText(data)
        self.command_history.appendPlainText("Estimated time required (seconds): " + str(required_time))
        
        try:
            arduinoservodoor.write(90)
        except:
            pass

        try:
            arduino.write(data)

            # In a separate thread, block new inputs until Arduino is ready
            if self.steps != 0:
                self.progress_bar.setRange(0, self.steps)
                self.motor_progress = update_thread(self.steps)
                self.motor_progress.start()
                self.motor_progress.bar_value.connect(self.update_progress)
            else:
                self.update_progress(0)
        except:
            self.command_history.appendPlainText("The Arduino is not connected.")
            self.btn_run.setEnabled(True)
		#### I think hall effect sensor reading should go here
        self.command_history.appendPlainText("Current position: " + str(self.currentPosition))
        self.command_history.appendPlainText("")
		

    def level_calculations(self):
        # This method is called in collectMotorData() and updateUI()
        current_level = int(self.comboBox_level.currentText())
        #self.emit(QtCore.SIGNAL('LEVEL'), current_level)
		
        steps = abs(self.currentPosition - self.level_position[current_level])
        if self.currentPosition > self.level_position[current_level]:
            direction = "Down"
        else:
            direction = "Up"
        return steps, direction

    def assignPosition(self):
        # Reassign elevator levels if necessary
        current_level = int(self.comboBox_level.currentText())
        difference = self.currentPosition - self.level_position[current_level]
        if difference != 0:        
            for level in self.level_position.keys():
                self.level_position[level] += difference
            self.command_history.appendPlainText("New level positions:")
        else:
            self.errorMessage(7)
            self.command_history.appendPlainText("Current level positions:")

        self.command_history.appendPlainText("Level 1: " + str(self.level_position[1]))
        self.command_history.appendPlainText("Level 2: " + str(self.level_position[2]))
        self.command_history.appendPlainText("Level 3: " + str(self.level_position[3]))
        self.command_history.appendPlainText("")

    def updateUI(self):
        steps, direction = self.level_calculations()
        # If preset levels are used, disable corresponding manual inputs
        if self.preset_checkbox.checkState() == 0:
            self.lineEdit_steps.setEnabled(True)
            self.lineEdit_steps.setText("0")
            self.comboBox_direction.setEnabled(True)
            self.comboBox_level.setEnabled(False)
            self.btn_assign.setEnabled(False)
        if self.preset_checkbox.checkState() == 2:
            self.lineEdit_steps.setEnabled(False)
            self.lineEdit_steps.setText(str(steps))
            self.comboBox_direction.setEnabled(False)
            if direction == "Up":
                self.comboBox_direction.setCurrentIndex(0)
            else:
                self.comboBox_direction.setCurrentIndex(1)
            self.comboBox_level.setEnabled(True)
            self.btn_assign.setEnabled(True)

    def errorMessage(self, num):
        invalid_box = QtGui.QMessageBox()
        invalid_box.setIcon(QtGui.QMessageBox.Warning)

        if num == 0:
            invalid_box.setText("<br>Invalid input(s).")
            invalid_box.setInformativeText("<big>Inputs must be numbers.")
        if num == 1:
            invalid_box.setText("<br>The speed has not been set.")
            invalid_box.setInformativeText("<big>Please set a speed to start the motor.")
        if num == 2:
            invalid_box.setText("<br>The speed cannot be set.")
            invalid_box.setInformativeText("<big>The speed must be greater than 0 but less than the maximum RPM of 150. The steps have been set to 0. Please try again at a lower speed.")           
        if num == 3:
            invalid_box.setText("<br>The distance has not been set.")
            invalid_box.setInformativeText("<big>Please set a distance to start the motor.") 
        if num == 4:
            invalid_box.setText("<br>Distance exceeds maze height.")
            invalid_box.setInformativeText("<big>The elevator will stop at the top of the maze.")
        if num == 5:
            invalid_box.setText("<br>Distance exceeds bottom of maze.")
            invalid_box.setInformativeText("<big>The elevator will stop at the bottom of the maze.")
        if num == 6:
            invalid_box.setText("<br>The distance cannot be set.")
            invalid_box.setInformativeText("<big>The elevator is already on this level.")  
        if num == 7:
            invalid_box.setText("<br>The levels cannot be assigned.")
            invalid_box.setInformativeText("<big>This level is already assigned to the current position.")
        if num == 8:
            invalid_box.setText("<br>The distance cannot be set.")
            invalid_box.setInformativeText("<big>The number of steps must be greater than 0.")             

        invalid_box.exec_()

    def update_progress(self, num):
        self.progress_bar.setValue(num)
        self.btn_run.setText(str(num) + "/" + str(self.steps))

        # Allow new input when motor is done stepping
        if num == self.steps:
            self.btn_run.setText("Run")
            self.btn_run.setEnabled(True)
            self.progress_bar.reset()
            if self.preset_checkbox.checkState() == 2:
                self.updateUI()


class update_thread(QtCore.QThread):
    bar_value = QtCore.pyqtSignal(int)

    def __init__(self, steps):
        super(update_thread, self).__init__()
        self.steps = steps

    def run(self):
        # Track steps completed by reading serial port       
        all_entries = []
        step_entry = []
        lencount = len(all_entries)
        count = 0
        while len(all_entries) < self.steps:
            if lencount == len(all_entries):
                count += 1
                if count > 5:
                    self.bar_value.emit(self.steps)
                    break
            lencount = len(all_entries)
            for byte in arduino.read():                
                count = 0                
                #print (byte)
                step_entry.append(byte)
                #print (step_entry)
                
                #length of previous all_entries
                #compare to current length
                #if value is same increment counter
                #update lencount               
                if byte == '\n':
                    all_entries.append(step_entry)
                    #print(all_entries)
                    self.bar_value.emit(len(all_entries))
                    step_entry = []
            #print (len(all_entries),"moo", count)
            

class level(QtCore.QThread): #shows what level we are on and will run the reward wells
	
	def run (self):
		
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM)
		checker1 = 1
		checker2 = 0
		trigger1 = 26
		pump1 = 13
		trigger2 = 21
		pump2 = 16

		GPIO.setup(pump1, GPIO.OUT)
		GPIO.setup(trigger1, GPIO.IN)
		GPIO.setup(pump2, GPIO.OUT)
		GPIO.setup(trigger2, GPIO.IN)

		#for outputs, 0 enables pump and 1 turns it off 

		while True:
			if GPIO.input(trigger1) == True and checker1 == 1: 
				GPIO.output(pump1, 0)
				print "triggering reward! :)"
				time.sleep(5)
				GPIO.output(pump1,1)
				checker1 = 0
				checker2 = 1
			else:
				GPIO.output(pump2,1)
			if GPIO.input(trigger2) == True and checker2 == 1: 
				GPIO.output(pump2, 0)
				print "triggering reward again! :)"
				time.sleep(5)
				GPIO.output(pump2,1)
				checker2 = 0
				checker1 = 1
			else:
				GPIO.output(pump1,1)



class receiving(QtCore.QThread):
	def run(self):
		UDP_IPr = "127.0.0.1"
		UDP_PORTr = 5005
		
		sockr = socket.socket(socket.AF_INET, # Internet
		                     socket.SOCK_DGRAM) # UDP
		sockr.bind((UDP_IPr, UDP_PORTr))
		while True:
			data, addr = sockr.recvfrom(1024) # buffer size is 1024 bytes
			data = float (data)
			self.emit(QtCore.SIGNAL('PERCENTDIF'), data)



def callPiCamDisplay():
	os.system('python PiCamDisplay.py')

def callRewardWell1():
	os.system('python RewardWellLevel1.py')

def callRewardWell2():
	os.system('python RewardWellLevel2.py')

def callRewardWell3():
	os.system('python RewardWellLevel3.py')

#def callRewardWell():
	#os.system('python RewardWell.py')

if __name__ == '__main__':

	p = multiprocessing.Process(target = callPiCamDisplay)
	p.start()
	#time.sleep(5)
	#os.kill(p.pid, signal.SIGKILL)
	q = multiprocessing.Process(target = callRewardWell1)
	q.start()

	w = multiprocessing.Process(target = callRewardWell2)
	w.start()

	e = multiprocessing.Process(target = callRewardWell3)
	e.start()

	app = QtGui.QApplication(sys.argv)
	ex = Ui_Form()
	ex.show()

	ex.raise_()

	sys.exit(app.exec_())

	

