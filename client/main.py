import socket
import time
import sys

import pickle as pk
import json
import pandas as pd

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

class LoginForm(QWidget):
    def __init__(self):
        super().__init__()
        self.init()

    def init(self):
        self.s = socket.socket()

        self.greeting_text = QLabel('Добро пожаловать!', self)

        self.email_text = QLabel('Эл. почта', self)
        self.email_input = QLineEdit(self, maxLength=50)
        self.email_input.setMaximumWidth(200)

        self.passwd_text = QLabel('Пароль', self)
        self.passwd_input = QLineEdit(self, maxLength=50)
        self.passwd_input.setMaximumWidth(200)

        self.whoami_text = QLabel('Кто вы?', self)
        self.whoami = QComboBox(self, editable=False)
        self.whoami.addItem('Студент', 'stud')
        self.whoami.addItem('Преподаватель', 'teach')
        self.whoami.addItem('Администратор', 'admin')

        self.enter_button = QPushButton('Авторизоваться', self)

        self.error_text = QLabel('', self)
        self.error_text.setVisible(False)

        self.login_layout = QBoxLayout(QBoxLayout.TopToBottom, self)
        self.login_layout.addWidget(self.greeting_text)
        self.login_layout.addWidget(self.email_text)
        self.login_layout.addWidget(self.email_input)
        self.login_layout.addWidget(self.passwd_text)
        self.login_layout.addWidget(self.passwd_input)
        self.login_layout.addWidget(self.whoami_text)
        self.login_layout.addWidget(self.whoami)
        self.login_layout.addWidget(self.enter_button)
        self.login_layout.addWidget(self.error_text)

        self.login_layout.setAlignment(Qt.AlignCenter)



class PandasModel(QAbstractTableModel):
    def __init__(self, dataframe: pd.DataFrame, parent=None):
        super().__init__(self, parent)
        self._dataframe = dataframe
    
    def rowCount(self, parent=QModelIndex()) -> int:
        if parent == QModelIndex():
            return len(self._dataframe)
        return 0

    def columnCount(self, parent=QModelIndex()) -> int:
        if parent == QModelIndex():
            return len(self._dataframe.columns)
        return 0

    def data(self, index: QModelIndex, role=Qt.ItemDataRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self._dataframe.iloc[index.row(), index.column()])
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._dataframe.columns[section])
            if orientation == Qt.Vertical:
                return str(self._dataframe.index[section])
        return None



class ExerciseForm(QWidget):
    def __init__(self):
        super().__init__()
        self.init()

    def init(self):
        self.exercise_desc = QTextBrowser(self)
        self.exercise_layout = QGridLayout(self)
        self.exercise_layout.setAlignment(Qt.AlignCenter)
        self.exercise_layout.addWidget(self.exercise_desc)

    # def changeData(self):
        self.exercise_desc.setHtml('''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }</style></head>'''+'''<body style=" font-family:'Sans Serif'; font-size:9pt; font-weight:400; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-size:24pt;">Задание</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-size:18pt;">Текст 1</span></p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-size:14pt;">Текст 2</span></p></body></html>''')



class TableForm(QWidget):
    def __init__(self):
        super().__init__()
        self.init()

    def init(self):
        self.toolbar = QToolBar(self, movable=False, allowedAreas=Qt.TopToolBarArea)
        self.common_table = QTableView(self)


class SocketWrapper():
    connected = False
    s = socket.socket()
    buf = object()

    def __init__(self):
        self.s.settimeout(3.0)

    def tryConnect(self):
        if not self.connected:
            try:
                self.s.connect(('192.168.122.179', 28735))
                self.buf = self.s.makefile('wrb')
            except:
                print('exception while connecting')
                self.connected = False
                raise Exception()
            finally:
                self.connected = True

    def sendMessage(self, msg):
        try:
            pk.dump(json.dumps(msg), self.buf)
            # self.buf.write('hello'.encode('utf8'))
            self.buf.flush()
        except:
            print('exception while sending')
            self.connected = False
            self.buf.close()

    def recieveMessage(self):

        return 



class MainWindow(QMainWindow):
    isDataChanged = False

    def __init__(self):
        super().__init__()
        self.init()

    def init(self):
        self.setWindowTitle("Test")
        self.resize(600, 400)
        self.setWindowState(Qt.WindowMaximized)
        self.sock_wrap = SocketWrapper()
        self.login_form = LoginForm()
        self.exercise_form = ExerciseForm()
        self.list_form = TableForm()
        self.placeholder = QWidget(self)
        self.left_dock = QDockWidget("Просмотр", self, floating=False, allowedAreas=Qt.LeftDockWidgetArea, features=QDockWidget.NoDockWidgetFeatures)
        self.dock_widget = QWidget(self.left_dock)
        self.dock_layout = QVBoxLayout(self.dock_widget)
        self.dock_layout.setAlignment(Qt.AlignTop)

        self.courses_button = QPushButton('Курсы', self)
        self.groups_button = QPushButton('Группы', self)

        self.Alogin = QAction('Авторизоваться', self)
        self.ASave = QAction('Отправить изменения', self)
        self.toolbar = self.addToolBar('Панель инструментов')
        self.toolbar.setMovable(False)
        self.toolbar.setVisible(False)

        self.left_dock.setVisible(False)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.left_dock)

        self.left_dock.setWidget(self.dock_widget)
        self.dock_layout.addWidget(self.courses_button)
        self.dock_layout.addWidget(self.groups_button)

        self.setCentralWidget(self.login_form)
        self.initWidgets()

    def initWidgets(self):
        self.login_form.enter_button.clicked.connect(self.tryLogin)
        self.toolbar.addAction(self.ASave)
    
    # funcs

    def enableUI(self):
        self.left_dock.setVisible(True)
        self.toolbar.setVisible(True)
        self.setCentralWidget(self.placeholder)
    
    def tryLogin(self):
        try:
            self.sock_wrap.tryConnect()
        except:
            self.login_form.error_text.setVisible(True)
            self.login_form.error_text.setText('Ошибка соединения')
            pass
        finally:
            self.sock_wrap.sendMessage({'type': 'login',
                                   'contents': {
                                       'email': self.login_form.email_input.text(),
                                       'password': self.login_form.passwd_input.text(),
                                       'whois': self.login_form.whoami.currentData()
                                   }})
            self.enableUI()

    def closeEvent(self, event):
        self.sock_wrap.buf.close()
        self.sock_wrap.s.close()
        return super().closeEvent(event)
            

if __name__ == "__main__":
    app = QApplication()

    main = MainWindow()
    main.show()

    sys.exit(app.exec())