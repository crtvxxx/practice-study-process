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
    def __init__(self, data):
        super().__init__()
        self.init()

    def init(self):
        ""






class TableForm(QWidget):
    def __init__(self, data):
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
            # pk.dump(json.dumps(msg), self.buf)
            self.buf.write('hello'.encode('utf8'))
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

        self.Alogin = QAction('Авторизоваться', self)
        self.ASave = QAction('Отправить изменения', self)
        self.toolbar = self.addToolBar('Панель инструментов')
        self.toolbar.setMovable(False)
        self.toolbar.setVisible(False)

        self.setCentralWidget(self.login_form)
        self.initWidgets()

    def initWidgets(self):
        self.login_form.enter_button.clicked.connect(self.tryLogin)
        self.toolbar.addAction(self.ASave)
    # funcs
    
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

            

if __name__ == "__main__":
    app = QApplication()

    main = MainWindow()
    main.show()

    sys.exit(app.exec())