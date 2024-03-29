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
from time import sleep

from qgis.PyQt.QtCore import (
  QCoreApplication, Qt,
  QObject, QPointF,
  pyqtSlot, pyqtSignal
)
from qgis.PyQt.QtWidgets import (
  QWidget, QDockWidget,
  QLayout, QHBoxLayout, QVBoxLayout,
  QGroupBox,
  QLabel, QLineEdit, QPushButton,
  QRadioButton, QCheckBox, QSpinBox,
  QSpacerItem, QSizePolicy
)
from qgis.PyQt.QtGui import QColor, QFont, QTextDocument

from qgis.core import (
    QgsApplication, QgsProject,
    QgsPointXY,
    QgsTextAnnotation, QgsMarkerSymbol, QgsFillSymbol,
    QgsTask
)



class DockWidgetToggleGroupVisibility(QDockWidget):
    keyReleased = pyqtSignal('QKeyEvent*')
    def __init__(self, iface):
        def setupUi():
            def groupLayout(parent):
                lyt = QVBoxLayout()
                msg = QCoreApplication.translate('ToggleGroupVisibility', 'Select Group')
                w = QPushButton( msg, parent )
                self.__dict__['btn_group'] = w
                w.setEnabled( False )
                lyt.addWidget( w )
                w =  QLabel('', parent )
                self.__dict__['lbl_group'] = w
                lyt.addWidget( w )
                s = QSpacerItem( 10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum )
                lyt.addItem( s )
                return lyt

            def navigationGroup(parent):
                def getSpinTime(parent, value):
                    sp = QSpinBox( parent )
                    sp.setRange(1, 50)
                    sp.setSingleStep(1)
                    sp.setSuffix(' second')
                    sp.setValue(value)
                    return sp

                lytGroup = QVBoxLayout()
                # Upper & Down
                lyt = QHBoxLayout()
                msg = QCoreApplication.translate('ToggleGroupVisibility', u'\u2191'+ ' Upper')
                w = QPushButton( msg, parent )
                self.__dict__['btn_upper'] = w
                lyt.addWidget( w )
                msg = QCoreApplication.translate('ToggleGroupVisibility', u'\u2193'+ ' Down')
                w = QPushButton( msg, parent )
                self.__dict__['btn_down'] = w
                lyt.addWidget( w )
                lytGroup.addLayout( lyt )
                # Loop & second
                lyt = QHBoxLayout()
                msg = QCoreApplication.translate('ToggleGroupVisibility', '[L]oop')
                w = QPushButton( msg, parent )
                self.__dict__['btn_loop'] = w
                lyt.addWidget( w )
                w = getSpinTime( parent, 1)
                self.__dict__['sb_time'] = w
                lyt.addWidget( w )
                lytGroup.addLayout( lyt )
                # Check box Upper  & Down
                lyt = QHBoxLayout()
                w = QLineEdit('', parent )
                w.setToolTip('Put cursor here for use shortcuts')
                _color = 224
                _rgb = f"rgb({_color}, {_color},{_color})"
                w.setStyleSheet('QLineEdit { background : _rgb; color: _rgb; }'.replace('_rgb', _rgb))
                lyt.addWidget( w )
                msg = QCoreApplication.translate('ToggleGroupVisibility', 'Upper')
                w =  QRadioButton( msg, parent )
                lyt.addWidget( w )
                msg = QCoreApplication.translate('ToggleGroupVisibility', 'Down')
                w =  QRadioButton( msg, parent )
                self.__dict__['rb_down'] = w
                w.setChecked( True )
                lyt.addWidget( w )
                lytGroup.addLayout( lyt )
                # Set current and Copy
                lyt = QHBoxLayout()
                msg = QCoreApplication.translate('ToggleGroupVisibility', '[?] Set current')
                w = QPushButton( msg, parent )
                self.__dict__['btn_current'] = w
                lyt.addWidget( w )
                msg = QCoreApplication.translate('ToggleGroupVisibility', '[C]opy')
                w = QPushButton( msg, parent )
                self.__dict__['btn_copy'] = w
                lyt.addWidget( w )
                lytGroup.addLayout( lyt )
                # Enable annotation
                w = QCheckBox('[E]nable annotation', parent )
                self.__dict__['ck_annotation'] = w
                w.setChecked( False )
                lytGroup.addWidget( w )
                #
                lyt = QHBoxLayout()
                s = QSpacerItem( 10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum )
                lyt.addItem( s )
                lytGroup.addLayout( lyt )
                #              
                w = QGroupBox('', parent )
                w.setLayout( lytGroup )
                return w

            self.setObjectName('togglegroupvisibility_dockwidget')
            wgtMain = QWidget( self )
            wgtMain.setAttribute(Qt.WA_DeleteOnClose)
            lytMain = QVBoxLayout()
            #
            lytMain.addLayout( groupLayout( wgtMain ) )
            self.gbx_navigation = navigationGroup( wgtMain )
            lytMain.addWidget( self.gbx_navigation )
            #
            s = QSpacerItem( 10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding )
            lytMain.addItem( s )
            #
            wgtMain.setLayout( lytMain )
            self.setWidget( wgtMain )

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


class AnnotationCanvas(QObject):
    def __init__(self, mapCanvas):
        super().__init__()
        self.annotationManager = QgsProject.instance().annotationManager()
        self.mapCanvas = mapCanvas
        self.annot, self.text = None, None

    def setText(self, text, changeAnnotation=False):
        if not text:
            self._remove()
            self.mapCanvas.extentsChanged.disconnect( self.extentsChanged )
            return
        self.text = text
        if not self.annot or changeAnnotation:
            if changeAnnotation:
                self._remove()
            self.annot = self._createAnnotationCurrentLayer()
            self.annotationManager.addAnnotation( self.annot )
            self.mapCanvas.extentsChanged.connect( self.extentsChanged )

    @pyqtSlot()
    def extentsChanged(self):
        self._remove()
        self.annot = self._createAnnotationCurrentLayer()
        self.annotationManager.addAnnotation( self.annot )

    def _remove(self):
        if self.annot in self.annotationManager.annotations():
            self.annotationManager.removeAnnotation( self.annot )
            self.annot = None

    def _createAnnotationCurrentLayer(self):
        def setPosition(annotation):
            e = self.mapCanvas.extent()
            p = QgsPointXY(e.xMinimum(), e.yMaximum() )
            annotation.setMapPosition( p )

        def setFrameDocument(annotation):
            font = QFont()
            font.setPointSize(20)
            td = QTextDocument( self.text )
            td.setDefaultFont( font )
            annotation.setFrameOffsetFromReferencePointMm(QPointF(0,0))
            annotation.setFrameSize( td.size() )
            annotation.setDocument( td )

        def setFillMarker(annotation):
            annotation.setFillSymbol( QgsFillSymbol.createSimple({'color': 'white', 'outline_color': 'white'}) )
            marker = QgsMarkerSymbol()
            marker.setColor(QColor('white'))
            marker.setOpacity(0)
            annotation.setMarkerSymbol(  marker )

        annot = QgsTextAnnotation()
        setPosition( annot )

        setFrameDocument( annot)
        setFillMarker( annot )
        return annot


class ToggleGroupVisibility(QObject):
    changeVisibility = pyqtSignal(list, DirectionVisibilityChange)
    nameModulus = "ToggleGroupVisibility"
    def __init__(self, iface, dockWidget):
        super().__init__()
        dockWidget.gbx_navigation.setEnabled( False )
        self.dockWidget = dockWidget
        self.mapCanvas = iface.mapCanvas()
        self.annotationCanvas = AnnotationCanvas( self.mapCanvas )
        #
        self.shortcuts = {
            Qt.Key_Down: self.top2BottomVisibilityItem,
            Qt.Key_Up: self.bottom2TopVisibilityItem,
            Qt.Key_L: self.loopVisibilityItem,
            Qt.Key_Question: self.setCurrentVisibility,
            Qt.Key_C: self.copyCurrentVisible,
            Qt.Key_E: self.enabledAnnotation
        }
        self.ltView = iface.layerTreeView()
        self.modelRoot = self.ltView.layerTreeModel()
        self.ltRoot = QgsProject.instance().layerTreeRoot()
        #
        self.hasConnect = None
        self._connect()
        #
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
            { 'signal': self.dockWidget.keyReleased, 'slot': self.keyReleased },
            { 'signal': self.ltView.selectionModel().currentChanged, 'slot': self.currentChanged },
            { 'signal': self.dockWidget.btn_group.clicked, 'slot': self.setSelectGroup },
            { 'signal': self.dockWidget.btn_upper.clicked, 'slot': self.bottom2TopVisibilityItem },
            { 'signal': self.dockWidget.btn_down.clicked, 'slot': self.top2BottomVisibilityItem },
            { 'signal': self.dockWidget.btn_loop.clicked, 'slot': self.loopVisibilityItem },
            { 'signal': self.dockWidget.btn_current.clicked, 'slot': self.setCurrentVisibility },
            { 'signal': self.dockWidget.btn_copy.clicked, 'slot': self.copyCurrentVisible },
            { 'signal': self.dockWidget.ck_annotation.stateChanged, 'slot': self.enabledAnnotation },
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

    def runTaskLoop(self, time, children, direction):
        def finished(exception, dataResult):
            pass

        def run(task, time, children, direction):
            self.refreshed = True
            while(1):
                if task.isCanceled():
                    return False
                if self.refreshed:
                    self.refreshed = False
                    self.changeVisibility.emit( children, direction )
                    sleep( time )
        
        task = QgsTask.fromFunction('ToggleGroupVisibility Task', run, time, children, direction, on_finished=finished )
        layers = [ ltl.layer() for ltl in self.group.findLayers() ]
        task.setDependentLayers( layers )
        self.taskId = self.taskManager.addTask( task )
        # Debug
        # r = run( task, time, children, direction )
        # finished( None, r)

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
    
    @pyqtSlot() # Runnig Task Loop
    def mapCanvasRefreshed(self):
        self.refreshed = True

    @pyqtSlot('QKeyEvent*')
    def keyReleased(self, e):
        key = e.key()
        if key in self.shortcuts:
            self.shortcuts[ key ]()

    @pyqtSlot('QModelIndex', 'QModelIndex')
    def currentChanged(self, current, previus):
        node = self.ltView.currentNode()
        if not node or not node.nodeType() == node.NodeGroup:
            self.dockWidget.btn_group.setEnabled( False )
            return

        totalLayers = len( node.findLayers() )
        enabled = True if totalLayers > 0 else False
        self.dockWidget.btn_group.setEnabled( enabled )
        self.dockWidget.btn_group.setToolTip( f"{node.name()} ({totalLayers} layers)")

    @pyqtSlot()
    def setSelectGroup(self):
        if self.group:
            self.group.destroyed.disconnect( self.destroyedGroup )
            self.group.visibilityChanged.disconnect( self.visibilityChangedGroup )
        
        node  = self.ltView.currentNode()
        node.setIsMutuallyExclusive( True )
        node.setItemVisibilityChecked( True)
        node.destroyed.connect( self.destroyedGroup )
        node.visibilityChanged.connect( self.visibilityChangedGroup )

        self.dockWidget.lbl_group.setText( node.name() )

        self.modelGroup = self.modelRoot.node2index( node ).model()

        self.visibleRow = 0
        nodeChild = node.children()[ self.visibleRow ]
        nodeChild.setItemVisibilityChecked( True )
        self.dockWidget.gbx_navigation.setTitle( nodeChild.name() )
        self.dockWidget.gbx_navigation.setEnabled( True )

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
            if self.dockWidget.rb_down.isChecked() \
            else DirectionVisibilityChange.BOTTOM2TOP
        data = {
            'time': self.dockWidget.sb_time.value(),
            'children': children,
            'direction': direction
        }
        self.runTaskLoop( **data )

    @pyqtSlot()
    def setCurrentVisibility(self):
        if self.group is None:
            return
        visibleNode = self.getVisibleNode()
        if visibleNode is None:
            return
        self.ltView.setCurrentIndex( self.modelRoot.node2index( visibleNode ) )

    @pyqtSlot()
    def copyCurrentVisible(self):
        if self.group is None:
            return
        visibleNode = self.getVisibleNode()
        if visibleNode is None:
            return
        if self.groupCopied is None:
            self.groupCopied = self.ltRoot.insertGroup(0, 'GroupVisibility')
            self.groupCopied.setIsMutuallyExclusive( True )
            self.groupCopied.setItemVisibilityChecked(False)
            self.groupCopied.destroyed.connect( self.destroyedGroupCopied)
        self.groupCopied.addChildNode( visibleNode.clone() )

    @pyqtSlot()
    @pyqtSlot(int)
    def enabledAnnotation(self, state=None):
        if self.group is None:
            return
        if state is None: # Shortcut
            isChecked = not self.dockWidget.ck_annotation.isChecked()
            self.dockWidget.ck_annotation.stateChanged.disconnect( self.enabledAnnotation )
            self.dockWidget.ck_annotation.setChecked( isChecked )
            self.dockWidget.ck_annotation.stateChanged.connect( self.enabledAnnotation )
        else: # Gui
            isChecked = state == Qt.Checked
        if isChecked:
            self.annotationCanvas.setText( self.dockWidget.gbx_navigation.title() )
            return
        self.annotationCanvas.setText(None)

    @pyqtSlot('QObject*')
    def destroyedGroup(self, obj):
        if self.group is None:
            return
        self.group = None
        self.dockWidget.lbl_group.setText('')
        self.dockWidget.gbx_navigation.setTitle('')
        self.cancelTask()

    @pyqtSlot('QgsLayerTreeNode*')
    def visibilityChangedGroup(self, node):
        if node.itemVisibilityChecked():
            name = node.name()
            self.dockWidget.gbx_navigation.setTitle( name )
            if self.dockWidget.ck_annotation.isChecked():
                self.annotationCanvas.setText( name, True )
            self.visibleRow = self.modelGroup.node2index( node ).row()

    @pyqtSlot('QObject*')
    def destroyedGroupCopied(self, obj):
        if self.groupCopied is None:
            return
        self.groupCopied = None
