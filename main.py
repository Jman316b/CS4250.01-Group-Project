import sys
from PyQt5 import QtWidgets
import SearchEngineAttached

#needed to run the program
app = QtWidgets.QApplication(sys.argv)
searchUi_win = QtWidgets.QMainWindow()
searchUi_ui = SearchEngineAttached.SearchEngineAttached(searchUi_win)
app.exec_()
