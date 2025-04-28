# label_template_ui.py
# -*- coding: utf-8 -*-
#
# Form implementation generated from reading ui file 'label_template.ui'
#
from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(240, 240)
        Form.setMinimumSize(QtCore.QSize(240, 240))
        Form.setMaximumSize(QtCore.QSize(240, 240))

        self.labelArticul = QtWidgets.QLabel(Form)
        self.labelArticul.setGeometry(QtCore.QRect(10, 10, 220, 21))
        font = QtGui.QFont()
        font.setPointSize(76)
        self.labelArticul.setFont(font)
        self.labelArticul.setObjectName("labelArticul")

        self.labelSize = QtWidgets.QLabel(Form)
        self.labelSize.setGeometry(QtCore.QRect(10, 35, 220, 21))
        font = QtGui.QFont()
        font.setPointSize(76)
        self.labelSize.setFont(font)
        self.labelSize.setObjectName("labelSize")

        self.labelHeight = QtWidgets.QLabel(Form)
        self.labelHeight.setGeometry(QtCore.QRect(10, 60, 220, 21))
        font = QtGui.QFont()
        font.setPointSize(76)
        self.labelHeight.setFont(font)
        self.labelHeight.setObjectName("labelHeight")

        self.labelQR = QtWidgets.QLabel(Form)
        self.labelQR.setGeometry(QtCore.QRect(50, 60, 140, 140))
        self.labelQR.setText("")
        self.labelQR.setScaledContents(True)
        self.labelQR.setObjectName("labelQR")

        self.labelBarcode = QtWidgets.QLabel(Form)
        self.labelBarcode.setGeometry(QtCore.QRect(20, 205, 200, 30))
        self.labelBarcode.setText("")
        self.labelBarcode.setScaledContents(True)
        self.labelBarcode.setObjectName("labelBarcode")

        self.frameBorder = QtWidgets.QFrame(Form)
        self.frameBorder.setGeometry(QtCore.QRect(0, 0, 240, 240))
        self.frameBorder.setFrameShape(QtWidgets.QFrame.Box)
        self.frameBorder.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frameBorder.setLineWidth(1)
        self.frameBorder.setObjectName("frameBorder")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)


    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.labelArticul.setText(_translate("Form", "АРТИКУЛ"))
        self.labelSize.setText(_translate("Form", "РАЗМЕР"))
        self.labelHeight.setText(_translate("Form", "РОСТ"))
