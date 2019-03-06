# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Toggle Group Visibility
Description          : Plugin for change the visibility of each item in a group
Date                 : March, 2019
copyright            : (C) 2019 by Luiz Motta
email                : motta.luiz@gmail.com

 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
__author__ = 'Luiz Motta'
__date__ = '2019-03-11'
__copyright__ = '(C) 2019, Luiz Motta'
__revision__ = '$Format:%H$'


import os

from qgis.PyQt.QtCore import Qt, QObject, pyqtSlot, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from .togglegroupvisibility import DockWidgetToggleGroupVisibility
from .translate import Translate


def classFactory(iface):
  return ToggleGroupVisibilityPlugin( iface )

class ToggleGroupVisibilityPlugin(QObject):

  def __init__(self, iface):
    super().__init__()
    self.iface = iface
    self.name = u"&ToggleGroupVisibility"
    self.dock = None
    self.translate = Translate('togglegroupvisibility')

  def initGui(self):
    name = "ToggleGroupVisibility"
    about = QCoreApplication.translate('ToggleGroupVisibility', 'Change the visibility of each item in a group')
    icon = QIcon( os.path.join( os.path.dirname(__file__), 'togglegroupvisibility.svg' ) )
    self.action = QAction( icon, name, self.iface.mainWindow() )
    self.action.setObjectName( name.replace(' ', '') )
    self.action.setWhatsThis( about )
    self.action.setStatusTip( about )
    self.action.setCheckable( True )
    self.action.triggered.connect( self.run )

    self.iface.addToolBarIcon( self.action )
    self.iface.addPluginToMenu( self.name, self.action )

    self.dock = DockWidgetToggleGroupVisibility( self.iface )
    self.iface.addDockWidget( Qt.RightDockWidgetArea , self.dock )
    self.dock.visibilityChanged.connect( self.dockVisibilityChanged )

  def unload(self):
    self.iface.removeToolBarIcon( self.action )
    self.iface.removePluginMenu( self.name, self.action )

    self.dock.close()
    del self.dock
    self.dock = None

    del self.action

  @pyqtSlot()
  def run(self):
    if self.dock.isVisible():
      self.dock.hide()
    else:
      self.dock.show()

  @pyqtSlot(bool)
  def dockVisibilityChanged(self, visible):
    self.action.setChecked( visible )
