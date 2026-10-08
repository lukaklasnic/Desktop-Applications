from PyQt6.QtWidgets import ( QApplication, QMainWindow, QWidget, QVBoxLayout, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QPushButton, QSplashScreen, QFileDialog, QMessageBox )
from generator import ( generateResources, generateComponents )
from PyQt6.QtGui import ( QPixmap, QIcon )
from PyQt6.QtCore import ( Qt, QTimer )
from ui_components import *
from properties import * 
from pathlib import Path
from widgets import *
import ctypes
import sys

class MainWindow( QMainWindow ):
    def __init__( self ):
        super().__init__()
        self.output_dir = None 
        self.output_dir_label = None 
        self.initMultipleCanvas()
        self.setTitleBar()
        self.setScrollArea()
        self.setMainLayouts()
        self.all_canvas_data = {}

    def setTitleBar( self ):
        self.setWindowTitle( "FT800 Designer" )
        self.setWindowIcon( QIcon( str( Path( __file__ ).resolve().parent / "designer_logo_ic.ico" ) ) )

    def setScrollArea( self ):
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable( False )
        self.scroll_area.setHorizontalScrollBarPolicy( Qt.ScrollBarPolicy.ScrollBarAsNeeded )
        self.scroll_area.setVerticalScrollBarPolicy( Qt.ScrollBarPolicy.ScrollBarAsNeeded )
        self.scroll_area.setFrameShape( QScrollArea.Shape.NoFrame )

    def setMainLayouts( self ):
        self.main_widget = QWidget()
        self.main_widget.setMinimumSize( 1919, 1008 )
        self.main_widget.mousePressEvent = self.onMainWidgetClick
        self.main_widget.setFocusPolicy( Qt.FocusPolicy.StrongFocus )

        main_horizontal_layout = QHBoxLayout( self.main_widget )
        main_horizontal_layout.setContentsMargins( 0, 0, 0, 0 )
        main_horizontal_layout.setSpacing( 0 )

        self.properties_widget = QWidget()
        self.properties_widget.setMinimumWidth( 248 )
        
        self.central_widget = QWidget()
        
        self.widgets_icon_widget = QWidget()
        self.widgets_icon_widget.setMinimumWidth( 248 )

        self.addWidgetsToPropertiesBar( self.properties_widget )
        self.addWidgetsToCentralLayout( self.central_widget )
        self.addWidgetsToIconsPanel( self.widgets_icon_widget )

        main_horizontal_layout.addWidget( self.properties_widget, 1 )
        
        separate_line_1 = QFrame()
        separate_line_1.setFrameShape( QFrame.Shape.VLine )
        separate_line_1.setFrameShadow( QFrame.Shadow.Sunken )
        separate_line_1.setStyleSheet( "background-color: #666666;" )
        separate_line_1.setLineWidth( 2 )

        main_horizontal_layout.addWidget( separate_line_1 )
        main_horizontal_layout.addWidget( self.central_widget, 4 )
        
        separate_line_2 = QFrame()
        separate_line_2.setFrameShape( QFrame.Shape.VLine )
        separate_line_2.setFrameShadow( QFrame.Shadow.Sunken )
        separate_line_2.setStyleSheet( "background-color: #666666;" )
        separate_line_2.setLineWidth( 2 )

        main_horizontal_layout.addWidget( separate_line_2 )
        main_horizontal_layout.addWidget( self.widgets_icon_widget, 1 )
        
        self.scroll_area.setWidget( self.main_widget )
        self.setCentralWidget( self.scroll_area )
        
        self.canvas_properties_visible = False
        self.shape_properties_visible = False
        self.object_attached = False
        self.selected_shape = None
        self.current_shape = None
        
    def initMultipleCanvas( self ):
        self.canvases = []
        self.current_canvas_index = 0 
        self.canvas_widgets = {}
        
        self.createNewCanvas()
        
    def createNewCanvas( self ):
        canvas_id = len( self.canvases )
        canvas = Canvas()
        canvas.clicked.connect( self.onCanvasClicked )

        canvas.canvas_id = canvas_id 
        canvas.custom_name = f"Screen_{ canvas_id }"

        canvas.data_dict[ 'id' ] = canvas_id
        canvas.data_dict[ 'name' ] = canvas.custom_name

        self.canvases.append( canvas )
        self.canvas_widgets[ canvas_id ] = []

        return canvas_id

    def showCanvas( self, canvas_index ):
        if 0 <= canvas_index < len( self.canvases ):
            self.hideCanvasProperties()
            self.hideShapeProperties()
            self.deselectAllShapes()
            
            self.current_canvas_index = canvas_index
            
            for canvas in self.canvases:
                canvas.hide()
            
            current_canvas = self.canvases[ canvas_index ]
            current_canvas.show()
            
            if hasattr( self, 'prev_btn' ):
                self.prev_btn.setEnabled( canvas_index > 0 )
    
            if hasattr( self, 'next_btn' ):
                self.next_btn.setEnabled( canvas_index < len( self.canvases ) - 1 )
            
            if hasattr( self, 'canvas_counter_label' ):
                self.canvas_counter_label.setText( f"Canvas { canvas_index + 1 } / { len( self.canvases ) }" )
            
    def addWidgetsToPropertiesBar( self, properties_widget ):
        self.properties_layout = QVBoxLayout( properties_widget )
        self.properties_layout.setContentsMargins( 10, 10, 10, 10 )
        self.properties_layout.setAlignment( Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft )

    def addWidgetsToCentralLayout( self, central_widget ):
        central_layout = QVBoxLayout( central_widget )
        central_layout.setContentsMargins( 10, 10, 10, 10 )
        central_layout.setAlignment( Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft )

        top_layout = QHBoxLayout()
        top_layout.addStretch( 1 )

        generate_button = QPushButton( "Generate" )
        generate_button.setFixedSize( 100, 50 )
        generate_button.setStyleSheet( """
            QPushButton {
                background-color: #dea24a;
                color: black;
                font-weight: bold;
                border: 2px solid #dea24a;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: darkorange;
                border: 2px solid darkorange;
            }
            QPushButton:pressed {
                background-color: #cc5500;
                border: 2px solid #cc5500;
            }
        """ )
        generate_button.clicked.connect( self.generateAllFiles )

        top_layout.addWidget( generate_button )
        top_layout.addStretch( 1 )

        central_layout.addLayout( top_layout )
        central_layout.addStretch( 1 )

        self.canvas_nav_container = QWidget()
        canvas_nav_layout = QVBoxLayout( self.canvas_nav_container )
        canvas_nav_layout.setContentsMargins( 0, 0, 0, 0 )
        canvas_nav_layout.setSpacing( 10 )

        canvas_horizontal_layout = QHBoxLayout()
        canvas_horizontal_layout.setContentsMargins( 0, 0, 0, 0 )
        canvas_horizontal_layout.setSpacing( 10 )

        self.prev_btn = QPushButton( "←" )
        self.prev_btn.setFixedSize( 30, 30 )
        self.prev_btn.setStyleSheet( """
            QPushButton {
                background-color: #666666;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover:enabled {
                background-color: #888888;
            }
            QPushButton:disabled {
                background-color: #444444;
                color: #888888;
            }
        """ )

        self.prev_btn.clicked.connect( self.prevCanvas )
        self.prev_btn.setEnabled( False )
        canvas_horizontal_layout.addWidget( self.prev_btn )

        self.canvas_display_container = QWidget()
        self.canvas_display_container.setFixedSize( 500, 300 )
        canvas_horizontal_layout.addWidget( self.canvas_display_container )

        self.next_btn = QPushButton( "→" )
        self.next_btn.setFixedSize( 30, 30 )
        self.next_btn.setStyleSheet( """
            QPushButton {
                background-color: #666666;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover:enabled {
                background-color: #888888;
            }
            QPushButton:disabled {
                background-color: #444444;
                color: #888888;
            }
        """ )
        self.next_btn.clicked.connect( self.nextCanvas )
        self.next_btn.setEnabled( False )
        canvas_horizontal_layout.addWidget( self.next_btn )
        canvas_nav_layout.addLayout( canvas_horizontal_layout )

        canvas_buttons_layout = QHBoxLayout()
        canvas_buttons_layout.setContentsMargins( 0, 10, 0, 0 )
        canvas_buttons_layout.setSpacing( 10 )
        canvas_buttons_layout.setAlignment( Qt.AlignmentFlag.AlignCenter )

        add_canvas_btn = QPushButton( "+" )
        add_canvas_btn.setFixedSize( 30, 30 )
        add_canvas_btn.setStyleSheet( """
            QPushButton {
                background-color: #666666;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover:enabled {
                background-color: #888888;
            }
            QPushButton:disabled {
                background-color: #444444;
                color: #888888;
            }
        """ )
        add_canvas_btn.clicked.connect( self.addNewCanvas )
        add_canvas_btn.setToolTip( "Add new canvas" )
        canvas_buttons_layout.addWidget( add_canvas_btn )

        self.delete_canvas_btn = QPushButton( "-" )
        self.delete_canvas_btn.setFixedSize( 30, 30 )
        self.delete_canvas_btn.setStyleSheet( """
            QPushButton {
                background-color: #666666;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover:enabled {
                background-color: #888888;
            }
            QPushButton:disabled {
                background-color: #444444;
                color: #888888;
            }
        """ )
        self.delete_canvas_btn.clicked.connect( self.deleteCurrentCanvas )
        self.delete_canvas_btn.setToolTip( "Delete current canvas" )
        self.delete_canvas_btn.setEnabled( len( self.canvases ) > 1 )
        canvas_buttons_layout.addWidget( self.delete_canvas_btn )

        canvas_nav_layout.addLayout( canvas_buttons_layout )

        central_layout.addWidget( self.canvas_nav_container )
        central_layout.addStretch( 1 )

        bottom_container = QWidget()
        bottom_layout = QHBoxLayout( bottom_container )
        bottom_layout.setContentsMargins( 5, 5, 5, 5 )
        bottom_layout.setSpacing( 10 )

        self.output_dir_label = QLabel( "Output: Not selected" )
        self.output_dir_label.setStyleSheet( """
            QLabel {
                color: white;
                font-size: 11px;
                background-color: #333333;
                padding: 5px;
                border-radius: 3px;
                border: 1px solid #555555;
            }
        """ )
        self.output_dir_label.setMinimumHeight( 30 )
        self.output_dir_label.setAlignment( Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter )
        bottom_layout.addWidget( self.output_dir_label, 1 ) 

        browse_button = QPushButton( "Browse..." )
        browse_button.setFixedSize( 80, 30 )
        browse_button.setStyleSheet( """
            QPushButton {
                background-color: #666666;
                color: lightsalmon;
                font-weight: normal;
                border: 1px solid #777777;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #777777;
                border: 1px solid #888888;
            }
            QPushButton:pressed {
                background-color: #555555;
                border: 1px solid #666666;
            }
        """ )

        browse_button.clicked.connect( self.chooseOutputDirectory )
        browse_button.setToolTip( "Change output directory" )
        bottom_layout.addWidget( browse_button )
        central_layout.addWidget( bottom_container )

        self.setupCanvasesInContainer()

        if self.canvases:
            self.showCanvas( 0 )
            
        self.updateOutputDirLabel()

    def deleteCurrentCanvas( self ):
        if len( self.canvases ) <= 1:
            return

        current_canvas = self.getCurrentCanvas()
        if not current_canvas:
            return

        current_canvas_id = current_canvas.canvas_id
        current_canvas_name = current_canvas.custom_name
        reply = QMessageBox.question( self, 'Confirm Delete', f'Are you sure you want to delete { current_canvas_name } canvas ?\nAll widgets on this canvas will be lost.', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No )

        if reply == QMessageBox.StandardButton.No:
            return

        self.hideCanvasProperties()
        self.hideShapeProperties()
        self.deselectAllShapes()

        if current_canvas_id in self.canvas_widgets:
            widgets = self.canvas_widgets[ current_canvas_id ]

            for widget in widgets:
                widget.deleteLater()

            del self.canvas_widgets[ current_canvas_id ]

        canvas_to_delete = self.canvases.pop( self.current_canvas_index )
        canvas_to_delete.deleteLater()

        self.renumberCanvases()

        if self.current_canvas_index >= len( self.canvases ):
            self.current_canvas_index = len( self.canvases ) - 1

        if self.canvases:
            self.showCanvas( self.current_canvas_index )

        self.delete_canvas_btn.setEnabled( len( self.canvases ) > 1 )

    def renumberCanvases( self ):
        new_canvases = []
        new_canvas_widgets = {}

        for i, canvas in enumerate( self.canvases ):
            old_id = canvas.canvas_id
            canvas.canvas_id = i
            canvas.custom_name = f"Screen_{ i }"

            if old_id in self.canvas_widgets:
                new_canvas_widgets[ i ] = self.canvas_widgets[ old_id ]

            new_canvases.append( canvas )

        self.canvases = new_canvases
        self.canvas_widgets = new_canvas_widgets
        
    def setupCanvasesInContainer( self ):
        if not hasattr( self, 'canvas_display_container' ) or not hasattr( self, 'canvases' ):
            return
            
        container_layout = QVBoxLayout( self.canvas_display_container )
        container_layout.setContentsMargins( 10, 10, 10, 10 )
        container_layout.setAlignment( Qt.AlignmentFlag.AlignCenter )
        
        for canvas in self.canvases:
            container_layout.addWidget( canvas )
            canvas.hide()
        
    def addWidgetsToIconsPanel( self, widgets_icon_widget ):
        widgets_layout = QVBoxLayout( widgets_icon_widget )
        widgets_layout.setContentsMargins( 10, 10, 10, 10 )
        widgets_layout.setAlignment( Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter )

        label = QLabel( "Widgets" )
        label.setStyleSheet( "color: white; font-size: 16px; font-weight: normal;" )
        widgets_layout.addWidget( label )

        icons_container = QWidget()
        icons_layout = QGridLayout( icons_container )
        icons_layout.setSpacing( 20 )
        icons_layout.setAlignment( Qt.AlignmentFlag.AlignTop )

        widgets_shapes = [ "Line", "Rectangle", "Circle", "Ellipse", "Button", "Keys", "Clock", "Gauge", "Dial", "Toggle", "Scroll bar", "Slider", "Progress bar", "Image", "Label", "Numeric" ]

        row = 0
        col = 0

        for i, shape in enumerate( widgets_shapes ):
            widget_icon = WidgetIcon( shape )
            icons_layout.addWidget( widget_icon, row, col )
            col += 1

            if col >= 2:
                col = 0
                row += 1

        widgets_layout.addWidget( icons_container )
        
    def addNewCanvas( self ):
        self.hideCanvasProperties()
        self.hideShapeProperties()
        self.deselectAllShapes()

        canvas_id = self.createNewCanvas()

        if hasattr( self, 'canvas_display_container' ):
            self.canvas_display_container.layout().addWidget( self.canvases[ - 1 ] )

        self.showCanvas( canvas_id )
        current_canvas = self.getCurrentCanvas()

        if current_canvas:
            current_canvas.custom_name = f"Screen_{ canvas_id }"

            showCanvasProperties( self, current_canvas )
            self.canvas_properties_visible = True
            self.shape_properties_visible = False

        self.delete_canvas_btn.setEnabled( len( self.canvases ) > 1 )
        
    def prevCanvas( self ):
        if self.current_canvas_index > 0:
            self.hideCanvasProperties()
            self.hideShapeProperties()
            self.deselectAllShapes()
            self.showCanvas( self.current_canvas_index - 1 )
            
            current_canvas = self.getCurrentCanvas()
            if current_canvas:
                showCanvasProperties( self, current_canvas )
                self.canvas_properties_visible = True
                self.shape_properties_visible = False
            
    def nextCanvas( self ):
        if self.current_canvas_index < len( self.canvases ) - 1:
            self.hideCanvasProperties()
            self.hideShapeProperties()
            self.deselectAllShapes()
            self.showCanvas( self.current_canvas_index + 1 )
            current_canvas = self.getCurrentCanvas()

            if current_canvas:
                showCanvasProperties( self, current_canvas )
                self.canvas_properties_visible = True
                self.shape_properties_visible = False
            
    def getCurrentCanvas( self ):
        if 0 <= self.current_canvas_index < len( self.canvases ):
            return self.canvases[ self.current_canvas_index ]
        
        return None
        
    def getCurrentCanvasWidgets( self ):
        current_canvas = self.getCurrentCanvas()

        if current_canvas:
            return self.canvas_widgets.get( current_canvas.canvas_id, [] )
        
        return []
        
    def onCanvasClicked( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.current_shape:
                current_canvas = self.getCurrentCanvas()
    
                if current_canvas:
                    self.hideCanvasProperties()
                    self.hideShapeProperties()
                    showCanvasProperties( self, current_canvas )
                    self.canvas_properties_visible = True
                    self.shape_properties_visible = False
                    
    def onMainWidgetClick( self, event ):
        if not self.canvases:
            QWidget.mousePressEvent( self.main_widget, event )
            return

        current_canvas = self.getCurrentCanvas()

        if not current_canvas:
            QWidget.mousePressEvent( self.main_widget, event )
            return

        canvas_global = current_canvas.frameGeometry()
        canvas_global.moveTopLeft(current_canvas.mapToGlobal( current_canvas.rect().topLeft() ) )
        properties_global = self.properties_widget.frameGeometry()
        properties_global.moveTopLeft( self.properties_widget.mapToGlobal( self.properties_widget.rect().topLeft() ) )
        global_pos = event.globalPosition().toPoint()

        if not canvas_global.contains( global_pos ) and not properties_global.contains( global_pos ):
            if self.object_attached and self.selected_shape:
                QApplication.restoreOverrideCursor()
                self.object_attached = False
                self.selected_shape = None

            self.hideCanvasProperties()
            self.deselectAllShapes()
            self.hideShapeProperties()

            QWidget.mousePressEvent( self.main_widget, event )
            return

        if canvas_global.contains( global_pos ):
            clicked_on_shape = False
            current_widgets = self.getCurrentCanvasWidgets()

            if self.object_attached and self.selected_shape:
                self.addShapeToCanvas( global_pos )
                event.accept()
                return

            for shape in current_widgets:
                global_shape = shape.frameGeometry()
                global_shape.moveTopLeft( shape.mapToGlobal( shape.rect().topLeft() ) )

                if global_shape.contains( global_pos ):
                    clicked_on_shape = True
                    break

            if clicked_on_shape:
                pass  

            elif self.selected_shape and self.object_attached:
                self.addShapeToCanvas( global_pos )

            else:
                self.deselectAllShapes()
                self.hideShapeProperties()

        QWidget.mousePressEvent( self.main_widget, event )

    def hideCanvasProperties( self ):
        if hasattr( self, 'canvas_properties_visible' ) and not self.canvas_properties_visible:
            return

        for i in reversed( range( self.properties_layout.count() ) ):
            widget = self.properties_layout.itemAt( i ).widget()
            if widget:
                widget.hide()
                self.properties_layout.removeWidget( widget )
                widget.deleteLater()

        if hasattr( self, 'canvas_properties_visible' ):
            self.canvas_properties_visible = False

    def deselectAllShapes( self ):
        current_widgets = self.getCurrentCanvasWidgets()

        for shape in current_widgets:
            if shape:
                shape.setSelected( False )

        self.current_shape = None

    def keyPressEvent( self, event ):
        if event.key() == Qt.Key.Key_Delete and self.current_shape:
            self.deleteSelectedShape()

        elif event.key() == Qt.Key.Key_Escape:
            if self.object_attached and self.selected_shape:
                QApplication.restoreOverrideCursor()
                self.object_attached = False
                self.selected_shape = None
                event.accept()
                return

            if self.current_shape:
                self.deselectAllShapes()
                self.hideShapeProperties()
                event.accept()
                return

        else:
            super().keyPressEvent( event )
    
    def deleteSelectedShape( self ):
        if self.current_shape:
            current_canvas = self.getCurrentCanvas()
            
            if not current_canvas:
                return
                
            current_canvas_id = current_canvas.canvas_id
            current_widgets = self.canvas_widgets.get( current_canvas_id, [] )
            
            if self.current_shape in current_widgets:
                current_widgets.remove( self.current_shape )
                
                if hasattr( current_canvas, 'removeWidgetData' ) and hasattr( self.current_shape, 'data_dict' ):
                    widget_id = self.current_shape.data_dict.get( 'id' )

                    if widget_id:
                        current_canvas.removeWidgetData( widget_id )
            
            self.current_shape.deleteLater()
            self.current_shape = None
            self.hideShapeProperties()
            self.deselectAllShapes()
            self.renumberStackOrders()
            self.renumberAllWidgets()

    def getAllCanvasData( self ):
        all_data = {}

        for canvas in self.canvases:
            if hasattr( canvas, 'getDataDict' ):
                all_data[ canvas.canvas_id ] = canvas.getDataDict()

        return all_data

    def renumberAllWidgets( main_window ):
        if hasattr( main_window, 'canvas_widgets' ):
            for canvas_id, widgets in main_window.canvas_widgets.items():
                sorted_widgets = sorted( widgets, key = lambda x: x.stack_order )

                for i, widget in enumerate( sorted_widgets, 1 ):
                    widget.stack_order = i

                for widget in widgets:
                    widget.lower()

                for widget in sorted_widgets:
                    widget.raise_()

        else:

            if not hasattr( main_window, 'all_shapes' ):
                return

            for i, shape in enumerate( main_window.all_shapes, 1 ):
                shape.stack_order = i

            sorted_widgets = sorted( main_window.all_shapes, key = lambda x: x.stack_order )

            for widget in main_window.all_shapes:
                widget.lower()

            for widget in sorted_widgets:
                widget.raise_()

    def renumberStackOrders( self ):
        current_widgets = self.getCurrentCanvasWidgets()

        if not current_widgets:
            return

        sorted_widgets = sorted( current_widgets, key = lambda x: x.stack_order )
        for i, widget in enumerate( sorted_widgets, 1 ):
            widget.stack_order = i

        self.sortWidgetsByStackOrder()

    def hideShapeProperties( self ):
        if hasattr( self, 'shape_properties_visible' ) and not self.shape_properties_visible:
            return

        for i in reversed( range( self.properties_layout.count() ) ):
            widget = self.properties_layout.itemAt( i ).widget()

            if widget:
                widget.hide()
                self.properties_layout.removeWidget( widget )
                widget.deleteLater()

        if hasattr( self, 'shape_properties_visible' ):
            self.shape_properties_visible = False

    def selectShape( self, shape ):
        self.deselectAllShapes()
        shape.setSelected( True )
        self.current_shape = shape
        self.main_widget.setFocus()
        self.hideCanvasProperties()
        self.showShapeProperties()

    def addShapeToCanvas( self, global_pos ):
        current_canvas = self.getCurrentCanvas()

        if not current_canvas:
            return
            
        widget_container = current_canvas.widget_container

        if not widget_container:
            return
        
        canvas_container = current_canvas.container

        if not canvas_container:
            return
        
        canvas_global = canvas_container.frameGeometry()
        canvas_global.moveTopLeft( canvas_container.mapToGlobal( canvas_container.rect().topLeft() ) )
        
        if not canvas_global.contains( global_pos ):
            return
        
        container_pos = widget_container.mapFromGlobal( global_pos )
        shape = None

        if self.selected_shape == "Line":
            shape = LineWidget( widget_container )
            shape.setLinePosition( container_pos.x() , container_pos.y(), container_pos.x() + 100, container_pos.y() + 100 )
            shape.clicked.connect( self.selectShape )
            shape.custom_name = generateWidgetName( self, "Line" )
            shape.stack_order = len( self.getCurrentCanvasWidgets() ) + 1
            shape.tag = generateAutoTag( self, shape )

        elif self.selected_shape == "Rectangle":
            shape = RectangleWidget( widget_container )
            shape.move( container_pos.x(), container_pos.y() )
            shape.clicked.connect( self.selectShape )
            shape.custom_name = generateWidgetName( self, "Rectangle" )
            shape.stack_order = len( self.getCurrentCanvasWidgets() ) + 1
            shape.tag = generateAutoTag( self, shape )

        elif self.selected_shape == "Circle":
            shape = CircleWidget( widget_container )
            shape.move( container_pos.x() - shape.width() // 2, container_pos.y() - shape.height() // 2 )
            shape.clicked.connect( self.selectShape )
            shape.custom_name = generateWidgetName( self, "Circle" )
            shape.stack_order = len( self.getCurrentCanvasWidgets() ) + 1
            shape.tag = generateAutoTag( self, shape )

        elif self.selected_shape == "Ellipse":
            shape = EllipseWidget( widget_container )
            shape.move( container_pos.x() - shape.width() // 2, container_pos.y() - shape.height() // 2 )
            shape.clicked.connect( self.selectShape )
            shape.custom_name = generateWidgetName( self, "Ellipse" )
            shape.stack_order = len( self.getCurrentCanvasWidgets() ) + 1
            shape.tag = generateAutoTag( self, shape )

        elif self.selected_shape == "Button":
            shape = ButtonWidget( widget_container )
            shape.move( container_pos.x() , container_pos.y() )
            shape.clicked.connect( self.selectShape )
            shape.custom_name = generateWidgetName( self, "Button" )
            shape.stack_order = len( self.getCurrentCanvasWidgets() ) + 1
            shape.tag = generateAutoTag( self, shape )

        elif self.selected_shape == "Keys":
            shape = KeysWidget( widget_container )
            shape.move( container_pos.x() , container_pos.y() )
            shape.clicked.connect( self.selectShape )
            shape.custom_name = generateWidgetName( self, "Keys" )
            shape.stack_order = len( self.getCurrentCanvasWidgets() ) + 1

        elif self.selected_shape == "Clock":
            shape = ClockWidget( widget_container )
            shape.move( container_pos.x() - shape.width() // 2, container_pos.y() - shape.height() // 2 )
            shape.clicked.connect( self.selectShape )
            shape.custom_name = generateWidgetName( self, "Clock" )
            shape.stack_order = len( self.getCurrentCanvasWidgets() ) + 1

        elif self.selected_shape == "Gauge":
            shape = GaugeWidget( widget_container )
            shape.move( container_pos.x() - shape.width() // 2, container_pos.y() - shape.height() // 2 )
            shape.clicked.connect( self.selectShape )
            shape.custom_name = generateWidgetName( self, "Gauge" )
            shape.stack_order = len( self.getCurrentCanvasWidgets() ) + 1

        elif self.selected_shape == "Dial":
            shape = DialWidget( widget_container )
            shape.move( container_pos.x() - shape.width() // 2, container_pos.y() - shape.height() // 2 )
            shape.clicked.connect( self.selectShape )
            shape.custom_name = generateWidgetName( self, "Dial" )
            shape.stack_order = len( self.getCurrentCanvasWidgets() ) + 1
            shape.tag = generateAutoTag( self, shape )

        elif self.selected_shape == "Toggle":
            shape = ToggleWidget( widget_container )
            shape.move( container_pos.x() , container_pos.y() )
            shape.clicked.connect( self.selectShape )
            shape.custom_name = generateWidgetName( self, "Toggle" )
            shape.stack_order = len( self.getCurrentCanvasWidgets() ) + 1
            shape.tag = generateAutoTag( self, shape )

        elif self.selected_shape == "Scroll bar":
            shape = ScrollBarWidget( widget_container )
            shape.move( container_pos.x() , container_pos.y() )
            shape.clicked.connect( self.selectShape )
            shape.custom_name = generateWidgetName( self, "ScrollBar" )
            shape.stack_order = len( self.getCurrentCanvasWidgets() ) + 1
            shape.tag = generateAutoTag( self, shape )

        elif self.selected_shape == "Slider":
            shape = SliderWidget( widget_container )
            shape.move( container_pos.x() , container_pos.y() )
            shape.clicked.connect( self.selectShape )
            shape.custom_name = generateWidgetName( self, "Slider" )
            shape.stack_order = len( self.getCurrentCanvasWidgets() ) + 1
            shape.tag = generateAutoTag( self, shape )

        elif self.selected_shape == "Progress bar":
            shape = ProgressBarWidget( widget_container )
            shape.move( container_pos.x() , container_pos.y() )
            shape.clicked.connect( self.selectShape )
            shape.custom_name = generateWidgetName( self, "ProgressBar" )
            shape.stack_order = len( self.getCurrentCanvasWidgets() ) + 1
            
        elif self.selected_shape == "Image":
            shape = ImageWidget( widget_container )
            shape.move( container_pos.x() , container_pos.y() )
            shape.clicked.connect( self.selectShape )
            shape.custom_name = generateWidgetName(self, "Image")
            shape.stack_order = len( self.getCurrentCanvasWidgets() ) + 1

        elif self.selected_shape == "Label":
            shape = LabelWidget( widget_container )
            shape.move( container_pos.x(), container_pos.y() )
            shape.clicked.connect( self.selectShape )
            shape.custom_name = generateWidgetName( self, "Label" )
            shape.stack_order = len( self.getCurrentCanvasWidgets() ) + 1

        elif self.selected_shape == "Numeric":
            shape = NumericWidget( widget_container )
            shape.move( container_pos.x() , container_pos.y() )
            shape.clicked.connect( self.selectShape )
            shape.custom_name = generateWidgetName( self, "Numeric" )
            shape.stack_order = len( self.getCurrentCanvasWidgets() ) + 1

        if shape:
            current_widgets_count = len( self.getCurrentCanvasWidgets() )
            shape.stack_order = current_widgets_count + 1
            
            widget_id = f"{ current_canvas.canvas_id }_widget_{ len( self.getCurrentCanvasWidgets() ) }"
            shape.setDataId( widget_id )
            shape.show()
            shape.raise_()
            
            self.canvas_widgets[ current_canvas.canvas_id ].append( shape )
            
            if hasattr( current_canvas, 'addWidgetData' ):
                current_canvas.addWidgetData( shape.getDataDict() )
            
            self.sortWidgetsByStackOrder()
            self.selectShape( shape )
            
            QApplication.restoreOverrideCursor()
            self.object_attached = False
            self.selected_shape = None
            
    def updateWidgetsZOrder( self ):
        current_widgets = self.getCurrentCanvasWidgets()
        sorted_widgets = sorted( current_widgets, key = lambda x: x.stack_order )

        for widget in current_widgets:
            widget.lower()

        for widget in sorted_widgets:
            widget.raise_()

    def showShapeProperties( self ):
        self.hideShapeProperties()
        self.hideCanvasProperties()
        
        current_index = 0

        if isinstance( self.current_shape, LineWidget ):
            current_index = showLineProperties( self, current_index )

        elif isinstance( self.current_shape, RectangleWidget ):
            current_index = showRectangleProperties( self, current_index )

        elif isinstance( self.current_shape, CircleWidget ):
            current_index = showCircleProperties( self, current_index )

        elif isinstance( self.current_shape, EllipseWidget ):
            current_index = showEllipseProperties( self, current_index )

        elif isinstance( self.current_shape, ButtonWidget ):
            current_index = showButtonProperties( self, current_index )

        elif isinstance( self.current_shape, KeysWidget ):
            current_index = showKeysProperties( self, current_index )

        elif isinstance( self.current_shape, ClockWidget ):
            current_index = showClockProperties( self, current_index )

        elif isinstance( self.current_shape, GaugeWidget ):
            current_index = showGaugeProperties( self, current_index )

        elif isinstance( self.current_shape, DialWidget ):
            current_index = showDialProperties( self, current_index )

        elif isinstance( self.current_shape, ToggleWidget ):
            current_index = showToggleProperties( self, current_index )

        elif isinstance( self.current_shape, ScrollBarWidget ):
            current_index = showScrollBarProperties( self, current_index )

        elif isinstance( self.current_shape, SliderWidget ):
            current_index = showSliderProperties( self, current_index )

        elif isinstance( self.current_shape, ProgressBarWidget ):
            current_index = showProgressBarProperties( self, current_index )

        elif isinstance( self.current_shape, ImageWidget ):
            current_index = showImageProperties( self, current_index )

        elif isinstance( self.current_shape, LabelWidget ):
            current_index = showLabelProperties( self, current_index )

        elif isinstance( self.current_shape, NumericWidget ):
            current_index = showNumericProperties( self, current_index )

        self.shape_properties_visible = True

    def sortWidgetsByStackOrder( self ):
        current_widgets = self.getCurrentCanvasWidgets()

        if not current_widgets:
            return
    
        sorted_widgets = sorted( current_widgets, key = lambda x: x.stack_order )
    
        for widget in current_widgets:
            widget.lower()
    
        for widget in sorted_widgets:
            widget.raise_()
    
    def updateOutputDirLabel( self ):
        if not hasattr( self, 'output_dir_label' ) or not self.output_dir_label:
            return

        if hasattr( self, 'output_dir' ) and self.output_dir:
            display_path = self.output_dir

            if len( display_path ) > 50:
                display_path = display_path[ :20 ] + "..." + display_path[ -27: ]

            self.output_dir_label.setText( f"Output: { display_path }" )
            self.output_dir_label.setToolTip( self.output_dir )

        else:
            self.output_dir_label.setText( "Output: Not selected" )
            self.output_dir_label.setToolTip("")
            self.output_dir_label.setStyleSheet( "color: red; background-color: #383838;" )

    def chooseOutputDirectory( self ):
        dir_path = QFileDialog.getExistingDirectory( self, "Select output directory for generated files" )

        if dir_path:
            self.output_dir = dir_path
            self.updateOutputDirLabel()

    def generateAllFiles( self ):
        if not self.output_dir:
            self.chooseOutputDirectory()

        self.updateOutputDirLabel()
        generateResources( self, self.output_dir )
        generateComponents( self, self.output_dir )

def startApp():
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID( 'ft800.designer.app.1.0' )

    pix = QPixmap(str( Path( __file__ ).resolve().parent / "bootup_logo.png" ) )
    splash_pix = pix.scaled( 800, 450, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation )
    splash = QSplashScreen( splash_pix, Qt.WindowType.WindowStaysOnTopHint )
    splash.show()

    QApplication.processEvents()
    window = MainWindow()
    QTimer.singleShot( 3000, lambda:( splash.finish( window ), window.showMaximized() ) )

    return window

if __name__ == "__main__":
    app = QApplication( sys.argv )
    window = startApp()
    sys.exit( app.exec() )