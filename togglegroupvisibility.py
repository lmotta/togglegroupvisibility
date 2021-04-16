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

from enum import Enum

from qgis.PyQt.QtCore import (
  QCoreApplication, Qt,
  QVariant, QObject,
  pyqtSlot, pyqtSignal
)
from qgis.PyQt.QtWidgets import (
  QApplication,
  QWidget, QDockWidget,
  QLayout, QGridLayout, QGroupBox, QHBoxLayout, 
  QLabel, QSizePolicy, QPushButton,
  QRadioButton, QCheckBox, QSpinBox
)
from qgis.PyQt.QtGui import QIcon, QFont, QCursor

from qgis.core import (
    QgsApplication, QgsProject, Qgis,
    QgsLayerTreeNode,
    QgsTask
)


class DockWidgetToggleGroupVisibility(QDockWidget):
    keyReleased = pyqtSignal('QKeyEvent*')
    def __init__(self, iface):
        def setupUi():
            def getLayout(parent, widgets):
                lyt = QGridLayout( parent )
                for item in widgets:
                    funcAdd = lyt.addWidget if isinstance( item['widget'], QWidget) else lyt.addLayout
                    if 'spam' in item:
                        sRow, sCol = item['spam']['row'], item['spam']['col']
                        funcAdd( item['widget'], item['row'], item['col'], sRow, sCol, Qt.AlignLeft )
                    else:
                        funcAdd( item['widget'], item['row'], item['col'], Qt.AlignLeft )
                return lyt

            def getGroupBox(name, parent, widgets):
                lyt = getLayout( parent, widgets )
                gbx = QGroupBox(name, parent )
                gbx.setLayout( lyt )
                return gbx

            def getSpinTime(wgt, value):
                sp = QSpinBox( wgt)
                sp.setRange(1, 50)
                sp.setSingleStep(1)
                sp.setSuffix(' second')
                sp.setValue(value)
                return sp

            self.setObjectName('togglegroupvisibility_dockwidget')
            wgt = QWidget( self )
            wgt.setAttribute(Qt.WA_DeleteOnClose)
            # Group
            msg = QCoreApplication.translate('ToggleGroupVisibility', 'Select Group')
            self.btnSelectGroup = QPushButton( msg, wgt )
            self.lblGroup = QLabel('', wgt )
            # Visible Item
            msg = QCoreApplication.translate('ToggleGroupVisibility', 'Up [<]')
            self.btnUp = QPushButton( msg, wgt )
            msg = QCoreApplication.translate('ToggleGroupVisibility', 'Down [>]')
            self.btnDown = QPushButton( msg, wgt )
            msg = QCoreApplication.translate('ToggleGroupVisibility', 'Loop [L]')
            self.btnLoop = QPushButton( msg, wgt )
            lytRadioButton = QHBoxLayout()
            msg = QCoreApplication.translate('ToggleGroupVisibility', 'Up')
            rbUp = QRadioButton( msg, wgt )
            lytRadioButton.addWidget( rbUp )
            msg = QCoreApplication.translate('ToggleGroupVisibility', 'Down')
            self.rbDown = QRadioButton( msg, wgt )
            self.rbDown.setChecked(True)
            lytRadioButton.addWidget( self.rbDown )
            self.sbLoopTime = getSpinTime( wgt, 1 )
            msg = QCoreApplication.translate('ToggleGroupVisibility', 'Set current [?]')
            self.btnCurrent = QPushButton( msg, wgt )
            msg = QCoreApplication.translate('ToggleGroupVisibility', 'Copy [C]')
            self.btnCopy = QPushButton( msg, wgt )
            msg = QCoreApplication.translate('ToggleGroupVisibility', 'Enable shortcuts')
            self.ckEnableShortcuts = QCheckBox( msg, wgt )
            l_wts = [
                { 'widget': self.btnUp,             'row': 0, 'col': 0 },
                { 'widget': self.btnDown,           'row': 0, 'col': 1 },
                { 'widget': self.btnLoop,           'row': 1, 'col': 0 },
                { 'widget': self.sbLoopTime,        'row': 1, 'col': 1 },
                { 'widget': lytRadioButton,         'row': 2, 'col': 1 },
                { 'widget': self.btnCurrent,        'row': 3, 'col': 0 },
                { 'widget': self.btnCopy,           'row': 3, 'col': 1 },
                { 'widget': self.ckEnableShortcuts, 'row': 4, 'col': 0 }
            ]
            self.gbxItem = getGroupBox( '', wgt, l_wts)
            #
            l_wts = [
                { 'widget': self.btnSelectGroup, 'row': 0, 'col': 0 },
                { 'widget': self.lblGroup,       'row': 1, 'col': 0 },
                { 'widget': self.gbxItem,             'row': 2, 'col': 0 }
            ]
            lyt = getLayout( wgt, l_wts )
            lyt.setSizeConstraint( QLayout.SetMaximumSize )
            wgt.setLayout( lyt )
            self.setWidget( wgt )

        super().__init__('Toggle Group Visibility', iface.mainWindow() )
        setupUi()
        self.gvc = ToggleGroupVisibility( iface, self )

    def __del__(self):
        del self.gvc

    def keyReleaseEvent(self, event):
        self.keyReleased.emit( event )


class DirectionVisibilityChange(Enum):
    TOP2BOTTOM = 1
    BOTTOM2TOP = 2


class ToggleGroupVisibility(QObject):
    changeVisibility = pyqtSignal(list, DirectionVisibilityChange)
    nameModulus = "ToggleGroupVisibility"
    def __init__(self, iface, dockWidget):
        super().__init__()
        self.dockWidget = dockWidget
        self.mapCanvas = iface.mapCanvas()
        #
        self.shortcuts = {
            Qt.Key_Greater: self.top2BottomVisibilityItem,
            Qt.Key_Less: self.bottom2TopVisibilityItem,
            Qt.Key_L: self.loopVisibilityItem,
            Qt.Key_Question: self.setCurrentVisibility,
            Qt.Key_C: self.copyCurrentVisible
        }
        self.enableShortcuts = self.dockWidget.ckEnableShortcuts.checkState() == Qt.Checked
        self.ltv = iface.layerTreeView()
        self.hasConnect = None
        self._connect()
        #
        self.msgBar = iface.messageBar()
        self.modelRoot = self.ltv.layerTreeModel()
        self.root = QgsProject.instance().layerTreeRoot()
        self.group, self.modelGroup, self.visibleRow = None, None, None # setSelectGroup
        self.groupCopied = None # copyCurrentVisible
        # Task
        # Use connections: mapCanvasRefreshed, changeVisibility
        self.taskManager = QgsApplication.taskManager()
        self.taskId = None
        self.refreshed = None

    def __del__(self):
        self.cancelTask()
        self._connect(False)

    def _connect(self, isConnect = True):
        ss = [
            { 'signal': self.changeVisibility, 'slot': self.changeVisibilityItem },
            { 'signal': self.mapCanvas.mapCanvasRefreshed, 'slot': self.mapCanvasRefreshed },
            { 'signal': self.mapCanvas.keyReleased, 'slot': self.keyReleased },
            { 'signal': self.dockWidget.keyReleased, 'slot': self.keyReleased },
            { 'signal': self.ltv.selectionModel().currentChanged, 'slot': self.currentChanged },
            { 'signal': self.dockWidget.btnSelectGroup.clicked, 'slot': self.setSelectGroup },
            { 'signal': self.dockWidget.btnUp.clicked, 'slot': self.bottom2TopVisibilityItem },
            { 'signal': self.dockWidget.btnDown.clicked, 'slot': self.top2BottomVisibilityItem },
            { 'signal': self.dockWidget.btnLoop.clicked, 'slot': self.loopVisibilityItem },
            { 'signal': self.dockWidget.btnCurrent.clicked, 'slot': self.setCurrentVisibility },
            { 'signal': self.dockWidget.btnCopy.clicked, 'slot': self.copyCurrentVisible },
            { 'signal': self.dockWidget.ckEnableShortcuts.clicked, 'slot': self.ckenableShortcuts }
        ]
        if isConnect:
            self.hasConnect = True
            for item in ss:
                item['signal'].connect( item['slot'] )  
        else:
            self.hasConnect = False
            for item in ss:
                item['signal'].disconnect( item['slot'] )

    def getVisibleNode(self):
        visibleNode = None
        for node in self.group.children():
            if node.itemVisibilityChecked():
                visibleNode = node
                break
        return visibleNode

    def runTask(self, data):
        def finished(exception, dataResult):
            pass

        def run(task, d):
            self.refreshed = True
            while(1):
                if task.isCanceled():
                    return False
                if self.refreshed:
                    self.refreshed = False
                    self.changeVisibility.emit( d['children'], d['direction'] )
                    task.waitForFinished( d['time'] * 1000 )
        
        task = QgsTask.fromFunction('ToggleGroupVisibility Task', run, data, on_finished=finished )
        layers = [ ltl.layer() for ltl in self.group.findLayers() ]
        task.setDependentLayers( layers )
        self.taskId = self.taskManager.addTask( task )

    def cancelTask(self):
        if self.taskId is None:
            return False
        task = self.taskManager.task( self.taskId )
        if task is None:
            return False
        task.cancel()
        return True

    @pyqtSlot(list, DirectionVisibilityChange)
    def changeVisibilityItem(self, children, direction):
        if direction == DirectionVisibilityChange.TOP2BOTTOM:
            self.visibleRow += 1
            if self.visibleRow > len( children )-1:
                self.visibleRow = 0
        elif direction == DirectionVisibilityChange.BOTTOM2TOP:
            self.visibleRow -= 1
            if self.visibleRow < 0:
                self.visibleRow = len( children )-1
        else: 
            return
        node = children[ self.visibleRow ]
        node.setItemVisibilityChecked( True )

    @pyqtSlot() # runTask
    def mapCanvasRefreshed(self):
        self.refreshed = True

    @pyqtSlot('QKeyEvent*')
    def keyReleased(self, e):
        if not self.enableShortcuts:
            return
        key = e.key()
        if key in self.shortcuts:
            self.shortcuts[ key ]()

    @pyqtSlot('QModelIndex', 'QModelIndex')
    def currentChanged(self, current, previus):
        # self.modelRoot.currentIndex().row() == -1: a Group
        if not self.modelRoot.currentIndex().row() == -1:
            self.dockWidget.btnSelectGroup.setEnabled( False )
            return

        node = self.modelRoot.index2node( current )
        totalLayers = len( node.findLayers() )
        enabled = True if totalLayers > 0 else False
        self.dockWidget.btnSelectGroup.setEnabled( enabled )
        self.dockWidget.btnSelectGroup.setToolTip( f"{node.name()} ({totalLayers} layers)")

    @pyqtSlot()
    def setSelectGroup(self):
        if self.group:
            self.group.destroyed.disconnect( self.destroyedGroup )
            self.group.visibilityChanged.disconnect( self.visibilityChangedGroup )
        
        node  = self.ltv.currentNode()
        node.setIsMutuallyExclusive( True )
        node.setItemVisibilityChecked( True)
        node.destroyed.connect( self.destroyedGroup )
        node.visibilityChanged.connect( self.visibilityChangedGroup )

        self.dockWidget.lblGroup.setText( node.name() )

        self.modelGroup = self.modelRoot.node2index( node ).model()

        self.visibleRow = 0
        nodeChild = node.children()[ self.visibleRow ]
        nodeChild.setItemVisibilityChecked( True )
        self.dockWidget.gbxItem.setTitle( nodeChild.name() )

        self.group = node
        
    @pyqtSlot()
    def top2BottomVisibilityItem(self):
        if self.group is None:
            return
        children = self.group.children()
        self.changeVisibilityItem( children, DirectionVisibilityChange.TOP2BOTTOM )

    @pyqtSlot()
    def bottom2TopVisibilityItem(self):
        if self.group is None:
            return
        children = self.group.children()
        self.changeVisibilityItem( children, DirectionVisibilityChange.BOTTOM2TOP )

    @pyqtSlot()
    def loopVisibilityItem(self):
        if self.group is None:
            return
        if self.cancelTask():
            return
        children = self.group.children()
        direction = DirectionVisibilityChange.TOP2BOTTOM \
            if self.dockWidget.rbDown.isChecked() \
            else DirectionVisibilityChange.BOTTOM2TOP
        data = {
            'time': self.dockWidget.sbLoopTime.value(),
            'children': children,
            'direction': direction
        }
        self.runTask( data )

    @pyqtSlot()
    def setCurrentVisibility(self):
        if self.group is None:
            return
        visibleNode = self.getVisibleNode()
        if visibleNode is None:
            return
        self.ltv.setCurrentIndex( self.modelRoot.node2index( visibleNode ) )

    @pyqtSlot()
    def copyCurrentVisible(self):
        if self.group is None:
            return
        visibleNode = self.getVisibleNode()
        if visibleNode is None:
            return
        if self.groupCopied is None:
            self.groupCopied = self.root.insertGroup(0, 'GroupVisibility')
            self.groupCopied.setIsMutuallyExclusive( True )
            self.groupCopied.setItemVisibilityChecked(False)
            self.groupCopied.destroyed.connect( self.destroyedGroupCopied)
        self.groupCopied.addChildNode( visibleNode.clone() )

    @pyqtSlot()
    def ckenableShortcuts(self):
        self.enableShortcuts = self.dockWidget.ckEnableShortcuts.checkState() == Qt.Checked

    @pyqtSlot('QObject*')
    def destroyedGroup(self, obj):
        if self.group is None:
            return
        self.group = None
        self.dockWidget.lblGroup.setText('')
        self.dockWidget.gbxItem.setTitle('')
        self.cancelTask()

    @pyqtSlot('QgsLayerTreeNode*')
    def visibilityChangedGroup(self, node):
        if node.itemVisibilityChecked():
            self.dockWidget.gbxItem.setTitle( node.name() )
            self.visibleRow = self.modelGroup.node2index( node ).row()

    @pyqtSlot('QObject*')
    def destroyedGroupCopied(self, obj):
        if self.groupCopied is None:
            return
        self.groupCopied = None
