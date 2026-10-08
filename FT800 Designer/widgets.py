from PyQt6.QtWidgets import ( QWidget, QMainWindow, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox )
from PyQt6.QtGui import ( QPainter, QPen, QColor, QLinearGradient, QFont, QBrush, QPixmap, QFontMetrics )
from PyQt6.QtCore import ( Qt, QPoint, QRect, QPointF, pyqtSignal, QSize, QRectF )
import math
import os
        
class LineWidget( QWidget ):
    clicked = pyqtSignal( object )
    
    def __init__( self, parent = None ):
        super().__init__( parent )

        self.defaultValues()
        self.setMouseTracking( True )
        self.setFocusPolicy( Qt.FocusPolicy.StrongFocus )
        self.setupDataDict()

    def defaultValues( self ):
        self.active = True
        self.visible = True
        self.static = False
        self.custom_name = ""
        self.stack_order = 1
        self.tag = 0
        self.start_x = 0
        self.start_y = 0
        self.end_x = 100
        self.end_y = 100
        self.line_color = QColor( 0, 0, 0 ) 
        self.line_width = 1

        self.selected = False
        self.resizing = False
        self.dragging = False
        self.resize_start_pos = QPoint()
        self.resize_start_size = QPoint()
        self.resize_corner = None
        self.drag_start_global_pos = QPoint()
        self.drag_start_line_pos = None

    def paintEvent( self, event ):
        if self.visible and self.active:
            alpha = 255

        else:
            alpha = 50

        painter = QPainter( self )
        painter.setRenderHint( QPainter.RenderHint.Antialiasing )

        local_start_x = self.start_x - self.x()
        local_start_y = self.start_y - self.y()
        local_end_x = self.end_x - self.x()
        local_end_y = self.end_y - self.y()

        line_color = QColor( self.line_color )
        line_color.setAlpha( alpha )

        pen = QPen( line_color )
        pen.setWidth( 2 * self.line_width )
        pen.setCapStyle( Qt.PenCapStyle.RoundCap )
        painter.setPen( pen )
        painter.drawLine( local_start_x, local_start_y, local_end_x, local_end_y )

        if self.selected:
            self.drawSelectionBorder( painter )
            self.drawSelectionHandles( painter, local_start_x, local_start_y, local_end_x, local_end_y )
    
    def drawSelectionHandles( self, painter, start_x, start_y, end_x, end_y ):
        handle_size = 8
        half_size = handle_size // 2

        painter.setBrush( QColor( 255, 142, 62 ) )
        painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )
        painter.drawEllipse( start_x - half_size, start_y - half_size, handle_size, handle_size )
        painter.drawEllipse( end_x - half_size, end_y - half_size, handle_size, handle_size )
        painter.setBrush( QColor( 255, 142, 62 ) )
        painter.setPen( Qt.PenStyle.NoPen )
        painter.drawEllipse( start_x - 1, start_y - 1, 2, 2 )
        painter.drawEllipse( end_x - 1, end_y - 1, 2, 2 )
    
    def drawSelectionBorder( self, painter ):
        local_start_x = self.start_x - self.x()
        local_start_y = self.start_y - self.y()
        local_end_x = self.end_x - self.x()
        local_end_y = self.end_y - self.y()
        
        min_x = min( local_start_x, local_end_x )
        min_y = min( local_start_y, local_end_y )
        max_x = max( local_start_x, local_end_x )
        max_y = max( local_start_y, local_end_y )
        
        selection_rect = QRect( min_x, min_y, max_x - min_x, max_y - min_y )
        
        selection_pen = QPen( QColor( 255, 0, 0 ) )
        selection_pen.setWidth( 2 )
        selection_pen.setStyle( Qt.PenStyle.DashLine )
        selection_pen.setDashPattern( [ 4, 2 ] )
        
        painter.setPen( selection_pen )
        painter.setBrush( Qt.BrushStyle.NoBrush )
        painter.drawRect( selection_rect )

    def handleResize( self, global_pos ):
        if not self.resize_corner or not self.resize_start_size:
            return

        delta = global_pos - self.resize_start_pos
        
        start_x_start, start_y_start, end_x_start, end_y_start = self.resize_start_size
        
        if self.resize_corner == "start":
            self.start_x = start_x_start + delta.x()
            self.start_y = start_y_start + delta.y()

        elif self.resize_corner == "end":
            self.end_x = end_x_start + delta.x()
            self.end_y = end_y_start + delta.y()
        
        self.updateWidgetPosition()
        self.update()

    def isPointOnLine( self, pos ):
        if self.parent():
            global_pos = self.parent().mapToGlobal( self.mapToParent( pos ) )

        else:
            global_pos = self.mapToGlobal( pos )
        
        if self.parent():
            parent_global = self.parent().mapFromGlobal( global_pos )

        else:
            parent_global = self.mapFromGlobal( global_pos )
        
        x1, y1, x2, y2 = self.start_x, self.start_y, self.end_x, self.end_y
        
        if x1 == x2 and y1 == y2:
            distance = math.sqrt( ( parent_global.x() - x1 ) ** 2 + ( parent_global.y() - y1 ) ** 2 )

            return distance <= self.line_width / 2 + 5
        
        A = parent_global.x() - x1
        B = parent_global.y() - y1
        C = x2 - x1
        D = y2 - y1
        
        dot = A * C + B * D
        len_sq = C * C + D * D
        param = -1
        
        if len_sq != 0:
            param = dot / len_sq
        
        if param < 0:
            xx, yy = x1, y1

        elif param > 1:
            xx, yy = x2, y2

        else:
            xx = x1 + param * C
            yy = y1 + param * D
        
        distance = math.sqrt( ( parent_global.x() - xx ) ** 2 + ( parent_global.y() - yy ) ** 2 )
        
        return distance <= self.line_width / 2 + 5

    def getCornerAt( self, pos ):
        handle_size = 16
        
        if self.parent():
            global_pos = self.parent().mapToGlobal( self.mapToParent( pos ) )

        else:
            global_pos = self.mapToGlobal( pos )
        
        if self.parent():
            parent_global = self.parent().mapFromGlobal( global_pos )

        else:
            parent_global = self.mapFromGlobal( global_pos )
        
        start_rect = QRect( self.start_x - handle_size // 2, self.start_y - handle_size // 2, handle_size, handle_size )

        if start_rect.contains( parent_global ):
            return "start"
        
        end_rect = QRect( self.end_x - handle_size // 2, self.end_y - handle_size // 2, handle_size, handle_size ) 

        if end_rect.contains( parent_global ):
            return "end"
        
        return None

    def setSelected( self, selected ):
        self.selected = selected
        self.update()

    def setLinePosition( self, start_x, start_y, end_x, end_y ):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y

        self.updateWidgetPosition()
        self.update()

    def updateWidgetPosition( self ):
        margin = 20 
        min_x = min( self.start_x, self.end_x )
        min_y = min( self.start_y, self.end_y )
        max_x = max( self.start_x, self.end_x )
        max_y = max( self.start_y, self.end_y )
        width = max( 20, max_x - min_x ) + 2 * margin
        height = max( 20, max_y - min_y ) + 2 * margin
        
        self.setFixedSize( width, height )
        
        center_x = ( self.start_x + self.end_x ) // 2
        center_y = ( self.start_y + self.end_y ) // 2
        new_x = center_x - self.width() // 2
        new_y = center_y - self.height() // 2
        
        if self.x() != new_x or self.y() != new_y:
            self.move( new_x, new_y )

    def updateLinePositionPropertiesPosition( self ):
        main_window = self.findMainWindow()

        if ( hasattr( main_window, 'current_shape' ) and main_window.current_shape == self ):
            try:
                if hasattr( main_window, 'start_x_spin_line' ):
                    main_window.start_x_spin_line.blockSignals( True )
                    main_window.start_x_spin_line.setValue( self.start_x )
                    main_window.start_x_spin_line.blockSignals( False )

                if hasattr( main_window, 'start_y_spin_line' ):
                    main_window.start_y_spin_line.blockSignals( True )
                    main_window.start_y_spin_line.setValue( self.start_y )
                    main_window.start_y_spin_line.blockSignals( False )

                if hasattr(main_window, 'end_x_spin_line'):
                    main_window.end_x_spin_line.blockSignals( True )
                    main_window.end_x_spin_line.setValue( self.end_x )
                    main_window.end_x_spin_line.blockSignals( False )

                if hasattr(main_window, 'end_y_spin_line'):
                    main_window.end_y_spin_line.blockSignals( True )
                    main_window.end_y_spin_line.setValue( self.end_y )
                    main_window.end_y_spin_line.blockSignals( False )

            except:
                pass

    def setupDataDict( self ):
        self.data_dict = {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'tag': self.tag,
            'start_x': self.start_x,
            'start_y': self.start_y,
            'end_x': self.end_x,
            'end_y': self.end_y,
            'line_color': self.line_color,
            'line_width': self.line_width,

            'type': 'Line',
            'id': None
        }
    
    def updateDataDict( self ):
        self.data_dict.update( {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'tag': self.tag,
            'start_x': self.start_x,
            'start_y': self.start_y,
            'end_x': self.end_x,
            'end_y': self.end_y,
            'line_color':  self.line_color,
            'line_width': self.line_width,
        } )
        return self.data_dict
    
    def getDataDict( self ):
        return self.updateDataDict()
    
    def setDataId(self, data_id):
        self.data_dict[ 'id' ] = data_id

    def findMainWindow( self ):
        parent = self.parent()

        while parent:
            if isinstance( parent, QMainWindow ):

                return parent
            
            parent = parent.parent()

        return None

    def mousePressEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.findMainWindow()

            if main_window and hasattr( main_window, 'object_attached' ) and main_window.object_attached:
                event.ignore()
                return 

            mouse_pos = event.pos()
            self.resize_corner = self.getCornerAt( mouse_pos )

            if self.resize_corner:
                self.resizing = True
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_size = ( self.start_x, self.start_y, self.end_x, self.end_y )

            else:
                if self.isPointOnLine( mouse_pos ):
                    self.dragging = True
                    self.drag_start_global_pos = event.globalPosition().toPoint()
                    self.drag_start_line_pos = ( self.start_x, self.start_y, self.end_x, self.end_y )

                self.clicked.emit( self )
                event.accept() 
        else:
            event.ignore()

    def mouseReleaseEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = False
            self.dragging = False
            self.resize_corner = None
            self.resize_start_size = None
            self.drag_start_line_pos = None

        self.updateDataDict()
        event.accept()

    def mouseMoveEvent( self, event ):
        mouse_pos = event.pos()
        point = self.getCornerAt( mouse_pos )

        if point:
            self.setCursor( Qt.CursorShape.SizeAllCursor )

        elif self.isPointOnLine( mouse_pos ):
            self.setCursor( Qt.CursorShape.SizeAllCursor )

        else:
            self.setCursor( Qt.CursorShape.ArrowCursor )
        
        if self.resizing and event.buttons() & Qt.MouseButton.LeftButton:
            self.handleResize( event.globalPosition().toPoint() )
            self.updateLinePositionPropertiesPosition()

        elif self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            current_global_pos = event.globalPosition().toPoint()
            delta = current_global_pos - self.drag_start_global_pos
            
            if self.drag_start_line_pos:
                start_x_start, start_y_start, end_x_start, end_y_start = self.drag_start_line_pos
                self.start_x = start_x_start + delta.x()
                self.start_y = start_y_start + delta.y()
                self.end_x = end_x_start + delta.x()
                self.end_y = end_y_start + delta.y()
                
                self.updateWidgetPosition()
                self.update()
                self.updateLinePositionPropertiesPosition()
        
        event.accept()

class RectangleWidget( QWidget ):
    clicked = pyqtSignal( object )
    
    def __init__( self, parent = None ):
        super().__init__( parent )

        self.defaultValues()
        self.setFixedSize( self.rectangle_width, self.rectangle_height )
        self.setMouseTracking( True )
        self.setFocusPolicy( Qt.FocusPolicy.StrongFocus )
        self.setupDataDict()
        
    def defaultValues( self ):
        self.active = True
        self.visible = True
        self.static = False
        self.custom_name = ""
        self.stack_order = 1
        self.tag = 0
        self.rectangle_width = 100 
        self.rectangle_height = 80 
        self.edges_color = QColor( 0, 0, 0 )
        self.edges_width = 1
        self.filled = False 
        self.gradient_direction = "Top-Bottom"
        self.start_color = QColor( 255, 0, 0 )
        self.end_color = QColor( 0, 0, 255 )

        self.selected = False
        self.resizing = False
        self.dragging = False
        self.resize_start_pos = QPoint()
        self.resize_start_size = QSize()
        self.resize_start_position = QPoint()
        self.resize_corner = None
        self.drag_start_pos = QPoint()

    def paintEvent( self, event ):
        if self.visible and self.active:
            self.edges_color.setAlpha( 255 )
            self.start_color.setAlpha( 255 )
            self.end_color.setAlpha( 255 )

        else:
            self.edges_color.setAlpha( 50 )
            self.start_color.setAlpha( 50 )
            self.end_color.setAlpha( 50 )

        painter = QPainter( self )
        painter.setRenderHint( QPainter.RenderHint.Antialiasing )

        if self.filled:
            gradient = None
            
            if self.gradient_direction == "Top-Bottom":
                gradient = QLinearGradient( 0, 0, 0, self.height() )
            elif self.gradient_direction == "Bottom-Top":
                gradient = QLinearGradient( 0, self.height(), 0, 0 )
            elif self.gradient_direction == "Left-Right":
                gradient = QLinearGradient( 0, 0, self.width(), 0 )
            elif self.gradient_direction == "Right-Left":
                gradient = QLinearGradient( self.width(), 0, 0, 0 )

            gradient.setColorAt( 0.0, self.start_color )
            gradient.setColorAt( 0.6, self.end_color )
            gradient.setColorAt( 1.0, self.end_color )    
            painter.fillRect( self.rect(), gradient )

        pen = QPen( self.edges_color )
        pen.setWidth( 2 * self.edges_width )
        painter.setPen( pen )
        painter.setBrush( Qt.BrushStyle.NoBrush )
        painter.drawRect( 0, 0, self.width(), self.height() )
        
        if self.selected:
            self.drawSelectionBorder( painter )
            self.drawSelectionHandles( painter )

    def drawSelectionHandles( self, painter ):
        handle_size = 8
        half_size = handle_size // 2

        painter.setBrush( QColor( 255, 142, 62 ) )
        painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

        corners = [ QPoint( 4, 4 ), QPoint( self.width() - 4, 4 ), QPoint( 4, self.height() - 4 ), QPoint( self.width() - 4, self.height() - 4 ) ]

        for corner in corners:
            painter.drawEllipse( corner.x() - half_size, corner.y() - half_size, handle_size, handle_size )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( Qt.PenStyle.NoPen )
            painter.drawEllipse( corner.x() - 1, corner.y() - 1, 2, 2 )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

    def drawSelectionBorder( self, painter ):
        selection_rect = QRect( 0, 0, self.width(), self.height() )
        selection_pen = QPen( QColor( 255, 0, 0 ) )
        selection_pen.setWidth( 2 )
        selection_pen.setStyle( Qt.PenStyle.DashLine )
        selection_pen.setDashPattern( [ 4, 2 ] )

        painter.setPen( selection_pen )
        painter.setBrush( Qt.BrushStyle.NoBrush )
        painter.drawRect( selection_rect )

    def handleResize( self, global_pos ):
        if not self.resize_corner:
            return

        delta = global_pos - self.resize_start_pos

        new_width = self.resize_start_size.width()
        new_height = self.resize_start_size.height()
        new_x = self.resize_start_position.x()
        new_y = self.resize_start_position.y()

        if self.resize_corner == "bottom_right":
            new_width = max( 10, self.resize_start_size.width() + delta.x() )
            new_height = max( 10, self.resize_start_size.height() + delta.y() )

        elif self.resize_corner == "top_right":
            new_width = max( 10, self.resize_start_size.width() + delta.x() )
            new_height = max( 10, self.resize_start_size.height() - delta.y() )
            new_y = self.resize_start_position.y() + delta.y()

        elif self.resize_corner == "bottom_left":
            new_width = max( 10, self.resize_start_size.width() - delta.x() )
            new_x = self.resize_start_position.x() + delta.x()
            new_height = max( 10, self.resize_start_size.height() + delta.y() )

        elif self.resize_corner == "top_left":
            new_width = max( 10, self.resize_start_size.width() - delta.x() )
            new_x = self.resize_start_position.x() + delta.x()
            new_height = max( 10, self.resize_start_size.height() - delta.y() )
            new_y = self.resize_start_position.y() + delta.y()

        self.rectangle_width = new_width
        self.rectangle_height = new_height
        self.setFixedSize( new_width, new_height )
        
        if self.resize_corner in [ "top_left", "bottom_left" ]:
            self.move( new_x, new_y )

        elif self.resize_corner == "top_right":
            self.move( self.x(), new_y )

        self.updateRectanglePropertiesSize()
        self.updateRectanglePropertiesPosition()

    def getCornerAt( self, pos ):
        handle_size = 16
        half_size = handle_size // 2
        
        corners = {
            "top_left": QPoint( 0, 0 ),
            "top_right": QPoint( self.width(), 0 ),
            "bottom_left": QPoint( 0, self.height() ),
            "bottom_right": QPoint( self.width(), self.height() )
        }
        
        for corner_name, corner_pos in corners.items():
            corner_rect = QRect( corner_pos.x() - half_size, corner_pos.y() - half_size, handle_size, handle_size )

            if corner_rect.contains( pos ):
                return corner_name
        
        return None

    def setSelected( self, selected ):
        self.selected = selected
        self.update()

    def updateRectanglePropertiesSize( self ):
        main_window = self.findMainWindow()
        
        try:
            if main_window and main_window.current_shape == self:
                if hasattr( main_window, 'width_spin_rect' ):
                    main_window.width_spin_rect.blockSignals( True )
                    main_window.width_spin_rect.setValue( self.rectangle_width )
                    main_window.width_spin_rect.blockSignals( False )
                
                if hasattr( main_window, 'height_spin_rect' ):
                    main_window.height_spin_rect.blockSignals( True )
                    main_window.height_spin_rect.setValue( self.rectangle_height )
                    main_window.height_spin_rect.blockSignals( False )
        except:
            pass

    def updateRectanglePropertiesPosition( self ):
        main_window = self.findMainWindow()
        
        try:
            if main_window and main_window.current_shape == self:
                if hasattr( main_window, 'pos_x_spin_rect' ):
                    main_window.pos_x_spin_rect.blockSignals( True )
                    main_window.pos_x_spin_rect.setValue( self.x() )
                    main_window.pos_x_spin_rect.blockSignals( False )
                
                if hasattr( main_window, 'pos_y_spin_rect' ):
                    main_window.pos_y_spin_rect.blockSignals( True )
                    main_window.pos_y_spin_rect.setValue( self.y() )
                    main_window.pos_y_spin_rect.blockSignals( False )
        except:
            pass

    def setupDataDict( self ):
        self.data_dict = {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'tag': self.tag,
            'position_x': self.x(),
            'position_y': self.y(),
            'rectangle_width': self.rectangle_width,
            'rectangle_height': self.rectangle_height,
            'edges_color': self.edges_color,
            'edges_width': self.edges_width,
            'filled': self.filled,
            'gradient_direction': self.gradient_direction,
            'gradient_start_color': self.start_color,
            'gradient_end_color': self.end_color,
            'type': 'Rectangle',
            'id': None
        }
    
    def updateDataDict( self ):
        self.data_dict.update( {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'tag': self.tag,
            'position_x': self.x(),
            'position_y': self.y(),
            'rectangle_width': self.rectangle_width,
            'rectangle_height': self.rectangle_height,
            'edges_color': self.edges_color,
            'edges_width': self.edges_width,
            'filled': self.filled,
            'gradient_direction': self.gradient_direction,
            'gradient_start_color': self.start_color,
            'gradient_end_color': self.end_color
        } )
        return self.data_dict
    
    def getDataDict( self ):
        return self.updateDataDict()
    
    def setDataId( self, data_id ):
        self.data_dict[ 'id' ] = data_id

    def findMainWindow( self ):
        parent = self.parent()
        while parent:
            if isinstance(parent, QMainWindow):
                return parent
            parent = parent.parent()
        return None

    def mousePressEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.findMainWindow()

            if main_window and hasattr( main_window, 'object_attached' ) and main_window.object_attached:
                event.ignore()
                return

            mouse_pos = event.pos()
            self.resize_corner = self.getCornerAt( mouse_pos )

            if self.resize_corner:
                self.resizing = True
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_size = self.size()
                self.resize_start_position = self.pos()

            else:
                self.dragging = True
                self.drag_start_pos = mouse_pos
                self.clicked.emit( self )

        event.accept()

    def mouseReleaseEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = False
            self.dragging = False
            self.resize_corner = None

            self.updateRectanglePropertiesSize()
            self.updateRectanglePropertiesPosition()

        self.updateDataDict()
        event.accept()

    def mouseMoveEvent( self, event ):
        mouse_pos = event.pos()
        corner = self.getCornerAt( mouse_pos )

        if corner:
            if corner in [ "top_left", "bottom_right" ]:
                self.setCursor( Qt.CursorShape.SizeFDiagCursor )

            elif corner in [ "top_right", "bottom_left" ]:
                self.setCursor( Qt.CursorShape.SizeBDiagCursor )

        else:
            self.setCursor( Qt.CursorShape.ArrowCursor )
        
        if self.resizing and event.buttons() & Qt.MouseButton.LeftButton:
            self.handleResize( event.globalPosition().toPoint() )

        elif self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            delta = mouse_pos - self.drag_start_pos
            new_x = self.x() + delta.x()
            new_y = self.y() + delta.y()
            self.move( new_x, new_y )
            self.updateRectanglePropertiesPosition()
            
        event.accept()

class CircleWidget( QWidget ):
    clicked = pyqtSignal( object )
    
    def __init__( self, parent = None ):
        super().__init__( parent )

        self.defaultValues()
        self.setFixedSize( self.diameter, self.diameter )
        self.setMouseTracking( True )
        self.setFocusPolicy( Qt.FocusPolicy.StrongFocus )
        self.setupDataDict()
        
    def defaultValues( self ):
        self.active = True
        self.visible = True
        self.static = False
        self.custom_name = ""
        self.stack_order = 1
        self.tag = 0
        self.center_x = 0
        self.center_y = 0
        self.diameter = 100
        self.edges_color = QColor( 0, 0, 0 )
        self.edges_width = 1
        self.filled = False 
        self.fill_color = QColor( 255, 0, 0 )

        self.selected = False
        self.resizing = False
        self.dragging = False
        self.resize_start_pos = QPoint()
        self.drag_start_pos = QPoint()
        self.resize_corner = None
        self.resize_start_diameter = 0

    def paintEvent( self, event ):
        if self.visible and self.active:
            self.edges_color.setAlpha( 255 )
            self.fill_color.setAlpha( 255 )

        else:
            self.edges_color.setAlpha( 50 )
            self.fill_color.setAlpha( 50 )

        painter = QPainter( self )
        painter.setRenderHint( QPainter.RenderHint.Antialiasing )
        rect_size = min( self.width(), self.height() ) - 2 * self.edges_width

        x_offset = ( self.width() - rect_size ) // 2
        y_offset = ( self.height() - rect_size ) // 2

        circle_rect = QRectF( x_offset, y_offset, rect_size, rect_size )

        if self.filled:
            painter.setBrush( self.fill_color )
            painter.setPen( Qt.PenStyle.NoPen )
            painter.drawEllipse( circle_rect )

        pen = QPen( self.edges_color, 2 * self.edges_width )
        pen.setJoinStyle( Qt.PenJoinStyle.RoundJoin )
        pen.setCapStyle( Qt.PenCapStyle.RoundCap )
        painter.setPen( pen )
        painter.setBrush( Qt.BrushStyle.NoBrush )
        painter.drawEllipse( circle_rect )

        if self.selected:
            self.drawSelectionBorder( painter )
            self.drawSelectionHandles( painter )
            
    def drawSelectionHandles( self, painter ):
        handle_size = 8
        half_size = handle_size // 2

        painter.setBrush( QColor( 255, 142, 62 ) )
        painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

        corners = [ QPoint( 4, 4 ), QPoint( self.width() - 4, 4 ), QPoint( 4, self.height() - 4 ), QPoint( self.width() - 4, self.height() - 4 ) ]

        for point in corners:
            painter.drawEllipse( point.x() - half_size, point.y() - half_size, handle_size, handle_size )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( Qt.PenStyle.NoPen )
            painter.drawEllipse( point.x() - 1, point.y() - 1, 2, 2 )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

    def drawSelectionBorder( self, painter ):
        selection_rect = QRectF( 0, 0, self.width(), self.height() )
        
        selection_pen = QPen( QColor( 255, 0, 0 ) )
        selection_pen.setWidth( 2 )
        selection_pen.setStyle( Qt.PenStyle.DashLine )
        selection_pen.setDashPattern( [ 4, 2 ] )
        
        painter.setPen( selection_pen )
        painter.setBrush( Qt.BrushStyle.NoBrush )
        painter.drawRect( selection_rect )

    def handleResize( self, global_pos ):
        delta = global_pos - self.resize_start_pos
        new_diameter = self.resize_start_diameter

        if "right" in self.resize_corner:
            new_diameter = max( 10, self.resize_start_diameter + 2 * delta.x() )

        elif "left" in self.resize_corner:
            new_diameter = max( 10, self.resize_start_diameter - 2 * delta.x() )

        elif "top" in self.resize_corner:
            new_diameter = max( 10, self.resize_start_diameter - 2 * delta.y() )

        elif "bottom" in self.resize_corner:
            new_diameter = max( 10, self.resize_start_diameter + 2 * delta.y() )

        old_center_x = self.x() + self.diameter // 2
        old_center_y = self.y() + self.diameter // 2

        self.diameter = new_diameter
        self.setFixedSize( new_diameter, new_diameter )

        new_x = old_center_x - new_diameter // 2
        new_y = old_center_y - new_diameter // 2
        self.move( new_x, new_y )

        self.updateCenterPosition()
        self.updateCirclePropertiesSize()
        self.updateCircleCenterPositionProperties()
        self.update()

    def getCornerAt( self, pos ):
        handle_size = 16 
        half_size = handle_size // 2
        
        corners = {
            "top_left": QPoint( 0, 0 ),
            "top_right": QPoint( self.width(), 0 ),
            "bottom_left": QPoint( 0, self.height() ),
            "bottom_right": QPoint( self.width(), self.height() )
        }
        
        for corner_name, corner_pos in corners.items():
            corner_rect = QRect( corner_pos.x() - half_size, corner_pos.y() - half_size, handle_size, handle_size )
            
            if corner_rect.contains( pos ):
                return corner_name
        
        return None

    def setSelected( self, selected ):
        self.selected = selected
        self.update()
    
    def updateCenterPosition( self ):
        self.center_x = self.x() + self.diameter // 2
        self.center_y = self.y() + self.diameter // 2

    def updateCirclePropertiesSize( self ):
        main_window = self.findMainWindow()
        try:
            if ( hasattr( main_window, 'current_shape' ) and main_window.current_shape == self and  hasattr( main_window, 'diameter_spin_circle' ) ):
                
                main_window.diameter_spin_circle.blockSignals( True )
                main_window.diameter_spin_circle.setValue( self.diameter )
                main_window.diameter_spin_circle.blockSignals( False )

        except:
            pass

    def updateCircleCenterPositionProperties( self ):
        main_window = self.findMainWindow()
        self.updateCenterPosition()

        try:
            if ( hasattr( main_window, 'current_shape' ) and main_window.current_shape == self ):
                
                if hasattr( main_window, 'pos_x_spin_circle' ):
                    main_window.pos_x_spin_circle.blockSignals( True )
                    main_window.pos_x_spin_circle.setValue( self.center_x )
                    main_window.pos_x_spin_circle.blockSignals( False )

                if hasattr( main_window, 'pos_y_spin_circle' ):
                    main_window.pos_y_spin_circle.blockSignals( True )
                    main_window.pos_y_spin_circle.setValue( self.center_y )
                    main_window.pos_y_spin_circle.blockSignals( False )

        except:
            pass

    def setupDataDict( self ):
        self.updateCenterPosition()
        
        self.data_dict = {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'tag': self.tag,
            'center_x': self.center_x,
            'center_y': self.center_y,
            'diameter': self.diameter,
            'edges_color': self.edges_color,
            'edges_width': self.edges_width,
            'filled': self.filled,
            'fill_color': self.fill_color,
            'type': 'Circle',
            'id': None
        }
    
    def updateDataDict( self ):
        self.updateCenterPosition()
        
        self.data_dict.update( {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'tag': self.tag,
            'center_x': self.center_x,
            'center_y': self.center_y,
            'diameter': self.diameter,
            'edges_color': self.edges_color,
            'edges_width': self.edges_width,
            'filled': self.filled,
            'fill_color': self.fill_color
        } )
        return self.data_dict
    
    def getDataDict( self ):
        return self.updateDataDict()
    
    def setDataId( self, data_id ):
        self.data_dict[ 'id' ] = data_id

    def move( self, x, y ):
        super().move(x, y)
        self.updateCenterPosition()

    def setGeometry( self, x, y, width, height ):
        super().setGeometry(x, y, width, height)
        self.updateCenterPosition()

    def findMainWindow( self ):
        parent = self.parent()

        while parent:
            if isinstance( parent, QMainWindow ):
                return parent
            
            parent = parent.parent()

        return None

    def mousePressEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.findMainWindow()

            if main_window and hasattr( main_window, 'object_attached' ) and main_window.object_attached:
                event.ignore() 
                return  

            mouse_pos = event.pos()
            self.resize_corner = self.getCornerAt( mouse_pos )

            if self.resize_corner:
                self.resizing = True
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_diameter = self.diameter

            else:
                self.dragging = True
                self.drag_start_pos = mouse_pos
                self.clicked.emit( self )

            self.updateCircleCenterPositionProperties()
            event.accept()

    def mouseReleaseEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = False
            self.dragging = False
            self.resize_corner = None
            
            self.updateCirclePropertiesSize()
            self.updateCircleCenterPositionProperties()
            self.updateDataDict()

        event.accept()

    def mouseMoveEvent( self, event ):
        mouse_pos = event.pos()
        corner = self.getCornerAt( mouse_pos )

        if corner:
            if corner in [ "top_left", "bottom_right" ]:
                self.setCursor( Qt.CursorShape.SizeFDiagCursor )

            elif corner in [ "top_right", "bottom_left" ]:
                self.setCursor( Qt.CursorShape.SizeBDiagCursor )

        else:
            self.setCursor( Qt.CursorShape.ArrowCursor )

        if self.resizing and event.buttons() & Qt.MouseButton.LeftButton:
            self.handleResize( event.globalPosition().toPoint() )

        elif self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            delta = mouse_pos - self.drag_start_pos
            new_x = self.x() + delta.x()
            new_y = self.y() + delta.y()
            self.move( new_x, new_y )
            self.updateCircleCenterPositionProperties()
            self.updateDataDict()

        event.accept()

class EllipseWidget( QWidget ):
    clicked = pyqtSignal( object )
    
    def __init__( self, parent = None ):
        super().__init__( parent )

        self.defaultValues()
        self.setFixedSize( self.ellipse_width, self.ellipse_height )
        self.setMouseTracking( True )
        self.setFocusPolicy( Qt.FocusPolicy.StrongFocus )
        self.setupDataDict()

    def defaultValues( self ):
        self.active = True
        self.visible = True
        self.static = False
        self.custom_name = ""
        self.stack_order = 1
        self.tag = 0
        self.ellipse_width = 120
        self.ellipse_height = 80
        self.center_x = 0
        self.center_y = 0
        self.edges_color = QColor( 0, 0, 0 )
        self.edges_width = 1
        self.filled = False
        self.show_ellipse_warning = True
        self.gradient_direction = "Top-Bottom"
        self.gradient_start_color = QColor( 255, 0, 0 )
        self.gradient_end_color = QColor( 0, 0, 255 )

        self.selected = False
        self.resizing = False
        self.dragging = False
        self.resize_start_pos = QPoint()
        self.drag_start_pos = QPoint()
        self.resize_corner = None
        self.resize_start_size = QSize()

    def paintEvent( self, event ):
        if self.visible and self.active:
            self.edges_color.setAlpha( 255 )
            self.gradient_start_color.setAlpha( 255 )
            self.gradient_end_color.setAlpha( 255 )

        else:
            self.edges_color.setAlpha( 50 )
            self.gradient_start_color.setAlpha( 50 )
            self.gradient_end_color.setAlpha( 50 )

        painter = QPainter( self )
        painter.setRenderHint( QPainter.RenderHint.Antialiasing )

        margin = self.edges_width
        ellipse_rect = QRect( margin, margin, self.ellipse_width - 2 * margin, self.ellipse_height - 2 * margin )

        if self.filled:
            if self.gradient_direction == "Top-Bottom":
                gradient = QLinearGradient( 0, 0, 0, self.ellipse_height )

            elif self.gradient_direction == "Bottom-Top":
                gradient = QLinearGradient( 0, self.ellipse_height, 0, 0 )

            elif self.gradient_direction == "Left-Right":
                gradient = QLinearGradient( 0, 0, self.ellipse_width, 0 )

            elif self.gradient_direction == "Right-Left":
                gradient = QLinearGradient( self.ellipse_width, 0, 0, 0 )

            else:
                gradient = QLinearGradient( 0, 0, 0, self.ellipse_height )

            gradient.setColorAt( 0, self.gradient_start_color )
            gradient.setColorAt( 1, self.gradient_end_color )
            painter.setBrush( QBrush( gradient ) )
        else:
            painter.setBrush( Qt.BrushStyle.NoBrush )

        painter.setPen( QPen( self.edges_color, 2 * self.edges_width ) )
        painter.drawEllipse( ellipse_rect )

        if self.selected:
            self.drawSelectionBorder( painter )
            self.drawSelectionHandles( painter )

    def drawSelectionHandles( self, painter ):
        handle_size = 8
        half_size = handle_size // 2

        painter.setBrush( QColor( 255, 142, 62 ) )
        painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

        corners = [ QPoint( 4, 4 ), QPoint( self.width() - 4, 4 ), QPoint( 4, self.height() - 4 ), QPoint( self.width() - 4, self.height() - 4 ) ]

        for corner in corners:
            painter.drawEllipse( corner.x() - half_size, corner.y() - half_size, handle_size, handle_size )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( Qt.PenStyle.NoPen )
            painter.drawEllipse( corner.x() - 1, corner.y() - 1, 2, 2 )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )
    
    def drawSelectionBorder( self, painter ):
        border_rect = QRect( 0, 0, self.width(), self.height() )

        selection_pen = QPen( QColor( 255, 0, 0 ) )
        selection_pen.setWidth( 2 )
        selection_pen.setStyle( Qt.PenStyle.DashLine )
        selection_pen.setDashPattern( [ 4, 2 ] )

        painter.setPen( selection_pen )
        painter.setBrush( Qt.BrushStyle.NoBrush )
        painter.drawRect( border_rect )

    def handleResize( self, global_pos ):
        delta = global_pos - self.resize_start_pos
        new_width = self.resize_start_size.width()
        new_height = self.resize_start_size.height()

        old_center_x = self.x() + self.ellipse_width // 2
        old_center_y = self.y() + self.ellipse_height // 2

        if self.resize_corner == "bottom_right":
            new_width = max( 10, self.resize_start_size.width() + delta.x() )
            new_height = max( 10, self.resize_start_size.height() + delta.y() )

        elif self.resize_corner == "top_right":
            new_width = max( 10, self.resize_start_size.width() + delta.x() )
            new_height = max( 10, self.resize_start_size.height() - delta.y() )
            delta_height = new_height - self.resize_start_size.height()
            self.move( self.x(), self.y() - delta_height )

        elif self.resize_corner == "bottom_left":
            new_width = max( 10, self.resize_start_size.width() - delta.x() )
            new_height = max( 10, self.resize_start_size.height() + delta.y() )
            delta_width = new_width - self.resize_start_size.width()
            self.move(self.x() - delta_width, self.y())

        elif self.resize_corner == "top_left":
            new_width = max( 10, self.resize_start_size.width() - delta.x() )
            new_height = max( 10, self.resize_start_size.height() - delta.y() )
            delta_width = new_width - self.resize_start_size.width()
            delta_height = new_height - self.resize_start_size.height()
            self.move( self.x() - delta_width, self.y() - delta_height )

        self.ellipse_width = max( 20, new_width )
        self.ellipse_height = max( 20, new_height )

        new_center_x = self.x() + self.ellipse_width // 2
        new_center_y = self.y() + self.ellipse_height // 2

        if new_center_x != old_center_x or new_center_y != old_center_y:
            self.move( old_center_x - self.ellipse_width // 2, old_center_y - self.ellipse_height // 2 )

        self.setFixedSize( self.ellipse_width, self.ellipse_height )
        self.updateCenterPosition()
        self.updateEllipsePropertiesSize()
        self.updateEllipseCenterPositionProperties()
        self.update()
    
    def getCornerAt( self, pos ):
        handle_size = 16 
        half_size = handle_size // 2
        
        corners = {
            "top_left": QPoint( 0, 0 ),
            "top_right": QPoint( self.width(), 0 ),
            "bottom_left": QPoint( 0, self.height() ),
            "bottom_right": QPoint( self.width(), self.height() )
        }
        
        for corner_name, corner_pos in corners.items():
            corner_rect = QRect( corner_pos.x() - half_size, corner_pos.y() - half_size, handle_size, handle_size )
            
            if corner_rect.contains( pos ):
                return corner_name
        
        return None
    
    def setSelected( self, selected ):
        self.selected = selected
        self.update()
    
    def updateCenterPosition( self ):
        self.center_x = self.x() + self.ellipse_width // 2
        self.center_y = self.y() + self.ellipse_height // 2

    def updateEllipsePropertiesSize( self ):
        main_window = self.findMainWindow()

        if not main_window:
            return

        try:
            if ( hasattr( main_window, 'current_shape' ) and main_window.current_shape == self ):
                
                if hasattr( main_window, 'width_spin_ellipse' ):
                    main_window.width_spin_ellipse.blockSignals( True )
                    main_window.width_spin_ellipse.setValue( self.ellipse_width )
                    main_window.width_spin_ellipse.blockSignals( False )

                if hasattr( main_window, 'height_spin_ellipse' ):
                    main_window.height_spin_ellipse.blockSignals( True )
                    main_window.height_spin_ellipse.setValue( self.ellipse_height )
                    main_window.height_spin_ellipse.blockSignals( False )

        except:
            pass
            
    def updateEllipseCenterPositionProperties( self ):
        main_window = self.findMainWindow()
        self.updateCenterPosition()

        try:
            if ( hasattr( main_window, 'current_shape' ) and main_window.current_shape == self ):
                
                if hasattr( main_window, 'pos_x_spin_ellipse' ):
                    main_window.pos_x_spin_ellipse.blockSignals( True )
                    main_window.pos_x_spin_ellipse.setValue( self.center_x )
                    main_window.pos_x_spin_ellipse.blockSignals( False )

                if hasattr( main_window, 'pos_y_spin_ellipse' ):
                    main_window.pos_y_spin_ellipse.blockSignals( True )
                    main_window.pos_y_spin_ellipse.setValue( self.center_y )
                    main_window.pos_y_spin_ellipse.blockSignals( False )

        except:
            pass

    def showFilledWarning( self, state ):
        state = state == Qt.CheckState.Checked.value

        if state and self.show_ellipse_warning:
            warning_dialog = QDialog( self )
            warning_dialog.setWindowTitle( "Information" )
            warning_dialog.setFixedSize( 400, 200 )
            warning_dialog.setStyleSheet( "QDialog {background-color: #2b2b2b; border: 1px solid #555555;}" )
            layout = QVBoxLayout(warning_dialog)
            info_label = QLabel( "This option is resource intensive and may cause unpredictable display behavior." )
            info_label.setWordWrap( True )
            info_label.setStyleSheet( "color: white; font-size: 12px; padding: 10px; border: none;" )
            layout.addWidget( info_label )

            dont_show_layout = QHBoxLayout()
            dont_show_checkbox = QCheckBox( "Do not show again" )
            dont_show_checkbox.setStyleSheet( "color: white; border: none;" )
            dont_show_layout.addWidget( dont_show_checkbox )
            dont_show_layout.addStretch( 1 )
            layout.addLayout( dont_show_layout )

            button_layout = QHBoxLayout()
            ok_button = QPushButton( "OK" )
            ok_button.clicked.connect( warning_dialog.accept )
            ok_button.setFixedWidth( 80 )
            button_layout.addStretch( 1 )
            button_layout.addWidget( ok_button )
            layout.addLayout( button_layout )
            warning_dialog.exec()

            if dont_show_checkbox.isChecked():
                self.show_ellipse_warning = False

    def setupDataDict( self ):
        self.updateCenterPosition() 
        
        self.data_dict = {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'tag': self.tag,
            'center_x': self.center_x,
            'center_y': self.center_y,
            'ellipse_width': self.ellipse_width,
            'ellipse_height': self.ellipse_height,
            'edges_color': self.edges_color,
            'edges_width': self.edges_width,
            'filled': self.filled,
            'gradient_direction': self.gradient_direction,
            'gradient_start_color': self.gradient_start_color,
            'gradient_end_color': self.gradient_end_color,
            'type': 'Ellipse',
            'id': None
        }
    
    def updateDataDict( self ):
        self.updateCenterPosition()  
        
        self.data_dict.update( {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'tag': self.tag,
            'center_x': self.center_x,
            'center_y': self.center_y,
            'ellipse_width': self.ellipse_width,
            'ellipse_height': self.ellipse_height,
            'edges_color': self.edges_color,
            'edges_width': self.edges_width,
            'filled': self.filled,
            'gradient_direction': self.gradient_direction,
            'gradient_start_color': self.gradient_start_color,
            'gradient_end_color': self.gradient_end_color
        } )
        return self.data_dict
    
    def getDataDict( self ):
        return self.updateDataDict()
    
    def setDataId( self, data_id ):
        self.data_dict[ 'id' ] = data_id

    def move( self, x, y ):
        super().move( x, y )
        self.updateCenterPosition()

    def setGeometry( self, x, y, width, height ):
        super().setGeometry( x, y, width, height )
        self.updateCenterPosition()

    def findMainWindow( self ):
        parent = self.parent()

        while parent:
            if isinstance( parent, QMainWindow ):

                return parent
            
            parent = parent.parent()

        return None
    
    def mousePressEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.findMainWindow()

            if main_window and hasattr( main_window, 'object_attached' ) and main_window.object_attached:
                event.ignore() 
                return 

            mouse_pos = event.pos()
            self.resize_corner = self.getCornerAt( mouse_pos )

            if self.resize_corner:
                self.resizing = True
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_size = self.size()

            else:
                self.dragging = True
                self.drag_start_pos = mouse_pos
                self.clicked.emit( self )

            self.updateEllipseCenterPositionProperties()
            event.accept()

    def mouseReleaseEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = False
            self.dragging = False
            self.resize_corner = None
            
            self.updateEllipsePropertiesSize()
            self.updateEllipseCenterPositionProperties()
            self.updateDataDict()

        event.accept()

    def mouseMoveEvent( self, event ):
        mouse_pos = event.pos()
        corner = self.getCornerAt( mouse_pos )

        if corner:
            if corner in [ "top_left", "bottom_right" ]:
                self.setCursor( Qt.CursorShape.SizeFDiagCursor )

            elif corner in [ "top_right", "bottom_left" ]:
                self.setCursor( Qt.CursorShape.SizeBDiagCursor )

        else:
            self.setCursor( Qt.CursorShape.ArrowCursor )
        
        if self.resizing and event.buttons() & Qt.MouseButton.LeftButton:
            self.handleResize( event.globalPosition().toPoint() )

        elif self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            delta = mouse_pos - self.drag_start_pos
            new_x = self.x() + delta.x()
            new_y = self.y() + delta.y()
            self.move( new_x, new_y )
            self.updateEllipseCenterPositionProperties()
            self.updateDataDict()
        
        event.accept()
    
class ButtonWidget( QWidget ):
    clicked = pyqtSignal( object )
    
    def __init__( self, parent = None ):
        super().__init__( parent )
        
        self.defaultValues()
        self.setFixedSize( self.button_width, self.button_height )
        self.setMouseTracking( True )
        self.setFocusPolicy( Qt.FocusPolicy.StrongFocus )
        self.setupDataDict()
        
    def defaultValues( self ):
        self.active = True
        self.visible = True
        self.static = False
        self.custom_name = ""
        self.stack_order = 1
        self.tag = 0
        self.button_width = 100
        self.button_height = 50
        self.gradient_start_color = QColor( 255, 255, 255 )
        self.gradient_end_color = QColor( 0, 0, 255 )
        self.color_press = QColor( 0, 0, 255 )
        self.effect_3d = True
        self.effect_3d_press = True
        self.button_text = "Press"
        self.text_size = 28
        self.text_color = QColor( 255, 255, 255 )

        self.selected = False
        self.resizing = False
        self.dragging = False 
        self.resize_start_pos = QPoint()
        self.drag_start_pos = QPoint()
        self.resize_corner = None
        self.resize_start_size = QSize()
        self.resize_start_position = QPoint() 

    def paintEvent( self, event ):
        if self.visible and self.active:
            self.gradient_start_color.setAlpha( 255 )
            self.gradient_end_color.setAlpha( 255 )
            self.color_press.setAlpha( 255 )
            self.text_color.setAlpha( 255 )

        else:
            self.gradient_start_color.setAlpha( 50 )
            self.gradient_end_color.setAlpha( 50 )
            self.color_press.setAlpha( 50 )
            self.text_color.setAlpha( 50 )

        painter = QPainter( self )
        painter.setRenderHint( QPainter.RenderHint.Antialiasing )

  
        r = int( 4 / 5 * self.text_size - 89 / 5 )

        if self.effect_3d and self.effect_3d_press:
            gradient = QLinearGradient( 0, 0, 0, self.height() )
            self.gradient_start_color.setAlpha( 100 )
            gradient.setColorAt( 0.0, self.gradient_start_color )
            gradient.setColorAt( 0.4, self.gradient_end_color )   
            gradient.setColorAt( 1.0, self.gradient_end_color ) 
            painter.setBrush( QBrush( gradient ) )
            painter.setPen( Qt.PenStyle.NoPen )
            painter.drawRoundedRect( 0, 0, self.width(), self.height(), r, r )

            painter.setPen( QPen( QColor( 0, 0, 0 ), 2 ) )
            painter.drawLine( r, self.height() - 1, self.width() - r, self.height() - 1 )
            painter.drawLine( self.width() - 1, r, self.width() - 1, self.height() - r )
            painter.drawArc( self.width() - 2 * r - 1, self.height() - 2 * r - 1, 2 * r, 2 * r, 270 * 16, 90 * 16 )

        else:
            painter.setBrush( QBrush( self.color_press ) )
            painter.drawRoundedRect( 0, 0, self.width(), self.height(), r, r )

        painter.setPen( QPen( self.text_color ) )
        font = QFont()
        font.setPointSize( int( ( 23 / 5 ) * self.text_size - 548 / 5) )
        painter.setFont( font )
        painter.drawText( self.rect(), Qt.AlignmentFlag.AlignCenter, self.button_text )

        if self.selected:
            self.drawSelectionBorder( painter )
            self.drawSelectionHandles( painter )
            
    def drawSelectionHandles( self, painter ):
        handle_size = 8
        half_size = handle_size // 2

        painter.setBrush( QColor( 255, 142, 62 ) )
        painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

        corners = [ QPoint( 4, 4 ), QPoint( self.width() - 4, 4 ), QPoint( 4, self.height() - 4 ), QPoint( self.width() - 4, self.height() - 4 ) ]

        for corner in corners:
            painter.drawEllipse( corner.x() - half_size, corner.y() - half_size, handle_size, handle_size )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( Qt.PenStyle.NoPen )
            painter.drawEllipse( corner.x() - 1, corner.y() - 1, 2, 2 )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )
            
    def drawSelectionBorder(self, painter):
        border_rect = QRect( 0, 0, self.width(), self.height() )

        selection_pen = QPen( QColor( 255, 0, 0 ) )
        selection_pen.setWidth( 2 )
        selection_pen.setStyle( Qt.PenStyle.DashLine )
        selection_pen.setDashPattern( [ 4, 2 ] )

        painter.setPen( selection_pen )
        painter.setBrush( Qt.BrushStyle.NoBrush )
        painter.drawRect( border_rect )

    def handleResize( self, global_pos ):
        delta = global_pos - self.resize_start_pos
        new_width = self.resize_start_size.width()
        new_height = self.resize_start_size.height()
        new_x = self.resize_start_position.x()
        new_y = self.resize_start_position.y()

        if self.resize_corner == "bottom_right":
            new_width = max( 10, self.resize_start_size.width() + delta.x() )
            new_height = max( 10, self.resize_start_size.height() + delta.y() )

        elif self.resize_corner == "top_right":
            new_width = max( 10, self.resize_start_size.width() + delta.x() )
            new_height = max( 10, self.resize_start_size.height() - delta.y() )
            new_y = self.resize_start_position.y() + delta.y() 

        elif self.resize_corner == "bottom_left":
            new_width = max( 10, self.resize_start_size.width() - delta.x() )
            new_height = max( 10, self.resize_start_size.height() + delta.y() )
            new_x = self.resize_start_position.x() + delta.x()

        elif self.resize_corner == "top_left":
            new_width = max( 10, self.resize_start_size.width() - delta.x() )
            new_height = max( 10, self.resize_start_size.height() - delta.y() )
            new_x = self.resize_start_position.x() + delta.x() 
            new_y = self.resize_start_position.y() + delta.y()

        self.setFixedSize( new_width, new_height )

        if self.resize_corner in [ "top_left", "bottom_left" ]:
            self.move(new_x, new_y)

        elif self.resize_corner == "top_right":
            self.move( self.x(), new_y ) 

        self.update()
        self.updateButtonPropertiesSize()
        self.updateButtonPropertiesPosition()

    def getCornerAt( self, pos ):
        handle_size = 12 
        half_size = handle_size // 2
        
        corners = {
            "top_left": QPoint( 0, 0 ),
            "top_right": QPoint( self.width(), 0 ),
            "bottom_left": QPoint( 0, self.height() ),
            "bottom_right": QPoint( self.width(), self.height() )
        }
        
        for corner_name, corner_pos in corners.items():
            corner_rect = QRect( corner_pos.x() - half_size, corner_pos.y() - half_size, handle_size, handle_size )
            
            if corner_rect.contains( pos ):
                return corner_name
        
        return None
    

    def setSelected( self, selected ):
        self.selected = selected
        self.update()

    def updateButtonProperties3D( self ):
        main_window = self.findMainWindow()
        
        try:
            main_window.effect_3d_checkbox.blockSignals( True )
            main_window.effect_3d_checkbox.setChecked( self.effect_3d )
            main_window.effect_3d_checkbox.blockSignals( False )
        
        except:
            pass

    def updateButtonPropertiesSize( self ):
        main_window = self.findMainWindow()

        try:
            if main_window and main_window.current_shape == self:
                if hasattr( main_window, 'width_spin_button' ):
                    main_window.width_spin_button.blockSignals( True )
                    main_window.width_spin_button.setValue( self.width() )
                    main_window.width_spin_button.blockSignals( False )

                if hasattr( main_window, 'height_spin_button' ):
                    main_window.height_spin_button.blockSignals( True )
                    main_window.height_spin_button.setValue( self.height() )
                    main_window.height_spin_button.blockSignals( False )
                    
        except:
            pass

    def updateButtonPropertiesPosition( self ):
        main_window = self.findMainWindow()

        try:
            if hasattr( main_window, 'pos_x_spin_button' ):
                main_window.pos_x_spin_button.blockSignals( True )
                main_window.pos_x_spin_button.setValue( self.x() )
                main_window.pos_x_spin_button.blockSignals( False )

            if hasattr( main_window, 'pos_y_spin_button' ):
                main_window.pos_y_spin_button.blockSignals( True )
                main_window.pos_y_spin_button.setValue( self.y() )
                main_window.pos_y_spin_button.blockSignals( False )

        except:
            pass

    def setupDataDict( self ):
        self.data_dict = {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'tag': self.tag,
            'position_x': self.x(),
            'position_y': self.y(),
            'button_width': self.width(),
            'button_height': self.height(),
            'gradient_start_color': self.gradient_start_color,
            'gradient_end_color': self.gradient_end_color,
            'effect_3d': self.effect_3d,
            'text': self.button_text,
            'text_size': self.text_size,
            'text_color': self.text_color,

            'type': 'Button',
            'id': None
        }
    
    def updateDataDict( self ):
        self.data_dict.update( {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'tag': self.tag,
            'position_x': self.x(),
            'position_y': self.y(),
            'button_width': self.width(),
            'button_height': self.height(),
            'gradient_start_color': self.gradient_start_color,
            'gradient_end_color': self.gradient_end_color,
            'effect_3d': self.effect_3d,
            'text': self.button_text,
            'text_size': self.text_size,
            'text_color': self.text_color
        } )
        return self.data_dict
    
    def getDataDict( self ):
        return self.updateDataDict()
    
    def setDataId( self, data_id ):
        self.data_dict[ 'id' ] = data_id

    def findMainWindow( self ):
        parent = self.parent()

        while parent:
            if isinstance( parent, QMainWindow ):
                return parent
            parent = parent.parent()

        return None

    def mousePressEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.findMainWindow()

            if main_window and hasattr( main_window, 'object_attached' ) and main_window.object_attached:
                event.ignore()
                return 

            mouse_pos = event.pos()
            self.resize_corner = self.getCornerAt( mouse_pos )

            if self.resize_corner:
                self.resizing = True
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_size = self.size()
                self.resize_start_position = self.pos()

            else:
                self.dragging = True
                self.drag_start_pos = mouse_pos 
                self.clicked.emit( self )

                if self.effect_3d:
                    self.effect_3d_press = False
                    self.updateButtonProperties3D()
                    self.update()         

        event.accept()

    def mouseReleaseEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            
            self.resizing = False
            self.dragging = False
            self.resize_corner = None

            if self.effect_3d:
                self.effect_3d_press = True
                self.updateButtonProperties3D()
                self.update()

            self.updateButtonPropertiesSize()
            self.updateButtonPropertiesPosition()

        self.updateDataDict()
        event.accept()

    def mouseMoveEvent( self, event ):
        mouse_pos = event.pos()
        corner = self.getCornerAt( mouse_pos )

        if corner:
            if corner in [ "top_left", "bottom_right" ]:
                self.setCursor( Qt.CursorShape.SizeFDiagCursor )

            elif corner in [ "top_right", "bottom_left" ]:
                self.setCursor( Qt.CursorShape.SizeBDiagCursor )
        else:
            self.setCursor( Qt.CursorShape.ArrowCursor )
        
        if self.resizing and event.buttons() & Qt.MouseButton.LeftButton:
            self.handleResize( event.globalPosition().toPoint() )

        elif self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            delta = mouse_pos - self.drag_start_pos
            new_x = self.x() + delta.x()
            new_y = self.y() + delta.y()

            self.move(new_x, new_y)
            self.updateButtonPropertiesPosition()
        
        event.accept()

class KeysWidget( QWidget ):
    clicked = pyqtSignal( object )
    
    def __init__( self, parent = None ):
        super().__init__( parent )
        
        self.defaultValues()
        self.setMouseTracking( True )
        self.setFocusPolicy( Qt.FocusPolicy.StrongFocus )
        self.setupDataDict()

    def defaultValues( self ):
        self.active = True
        self.visible = True
        self.static = False
        self.custom_name = ""
        self.stack_order = 1
        self.gradient_start_color = QColor( 255, 255, 255 ) 
        self.gradient_end_color = QColor( 0, 0, 255 )
        self.text_color = QColor( 255, 255, 255 ) 
        self.effect_3d = True
        self.key_type = "QUERTZ"
        self.font_size = 26

        self.selected = False
        self.resizing = False
        self.dragging = False
        self.resize_start_pos = QPoint()
        self.drag_start_pos = QPoint()
        self.resize_corner = None
        self.resize_start_size = QSize()
        self.resize_start_position = QPoint()
        self.calculateOptimalSize()
    
    def paintEvent( self, event ):
        if self.visible and self.active:
            self.gradient_start_color.setAlpha( 255 )
            self.gradient_end_color.setAlpha( 255 )
            self.text_color.setAlpha( 255 )

        else:
            self.gradient_start_color.setAlpha( 50 )
            self.gradient_end_color.setAlpha( 50 )
            self.text_color.setAlpha( 50 )

        painter = QPainter( self )
        painter.setRenderHint( QPainter.RenderHint.Antialiasing )
        
        font = QFont()
        font.setPointSize( int( ( 23 / 5 ) * self.font_size - 548 / 5 ) )
        painter.setFont( font )

        margin_x = 0
        margin_y = 0

        current_x = margin_x
        current_y = margin_y

        r = int( 4 / 5 * self.font_size - 89 / 5 )

        if self.key_type == "NUM":
            numbers = [ 7, 8, 9, 4, 5, 6, 1, 2, 3 ]
            number_index = 0

            for i in range( 3 ):
                for j in range( 3 ):
                    current_number = numbers[ number_index ]
                    number_index += 1

                    gradient = QLinearGradient( current_x, current_y, current_x, current_y + self.key_height )
                    self.gradient_start_color.setAlpha( 50 )
                    gradient.setColorAt( 0.0, self.gradient_start_color )
                    gradient.setColorAt( 0.3, self.gradient_end_color )   
                    gradient.setColorAt( 1.0, self.gradient_end_color ) 

                    painter.setBrush( gradient)
                    painter.setPen( Qt.PenStyle.NoPen )
                    painter.drawRoundedRect( current_x, current_y, self.key_width, self.key_height, r, r )

                    if self.effect_3d:
                        self.draw3dEffect( painter, current_x, current_y, self.key_width, self.key_height, r )

                    text = str( current_number ) 
                    painter.setPen( QPen( self.text_color ) )
                    text_rect = painter.boundingRect( current_x, current_y, self.key_width, self.key_height, Qt.AlignmentFlag.AlignCenter, text )
                    painter.drawText( text_rect, Qt.AlignmentFlag.AlignCenter, text )

                    current_x += self.key_width + 2

                current_x = margin_x
                current_y += self.key_height + 1

            key_width_0 = self.key_width * 2 + 2

            gradient = QLinearGradient( current_x, current_y, current_x, current_y + self.key_height )
            self.gradient_start_color.setAlpha( 50 )
            gradient.setColorAt( 0.0, self.gradient_start_color )
            gradient.setColorAt( 0.3, self.gradient_end_color )   
            gradient.setColorAt( 1.0, self.gradient_end_color ) 

            painter.setBrush( gradient )
            painter.setPen( Qt.PenStyle.NoPen )
            painter.drawRoundedRect( current_x, current_y, key_width_0, self.key_height, r, r )

            if self.effect_3d:
                self.draw3dEffect( painter, current_x, current_y, key_width_0, self.key_height, r )

            text = "0"
            painter.setPen( QPen( self.text_color ) )
            text_rect = painter.boundingRect( current_x, current_y, key_width_0, self.key_height, Qt.AlignmentFlag.AlignCenter, text )
            painter.drawText( text_rect, Qt.AlignmentFlag.AlignCenter, text )

            current_x += key_width_0 + 2

            gradient = QLinearGradient( current_x, current_y, current_x, current_y + self.key_height )
            self.gradient_start_color.setAlpha( 50 )
            gradient.setColorAt( 0.0, self.gradient_start_color )
            gradient.setColorAt( 0.3, self.gradient_end_color )   
            gradient.setColorAt( 1.0, self.gradient_end_color ) 

            painter.setBrush( gradient )
            painter.setPen( Qt.PenStyle.NoPen )
            painter.drawRoundedRect( current_x, current_y, self.key_width, self.key_height, r, r )

            if self.effect_3d:
                self.draw3dEffect( painter, current_x, current_y, self.key_width, self.key_height, r )

            text = "."
            painter.setPen( QPen( self.text_color ) )
            text_rect = painter.boundingRect( current_x, current_y, self.key_width, self.key_height, Qt.AlignmentFlag.AlignCenter, text )
            painter.drawText( text_rect, Qt.AlignmentFlag.AlignCenter, text )
            self.adjustKeySizeFromWidgetSize()
            self.update()

        elif self.key_type == "QUERTZ":
            keys_row_1 = "QWERTZUIOP"

            for key in keys_row_1:
                gradient = QLinearGradient( current_x, current_y, current_x, current_y + self.key_height )
                self.gradient_start_color.setAlpha( 50 )
                gradient.setColorAt( 0.0, self.gradient_start_color )
                gradient.setColorAt( 0.3, self.gradient_end_color )   
                gradient.setColorAt( 1.0, self.gradient_end_color ) 

                painter.setBrush( gradient )
                painter.setPen( Qt.PenStyle.NoPen )
                painter.drawRoundedRect( current_x, current_y, self.key_width, self.key_height, r, r )

                if self.effect_3d:
                    self.draw3dEffect( painter, current_x, current_y, self.key_width, self.key_height, r )

                painter.setPen( QPen( self.text_color ) )
                text_rect = painter.boundingRect( current_x, current_y, self.key_width, self.key_height, Qt.AlignmentFlag.AlignCenter, key )
                painter.drawText( text_rect, Qt.AlignmentFlag.AlignCenter, key )

                current_x += self.key_width + 4

            current_x = margin_x + self.key_width // 2
            current_y += self.key_height + 4
            keys_row_2 = "ASDFGHJKL"

            for key in keys_row_2:
                gradient = QLinearGradient( current_x, current_y, current_x, current_y + self.key_height )
                self.gradient_start_color.setAlpha( 50 )
                gradient.setColorAt( 0.0, self.gradient_start_color )
                gradient.setColorAt( 0.4, self.gradient_end_color )   
                gradient.setColorAt( 1.0, self.gradient_end_color ) 

                painter.setBrush( gradient )
                painter.setPen( Qt.PenStyle.NoPen )
                painter.drawRoundedRect( current_x, current_y, self.key_width, self.key_height, r, r )

                if self.effect_3d:
                    self.draw3dEffect( painter, current_x, current_y, self.key_width, self.key_height, r )

                painter.setPen( QPen( self.text_color ) )
                text_rect = painter.boundingRect( current_x, current_y, self.key_width, self.key_height, Qt.AlignmentFlag.AlignCenter, key )
                painter.drawText( text_rect, Qt.AlignmentFlag.AlignCenter, key )

                current_x += self.key_width + 4

            current_x = margin_x
            current_y += self.key_height + 4
            keys_row_3 = [ "Ent", "Y", "X", "C", "V", "B", "N", "M", "Del" ]

            for i, key in enumerate( keys_row_3 ):
                if key in [ "Ent", "Del" ]:
                    key_width = self.key_width

                else:
                    key_width = int( self.key_width * 1.18 )

                gradient = QLinearGradient( current_x, current_y, current_x, current_y + self.key_height )
                self.gradient_start_color.setAlpha( 50 )
                gradient.setColorAt( 0.0, self.gradient_start_color )
                gradient.setColorAt( 0.4, self.gradient_end_color )   
                gradient.setColorAt( 1.0, self.gradient_end_color ) 

                painter.setBrush( gradient )
                painter.setPen( Qt.PenStyle.NoPen )
                painter.drawRoundedRect( current_x, current_y, key_width, self.key_height, r, r )

                if self.effect_3d:
                    self.draw3dEffect( painter, current_x, current_y, key_width, self.key_height, r )

                if key in [ "Ent", "Del" ]:
                    small_font = QFont()
                    small_font.setPointSize( int( ( 23 / 5 ) * self.font_size - 548 / 5 ) )
                    painter.setFont( small_font )

                painter.setPen( QPen( self.text_color ) )
                text_rect = painter.boundingRect( current_x, current_y, key_width, self.key_height, Qt.AlignmentFlag.AlignCenter, key )
                painter.drawText( text_rect, Qt.AlignmentFlag.AlignCenter, key )

                painter.setFont( font )

                current_x += key_width + 4

            current_x = margin_x
            current_y += self.key_height + 4
            space_width = self.keys_width - 2 * margin_x

            gradient = QLinearGradient( current_x, current_y, current_x, current_y + self.key_height )
            self.gradient_start_color.setAlpha( 50 )
            gradient.setColorAt( 0.0, self.gradient_start_color )
            gradient.setColorAt( 0.4, self.gradient_end_color )   
            gradient.setColorAt( 1.0, self.gradient_end_color ) 

            painter.setPen( Qt.PenStyle.NoPen )
            painter.setBrush( gradient )
            painter.drawRoundedRect( current_x, current_y, space_width, self.key_height, r, r )

            if self.effect_3d:
                self.draw3dEffect( painter, current_x, current_y, space_width, self.key_height, r )

            space_font = QFont()
            space_font.setPointSize( int( ( 23 / 5 ) * self.font_size - 548 / 5 ) )
            painter.setFont( space_font )

            painter.setPen( QPen( self.text_color ) )
            text_rect = painter.boundingRect( current_x, current_y, space_width, self.key_height, Qt.AlignmentFlag.AlignCenter, "SPACE" )
            painter.drawText( text_rect, Qt.AlignmentFlag.AlignCenter, "SPACE" )
            self.adjustKeySizeFromWidgetSize()
            self.update()

        if self.selected:
            self.drawSelectionBorder( painter )
            self.drawSelectionHandles( painter )

    def draw3dEffect( self, painter, x, y, width, height, r ):
        painter.setPen( QPen( QColor( 255, 255, 255 ), 1 ) )
        painter.drawLine( x + r, y, x + width - r, y )
        painter.drawLine( x, y + r, x, y + height - r )
        
        painter.setPen( QPen( QColor( 0, 0, 0 ), 1 ) )
        painter.drawLine( x + r, y + height, x + width - r, y + height )
        painter.drawLine( x + width, y + r, x + width, y + height - r )

    def drawSelectionHandles( self, painter ):
        handle_size = 8
        half_size = handle_size // 2

        painter.setBrush( QColor( 255, 142, 62 ) )
        painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

        corners = [ QPoint( 4, 4 ), QPoint( self.width() - 4, 4 ), QPoint( 4, self.height() - 4 ), QPoint( self.width() - 4, self.height() - 4 ) ]

        for corner in corners:
            painter.drawEllipse( corner.x() - half_size, corner.y() - half_size, handle_size, handle_size )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( Qt.PenStyle.NoPen )
            painter.drawEllipse( corner.x() - 1, corner.y() - 1, 2, 2 )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )
    
    def drawSelectionBorder( self, painter ):
        border_rect = QRect( 0, 0, self.keys_width, self.keys_height )

        selection_pen = QPen( QColor( 255, 0, 0 ) )
        selection_pen.setWidth( 2 )
        selection_pen.setStyle( Qt.PenStyle.DashLine )
        selection_pen.setDashPattern( [ 4, 2 ] )

        painter.setPen( selection_pen )
        painter.setBrush( Qt.BrushStyle.NoBrush )
        painter.drawRect( border_rect )
    
    def handleResize( self, global_pos ):
        if not self.resize_corner:
            return

        delta = global_pos - self.resize_start_pos
        new_width = self.resize_start_size.width()
        new_height = self.resize_start_size.height()
        new_x = self.resize_start_position.x()
        new_y = self.resize_start_position.y() 

        if self.resize_corner == "bottom_right":
            new_width = max( 185, self.resize_start_size.width() + delta.x() )
            new_height = max( 80, self.resize_start_size.height() + delta.y() )

        elif self.resize_corner == "top_right":
            new_width = max( 185, self.resize_start_size.width() + delta.x() )
            new_height = max( 80, self.resize_start_size.height() - delta.y() )
            new_y = self.resize_start_position.y() + delta.y()

        elif self.resize_corner == "bottom_left":
            new_width = max( 185, self.resize_start_size.width() - delta.x() )
            new_height = max( 80, self.resize_start_size.height() + delta.y() ) 
            new_x = self.resize_start_position.x() + delta.x() 

        elif self.resize_corner == "top_left":
            new_width = max( 185, self.resize_start_size.width() - delta.x() )
            new_height = max( 80, self.resize_start_size.height() - delta.y() )
            new_x = self.resize_start_position.x() + delta.x() 
            new_y = self.resize_start_position.y() + delta.y() 

        self.setFixedSize( new_width, new_height )

        if self.resize_corner in [ "top_left", "bottom_left" ]:
            self.move( new_x, new_y )

        elif self.resize_corner == "top_right":
            self.move( self.x(), new_y )

        self.adjustKeySizeFromWidgetSize()
        self.update()
        self.updateKeysPropertiesSize()
        self.updateKeysPropertiesPosition()

    def getCornerAt( self, pos ):
        handle_size = 12
        half_size = handle_size // 2
        
        corners = {
            "top_left": QPoint( 0, 0 ),
            "top_right": QPoint( self.width(), 0 ),
            "bottom_left": QPoint( 0, self.height() ),
            "bottom_right": QPoint( self.width(), self.height() )
        }
        
        for corner_name, corner_pos in corners.items():
            corner_rect = QRect( corner_pos.x() - half_size, corner_pos.y() - half_size, handle_size, handle_size )
            
            if corner_rect.contains( pos ):
                return corner_name
        
        return None

    def calculateOptimalSize( self ):
        if self.key_type == "NUM":
            base_key_width = 30
            base_key_height = 30
            
            key_spacing_x = 2
            key_spacing_y = 1

            total_width = ( base_key_width * 3 ) + ( key_spacing_x * 2 )
            
            total_height = ( base_key_height * 4 ) + ( key_spacing_y * 3 )
            
            self.key_width = base_key_width
            self.key_height = base_key_height
            self.keys_width = total_width
            self.keys_height = total_height
            
        elif self.key_type == "QUERTZ":
            base_key_width = 25
            base_key_height = 25
            
            key_spacing_x = 4
            key_spacing_y = 4
            
            max_keys_per_row = 10
            total_width = ( base_key_width * max_keys_per_row ) + ( key_spacing_x * ( max_keys_per_row - 1 ) )
            
            total_height = ( base_key_height * 4 ) + ( key_spacing_y * 3 )
            
            self.key_width = base_key_width
            self.key_height = base_key_height
            self.keys_width = total_width
            self.keys_height = total_height
        
        self.setFixedSize( self.keys_width, self.keys_height )
    
    def adjustKeySizeFromWidgetSize( self ):
        if self.key_type == "NUM":
            available_width = self.keys_width
            available_height = self.keys_height
            
            key_width = max( 20, ( available_width - 4 ) // 3 )
            key_height = max( 20, ( available_height - 3 ) // 4 )
            
            self.key_width = key_width
            self.key_height = key_height
            
        elif self.key_type == "QUERTZ":
            available_width = self.keys_width
            available_height = self.keys_height
            
            key_width = max( 15, ( available_width - 36 ) // 10 )
            key_height = max( 15, ( available_height - 12 ) // 4 )
            
            self.key_width = key_width
            self.key_height = key_height
        
    def resizeEvent( self, event ):
        super().resizeEvent( event )
        
        self.keys_width = self.width()
        self.keys_height = self.height()
        
        self.adjustKeySizeFromWidgetSize()

    def setSelected( self, selected ):
        self.selected = selected
        self.update()
    
    def updateKeysPropertiesSize( self ):
        main_window = self.findMainWindow()
        if not main_window:
            return
        
        try:
            if ( hasattr( main_window, 'current_shape' ) and main_window.current_shape == self ):
                if hasattr( main_window, 'width_spin_keys' ):
                    main_window.width_spin_keys.blockSignals( True )
                    main_window.width_spin_keys.setValue( self.keys_width )
                    main_window.width_spin_keys.blockSignals( False )

                if hasattr( main_window, 'height_spin_keys' ):
                    main_window.height_spin_keys.blockSignals( True )
                    main_window.height_spin_keys.setValue( self.keys_height )
                    main_window.height_spin_keys.blockSignals( False )
        except:
            pass
    
    def updateKeysPropertiesPosition( self ):
        main_window = self.findMainWindow()
        if not main_window:
            return

        try:
            if ( hasattr( main_window, 'current_shape' ) and main_window.current_shape == self ):
                if hasattr( main_window, 'pos_x_spin_keys' ):
                    main_window.pos_x_spin_keys.blockSignals( True )
                    main_window.pos_x_spin_keys.setValue( self.x() )
                    main_window.pos_x_spin_keys.blockSignals( False )

                if hasattr( main_window, 'pos_y_spin_keys' ):
                    main_window.pos_y_spin_keys.blockSignals( True )
                    main_window.pos_y_spin_keys.setValue( self.y() )
                    main_window.pos_y_spin_keys.blockSignals( False )

        except:
            pass

    def setupDataDict( self ):
        self.data_dict = {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'position_x': self.x(),
            'position_y': self.y(),
            'keys_width': self.keys_width,
            'keys_height': self.keys_height,
            'gradient_start_color': self.gradient_start_color,
            'gradient_end_color': self.gradient_end_color,
            'effect_3d': self.effect_3d,
            'font_size': self.font_size,
            'font_color': self.text_color,

            'type': 'Keys',
            'id': None
        }
    
    def updateDataDict( self ):
        self.data_dict.update( {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'position_x': self.x(),
            'position_y': self.y(),
            'keys_width': self.keys_width,
            'keys_height': self.keys_height,
            'gradient_start_color': self.gradient_start_color,
            'gradient_end_color': self.gradient_end_color,
            'effect_3d': self.effect_3d,
            'keys_type': self.key_type,
            'font_size': self.font_size,
            'font_color': self.text_color
        } )
        return self.data_dict
    
    def getDataDict( self ):
        return self.updateDataDict()
    
    def setDataId( self, data_id ):
        self.data_dict[ 'id' ] = data_id

    def findMainWindow( self ):
        parent = self.parent()

        while parent:
            if isinstance( parent, QMainWindow ):
                return parent
            parent = parent.parent()

        return None

    def mousePressEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.findMainWindow()

            if main_window and hasattr( main_window, 'object_attached' ) and main_window.object_attached:
                event.ignore()
                return 

            mouse_pos = event.pos()

            self.resize_corner = self.getCornerAt( mouse_pos )

            if self.resize_corner:
                self.resizing = True
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_size = self.size()
                self.resize_start_position = self.pos() 

            else:
                self.dragging = True
                self.drag_start_pos = mouse_pos
                self.clicked.emit( self )

        event.accept()

    def mouseReleaseEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = False
            self.dragging = False
            self.resize_corner = None

            self.updateKeysPropertiesSize()
            self.updateKeysPropertiesPosition()

        self.updateDataDict()
        event.accept()
    
    def mouseMoveEvent( self, event ):
        mouse_pos = event.pos()

        corner = self.getCornerAt( mouse_pos )

        if corner:
            if corner in [ "top_left", "bottom_right" ]:
                self.setCursor( Qt.CursorShape.SizeFDiagCursor )

            elif corner in [ "top_right", "bottom_left" ]:
                self.setCursor( Qt.CursorShape.SizeBDiagCursor )

        else:
            self.setCursor( Qt.CursorShape.ArrowCursor )

        if self.resizing and event.buttons() & Qt.MouseButton.LeftButton:
            self.handleResize( event.globalPosition().toPoint() )

        elif self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            delta = mouse_pos - self.drag_start_pos

            new_x = self.x() + delta.x()
            new_y = self.y() + delta.y()

            super().move( new_x, new_y )

            self.updateKeysPropertiesPosition()

        event.accept()

class ClockWidget( QWidget ):
    clicked = pyqtSignal( object )
    
    def __init__( self, parent = None ):
        super().__init__( parent )

        self.defaultValues()
        self.setFixedSize( self.diameter, self.diameter )
        self.setMouseTracking( True )
        self.setFocusPolicy( Qt.FocusPolicy.StrongFocus )
        self.setupDataDict()
        
    def defaultValues( self ):
        self.active = True
        self.visible = True
        self.static = False
        self.custom_name = ""
        self.stack_order = 1
        self.center_x = 0
        self.center_y = 0
        self.diameter = 100
        self.background_color = QColor( 0, 0, 255 )
        self.face_color = QColor( 255, 0, 0 )
        self.effect_3d = True
        self.hours = 0
        self.minutes = 0
        self.seconds = 0

        self.selected = False
        self.resizing = False
        self.dragging = False
        self.resize_start_pos = QPoint()
        self.drag_start_pos = QPoint()
        self.resize_corner = None
        self.resize_start_diameter = 0

    def paintEvent( self, event ):
        if self.visible and self.active:
            self.background_color.setAlpha( 255 )
            self.face_color.setAlpha( 255 )

        else:
            self.background_color.setAlpha( 50 )
            self.face_color.setAlpha( 50 )

        painter = QPainter( self )
        painter.setRenderHint( QPainter.RenderHint.Antialiasing )

        center_x = self.width() // 2
        center_y = self.height() // 2
        
        scale_factor = self.diameter / 720.0
        
        base_line_width = max( 1, int( 3 * scale_factor ) )
        big_mark_width = max( 1, int( 23 * scale_factor ) )
        needle1_width = max( 1, int( 10 * scale_factor ) )
        needle2_width = max( 1, int( 18 * scale_factor ) )
        needle3_width = max( 1, int( 25 * scale_factor ) )

        radius = int( 360 * scale_factor )
        point_radius = int( 290 * scale_factor )

        needle1_length = int( 290 * scale_factor )
        needle2_length = int( 220 * scale_factor )
        needle3_length = int( 150 * scale_factor )

        pen = QPen( self.background_color )
        pen.setWidth( base_line_width )
        painter.setPen( pen )
        painter.setBrush( self.background_color )
        painter.drawEllipse( QPointF( center_x, center_y ), radius, radius )

        if self.effect_3d:
            pen = QPen( QColor( 255, 255, 255 ) )
            pen.setWidth( base_line_width )
            painter.setPen( pen )
            painter.drawArc( center_x - radius, center_y - radius, radius * 2, radius * 2, 16 * 35, - 16 * 175 )

            pen = QPen( QColor( 0, 0, 0 ) )
            pen.setWidth( base_line_width )
            painter.setPen( pen )
            painter.drawArc( center_x - radius, center_y - radius, radius * 2, radius * 2, 35 * 16, 16 * 185 ) 

        painter.translate( center_x, center_y )

        seconds_angle = ( self.seconds * 6 )
        minutes_angle = ( self.minutes * 6 ) + ( self.seconds * 0.1 )
        hours_angle = ( ( self.hours % 12 ) * 30 ) + ( self.minutes * 0.5 )

        big_pen = QPen( self.face_color )
        big_pen.setWidth( big_mark_width )
        painter.setPen( big_pen )
        painter.rotate( - 180 )

        for i in range( 12 ):
            painter.drawPoint( 0, - point_radius )
            painter.rotate( 30 )

        painter.rotate( - 360 + 180 )

        painter.rotate( hours_angle )
        needle_pen = QPen( self.face_color )
        needle_pen.setWidth( needle3_width )
        painter.setPen( needle_pen )
        painter.drawLine( 0, 0, 0, - needle3_length )
        painter.rotate( - hours_angle )

        painter.rotate( minutes_angle )
        needle_pen.setWidth( needle2_width )
        painter.setPen( needle_pen )
        painter.drawLine( 0, 0, 0, - needle2_length )
        painter.rotate( - minutes_angle )

        painter.rotate( seconds_angle )
        needle_pen.setWidth( needle1_width )
        painter.setPen( needle_pen )
        painter.drawLine( 0, 0, 0, - needle1_length )

        if self.selected:
            painter.resetTransform()
            self.drawSelectionBorder( painter )
            self.drawSelectionHandles( painter )

    def drawSelectionHandles( self, painter ):
        handle_size = 8
        half_size = handle_size // 2

        painter.setBrush( QColor( 255, 142, 62 ) )
        painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

        corners = [ QPoint( 4, 4 ), QPoint( self.width() - 4, 4 ), QPoint( 4, self.height() - 4 ), QPoint( self.width() - 4, self.height() - 4 ) ]

        for point in corners:
            painter.drawEllipse( point.x() - half_size, point.y() - half_size, handle_size, handle_size )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( Qt.PenStyle.NoPen )
            painter.drawEllipse( point.x() - 1, point.y() - 1, 2, 2 )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

    def drawSelectionBorder( self, painter ):
        selection_rect = QRectF( 0, 0, self.width(), self.height() )
        
        selection_pen = QPen( QColor( 255, 0, 0 ) )
        selection_pen.setWidth( 2 )
        selection_pen.setStyle( Qt.PenStyle.DashLine )
        selection_pen.setDashPattern( [ 4, 2 ] )
        
        painter.setPen( selection_pen )
        painter.setBrush( Qt.BrushStyle.NoBrush )
        painter.drawRect( selection_rect )

    def handleResize( self, global_pos ):
        if not self.resize_corner:
            return

        delta = global_pos - self.resize_start_pos
        new_diameter = self.resize_start_diameter

        if "right" in self.resize_corner:
            new_diameter = max( 10, self.resize_start_diameter + 2 * delta.x() )

        elif "left" in self.resize_corner:
            new_diameter = max( 10, self.resize_start_diameter - 2 * delta.x() )

        elif "top" in self.resize_corner:
            new_diameter = max( 10, self.resize_start_diameter - 2 * delta.y() )

        elif "bottom" in self.resize_corner:
            new_diameter = max( 10, self.resize_start_diameter + 2 * delta.y() )

        old_center_x = self.x() + self.diameter // 2
        old_center_y = self.y() + self.diameter // 2

        self.diameter = new_diameter
        self.setFixedSize( new_diameter, new_diameter )

        new_x = old_center_x - new_diameter // 2
        new_y = old_center_y - new_diameter // 2
        self.move( new_x, new_y )

        self.updateCenterPosition()
        self.updateClockPropertiesSize()
        self.updateClockCenterPositionProperties()
        self.update()

    def getCornerAt( self, pos ):
        handle_size = 16 
        half_size = handle_size // 2
        
        corners = {
            "top_left": QPoint( 0, 0 ),
            "top_right": QPoint( self.width(), 0 ),
            "bottom_left": QPoint( 0, self.height() ),
            "bottom_right": QPoint( self.width(), self.height() )
        }
        
        for corner_name, corner_pos in corners.items():
            corner_rect = QRect( corner_pos.x() - half_size, corner_pos.y() - half_size, handle_size, handle_size )
            
            if corner_rect.contains( pos ):
                return corner_name
        
        return None

    def setSelected( self, selected ):
        self.selected = selected
        self.update()
    
    def updateCenterPosition( self ):
        self.center_x = self.x() + self.diameter // 2
        self.center_y = self.y() + self.diameter // 2

    def updateClockPropertiesSize( self ):
        main_window = self.findMainWindow()

        if not main_window:
            return

        try:
            if ( hasattr( main_window, 'current_shape' ) and main_window.current_shape == self and hasattr( main_window, 'diameter_spin_clock' )  ):
                
                main_window.diameter_spin_clock.blockSignals( True )
                main_window.diameter_spin_clock.setValue( self.diameter )
                main_window.diameter_spin_clock.blockSignals( False )

        except:
            pass

    def updateClockCenterPositionProperties( self ):
        main_window = self.findMainWindow()

        if not main_window:
            return

        self.updateCenterPosition()

        try:
            if ( hasattr( main_window, 'current_shape' ) and main_window.current_shape == self ):
                
                if hasattr( main_window, 'pos_x_spin_clock' ):
                    main_window.pos_x_spin_clock.blockSignals( True )
                    main_window.pos_x_spin_clock.setValue( self.center_x )
                    main_window.pos_x_spin_clock.blockSignals( False )

                if hasattr( main_window, 'pos_y_spin_clock' ):
                    main_window.pos_y_spin_clock.blockSignals( True )
                    main_window.pos_y_spin_clock.setValue( self.center_y )
                    main_window.pos_y_spin_clock.blockSignals( False )

        except:
            pass

    def setupDataDict( self ):
        self.updateCenterPosition() 
        
        self.data_dict = {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'center_x': self.center_x,
            'center_y': self.center_y,
            'diameter': self.diameter,
            'background_color': self.background_color,
            'face_color': self.face_color,
            'effect_3d': self.effect_3d,
            'hours': self.hours,
            'minutes': self.minutes,
            'seconds': self.seconds,
            'type': 'Clock',
            'id': None
        }
    
    def updateDataDict( self ):
        self.updateCenterPosition()
        
        self.data_dict.update( {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'center_x': self.center_x,
            'center_y': self.center_y,
            'diameter': self.diameter,
            'background_color': self.background_color,
            'face_color': self.face_color,
            'effect_3d': self.effect_3d,
            'hours': self.hours,
            'minutes': self.minutes,
            'seconds': self.seconds
        } )
        return self.data_dict
    
    def getDataDict( self ):
        return self.updateDataDict()
    
    def setDataId( self, data_id ):
        self.data_dict[ 'id' ] = data_id

    def move( self, x, y ):
        super().move( x, y )
        self.updateCenterPosition()

    def setGeometry( self, x, y, width, height ):
        super().setGeometry( x, y, width, height )
        self.updateCenterPosition()

    def findMainWindow( self ):
        parent = self.parent()

        while parent:
            if isinstance( parent, QMainWindow ):

                return parent
            
            parent = parent.parent()

        return None

    def mousePressEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.findMainWindow()

            if main_window and hasattr( main_window, 'object_attached' ) and main_window.object_attached:
                event.ignore()
                return

            mouse_pos = event.pos()
            self.resize_corner = self.getCornerAt( mouse_pos )

            if self.resize_corner:
                self.resizing = True
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_diameter = self.diameter

            else:
                self.dragging = True
                self.drag_start_pos = mouse_pos
                self.clicked.emit( self )

            self.updateClockCenterPositionProperties()
            event.accept()

    def mouseReleaseEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = False
            self.dragging = False
            self.resize_corner = None
            
            self.updateClockPropertiesSize()
            self.updateClockCenterPositionProperties()
            self.updateDataDict()

        event.accept()

    def mouseMoveEvent( self, event ):
        mouse_pos = event.pos()
        corner = self.getCornerAt( mouse_pos )

        if corner:
            if corner in [ "top_left", "bottom_right" ]:
                self.setCursor( Qt.CursorShape.SizeFDiagCursor )

            elif corner in [ "top_right", "bottom_left" ]:
                self.setCursor( Qt.CursorShape.SizeBDiagCursor )

        else:
            self.setCursor( Qt.CursorShape.ArrowCursor )

        if self.resizing and event.buttons() & Qt.MouseButton.LeftButton:
            self.handleResize( event.globalPosition().toPoint() )

        elif self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            delta = mouse_pos - self.drag_start_pos
            new_x = self.x() + delta.x()
            new_y = self.y() + delta.y()
            self.move( new_x, new_y )
            self.updateClockCenterPositionProperties()
            self.updateDataDict()

        event.accept()

class GaugeWidget( QWidget ):
    clicked = pyqtSignal( object )
    
    def __init__( self, parent = None ):
        super().__init__( parent )

        self.defaultValues()
        self.setFixedSize( self.diameter, self.diameter )
        self.setMouseTracking( True )
        self.setFocusPolicy( Qt.FocusPolicy.StrongFocus )
        self.setupDataDict()
        
    def defaultValues( self ):
        self.active = True
        self.visible = True
        self.static = False
        self.custom_name = ""
        self.stack_order = 1
        self.center_x = 0
        self.center_y = 0
        self.diameter = 100
        self.background_color = QColor( 0, 0, 255 )
        self.face_color = QColor( 255, 0, 0 )
        self.effect_3d = True
        self.major_subdivision = 6
        self.minor_subdivision = 4
        self.range_value = 100
        self.value = 50

        self.selected = False
        self.resizing = False
        self.dragging = False
        self.resize_start_pos = QPoint()
        self.drag_start_pos = QPoint()
        self.resize_corner = None
        self.resize_start_diameter = 0

    def paintEvent( self, event ):
        if self.visible and self.active:
            self.background_color.setAlpha( 255 )
            self.face_color.setAlpha( 255 )

        else:
            self.background_color.setAlpha( 50 )
            self.face_color.setAlpha( 50 )

        painter = QPainter( self )
        painter.setRenderHint( QPainter.RenderHint.Antialiasing )
        
        scale_factor = self.diameter / 500.0
        
        base_line_width = max( 1, int( 3 * scale_factor ) )
        big_mark_width = max( 1, int( 12 * scale_factor ) )
        small_mark_width = max( 1, int( 5 * scale_factor ) )
        needle_width = max( 1, int( 10 * scale_factor ) )
        
        pen = QPen( self.background_color )
        pen.setWidth( base_line_width )
        painter.setPen( pen )
        painter.setBrush( self.background_color )
        painter.drawEllipse( 0, 0, self.diameter, self.diameter )
        
        if self.effect_3d:
            pen = QPen( QColor( 255, 255, 255 ) )
            pen.setWidth( base_line_width )
            painter.setPen( pen )
            painter.drawArc( 0, 0, self.diameter, self.diameter, 16 * 35, - 16 * 175 )

            pen = QPen( QColor( 0, 0, 0 ) )
            pen.setWidth( base_line_width )
            painter.setPen( pen )
            painter.drawArc( 0, 0, self.diameter, self.diameter, 35 * 16, 16 * 185 )
        
        painter.translate( self.diameter // 2, self.diameter // 2 )
        
        total_divisions = self.major_subdivision * self.minor_subdivision
        angle_per_division = 270.0 / total_divisions
        
        painter.rotate( - 135 )

        big_mark_start = int( - 210 * scale_factor )
        big_mark_end = int( - 190 * scale_factor )
        
        small_mark_start = int( - 205 * scale_factor )
        small_mark_end = int( - 195 * scale_factor )
        
        needle_length = int( - 210 * scale_factor )

        for i in range( total_divisions + 1 ):
            if i % self.minor_subdivision == 0:
                big_pen = QPen( self.face_color )
                big_pen.setWidth( big_mark_width )
                painter.setPen( big_pen )
                painter.drawLine( 0, big_mark_start, 0, big_mark_end )
            else:
                small_pen = QPen( self.face_color )
                small_pen.setWidth( small_mark_width )
                painter.setPen( small_pen )
                painter.drawLine( 0, small_mark_start, 0, small_mark_end )
            
            if i < total_divisions:
                painter.rotate( angle_per_division )

        painter.rotate(- ( total_divisions * angle_per_division ) )

        if self.range_value > 0:
            needle_angle = ( 270 * self.value / self.range_value )

        else:
            needle_angle = - 135

        painter.rotate( needle_angle )
        needle_pen = QPen( self.face_color )
        needle_pen.setWidth( needle_width )
        painter.setPen( needle_pen )
        painter.drawLine( 0, 0, 0, needle_length )

        if self.selected:
            painter.resetTransform()
            self.drawSelectionBorder( painter )
            self.drawSelectionHandles( painter )

    def drawSelectionHandles( self, painter ):
        handle_size = 8
        half_size = handle_size // 2

        painter.setBrush( QColor( 255, 142, 62 ) )
        painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

        corners = [ QPoint( 4, 4 ), QPoint( self.width() - 4, 4 ), QPoint( 4, self.height() - 4 ), QPoint( self.width() - 4, self.height() - 4 ) ]

        for point in corners:
            painter.drawEllipse( point.x() - half_size, point.y() - half_size, handle_size, handle_size )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( Qt.PenStyle.NoPen )
            painter.drawEllipse( point.x() - 1, point.y() - 1, 2, 2 )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

    def drawSelectionBorder( self, painter ):
        selection_rect = QRectF( 0, 0, self.width(), self.height() )
        
        selection_pen = QPen( QColor( 255, 0, 0 ) )
        selection_pen.setWidth( 2 )
        selection_pen.setStyle( Qt.PenStyle.DashLine )
        selection_pen.setDashPattern( [ 4, 2 ] )
        
        painter.setPen( selection_pen )
        painter.setBrush( Qt.BrushStyle.NoBrush )
        painter.drawRect( selection_rect )

    def handleResize( self, global_pos ):
        if not self.resize_corner:
            return

        delta = global_pos - self.resize_start_pos
        new_diameter = self.resize_start_diameter

        if "right" in self.resize_corner:
            new_diameter = max( 10, self.resize_start_diameter + 2 * delta.x() )

        elif "left" in self.resize_corner:
            new_diameter = max( 10, self.resize_start_diameter - 2 * delta.x() )

        elif "top" in self.resize_corner:
            new_diameter = max( 10, self.resize_start_diameter - 2 * delta.y() )

        elif "bottom" in self.resize_corner:
            new_diameter = max( 10, self.resize_start_diameter + 2 * delta.y() )

        old_center_x = self.x() + self.diameter // 2
        old_center_y = self.y() + self.diameter // 2

        self.diameter = new_diameter
        self.setFixedSize( new_diameter, new_diameter )

        new_x = old_center_x - new_diameter // 2
        new_y = old_center_y - new_diameter // 2
        self.move( new_x, new_y )

        self.updateCenterPosition()
        self.updateGaugePropertiesSize()
        self.updateGaugeCenterPositionProperties()
        self.update()

    def getCornerAt( self, pos ):
        handle_size = 16 
        half_size = handle_size // 2
        
        corners = {
            "top_left": QPoint( 0, 0 ),
            "top_right": QPoint( self.width(), 0 ),
            "bottom_left": QPoint( 0, self.height() ),
            "bottom_right": QPoint( self.width(), self.height() )
        }
        
        for corner_name, corner_pos in corners.items():
            corner_rect = QRect( corner_pos.x() - half_size, corner_pos.y() - half_size, handle_size, handle_size )
            
            if corner_rect.contains( pos ):
                return corner_name
        
        return None

    def setSelected( self, selected ):
        self.selected = selected
        self.update()
    
    def updateCenterPosition( self ):
        self.center_x = self.x() + self.diameter // 2
        self.center_y = self.y() + self.diameter // 2

    def updateGaugePropertiesSize( self ):
        main_window = self.findMainWindow()

        if not main_window:
            return

        try:
            if ( hasattr( main_window, 'current_shape' ) and main_window.current_shape == self and hasattr( main_window, 'diameter_spin_gauge' ) ):
                main_window.diameter_spin_gauge.blockSignals( True )
                main_window.diameter_spin_gauge.setValue( self.diameter )
                main_window.diameter_spin_gauge.blockSignals( False )

        except:
            pass

    def updateGaugeCenterPositionProperties( self ):
        main_window = self.findMainWindow()

        if not main_window:
            return

        self.updateCenterPosition()

        try:
            if ( hasattr( main_window, 'current_shape' ) and main_window.current_shape == self ):
                if hasattr( main_window, 'pos_x_spin_gauge' ):
                    main_window.pos_x_spin_gauge.blockSignals( True )
                    main_window.pos_x_spin_gauge.setValue( self.center_x )
                    main_window.pos_x_spin_gauge.blockSignals( False )

                if hasattr( main_window, 'pos_y_spin_gauge' ):
                    main_window.pos_y_spin_gauge.blockSignals( True )
                    main_window.pos_y_spin_gauge.setValue( self.center_y )
                    main_window.pos_y_spin_gauge.blockSignals( False )

        except:
            pass

    def setupDataDict( self ):
        self.updateCenterPosition() 
        
        self.data_dict = {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'center_x': self.center_x,
            'center_y': self.center_y,
            'diameter': self.diameter,
            'background_color': self.background_color,
            'face_color': self.face_color,
            'effect_3d': self.effect_3d,
            'major_subdivision': self.major_subdivision,
            'minor_subdivision': self.minor_subdivision,
            'range': self.range_value,
            'value': self.value,
            'type': 'Gauge',
            'id': None
        }
    
    def updateDataDict( self ):
        self.updateCenterPosition() 
        
        self.data_dict.update( {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'center_x': self.center_x,
            'center_y': self.center_y,
            'diameter': self.diameter,
            'background_color': self.background_color,
            'face_color': self.face_color,
            'effect_3d': self.effect_3d,
            'major_subdivision': self.major_subdivision,
            'minor_subdivision': self.minor_subdivision,
            'range': self.range_value,
            'value': self.value
        } )
        return self.data_dict
    
    def getDataDict( self ):
        return self.updateDataDict()
    
    def setDataId( self, data_id ):
        self.data_dict[ 'id' ] = data_id

    def move( self, x, y ):
        super().move( x, y )
        self.updateCenterPosition()

    def setGeometry( self, x, y, width, height ):
        super().setGeometry( x, y, width, height )
        self.updateCenterPosition()

    def findMainWindow( self ):
        parent = self.parent()

        while parent:
            if isinstance( parent, QMainWindow ):
                return parent
            
            parent = parent.parent()

        return None

    def mousePressEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.findMainWindow()

            if main_window and hasattr( main_window, 'object_attached' ) and main_window.object_attached:
                event.ignore()
                return

            mouse_pos = event.pos()
            self.resize_corner = self.getCornerAt( mouse_pos )

            if self.resize_corner:
                self.resizing = True
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_diameter = self.diameter

            else:
                self.dragging = True
                self.drag_start_pos = mouse_pos
                self.clicked.emit( self )

            self.updateGaugeCenterPositionProperties()
            event.accept()

    def mouseReleaseEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = False
            self.dragging = False
            self.resize_corner = None
            
            self.updateGaugePropertiesSize()
            self.updateGaugeCenterPositionProperties()
            self.updateDataDict()

        event.accept()

    def mouseMoveEvent( self, event ):
        mouse_pos = event.pos()
        corner = self.getCornerAt( mouse_pos )

        if corner:
            if corner in [ "top_left", "bottom_right" ]:
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)

            elif corner in [ "top_right", "bottom_left" ]:
                self.setCursor( Qt.CursorShape.SizeBDiagCursor )
        else:
            self.setCursor( Qt.CursorShape.ArrowCursor )

        if self.resizing and event.buttons() & Qt.MouseButton.LeftButton:
            self.handleResize( event.globalPosition().toPoint() )

        elif self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            delta = mouse_pos - self.drag_start_pos
            new_x = self.x() + delta.x()
            new_y = self.y() + delta.y()
            self.move( new_x, new_y )
            self.updateGaugeCenterPositionProperties()
            self.updateDataDict()

        event.accept()

class DialWidget( QWidget ):
    clicked = pyqtSignal( object )
    
    def __init__( self, parent = None ):
        super().__init__( parent )
        
        self.defaultValues()
        self.setFixedSize( self.diameter, self.diameter )
        self.setMouseTracking( True )
        self.setFocusPolicy( Qt.FocusPolicy.StrongFocus )
        self.setupDataDict()
        
    def defaultValues( self ):
        self.active = True
        self.visible = True
        self.static = False
        self.custom_name = ""
        self.stack_order = 1
        self.tag = 0
        self.center_x = 0
        self.center_y = 0
        self.diameter = 80
        self.background_color = QColor( 0, 0, 255 )
        self.pointer_color = QColor( 255, 255, 255 )
        self.effect_3d = True
        self.value = 50

        self.selected = False
        self.resizing = False
        self.dragging = False
        self.value_changing = False
        self.resize_start_pos = QPoint()
        self.resize_start_diameter = 0
        self.resize_corner = None
        self.drag_start_pos = QPoint()

    def paintEvent( self, event ):
        if self.visible and self.active:
            self.background_color.setAlpha( 255 )
            self.pointer_color.setAlpha( 255 )

        else:
            self.background_color.setAlpha( 50 )
            self.pointer_color.setAlpha( 50 )

        painter = QPainter( self )
        painter.setRenderHint( QPainter.RenderHint.Antialiasing )
        
        r = self.diameter
        scale_factor = self.diameter / 100.0
        
        base_line_width = max( 1, int( r / 100 ) )
        arc_line_width = max( 1, int( 3 * scale_factor ) )
        line_width = max( 1, int( 3 * scale_factor ) )
        
        margin = 3
        adjusted_r = r - 2 * margin

        if self.effect_3d:
            pen = QPen( QColor( 0, 0, 0 ) )
            pen.setWidth( arc_line_width )
            painter.setPen( pen )
            painter.drawArc( margin, margin, adjusted_r, adjusted_r, 16 * 35, - 16 * 175 )
    
            pen = QPen( QColor( 255, 255, 255 ) )
            pen.setWidth( line_width )
            painter.setPen( pen )
            painter.drawArc( margin, margin, adjusted_r, adjusted_r, 35 * 16, 16 * 185 )
        
        pen = QPen( self.background_color )
        pen.setWidth( base_line_width )
        painter.setPen( pen )
        painter.setBrush( self.background_color )
        painter.drawEllipse( margin, margin, adjusted_r, adjusted_r )
        
        pen = QPen( self.pointer_color )
        pen.setWidth( max( 1, int( 4 * scale_factor ) ) )
        painter.setPen(pen)

        center_x = margin + adjusted_r // 2
        center_y = margin + adjusted_r // 2

        radius = adjusted_r // 2 - 10

        start_radius_percentage = 0.70
        start_radius = radius * start_radius_percentage

        angle = 90 + ( 360 * self.value / 100 )
        if angle > 360:
            angle -= 360
        
        angle_rad = math.radians( angle )
    
        start_x =  math.ceil ( center_x + start_radius * math.cos( angle_rad ) )
        start_y = math.ceil ( center_y + start_radius * math.sin( angle_rad ) )
    
        end_x = math.ceil ( center_x + radius * math.cos( angle_rad ) )
        end_y = math.ceil ( center_y + radius * math.sin( angle_rad ) )
    
        painter.drawLine( int( start_x ), int( start_y ), int( end_x ), int( end_y ) )
    
        if self.selected:
            self.drawSelectionBorder( painter )
            self.drawSelectionHandles( painter )

    def drawSelectionHandles( self, painter ):
        handle_size = 8
        half_size = handle_size // 2

        painter.setBrush( QColor( 255, 142, 62 ) )
        painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

        corners = [ QPoint( 4, 4 ), QPoint( self.width() - 4, 4 ), QPoint( 4, self.height() - 4 ), QPoint( self.width() - 4, self.height() - 4 ) ]

        for point in corners:
            painter.drawEllipse( point.x() - half_size, point.y() - half_size, handle_size, handle_size )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( Qt.PenStyle.NoPen )
            painter.drawEllipse( point.x() - 1, point.y() - 1, 2, 2 )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

    def drawSelectionBorder( self, painter ):
        selection_rect = QRectF( 0, 0, self.width(), self.height() )
        
        selection_pen = QPen( QColor( 255, 0, 0 ) )
        selection_pen.setWidth( 2 )
        selection_pen.setStyle( Qt.PenStyle.DashLine )
        selection_pen.setDashPattern( [ 4, 2 ] )
        
        painter.setPen( selection_pen )
        painter.setBrush( Qt.BrushStyle.NoBrush )
        painter.drawRect( selection_rect )

    def calculateValueFromPosition( self, pos ):
        margin = 3
        adjusted_r = self.diameter - 2 * margin

        center_x = margin + adjusted_r // 2
        center_y = margin + adjusted_r // 2

        dx = pos.x() - center_x
        dy = pos.y() - center_y

        if dx == 0 and dy == 0:
            return self.value

        angle_rad = math.atan2( dy, dx )
        angle_deg = math.degrees( angle_rad )

        if angle_deg < 0:
            angle_deg += 360

        angle_from_down = ( angle_deg - 90 ) % 360

        value = ( angle_from_down / 360.0 ) * 100
        value = max( 0, min( 100, value ) )

        return int( value )

    def handleResize( self, global_pos ):
        if not self.resize_corner:
            return

        delta = global_pos - self.resize_start_pos
        new_diameter = self.resize_start_diameter

        if "right" in self.resize_corner:
            new_diameter = max( 10, self.resize_start_diameter + 2 * delta.x() )

        elif "left" in self.resize_corner:
            new_diameter = max( 10, self.resize_start_diameter - 2 * delta.x() )

        elif "top" in self.resize_corner:
            new_diameter = max( 10, self.resize_start_diameter - 2 * delta.y() )

        elif "bottom" in self.resize_corner:
            new_diameter = max( 10, self.resize_start_diameter + 2 * delta.y() )

        old_center_x = self.x() + self.diameter // 2
        old_center_y = self.y() + self.diameter // 2

        self.diameter = new_diameter
        self.setFixedSize( new_diameter, new_diameter )

        new_x = old_center_x - new_diameter // 2
        new_y = old_center_y - new_diameter // 2
        self.move( new_x, new_y )

        self.updateCenterPosition()
        self.updateDialPropertiesSize()
        self.updateDialCenterPositionProperties()
        self.update()

    def getCornerAt( self, pos ):
        handle_size = 16 
        half_size = handle_size // 2
        
        corners = {
            "top_left": QPoint( 0, 0 ),
            "top_right": QPoint( self.width(), 0 ),
            "bottom_left": QPoint( 0, self.height() ),
            "bottom_right": QPoint( self.width(), self.height() )
        }
        
        for corner_name, corner_pos in corners.items():
            corner_rect = QRect( corner_pos.x() - half_size, corner_pos.y() - half_size, handle_size, handle_size )
            
            if corner_rect.contains( pos ):
                return corner_name
        
        return None

    def isPointOnDial( self, pos ):
        margin = 3
        adjusted_r = self.diameter - 2 * margin
        
        center_x = margin + adjusted_r // 2
        center_y = margin + adjusted_r // 2
        
        radius = adjusted_r // 2
        
        dx = pos.x() - center_x
        dy = pos.y() - center_y
        distance = math.sqrt( dx * dx + dy * dy )
        
        return distance <= radius

    def setSelected( self, selected ):
        self.selected = selected
        self.update()
    
    def updateCenterPosition (self ):
        self.center_x = self.x() + self.diameter // 2
        self.center_y = self.y() + self.diameter // 2

    def updateDialPropertiesSize( self ):
        main_window = self.findMainWindow()

        if not main_window:
            return

        try:
            if ( hasattr( main_window, 'current_shape' ) and  main_window.current_shape == self and hasattr( main_window, 'diameter_spin_dial' ) ):
                
                main_window.diameter_spin_dial.blockSignals( True )
                main_window.diameter_spin_dial.setValue( self.diameter )
                main_window.diameter_spin_dial.blockSignals( False )

        except:
            pass

    def updateDialCenterPositionProperties( self ):
        main_window = self.findMainWindow()

        if not main_window:
            return

        self.updateCenterPosition()

        try:
            if ( hasattr( main_window, 'current_shape' ) and main_window.current_shape == self ):
                if hasattr( main_window, 'pos_x_spin_dial' ):
                    main_window.pos_x_spin_dial.blockSignals( True )
                    main_window.pos_x_spin_dial.setValue( self.center_x )
                    main_window.pos_x_spin_dial.blockSignals( False )

                if hasattr( main_window, 'pos_y_spin_dial' ):
                    main_window.pos_y_spin_dial.blockSignals( True )
                    main_window.pos_y_spin_dial.setValue( self.center_y )
                    main_window.pos_y_spin_dial.blockSignals( False )

        except:
            pass
    
    def updateValueProperty( self ):
        main_window = self.findMainWindow()

        if not main_window:
            return

        try:
            if hasattr( main_window, 'value_spin_dial' ) and main_window.value_spin_dial:
                main_window.value_spin_dial.blockSignals( True )
                main_window.value_spin_dial.setValue( self.value )
                main_window.value_spin_dial.blockSignals( False )
        
        except:
            pass

    def setupDataDict( self ):
        self.updateCenterPosition()
        
        self.data_dict = {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'tag': self.tag,
            'center_x': self.center_x,
            'center_y': self.center_y,
            'diameter': self.diameter,
            'background_color': self.background_color,
            'pointer_color': self.pointer_color,
            'effect_3d': self.effect_3d,
            'value': self.value,
            'type': 'Dial',
            'id': None
        }
    
    def updateDataDict( self ):
        self.updateCenterPosition() 
        
        self.data_dict.update( {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'tag': self.tag,
            'center_x': self.center_x,
            'center_y': self.center_y,
            'diameter': self.diameter,
            'background_color': self.background_color,
            'pointer_color': self.pointer_color,
            'effect_3d': self.effect_3d,
            'value': self.value
        } )
        return self.data_dict
    
    def getDataDict( self ):
        return self.updateDataDict()
    
    def setDataId( self, data_id ):
        self.data_dict[ 'id' ] = data_id

    def move( self, x, y ):
        super().move( x, y )
        self.updateCenterPosition()

    def setGeometry( self, x, y, width, height ):
        super().setGeometry( x, y, width, height )
        self.updateCenterPosition()

    def findMainWindow( self ):
        parent = self.parent()

        while parent:
            if isinstance( parent, QMainWindow ):
                return parent
            parent = parent.parent()

        return None

    def mousePressEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.findMainWindow()

            if main_window and hasattr(main_window, 'object_attached') and main_window.object_attached:
                event.ignore()
                return

            mouse_pos = event.pos()
            self.resize_corner = self.getCornerAt( mouse_pos )

            if self.resize_corner:
                self.resizing = True
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_diameter = self.diameter

            elif self.isPointOnDial( mouse_pos ):
                self.value_changing = True
                new_value = self.calculateValueFromPosition( mouse_pos )

                if new_value != self.value:
                    self.value = new_value
                    self.update()
                    self.updateValueProperty()

                self.clicked.emit( self )
                event.accept()
                return

            else:
                self.dragging = True
                self.drag_start_pos = mouse_pos
                self.clicked.emit( self )

            self.updateDialCenterPositionProperties()
            event.accept()

    def mouseReleaseEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = False
            self.dragging = False
            self.value_changing = False
            self.resize_corner = None
            
            self.updateDialPropertiesSize()
            self.updateDialCenterPositionProperties()
            self.updateDataDict()

        event.accept()

    def mouseMoveEvent( self, event ):
        mouse_pos = event.pos()

        corner = self.getCornerAt( mouse_pos )

        if corner:
            if corner in [ "top_left", "bottom_right"  ]:
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)

            elif corner in [ "top_right", "bottom_left" ]:
                self.setCursor( Qt.CursorShape.SizeBDiagCursor )

        else:
            self.setCursor( Qt.CursorShape.ArrowCursor )

        if self.resizing and event.buttons() & Qt.MouseButton.LeftButton:
            self.handleResize( event.globalPosition().toPoint() )

        elif self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            delta = mouse_pos - self.drag_start_pos
            new_x = self.x() + delta.x()
            new_y = self.y() + delta.y()
            self.move( new_x, new_y )
            self.updateDialCenterPositionProperties()
            self.updateDataDict()

        elif self.value_changing and event.buttons() & Qt.MouseButton.LeftButton:
            new_value = self.calculateValueFromPosition( mouse_pos )

            if new_value != self.value:
                self.value = new_value
                self.update()
                self.updateValueProperty()
                self.updateDataDict()

        event.accept()

class ToggleWidget( QWidget ):
    clicked = pyqtSignal( object )
    
    def __init__( self, parent = None ):
        super().__init__( parent )

        self.defaultValues()
        self.setFixedSize( self.toggle_width, self.toggle_height )
        self.setMouseTracking( True )
        self.setFocusPolicy( Qt.FocusPolicy.StrongFocus )
        self.setupDataDict()
        
    def defaultValues( self ):
        self.active = True
        self.visible = True
        self.static = False
        self.custom_name = ""
        self.stack_order = 1
        self.tag = 0
        self.toggle_width = 80
        self.toggle_height = 30
        self.thumb_color = QColor( 255, 0, 0 )
        self.background_color = QColor( 0, 0, 255 )
        self.text_color = QColor( 255, 255, 255 )
        self.effect_3d = True
        self.state = True

        self.selected = False
        self.resizing = False
        self.dragging = False
        self.resize_start_pos = QPoint()
        self.drag_start_pos = QPoint()
        self.resize_corner = None
        self.resize_start_size = QSize()
        self.resize_start_position = QPoint()

    def paintEvent( self, event ):
        if self.visible and self.active:
            self.thumb_color.setAlpha( 255 )
            self.background_color.setAlpha( 255 )
            self.text_color.setAlpha( 255 )

        else:
            self.thumb_color.setAlpha( 50 )
            self.background_color.setAlpha( 50 )
            self.text_color.setAlpha( 50 )

        painter = QPainter( self )
        painter.setRenderHint( QPainter.RenderHint.Antialiasing )
        
        
        pen = QPen( self.background_color )
        painter.setPen( pen )
        painter.setBrush( self.background_color )
        
        radius = self.toggle_height // 2
        
        painter.drawRect( radius, 0, self.toggle_width - 2 * radius, self.toggle_height )
        painter.drawPie( 0, 0, 2 * radius, 2 * radius, 90 * 16, 180 * 16 )
        painter.drawPie( self.toggle_width - 2 * radius, 0, 2 * radius, 2 * radius, 90 * 16, - 180 * 16 )
        
        thumb_height = self.toggle_height - 5
        thumb_width = thumb_height
        
        if self.state:
            thumb_x = self.toggle_width - thumb_width - 2

        else:
            thumb_x = 2
            
        thumb_y = 3
        thumb_rect = QRect( thumb_x, thumb_y, thumb_width, thumb_height )

        pen = QPen( self.thumb_color )
        painter.setPen( pen )
        painter.setBrush( self.thumb_color )
        
        painter.drawEllipse( thumb_rect )
        
        font = QFont()
        font_size = max( 8, self.toggle_height // 2 )
        font.setPointSize( font_size )
        painter.setFont( font )
        painter.setPen( QColor( 255, 255, 255 )  )

        if self.effect_3d:
            pen = QPen( QColor( 255, 255, 255 ) )
            pen.setWidth( 1 )
            painter.setPen( pen )
            radius = self.toggle_height // 2
            
            painter.drawLine( radius, self.toggle_height, self.toggle_width - radius, self.toggle_height )
            painter.drawArc( self.toggle_width - 2 * radius, 0, 2 * radius, 2 * radius, 45 * 16, - 135 * 16 )
            painter.drawArc( 0, 0, 2 * radius, 2 * radius, 225 * 16, 45 * 16 )
            painter.drawArc( thumb_rect, 45 * 16, 135 * 16 )
            
            pen = QPen( QColor( 0, 0, 0 )  )
            pen.setWidth( 1 )
            painter.setPen( pen )

            painter.drawLine( radius, 0, self.toggle_width - radius, 0 )
            painter.drawArc( 0, 0, 2 * radius, 2 * radius, 90 * 16, 135 * 16 )
            painter.drawArc( self.toggle_width - 2 * radius, 0, 2 * radius, 2 * radius, 90 * 16, - 45 * 16 )
            painter.drawArc( thumb_rect, 45 * 16, - 135 * 16  )

        pen = QPen( self.text_color )
        pen.setWidth( 1 )
        painter.setPen( pen )

        if self.state:
            text_rect = QRect( 10, 0, self.toggle_width - thumb_rect.width() - 20, self.toggle_height )
            painter.drawText( text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "OFF" )
        else:
            text_rect = QRect( thumb_rect.width() + 10, 0, self.toggle_width - thumb_rect.width() - 20, self.toggle_height )
            painter.drawText( text_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "ON" )
        
        if self.selected:
            self.drawSelectionBorder( painter )
            self.drawSelectionHandles( painter )

    def drawSelectionHandles( self, painter ):
        handle_size = 8
        half_size = handle_size // 2

        painter.setBrush( QColor( 255, 142, 62 ) )
        painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

        corners = [ QPoint( 4, 4 ), QPoint( self.width()-4, 4), ]

        for corner in corners:
            painter.drawEllipse( corner.x() - half_size, corner.y() - half_size, handle_size, handle_size )
            painter.setBrush( QColor( 255, 142, 62 ) ) 
            painter.setPen( Qt.PenStyle.NoPen )
            painter.drawEllipse( corner.x() - 1, corner.y() - 1, 2, 2 )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

    def drawSelectionBorder( self, painter ):
        border_rect = QRect( 0, 0, self.width(), self.height() )

        selection_pen = QPen( QColor( 255, 0, 0 ) )
        selection_pen.setWidth( 2 )
        selection_pen.setStyle( Qt.PenStyle.DashLine )
        selection_pen.setDashPattern( [ 4, 2 ] )

        painter.setPen( selection_pen )
        painter.setBrush( Qt.BrushStyle.NoBrush )
        painter.drawRect( border_rect )

    def handleResize( self, global_pos ):
        if not self.resize_corner:
            return

        delta = global_pos - self.resize_start_pos
        new_width = self.resize_start_size.width()
        new_x = self.resize_start_position.x() 

        if self.resize_corner == "right":
            new_width = max( 80, self.resize_start_size.width() + delta.x() )

        elif self.resize_corner == "left":
            new_width = max( 80, self.resize_start_size.width() - delta.x() )
            new_x = self.resize_start_position.x() + delta.x() 

        self.toggle_width = new_width
        self.setFixedSize( self.toggle_width, self.toggle_height )

        if self.resize_corner == "left":
            self.move( new_x, self.y() )

        self.updateTogglePropertiesSize()
        self.updateTogglePropertiesPosition() 

    def getCornerAt( self, pos ):
        handle_size = 12 
        half_size = handle_size // 2
        
        corners = {
            "left": QPoint( 0, self.height() // 2 ),
            "right": QPoint( self.width(), self.height() // 2 )
        }
        
        for corner_name, corner_pos in corners.items():
            corner_rect = QRect( corner_pos.x() - half_size, corner_pos.y() - half_size, handle_size, handle_size )
            
            if corner_rect.contains( pos ):
                return corner_name
        
        return None

    def getThumbRect( self ):
        thumb_height = self.toggle_height - 5
        thumb_width = thumb_height
        
        if self.state:
            thumb_x = self.toggle_width - thumb_width - 2

        else:
            thumb_x = 2
            
        thumb_y = 3
        
        return QRect( thumb_x, thumb_y, thumb_width, thumb_height )

    def setSelected( self, selected ):
        self.selected = selected
        self.update()

    def updateTogglePropertiesPosition( self ):
        main_window = self.findMainWindow()

        if main_window and main_window.current_shape == self:
            try:
                if hasattr( main_window, 'pos_x_spin_toggle' ):
                    main_window.pos_x_spin_toggle.blockSignals( True )
                    main_window.pos_x_spin_toggle.setValue( self.x() )
                    main_window.pos_x_spin_toggle.blockSignals( False )

            except RuntimeError:
                pass
            
            try:
                if hasattr(main_window, 'pos_y_spin_toggle'):
                    main_window.pos_y_spin_toggle.blockSignals( True )
                    main_window.pos_y_spin_toggle.setValue( self.y() )
                    main_window.pos_y_spin_toggle.blockSignals( False )

            except RuntimeError:
                pass

    def updateTogglePropertiesSize( self ):
        main_window = self.findMainWindow()

        if main_window and hasattr( main_window, 'current_shape' ) and main_window.current_shape == self:
            try:
                if hasattr( main_window, 'width_spin_toggle' ):
                    main_window.width_spin_toggle.blockSignals( True )
                    main_window.width_spin_toggle.setValue( self.toggle_width  )
                    main_window.width_spin_toggle.blockSignals( False )

            except RuntimeError:
                pass
        
        self.update()      

    def updateToggleState( self, state ):
        self.state = state
        self.update()
        
        main_window = self.findMainWindow()

        if main_window and main_window.current_shape == self:
            try:
                if hasattr( main_window, 'state_checkbox_toggle' ):
                    main_window.state_checkbox_toggle.blockSignals( True )
                    main_window.state_checkbox_toggle.setChecked( self.state )
                    main_window.state_checkbox_toggle.blockSignals( False )

            except RuntimeError:
                pass

    def setupDataDict( self ):
        self.data_dict = {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'tag': self.tag,
            'position_x': self.x(),
            'position_y': self.y(),
            'toggle_width': self.toggle_width,
            'thumb_color': self.thumb_color,
            'background_color': self.background_color,
            'text_color': self.text_color,
            'effect_3d': self.effect_3d,
            'state': self.state,

            'type': 'Toggle',
            'id': None
        }
    
    def updateDataDict( self ):
        self.data_dict.update( {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'tag': self.tag,
            'position_x': self.x(),
            'position_y': self.y(),
            'toggle_width': self.toggle_width,
            'thumb_color': self.thumb_color,
            'background_color': self.background_color,
            'text_color': self.text_color,
            'effect_3d': self.effect_3d,
            'state': self.state
        } )
        return self.data_dict
    
    def getDataDict( self ):
        return self.updateDataDict()
    
    def setDataId( self, data_id ):
        self.data_dict[ 'id' ] = data_id

    def findMainWindow( self ):
        parent = self.parent()

        while parent:
            if isinstance( parent, QMainWindow ):
                return parent
            
            parent = parent.parent()

        return None

    def mousePressEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.findMainWindow()

            if main_window and hasattr( main_window, 'object_attached' ) and main_window.object_attached:
                event.ignore()
                return

            mouse_pos = event.pos()

            self.resize_corner = self.getCornerAt( mouse_pos )

            if self.resize_corner:
                self.resizing = True
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_size = self.size()
                self.resize_start_position = self.pos() 

            else:
                self.dragging = True
                self.drag_start_pos = mouse_pos

                thumb_rect = self.getThumbRect()

                if thumb_rect.contains( event.pos() ):
                    self.updateToggleState( not self.state )

                self.clicked.emit( self )

        event.accept()

    def mouseReleaseEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = False
            self.dragging = False
            self.resize_corner = None
            self.updateTogglePropertiesPosition()

        self.updateDataDict()
        event.accept()

    def mouseMoveEvent( self, event ):
        mouse_pos = event.pos()

        corner = self.getCornerAt( mouse_pos )
        if corner:
            self.setCursor( Qt.CursorShape.SizeHorCursor )

        else:
            self.setCursor( Qt.CursorShape.ArrowCursor )

        if self.resizing and event.buttons() & Qt.MouseButton.LeftButton:
            self.handleResize( event.globalPosition().toPoint() )

        elif self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            delta = mouse_pos - self.drag_start_pos

            new_x = self.x() + delta.x()
            new_y = self.y() + delta.y()

            self.move( new_x, new_y )
            self.updateTogglePropertiesPosition()

        event.accept()

class ScrollBarWidget( QWidget ):
    clicked = pyqtSignal( object )
    
    def __init__( self, parent = None ):
        super().__init__( parent )
        
        self.defaultValues()
        self.setFixedSize( self.scroll_bar_width, self.scroll_bar_height )
        self.setMouseTracking( True )
        self.setFocusPolicy( Qt.FocusPolicy.StrongFocus )
        self.setupDataDict()

    def defaultValues( self ):
        self.active = True
        self.visible = True
        self.static = False
        self.custom_name = ""
        self.stack_order = 1
        self.tag = 0
        self.scroll_bar_width = 200
        self.scroll_bar_height = 15
        self.background_color = QColor( 0, 0, 255 ) 
        self.thumb_color = QColor( 255, 0, 0 )
        self.effect_3d = True 
        self.range_value = 100 
        self.current_value = 50
        self.thumb_size = 30
        self.thumb_min_size = 20

        self.selected = False
        self.resizing = False
        self.dragging = False
        self.resize_start_pos = QPoint()
        self.drag_start_pos = QPoint()
        self.resize_corner = None
        self.resize_start_size = QSize()
        self.resize_start_position = QPoint() 

        self.thumb_dragging = False
        self.thumb_drag_start_pos = QPoint()
        self.thumb_drag_start_value = 0
        self.thumb_drag_mouse_start_pos = QPoint()
        self.rotated = False

    def paintEvent( self, event ):
        if self.visible and self.active:
            self.thumb_color.setAlpha( 255 )
            self.background_color.setAlpha( 255 )

        else:
            self.thumb_color.setAlpha( 50 )
            self.background_color.setAlpha( 50 )
        
        painter = QPainter( self )
        painter.setRenderHint( QPainter.RenderHint.Antialiasing )
        self.rotated = self.height() > self.width()
        
        if self.rotated:
            painter.translate( self.width(), 0 )
            painter.rotate( 90 )
            draw_width = self.height()
            draw_height = self.width()

        else:
            draw_width = self.width()
            draw_height = self.height()
        
        radius = max( 1, draw_height // 2 )
        
        pen = QPen( self.background_color )
        pen.setWidth( 3 )
        painter.setPen( pen )
        painter.setBrush( self.background_color )
        
        painter.drawPie( 0, 0, 2 * radius, 2 * radius, 90 * 16, 180 * 16 )
        painter.drawRect( radius, 0, draw_width - 2 * radius, draw_height )
        painter.drawPie( draw_width - 2 * radius, 0, 2 * radius, 2 * radius, 90 * 16, - 180 * 16 )
        
        if self.effect_3d:
            pen = QPen( QColor( 0, 0, 0 ) )
            pen.setWidth( 1 )
            painter.setPen( pen )
            painter.drawLine( radius, 0, draw_width - radius, 0 )
            painter.drawArc( 0, 0, 2 * radius, 2 * radius, 90 * 16, 135 * 16 )
            painter.drawArc( draw_width - 2 * radius, 0, 2 * radius, 2 * radius, 45 * 16, 45 * 16 )

            pen = QPen( QColor( 255, 255, 255 ) )
            pen.setWidth( 1 )
            painter.setPen( pen )
            
            painter.drawLine( radius, draw_height, draw_width - radius, draw_height )
            painter.drawArc( 0, 0, 2 * radius, 2 * radius, 225 * 16, 45 * 16 )
            painter.drawArc( draw_width - 2 * radius, 0, 2 * radius, 2 * radius, 45 * 16, - 135 * 16 )
        
        thumb_rect = self.getThumbRectForDrawing()
        
        if thumb_rect.width() > 0 and thumb_rect.height() > 0:
            pen = QPen( self.thumb_color )
            pen.setWidth( 2 )
            painter.setPen( pen )
            painter.setBrush( self.thumb_color )
            
            thumb_radius = min( thumb_rect.width(), thumb_rect.height() ) // 2
            thumb_radius = max( 1, thumb_radius )
            
            if thumb_radius >= 3:
                painter.drawPie( thumb_rect.x(), thumb_rect.y(), 2 * thumb_radius, 2 * thumb_radius, 90 * 16, 180 * 16 )
                painter.drawRect( thumb_rect.x() + thumb_radius, thumb_rect.y(), thumb_rect.width() - 2 * thumb_radius, thumb_rect.height() )
                painter.drawPie( thumb_rect.x() + thumb_rect.width() - 2 * thumb_radius, thumb_rect.y(), 2 * thumb_radius, 2 * thumb_radius, 90 * 16, - 180 * 16 )
                
            else:
                painter.drawRect (thumb_rect )
            
            if self.effect_3d:
                pen = QPen( QColor( 0, 0, 0 ) )
                pen.setWidth( 1 )
                painter.setPen( pen )
                
                if thumb_radius >= 3:
                    painter.drawLine( thumb_rect.x() + thumb_radius, thumb_rect.y(), thumb_rect.x() + thumb_rect.width() - thumb_radius, thumb_rect.y() )
                    painter.drawArc( thumb_rect.x(), thumb_rect.y(), 2 * thumb_radius, 2 * thumb_radius, 90 * 16, 135 * 16 )
                else:
                    painter.drawLine( thumb_rect.x(), thumb_rect.y(), thumb_rect.x() + thumb_rect.width(), thumb_rect.y() )
                
                
                pen.setWidth( 1 )
                painter.setPen( pen )
                pen = QPen( QColor( 255, 255, 255 ) )
                if thumb_radius >= 3:
                    painter.drawLine( thumb_rect.x() + thumb_radius, thumb_rect.y() + thumb_rect.height(), thumb_rect.x() + thumb_rect.width() - thumb_radius, thumb_rect.y() + thumb_rect.height() )
                    painter.drawArc( thumb_rect.x() + thumb_rect.width() - 2 * thumb_radius, thumb_rect.y(), 2 * thumb_radius, 2 * thumb_radius, 45 * 16, -135 * 16 )

                else:
                    painter.drawLine( thumb_rect.x(), thumb_rect.y() + thumb_rect.height(), thumb_rect.x() + thumb_rect.width(), thumb_rect.y() + thumb_rect.height() )
        
        if self.selected:
            painter.resetTransform()
            self.drawSelectionBorder( painter )
            self.drawSelectionHandles( painter )

    def drawSelectionHandles( self, painter ):
        handle_size = 8
        half_size = handle_size // 2

        painter.setBrush( QColor( 255, 142, 62 ) )
        painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

        corners = [ QPoint( 4, 4 ), QPoint( self.width() - 4, 4 ), QPoint( 4, self.height() - 4 ), QPoint( self.width() - 4, self.height() - 4 ) ]

        for corner in corners:
            painter.drawEllipse( corner.x() - half_size, corner.y() - half_size, handle_size, handle_size )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( Qt.PenStyle.NoPen )
            painter.drawEllipse( corner.x() - 1, corner.y() - 1, 2, 2 )
            painter.setBrush( QColor( 255, 142, 62 ) )
            pen = QPen( QColor( 56, 56, 56 ) )
            pen.setWidth( 1 )
            painter.setPen( pen )

    def drawSelectionBorder( self, painter ):
        border_rect = QRect( 0, 0, self.width(), self.height() )

        selection_pen = QPen( QColor( 255, 0, 0 ) )
        selection_pen.setWidth( 2 )
        selection_pen.setStyle( Qt.PenStyle.DashLine )
        selection_pen.setDashPattern( [ 4, 2 ] )

        painter.setPen(selection_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(border_rect)

    def handleResize( self, global_pos ):
        if not self.resize_corner:
            return

        delta = global_pos - self.resize_start_pos
        new_width = self.resize_start_size.width()
        new_height = self.resize_start_size.height()
        new_x = self.resize_start_position.x()
        new_y = self.resize_start_position.y()

        if self.resize_corner == "bottom_right":
            new_width = self.resize_start_size.width() + delta.x()
            new_height = self.resize_start_size.height() + delta.y()

        elif self.resize_corner == "top_right":
            new_width = self.resize_start_size.width() + delta.x()
            new_height = self.resize_start_size.height() - delta.y()
            new_y = self.resize_start_position.y() + delta.y() 

        elif self.resize_corner == "bottom_left":
            new_width = self.resize_start_size.width() - delta.x()
            new_height = self.resize_start_size.height() + delta.y()
            new_x = self.resize_start_position.x() + delta.x()

        elif self.resize_corner == "top_left":
            new_width = self.resize_start_size.width() - delta.x()
            new_height = self.resize_start_size.height() - delta.y()
            new_x = self.resize_start_position.x() + delta.x()
            new_y = self.resize_start_position.y() + delta.y()

        new_width = max( 1, new_width )
        new_height = max( 1, new_height )

        self.scroll_bar_width = new_width
        self.scroll_bar_height = new_height

        self.setFixedSize( self.scroll_bar_width, self.scroll_bar_height )

        if self.resize_corner in [ "top_left", "bottom_left" ]:
            self.move( new_x, new_y )

        elif self.resize_corner == "top_right":
            self.move( self.x(), new_y ) 

        self.update()
        self.updatePropertiesSize()
        self.updatePropertiesPosition()

    def calculateValueFromPosition( self, pos ):
        if self.rotated:
            y = pos.y()
            track_rect = self.getTrackRectForInteraction()
            thumb_rect = self.getThumbRectForInteraction()
            
            track_length = track_rect.height() - thumb_rect.height()

            if track_length > 0:
                relative_y = y - track_rect.y() - thumb_rect.height() / 2
                value = int( ( relative_y / track_length ) * self.range_value )

                return max( 0, min( self.range_value, value ) )
            
            return self.current_value
        
        else:
            x = pos.x()
            track_rect = self.getTrackRectForInteraction()
            thumb_rect = self.getThumbRectForInteraction()
            track_length = track_rect.width() - thumb_rect.width()

            if track_length > 0:
                relative_x = x - track_rect.x() - thumb_rect.width() / 2
                value = int( ( relative_x / track_length ) * self.range_value )

                return max( 0, min( self.range_value, value ) )
            
            return self.current_value

    def getCornerAt( self, pos ):
        handle_size = 12 
        half_size = handle_size // 2
        
        corners = {
            "top_left": QPoint( 0, 0 ),
            "top_right": QPoint( self.width(), 0 ),
            "bottom_left": QPoint( 0, self.height() ),
            "bottom_right": QPoint( self.width(), self.height() )
        }
        
        for corner_name, corner_pos in corners.items():
            corner_rect = QRect( corner_pos.x() - half_size, corner_pos.y() - half_size, handle_size, handle_size )
            
            if corner_rect.contains( pos ):
                return corner_name
        
        return None

    def getThumbRectForDrawing( self ):
        if self.rotated:
            draw_width = self.height()  
            draw_height = self.width()   

        else:
            draw_width = self.width()
            draw_height = self.height()
        
        track_height = draw_height
        track_radius = max( 1, track_height // 2 )
        track_length = max( 0, draw_width - 2 * track_radius )
        thumb_length = int( track_length * ( self.thumb_size / 100.0 ) )
        dynamic_min_size = max( self.thumb_min_size, int(track_height * 1.5 ) )
        thumb_length = max( dynamic_min_size, min( track_length, thumb_length ) )
        max_position = max( 0, track_length - thumb_length )

        if max_position > 0:
            thumb_x = track_radius + int( ( self.current_value / self.range_value ) * max_position )

        else:
            thumb_x = track_radius
        
        thumb_height = int( track_height * 0.8 ) 
        thumb_height = max( 6, thumb_height )
        thumb_y =  ( track_height - thumb_height ) // 2
        
        return QRect( thumb_x, thumb_y, thumb_length, thumb_height )

    def getThumbRectForInteraction( self ):
        if self.rotated:
            track_height = self.height()
            track_width = self.width()
            track_radius = max( 1, track_width // 2 )
            track_length = max( 0, track_height - 2 * track_radius )
            
            thumb_length = int( track_length * ( self.thumb_size / 100.0 ) )
            dynamic_min_size = max( self.thumb_min_size, int( track_width * 1.5 ) )
            thumb_length = max( dynamic_min_size, min( track_length, thumb_length ) )
            
            max_position = max( 0, track_length - thumb_length )

            if max_position > 0:
                thumb_y = track_radius + int( ( self.current_value / self.range_value ) * max_position )

            else:
                thumb_y = track_radius
            
            thumb_width = int( track_width * 0.8 )
            thumb_width = max( 6, thumb_width )
            thumb_x = ( track_width - thumb_width ) // 2
            
            return QRect( thumb_x, thumb_y, thumb_width, thumb_length )
        
        else:
            track_height = self.height()
            track_width = self.width()
            track_radius = max( 1, track_height // 2 )
            track_length = max( 0, track_width - 2 * track_radius )
            thumb_length = int( track_length * ( self.thumb_size / 100.0 ) )
            dynamic_min_size = max( self.thumb_min_size, int( track_height * 1.5 ) )
            thumb_length = max( dynamic_min_size, min( track_length, thumb_length ) )
            max_position = max( 0, track_length - thumb_length )

            if max_position > 0:
                thumb_x = track_radius + int( ( self.current_value / self.range_value ) * max_position )

            else:
                thumb_x = track_radius
            
            thumb_height = int( track_height * 0.8 )
            thumb_height = max( 6, thumb_height )
            thumb_y = ( track_height - thumb_height ) // 2
            
            return QRect( thumb_x, thumb_y, thumb_length, thumb_height )

    def getTrackRectForInteraction( self ):
        if self.rotated:
            radius = max( 1, self.width() // 2 )

            return QRect( radius, 0, self.width() - 2 * radius, self.height() )
        
        else:
            radius = max( 1, self.height() // 2 )
            track_width = max( 0, self.width() - 2 * radius )

            return QRect( radius, 0, track_width, self.height() )
    
    def setSelected( self, selected ):
        self.selected = selected
        self.update()

    def updatePropertiesSize( self ):
        main_window = self.findMainWindow()
        if not main_window:
            return
        
        if hasattr( main_window, 'current_shape' ) and main_window.current_shape == self:
            if hasattr(main_window, 'width_spin_scrollbar'):
                try:
                    main_window.width_spin_scrollbar.blockSignals( True )
                    main_window.width_spin_scrollbar.setValue( self.scroll_bar_width )
                    main_window.width_spin_scrollbar.blockSignals( False )
                
                except:
                    pass
                
            if hasattr( main_window, 'height_spin_scrollbar' ):
                try:
                    main_window.height_spin_scrollbar.blockSignals( True )
                    main_window.height_spin_scrollbar.setValue( self.scroll_bar_height )
                    main_window.height_spin_scrollbar.blockSignals( False )

                except:
                    pass

    def updatePropertiesPosition( self ):
        main_window = self.findMainWindow()

        if not main_window:
            return

        if hasattr( main_window, 'current_shape' ) and main_window.current_shape == self:
            if hasattr( main_window, 'pos_x_spin_scrollbar' ):
                try:
                    main_window.pos_x_spin_scrollbar.blockSignals( True )
                    main_window.pos_x_spin_scrollbar.setValue( self.x() )
                    main_window.pos_x_spin_scrollbar.blockSignals( False )

                except:
                    pass

            if hasattr( main_window, 'pos_y_spin_scrollbar' ):
                try:
                    main_window.pos_y_spin_scrollbar.blockSignals( True )
                    main_window.pos_y_spin_scrollbar.setValue( self.y() )
                    main_window.pos_y_spin_scrollbar.blockSignals( False )

                except:
                    pass

    def updatePropertiesValue( self ):
        main_window = self.findMainWindow()

        if not main_window:
            return
        
        if hasattr(main_window, 'current_shape') and main_window.current_shape == self:
            if hasattr(main_window, 'current_value_spin_scrollbar'):
                try:
                    main_window.current_value_spin_scrollbar.blockSignals( True )
                    main_window.current_value_spin_scrollbar.setValue( self.current_value )
                    main_window.current_value_spin_scrollbar.blockSignals( False )

                except:
                    pass
                
            if hasattr(main_window, 'thumb_size_spin_scrollbar'):
                try:
                    main_window.thumb_size_spin_scrollbar.blockSignals( True )
                    main_window.thumb_size_spin_scrollbar.setValue( self.thumb_size )
                    main_window.thumb_size_spin_scrollbar.blockSignals( False )

                except:
                    pass

    def setupDataDict( self ):
        self.data_dict = {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'tag': self.tag,
            'position_x': self.x(),
            'position_y': self.y(),
            'scroll_bar_width': self.scroll_bar_width,
            'scroll_bar_height': self.scroll_bar_height,
            'thumb_color': self.thumb_color,
            'background_color': self.background_color,
            'effect_3d': self.effect_3d,
            'current_value': self.current_value,
            'thumb_size': self.thumb_size,

            'type': 'ScrollBar',
            'id': None
        }
    
    def updateDataDict( self ):
        self.data_dict.update( {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'tag': self.tag,
            'position_x': self.x(),
            'position_y': self.y(),
            'scroll_bar_width': self.scroll_bar_width,
            'scroll_bar_height': self.scroll_bar_height,
            'thumb_color': self.thumb_color,
            'background_color': self.background_color,
            'effect_3d': self.effect_3d,
            'current_value': self.current_value,
            'thumb_size': self.thumb_size
        } )
        return self.data_dict
    
    def getDataDict( self ):
        return self.updateDataDict()
    
    def setDataId( self, data_id ):
        self.data_dict[ 'id' ] = data_id

    def findMainWindow( self ):
        parent = self.parent()
        while parent:
            if isinstance( parent, QMainWindow ):
                return parent
            parent = parent.parent()
        return None

    def mousePressEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.findMainWindow()

            if main_window and hasattr( main_window, 'object_attached' ) and main_window.object_attached:
                event.ignore()
                return

            mouse_pos = event.pos()
            self.resize_corner = self.getCornerAt( mouse_pos )

            if self.resize_corner:
                self.resizing = True
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_size = self.size()
                self.resize_start_position = self.pos()

            else:
                thumb_rect = self.getThumbRectForInteraction()

                if thumb_rect.contains( event.pos() ):
                    self.thumb_dragging = True
                    self.dragging = False
                    self.thumb_drag_start_pos = event.pos()
                    self.thumb_drag_mouse_start_pos = event.pos() 
                    self.thumb_drag_start_value = self.current_value

                else:
                    self.dragging = True
                    self.thumb_dragging = False
                    self.drag_start_pos = mouse_pos
                    track_rect = self.getTrackRectForInteraction()

                    if track_rect.contains( event.pos() ):
                        new_value = self.calculateValueFromPosition( event.pos() )
                        self.current_value = new_value 

                self.clicked.emit( self )
                self.updatePropertiesValue()

        event.accept()

    def mouseReleaseEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = False
            self.dragging = False
            self.thumb_dragging = False
            self.resize_corner = None
            self.updatePropertiesSize()
            self.updatePropertiesPosition()

        self.updateDataDict()
        event.accept()

    def mouseMoveEvent( self, event ):
        mouse_pos = event.pos()
        corner = self.getCornerAt( mouse_pos )

        if corner:
            if corner in [ "top_left", "bottom_right" ]:
                self.setCursor( Qt.CursorShape.SizeFDiagCursor )

            elif corner in [ "top_right", "bottom_left" ]:
                self.setCursor( Qt.CursorShape.SizeBDiagCursor )

        else:
            self.setCursor( Qt.CursorShape.ArrowCursor )
        
        if self.resizing and event.buttons() & Qt.MouseButton.LeftButton:
            self.handleResize( event.globalPosition().toPoint() )

        elif self.thumb_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            if self.rotated:
                delta_y = mouse_pos.y() - self.thumb_drag_mouse_start_pos.y()
                track_rect = self.getTrackRectForInteraction()
                thumb_rect = self.getThumbRectForInteraction()
                track_length = track_rect.height() - thumb_rect.height()

                if track_length > 0:
                    pixels_per_value = track_length / self.range_value
                    delta_value = int( delta_y / pixels_per_value )
                    new_value = self.thumb_drag_start_value + delta_value
                    self.current_value = max( 0, min( self.range_value, new_value ) )

            else:
                delta_x = mouse_pos.x() - self.thumb_drag_mouse_start_pos.x()
                track_rect = self.getTrackRectForInteraction()
                thumb_rect = self.getThumbRectForInteraction()
                track_length = track_rect.width() - thumb_rect.width()

                if track_length > 0:
                    pixels_per_value = track_length / self.range_value
                    delta_value = int( delta_x / pixels_per_value )
                    new_value = self.thumb_drag_start_value + delta_value
                    self.current_value = max( 0, min( self.range_value, new_value ) )
            
            self.updatePropertiesValue()
            self.update()

        elif self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            delta = mouse_pos - self.drag_start_pos
            new_x = self.x() + delta.x()
            new_y = self.y() + delta.y()

            super().move( new_x, new_y )
            self.updatePropertiesPosition()
        
        event.accept()

class SliderWidget( QWidget ):
    clicked = pyqtSignal( object )
    
    def __init__( self, parent = None ):
        super().__init__( parent )

        self.defaultValues()
        self.setFixedSize( self.slider_width, self.slider_height )
        self.setMouseTracking( True )
        self.setFocusPolicy( Qt.FocusPolicy.StrongFocus )
        self.setupDataDict()

    def defaultValues( self ):
        self.active = True
        self.visible = True
        self.static = False
        self.custom_name = ""
        self.stack_order = 1
        self.tag = 0
        self.slider_width = 200
        self.slider_height = 30
        self.background_color_left = QColor( 0, 255, 0 )
        self.thumb_color = QColor( 255, 0, 0 )
        self.background_color_right = QColor( 0, 0, 255 )
        self.effect_3d = True  
        self.value = 50

        self.selected = False
        self.resizing = False
        self.dragging = False
        self.thumb_dragging = False
        self.resize_start_pos = QPoint()
        self.drag_start_pos = QPoint()
        self.thumb_drag_start_pos = QPoint()
        self.thumb_drag_start_value = 0
        self.resize_corner = None
        self.resize_start_size = QSize()
        self.resize_start_position = QPoint()
        self.rotated = False

    def paintEvent( self, event ):
        if self.visible and self.active:
            self.background_color_left.setAlpha( 255 )
            self.thumb_color.setAlpha( 255 )
            self.background_color_right.setAlpha( 255 )

        else:
            self.background_color_left.setAlpha( 50 )
            self.thumb_color.setAlpha( 50 )
            self.background_color_right.setAlpha( 50 )

        painter = QPainter( self )
        painter.setRenderHint( QPainter.RenderHint.Antialiasing )

        self.rotated = self.height() > self.width()
        
        if self.rotated:
            painter.translate( self.width(), 0 )
            painter.rotate( 90 )

        track_rect = self.getTrackRectForDrawing()
        progress_rect = self.getProgressRectForDrawing()
        thumb_rect = self.getThumbRectForDrawing()
        track_right_rect = self.getTrackRightRectForDrawing()

        radius = track_rect.height() // 2

        pen = QPen( QColor( 0, 0, 0 ) )
        pen.setWidth( 3 )
        painter.setPen( pen )
        painter.setBrush( Qt.BrushStyle.NoBrush )

        painter.drawArc( track_rect.x() - radius, track_rect.y(), radius * 2, radius * 2, 90 * 16, 180 * 16 )
        painter.drawArc( track_rect.x() + track_rect.width() - radius, track_rect.y(), radius * 2, radius * 2, 90 * 16, -180 * 16 )
        painter.drawLine( track_rect.x(), track_rect.y(), track_rect.x() + track_rect.width(), track_rect.y() )
        painter.drawLine( track_rect.x(), track_rect.y() + track_rect.height(), track_rect.x() + track_rect.width(), track_rect.y() + track_rect.height() )

        if track_right_rect.width() > 0:
            pen = QPen( self.background_color_right )
            pen.setWidth ( 3 )
            painter.setPen( pen )
            painter.setBrush( self.background_color_right )

            if track_right_rect.width() > radius:
                painter.drawPie( track_rect.x() + track_rect.width() - radius, track_rect.y(), radius * 2, radius * 2, 90 * 16, - 180 * 16 )
                painter.drawRect( track_right_rect.x(), track_rect.y(), track_right_rect.width(), track_rect.height() )

            else:
                painter.drawRect( track_right_rect.x(), track_rect.y(), track_right_rect.width(), track_rect.height() )

        if progress_rect.width() > 0:
            pen = QPen( self.background_color_left )
            pen.setWidth( 3 )
            painter.setPen( pen )
            painter.setBrush( self.background_color_left )

            if progress_rect.width() > radius:
                painter.drawPie( track_rect.x() - radius, track_rect.y(), radius * 2, radius * 2, 90 * 16, 180 * 16 )
                painter.drawRect( track_rect.x(), track_rect.y(), progress_rect.width() - radius, track_rect.height() )

            else:
                painter.drawRect( track_rect.x(), track_rect.y(), progress_rect.width(), track_rect.height() )

            if track_right_rect.width() > 0:
                pen = QPen( self.background_color_right )
                pen.setWidth( 2 )
                painter.setPen( pen )
                painter.drawLine( track_rect.x(), track_rect.y() - 1, track_rect.x() + progress_rect.width(), track_rect.y() - 1 )
                painter.drawLine( track_rect.x(), track_rect.y() + progress_rect.height() + 1, track_rect.x() + progress_rect.width(), track_rect.y() + progress_rect.height() + 1 )
                painter.drawArc( track_rect.x() - radius - 1, track_rect.y() - 1, radius * 2 + 2, radius * 2 + 2, 90 * 16, 180 * 16 )


        if self.effect_3d:
            if progress_rect.width() > 0:
                pen = QPen( QColor( 255, 255, 255 ) )
                pen.setWidth( 1 )
                painter.setPen( pen )
                painter.drawLine( track_right_rect.x(), track_rect.y() + progress_rect.height() + 1, track_rect.x() + track_rect.width(), track_rect.y() + progress_rect.height() + 1 )
                painter.drawArc( track_rect.x() + track_rect.width() - radius - 1, track_rect.y() - 1, radius * 2 + 2, radius * 2 + 2, 90 * 16, - 180 * 16 )

                pen = QPen( QColor( 0, 0, 0 ) )
                pen.setWidth( 1 )
                painter.setPen( pen )
                painter.drawLine( track_rect.x()  , track_rect.y() - 1,  track_rect.width() + radius  , track_rect.y() - 1 )
                painter.drawArc( track_rect.x() - radius - 1, track_rect.y() - 1, radius * 2 + 2, radius * 2 + 2, 90 * 16, 180 * 16 )

        pen = QPen( self.thumb_color )
        pen.setWidth( 3 )
        painter.setPen( pen )
        painter.setBrush( self.thumb_color )
        painter.drawEllipse( thumb_rect )

        if self.effect_3d:
            pen = QPen( QColor( 236, 238, 241 ) )
            pen.setWidth( 1 )
            painter.setPen( pen )
            painter.drawArc( thumb_rect, 40 * 16, 160 * 16 )

            pen = QPen( QColor( 0, 0, 0 ) )
            pen.setWidth( 1 )
            painter.setPen( pen )
            painter.drawArc( thumb_rect, 200 * 16, 180 * 16 )

        if self.selected:
            painter.resetTransform()
            self.drawSelectionBorder( painter )
            self.drawSelectionHandles( painter )

    def drawSelectionHandles( self, painter ):
        handle_size = 8
        half_size = handle_size // 2

        painter.setBrush( QColor( 255, 142, 62 ) )
        painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

        corners = [ QPoint( 4, 4 ), QPoint( self.width() - 4, 4 ), QPoint( 4, self.height() - 4 ), QPoint( self.width() - 4, self.height() - 4 ) ]

        for corner in corners:
            painter.drawEllipse( corner.x() - half_size, corner.y() - half_size, handle_size, handle_size )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( Qt.PenStyle.NoPen )
            painter.drawEllipse( corner.x() - 1, corner.y() - 1, 2, 2 )
            painter.setBrush( QColor( 255, 142, 62 ) )
            pen = QPen( ( QColor( 56, 56, 56 ) ) )
            pen.setWidth( 1 )
            painter.setPen( pen )


    def drawSelectionBorder( self, painter ):
        border_rect = QRect( 0, 0, self.width(), self.height() )

        selection_pen = QPen( QColor( 255, 0, 0 ) )
        selection_pen.setWidth( 2 )
        selection_pen.setStyle( Qt.PenStyle.DashLine )
        selection_pen.setDashPattern( [ 4, 2 ] )

        painter.setPen( selection_pen )
        painter.setBrush( Qt.BrushStyle.NoBrush )
        painter.drawRect( border_rect )

    def handleResize( self, global_pos ):
        if not self.resize_corner:
            return

        delta = global_pos - self.resize_start_pos
        new_width = self.resize_start_size.width()
        new_height = self.resize_start_size.height()
        new_x = self.resize_start_position.x() 
        new_y = self.resize_start_position.y()

        if self.resize_corner == "bottom_right":
            new_width = max( 1, self.resize_start_size.width() + delta.x() )
            new_height = max( 1, self.resize_start_size.height() + delta.y() )

        elif self.resize_corner == "top_right":
            new_width = max( 1, self.resize_start_size.width() + delta.x() )
            new_height = max( 1, self.resize_start_size.height() - delta.y() )
            new_y = self.resize_start_position.y() + delta.y()

        elif self.resize_corner == "bottom_left":
            new_width = max( 1, self.resize_start_size.width() - delta.x() )
            new_height = max( 1, self.resize_start_size.height() + delta.y() )
            new_x = self.resize_start_position.x() + delta.x() 

        elif self.resize_corner == "top_left":
            new_width = max( 1, self.resize_start_size.width() - delta.x() )
            new_height = max( 1, self.resize_start_size.height() - delta.y() )
            new_x = self.resize_start_position.x() + delta.x() 
            new_y = self.resize_start_position.y() + delta.y()

        self.slider_width = new_width
        self.slider_height = new_height

        self.setFixedSize( self.slider_width, self.slider_height )
        self.rotated = self.height() > self.width()

        if self.resize_corner in [ "top_left", "bottom_left" ]:
            self.move( new_x, new_y )
        elif self.resize_corner == "top_right":
            self.move( self.x(), new_y )

        self.update()
        self.updatePropertiesSize()
        self.updatePropertiesPosition()

    def getCornerAt( self, pos ):
        handle_size = 12
        half_size = handle_size // 2
        
        corners = {
            "top_left": QPoint( 0, 0 ),
            "top_right": QPoint( self.width(), 0 ),
            "bottom_left": QPoint( 0, self.height() ),
            "bottom_right": QPoint( self.width(), self.height() )
        }
        
        for corner_name, corner_pos in corners.items():
            corner_rect = QRect( corner_pos.x() - half_size, corner_pos.y() - half_size, handle_size, handle_size )
            
            if corner_rect.contains( pos ):
                return corner_name
        
        return None

    def getTrackRectForDrawing( self ):
        if self.rotated:
            draw_width = self.height()
            draw_height = self.width()  

        else:
            draw_width = self.width()
            draw_height = self.height()
        
        track_height = draw_height // 3
        track_y = draw_height // 3
        radius = draw_height // 6 
        
        return QRect( radius, track_y, draw_width - 2 * radius, track_height )

    def getProgressRectForDrawing( self ):
        track_rect = self.getTrackRectForDrawing()
        progress_width = int( track_rect.width() * self.value / 100 )
        
        return QRect( track_rect.x(), track_rect.y(), progress_width, track_rect.height() )

    def getTrackRightRectForDrawing( self ):
        track_rect = self.getTrackRectForDrawing()
        thumb_rect = self.getThumbRectForDrawing()
        
        start_x = thumb_rect.x() + thumb_rect.width()
        width = track_rect.x() + track_rect.width() - start_x
        
        if width > 0:
            return QRect( start_x, track_rect.y(), width, track_rect.height() )
        
        return QRect()

    def getThumbRectForDrawing( self ):
        track_rect = self.getTrackRectForDrawing()
        
        if self.rotated:
            draw_height = self.width()

        else:
            draw_height = self.height()
            
        thumb_diameter = min( track_rect.height() * 2, draw_height * 0.8 )
        thumb_x = track_rect.x() + int( ( track_rect.width() - thumb_diameter ) * ( self.value / 100 ) )
        thumb_y = (draw_height - thumb_diameter) // 2
        
        return QRect( thumb_x, thumb_y, thumb_diameter, thumb_diameter )

    def getTrackRectForInteraction( self ):
        if self.rotated:
            return QRect( 0, 0, self.width(), self.height() )
        
        else:
            w = self.width()
            h = self.height()
            track_height = h // 3
            track_y = h // 3
            radius = h // 6 
            return QRect( radius, track_y, w - 2 * radius, track_height )

    def getThumbRectForInteraction( self ):
        if self.rotated:
            track_height = self.height()
            track_width = self.width()
            thumb_diameter = int( min( track_width * 2, track_height * 0.8 ) )
            thumb_diameter = int( max( 20, min( track_height, thumb_diameter ) ) )
            track_length = track_height
            available_track = max( 1, track_length - thumb_diameter )
            thumb_y = int( ( self.value / 100 ) * available_track )
            thumb_x = int( ( track_width - thumb_diameter ) // 2 )

            return QRect( thumb_x, thumb_y, thumb_diameter, thumb_diameter )
        else:
            track_width = self.width()
            track_height = self.height()

            thumb_diameter = int( min( track_height * 2, track_height * 0.8 ) )
            thumb_diameter = int( max( 20, min( track_width, thumb_diameter ) ) )

            thumb_x = int( ( track_width - thumb_diameter) * ( self.value / 100 ) )
            thumb_y = int( ( track_height - thumb_diameter) // 2 )

            return QRect( thumb_x, thumb_y, thumb_diameter, thumb_diameter )

    def setSelected( self, selected ):
        self.selected = selected
        self.update()

    def updatePropertiesSize( self ):
        main_window = self.findMainWindow()

        if not main_window:
            return
        
        if ( hasattr( main_window, 'current_shape' ) and main_window.current_shape == self ):
            if hasattr( main_window, 'width_spin_slider' ):
                main_window.width_spin_slider.blockSignals( True )
                main_window.width_spin_slider.setValue( self.slider_width )
                main_window.width_spin_slider.blockSignals( False )
                
            if hasattr( main_window, 'height_spin_slider' ):
                main_window.height_spin_slider.blockSignals( True )
                main_window.height_spin_slider.setValue( self.slider_height )
                main_window.height_spin_slider.blockSignals( False )

    def updatePropertiesPosition( self ):
        main_window = self.findMainWindow()

        if not main_window:
            return

        if ( hasattr( main_window, 'current_shape' ) and main_window.current_shape == self ):
            if hasattr( main_window, 'pos_x_spin_slider'):
                main_window.pos_x_spin_slider.blockSignals( True )
                main_window.pos_x_spin_slider.setValue( self.x() )
                main_window.pos_x_spin_slider.blockSignals( False )

            if hasattr(main_window, 'pos_y_spin_slider'):
                main_window.pos_y_spin_slider.blockSignals( True )
                main_window.pos_y_spin_slider.setValue( self.y() )
                main_window.pos_y_spin_slider.blockSignals( False )

    def updatePropertiesValue( self ):
        main_window = self.findMainWindow()

        if not main_window:
            return
        
        if ( hasattr( main_window, 'current_shape') and main_window.current_shape == self ):
            if hasattr( main_window, 'value_spin_slider' ):
                try:
                    main_window.value_spin_slider.blockSignals( True )
                    main_window.value_spin_slider.setValue( self.value ) 
                    main_window.value_spin_slider.blockSignals( False )

                except:
                    pass

    def setupDataDict( self ):
        self.data_dict = {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'tag': self.tag,
            'position_x': self.x(),
            'position_y': self.y(),
            'slider_width': self.slider_width,
            'slider_height': self.slider_height,
            'thumb_color': self.thumb_color,
            'left_background_color': self.background_color_left,
            'right_background_color': self.background_color_right,
            'effect_3d': self.effect_3d,
            'current_value': self.value,

            'type': 'Slider',
            'id': None
        }
    
    def updateDataDict( self ):
        self.data_dict.update( {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'tag': self.tag,
            'position_x': self.x(),
            'position_y': self.y(),
            'slider_width': self.slider_width,
            'slider_height': self.slider_height,
            'thumb_color': self.thumb_color,
            'left_background_color': self.background_color_left,
            'right_background_color': self.background_color_right,
            'effect_3d': self.effect_3d,
            'current_value': self.value
        } )
        return self.data_dict
    
    def getDataDict( self ):
        return self.updateDataDict()
    
    def setDataId( self, data_id ):
        self.data_dict[ 'id' ] = data_id

    def findMainWindow( self ):
        parent = self.parent()

        while parent:
            if isinstance( parent, QMainWindow ):
                return parent
            
            parent = parent.parent()

        return None

    def mousePressEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.findMainWindow()
            if main_window and hasattr( main_window, 'object_attached' ) and main_window.object_attached:
                event.ignore()
                return

            mouse_pos = event.pos()
            thumb_rect = self.getThumbRectForInteraction()
            self.resize_corner = self.getCornerAt( mouse_pos )

            if self.resize_corner:
                self.resizing = True
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_size = self.size()
                self.resize_start_position = self.pos() 

            elif thumb_rect.contains( mouse_pos ):
                self.thumb_dragging = True
                self.thumb_drag_start_pos = mouse_pos
                self.thumb_drag_start_value = self.value

            else:
                self.dragging = True
                self.drag_start_pos = mouse_pos
                track_rect = self.getTrackRectForInteraction()

                if track_rect.contains( event.pos() ):
                    if self.rotated:
                        thumb_diameter = int( min( track_rect.height() * 2, self.width() * 0.8 ) )
                        thumb_diameter = int( max( 20, min( track_rect.height(), thumb_diameter ) ) )
                        track_length = track_rect.height()
                        available_track = max( 1, track_length - thumb_diameter )
                        relative_y = event.pos().y() - track_rect.y() - thumb_diameter // 2
                        new_value = int( ( relative_y / available_track ) * 100 )

                    else:
                        relative_x = event.pos().x() - track_rect.x()
                        new_value = int( ( relative_x / track_rect.width() ) * 100 )

                    self.value = max( 0, min( 100, new_value ) )
                    self.update()
                    self.updatePropertiesValue()

            self.clicked.emit( self )
            self.updatePropertiesValue()

        event.accept()

    def mouseReleaseEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = False
            self.dragging = False
            self.thumb_dragging = False
            self.resize_corner = None

            self.updatePropertiesSize()
            self.updatePropertiesPosition()
            self.updatePropertiesValue()

        self.updateDataDict()
        event.accept()

    def mouseMoveEvent( self, event ):
        mouse_pos = event.pos()
        corner = self.getCornerAt( mouse_pos )

        if corner:
            if corner in [ "top_left", "bottom_right" ]:
                self.setCursor( Qt.CursorShape.SizeFDiagCursor )
            elif corner in [ "top_right", "bottom_left" ]:
                self.setCursor( Qt.CursorShape.SizeBDiagCursor )
        else:
            self.setCursor( Qt.CursorShape.ArrowCursor )

        if self.resizing and event.buttons() & Qt.MouseButton.LeftButton:
            self.handleResize( event.globalPosition().toPoint() )

        elif self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            delta = mouse_pos - self.drag_start_pos
            new_x = self.x() + delta.x()
            new_y = self.y() + delta.y()
            super().move( new_x, new_y )
            self.updatePropertiesPosition()

        elif self.thumb_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            if self.rotated:
                thumb_rect = self.getThumbRectForInteraction()
                track_height = self.height()
                thumb_diameter = thumb_rect.height()
                available_track = max( 1, track_height - thumb_diameter )
                new_y = mouse_pos.y() - thumb_diameter // 2
                new_y = max( 0, min( new_y, track_height - thumb_diameter ) )
                new_value = int( ( new_y / available_track ) * 100 )
                self.value = max( 0, min( 100, new_value ) )

            else:
                track_rect = self.getTrackRectForInteraction()
                delta_x = mouse_pos.x() - self.thumb_drag_start_pos.x()
                value_delta = int( ( delta_x / track_rect.width() ) * 100 )
                new_value = self.thumb_drag_start_value + value_delta
                self.value = max( 0, min( 100, new_value ) )

            self.update()
            self.updatePropertiesValue()

        event.accept()

class ProgressBarWidget( QWidget ):
    clicked = pyqtSignal( object )
    
    def __init__( self, parent = None ):
        super().__init__( parent )

        self.defaultValues()
        self.setFixedSize( self.progress_bar_width, self.progress_bar_height )
        self.setMouseTracking( True )
        self.setFocusPolicy( Qt.FocusPolicy.StrongFocus )
        self.setupDataDict()

    def defaultValues( self ):
        self.active = True
        self.visible = True
        self.static = False
        self.custom_name = ""
        self.stack_order = 1
        self.progress_bar_width = 200
        self.progress_bar_height = 15
        self.progress_color = QColor( 255, 0, 0 )
        self.background_color = QColor( 0, 0, 255 ) 
        self.effect_3d = True
        self.range = 100
        self.value = 50

        self.selected = False
        self.resizing = False
        self.dragging = False
        self.resize_start_pos = QPoint()
        self.drag_start_pos = QPoint()
        self.resize_corner = None
        self.resize_start_size = QSize()
        self.resize_start_position = QPoint()
        self.rotated = False

    def paintEvent( self, event ):
        if self.visible and self.active:
            self.progress_color.setAlpha( 255 )
            self.background_color.setAlpha( 255 )

        else:
            self.progress_color.setAlpha( 50 )
            self.background_color.setAlpha( 50 )

        painter = QPainter( self )
        painter.setRenderHint( QPainter.RenderHint.Antialiasing )
        
        self.rotated = self.height() > self.width()
        
        if self.rotated:
            painter.translate( self.width(), 0 )
            painter.rotate( 90 )
            draw_width = self.height()
            draw_height = self.width()

        else:
            draw_width = self.width()
            draw_height = self.height()
        
        pen = QPen( self.background_color )
        pen.setWidth( 3 )
        painter.setPen( pen )
        painter.setBrush( self.background_color )
        
        radius = draw_height // 2
        
        painter.drawPie( 0, 0, 2 * radius, 2 * radius, 90 * 16, 180 * 16 )
        painter.drawRect( radius, 0, draw_width - 2 * radius, draw_height )
        painter.drawPie( draw_width - 2 * radius, 0, 2 * radius, 2 * radius, 90 * 16, - 180 * 16 )
        
        pen = QPen( self.progress_color )
        pen.setWidth( 3 )
        painter.setPen( pen )
        painter.setBrush( self.progress_color )
        
        progress_width = int( draw_width * ( self.value / self.range ) )
        inner_offset = 6 
        inner_radius = radius - inner_offset // 2

        if progress_width < 2 * inner_radius:
            progress_width = 2 * inner_radius
        
        if progress_width > 0:
            painter.drawPie( inner_offset // 2, inner_offset // 2, 2 * inner_radius, 2 * inner_radius, 90 * 16, 180 * 16 )
            painter.drawRect( radius - 3 + inner_offset // 2, inner_offset // 2, progress_width - 2 * inner_radius - inner_offset, 2 * inner_radius )
            painter.drawPie( inner_offset // 2 + progress_width - 2 * inner_radius - inner_offset, inner_offset // 2, 2 * inner_radius, 2 * inner_radius, 90 * 16, - 180 * 16 )

        else:
            painter.drawEllipse( inner_offset, inner_offset // 2 , inner_radius * 2, inner_radius * 2 )

        if self.effect_3d:
            
            pen = QPen( QColor( 0, 0, 0 ) )
            pen.setWidth( 2 )
            painter.setPen( pen )

            painter.drawLine( radius, 1, draw_width - radius, 1 )
            painter.drawArc( draw_width - 2 * radius , 0, 2 * radius, 2 * radius, 90 * 16, - 45 * 16 )
            painter.drawArc( 0, 0, 2 * radius, 2 * radius, 90 * 16, 135 * 16 )

            pen = QPen( QColor( 255, 255, 255 ) )
            pen.setWidth( 2 )
            painter.setPen( pen )

            painter.drawLine( radius , draw_height - 1, draw_width - radius, draw_height - 1 )
            painter.drawArc( draw_width - 2 * radius, 0, 2 * radius, 2 * radius, 45 * 16, - 135 * 16 )
            painter.drawArc( 0, 0, 2 * radius, 2 * radius, 225 * 16, 45 * 16 )

        if self.selected:
            painter.resetTransform()
            self.drawSelectionBorder( painter )
            self.drawSelectionHandles( painter )

    def drawSelectionHandles( self, painter ):
        handle_size = 8
        half_size = handle_size // 2

        painter.setBrush( QColor( 255, 142, 62 ) )
        painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

        corners = [ QPoint( 4, 4 ), QPoint( self.width() - 4, 4 ), QPoint( 4, self.height() - 4 ), QPoint( self.width() - 4, self.height() - 4 ) ]

        for corner in corners:
            painter.drawEllipse( corner.x() - half_size, corner.y() - half_size, handle_size, handle_size )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( Qt.PenStyle.NoPen )
            painter.drawEllipse( corner.x() - 1, corner.y() - 1, 2, 2 )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

    def drawSelectionBorder( self, painter ):
        border_rect = QRect( 0, 0, self.width(), self.height() )

        selection_pen = QPen( QColor( 255, 0, 0 ) )
        selection_pen.setWidth( 2 )
        selection_pen.setStyle( Qt.PenStyle.DashLine )
        selection_pen.setDashPattern( [ 4, 2 ] )

        painter.setPen( selection_pen )
        painter.setBrush( Qt.BrushStyle.NoBrush )
        painter.drawRect( border_rect )

    def handleResize( self, global_pos ):
        if not self.resize_corner:
            return

        delta = global_pos - self.resize_start_pos
        new_width = self.resize_start_size.width()
        new_height = self.resize_start_size.height()
        new_x = self.resize_start_position.x() 
        new_y = self.resize_start_position.y()

        if self.resize_corner == "bottom_right":
            new_width = max( 1, self.resize_start_size.width() + delta.x() )
            new_height = max( 1, self.resize_start_size.height() + delta.y() )

        elif self.resize_corner == "top_right":
            new_width = max( 1, self.resize_start_size.width() + delta.x() )
            new_height = max( 1, self.resize_start_size.height() - delta.y() )
            new_y = self.resize_start_position.y() + delta.y()

        elif self.resize_corner == "bottom_left":
            new_width = max( 1, self.resize_start_size.width() - delta.x() )
            new_height = max( 1, self.resize_start_size.height() + delta.y() )
            new_x = self.resize_start_position.x() + delta.x()

        elif self.resize_corner == "top_left":
            new_width = max( 1, self.resize_start_size.width() - delta.x() )
            new_height = max( 1, self.resize_start_size.height() - delta.y() )
            new_x = self.resize_start_position.x() + delta.x() 
            new_y = self.resize_start_position.y() + delta.y()  

        self.progress_bar_width = new_width
        self.progress_bar_height = new_height
        self.setFixedSize( self.progress_bar_width, self.progress_bar_height )

        if self.resize_corner in [ "top_left", "bottom_left" ]:
            self.move( new_x, new_y )

        elif self.resize_corner == "top_right":
            self.move( self.x(), new_y ) 

        self.updatePropertiesSize()
        self.updatePropertiesPosition()

    def getCornerAt( self, pos ):
        handle_size = 12
        half_size = handle_size // 2
        
        corners = {
            "top_left": QPoint( 0, 0 ),
            "top_right": QPoint( self.width(), 0 ),
            "bottom_left": QPoint( 0, self.height() ),
            "bottom_right": QPoint( self.width(), self.height() )
        }
        
        for corner_name, corner_pos in corners.items():
            corner_rect = QRect( corner_pos.x() - half_size, corner_pos.y() - half_size, handle_size, handle_size )
            
            if corner_rect.contains( pos ):
                return corner_name
        
        return None

    def setSelected( self, selected ):
        self.selected = selected
        self.update()

    def updatePropertiesPosition( self ):
        main_window = self.findMainWindow()

        if main_window and main_window.current_shape == self:
            try:
                if hasattr( main_window, 'pos_x_spin_progress_bar' ):
                    main_window.pos_x_spin_progress_bar.blockSignals( True )
                    main_window.pos_x_spin_progress_bar.setValue( self.x() )
                    main_window.pos_x_spin_progress_bar.blockSignals( False )

            except RuntimeError:
                pass
            
            try:
                if hasattr( main_window, 'pos_y_spin_progress_bar' ):
                    main_window.pos_y_spin_progress_bar.blockSignals( True )
                    main_window.pos_y_spin_progress_bar.setValue( self.y() )
                    main_window.pos_y_spin_progress_bar.blockSignals( False )

            except RuntimeError:
                pass

    def updatePropertiesSize( self ):
        main_window = self.findMainWindow()

        if main_window and main_window.current_shape == self:
            try:
                if hasattr( main_window, 'width_spin_progress_bar' ):
                    main_window.width_spin_progress_bar.blockSignals( True )
                    main_window.width_spin_progress_bar.setValue( self.progress_bar_width )
                    main_window.width_spin_progress_bar.blockSignals( False )
            except RuntimeError:
                pass
            
            try:
                if hasattr( main_window, 'height_spin_progress_bar' ):
                    main_window.height_spin_progress_bar.blockSignals( True )
                    main_window.height_spin_progress_bar.setValue( self.progress_bar_height )
                    main_window.height_spin_progress_bar.blockSignals( False )
            except RuntimeError:
                pass
        
        self.update()

    def setupDataDict( self ):
        self.data_dict = {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'position_x': self.x(),
            'position_y': self.y(),
            'progress_bar_width': self.progress_bar_width,
            'progress_bar_height': self.progress_bar_height,
            'progress_color': self.progress_color,
            'background_color': self.background_color,
            'effect_3d': self.effect_3d,
            'range': self.range,
            'current_value': self.value,

            'type': 'ProgressBar',
            'id': None
        }
    
    def updateDataDict( self ):
        self.data_dict.update( {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'position_x': self.x(),
            'position_y': self.y(),
            'progress_bar_width': self.progress_bar_width,
            'progress_bar_height': self.progress_bar_height,
            'progress_color': self.progress_color,
            'background_color': self.background_color,
            'effect_3d': self.effect_3d,
            'range': self.range,
            'current_value': self.value
        } )
        return self.data_dict
    
    def getDataDict( self ):
        return self.updateDataDict()
    
    def setDataId( self, data_id ):
        self.data_dict[ 'id' ] = data_id

    def findMainWindow( self ):
        parent = self.parent()

        while parent:
            if isinstance( parent, QMainWindow ):
                return parent
            
            parent = parent.parent()

        return None

    def mousePressEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.findMainWindow()

            if main_window and hasattr( main_window, 'object_attached' ) and main_window.object_attached:
                event.ignore()
                return

            mouse_pos = event.pos()

            self.resize_corner = self.getCornerAt( mouse_pos )

            if self.resize_corner:
                self.resizing = True
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_size = self.size()
                self.resize_start_position = self.pos()

            else:
                self.dragging = True
                self.drag_start_pos = mouse_pos
                self.clicked.emit( self )

        event.accept()

    def mouseReleaseEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = False
            self.dragging = False
            self.resize_corner = None
            self.updatePropertiesPosition()
            self.updatePropertiesSize()

        self.updateDataDict()
        event.accept()

    def mouseMoveEvent( self, event ):
        mouse_pos = event.pos()
        corner = self.getCornerAt( mouse_pos )

        if corner:
            if corner in [ "top_left", "bottom_right" ]:
                self.setCursor( Qt.CursorShape.SizeFDiagCursor )

            elif corner in [ "top_right", "bottom_left" ]:
                self.setCursor( Qt.CursorShape.SizeBDiagCursor )

        else:
            self.setCursor( Qt.CursorShape.ArrowCursor )

        if self.resizing and event.buttons() & Qt.MouseButton.LeftButton:
            self.handleResize( event.globalPosition().toPoint() )

        elif self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            delta = mouse_pos - self.drag_start_pos
            new_x = self.x() + delta.x()
            new_y = self.y() + delta.y()

            self.move( new_x, new_y )
            self.updatePropertiesPosition()

        event.accept()

class ImageWidget( QWidget ):
    clicked = pyqtSignal( object )
    
    def __init__( self, parent = None ):
        super().__init__( parent )

        self.defaultValues()
        self.setFixedSize( self.image_width, self.image_height )
        self.setMouseTracking( True )
        self.setFocusPolicy( Qt.FocusPolicy.StrongFocus )
        self.setupDataDict()

    def defaultValues( self ):
        self.active = True
        self.visible = True
        self.static = False
        self.custom_name = ""
        self.stack_order = 1
        self.image_width = 100
        self.image_height = 100
        self.image_path = ""
        self.frame_enabled = False
        self.frame_color = QColor( 0, 0, 0 )
        self.frame_width = 5

        self.selected = False
        self.resizing = False
        self.dragging = False
        self.resize_start_pos = QPoint()
        self.drag_start_pos = QPoint()
        self.resize_corner = None
        self.resize_start_size = QSize()
        self.resize_start_position = QPoint()
        self.pixmap = QPixmap()
        self.original_pixmap = QPixmap()

    def paintEvent( self, event ):
        if self.visible and self.active:
            opacity = 1.0
            self.frame_color.setAlpha( 255 )
        else:
            opacity = 0.4
            self.frame_color.setAlpha( 50 )

        painter = QPainter( self )
        painter.setRenderHint( QPainter.RenderHint.Antialiasing )
        painter.setBrush( QColor( 240, 240, 240 ) )
        painter.setPen( Qt.PenStyle.NoPen )

        if self.frame_enabled:
            painter.drawRect( 0, 0, self.image_width , self.image_height  )
        else:
            painter.drawRect( 0, 0, self.image_width , self.image_height )

        if not self.pixmap.isNull():
            painter.setOpacity( opacity )
            painter.drawPixmap( 0, 0, self.pixmap )

        if self.frame_enabled:
            frame_color = QColor( self.frame_color )
            painter.setPen( QPen( frame_color, self.frame_width ) )
            painter.setBrush( Qt.BrushStyle.NoBrush )
            painter.drawRect( 0, 0, self.image_width, self.image_height )

        if self.selected:
            self.drawSelectionBorder( painter )
            self.drawSelectionHandles( painter )

    def drawSelectionHandles( self, painter ):
        handle_size = 8
        half_size = handle_size // 2

        painter.setBrush( QColor( 255, 142, 62 ) )
        painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )

        corners = [ QPoint( 4, 4 ), QPoint( self.width() - 4, 4 ), QPoint( 4, self.height() - 4 ), QPoint( self.width() - 4, self.height() - 4 ) ]

        for corner in corners:
            painter.drawEllipse( corner.x() - half_size, corner.y() - half_size, handle_size, handle_size )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( Qt.PenStyle.NoPen )
            painter.drawEllipse( corner.x() - 1, corner.y() - 1, 2, 2 )
            painter.setBrush( QColor( 255, 142, 62 ) )
            painter.setPen( QPen( QColor( 56, 56, 56 ), 1 ) )
    
    def drawSelectionBorder( self, painter ):
        border_rect = QRect( 0, 0, self.width(), self.height() )

        selection_pen = QPen( QColor( 255, 0, 0 ) )
        selection_pen.setWidth( 2 )
        selection_pen.setStyle( Qt.PenStyle.DashLine )
        selection_pen.setDashPattern( [ 4, 2 ] )

        painter.setPen( selection_pen )
        painter.setBrush( Qt.BrushStyle.NoBrush )
        painter.drawRect( border_rect )

    def handleResize( self, global_pos ):
        if not self.resize_corner:
            return

        delta = global_pos - self.resize_start_pos
        new_width = self.resize_start_size.width()
        new_height = self.resize_start_size.height()
        new_x = self.resize_start_position.x()
        new_y = self.resize_start_position.y()

        if self.resize_corner == "bottom_right":
            new_width = max( 10, self.resize_start_size.width() + delta.x() )
            new_height = max( 10, self.resize_start_size.height() + delta.y() )

        elif self.resize_corner == "top_right":
            new_width = max( 10, self.resize_start_size.width() + delta.x() )
            new_height = max( 10, self.resize_start_size.height() - delta.y() )
            new_y = self.resize_start_position.y() + delta.y() 

        elif self.resize_corner == "bottom_left":
            new_width = max( 10, self.resize_start_size.width() - delta.x() )
            new_height = max( 10, self.resize_start_size.height() + delta.y() )
            new_x = self.resize_start_position.x() + delta.x()

        elif self.resize_corner == "top_left":
            new_width = max( 10, self.resize_start_size.width() - delta.x() )
            new_height = max( 10, self.resize_start_size.height() - delta.y() )
            new_x = self.resize_start_position.x() + delta.x()
            new_y = self.resize_start_position.y() + delta.y()

        self.image_width = new_width
        self.image_height = new_height

        self.setFixedSize( new_width, new_height )

        if self.resize_corner in [ "top_left", "bottom_left" ]:
            self.move( new_x, new_y )

        elif self.resize_corner == "top_right":
            self.move( self.x(), new_y )

        if not self.original_pixmap.isNull():
            self.resizePixmap()

        self.updatePropertiesSize()
        self.updatePropertiesPosition() 

    def resizePixmap( self ):
        if self.original_pixmap.isNull():
            return
        
        content_width = max( 0, self.image_width )
        content_height = max( 0, self.image_height  )
        
        self.pixmap = self.original_pixmap.scaled( content_width, content_height, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation )
        
    def getCornerAt( self, pos ):
        handle_size = 12
        half_size = handle_size // 2
        
        corners = {
            "top_left": QPoint( 0, 0 ),
            "top_right": QPoint( self.width(), 0 ),
            "bottom_left": QPoint( 0, self.height() ),
            "bottom_right": QPoint( self.width(), self.height() )
        }
        
        for corner_name, corner_pos in corners.items():
            corner_rect = QRect( corner_pos.x() - half_size, corner_pos.y() - half_size, handle_size, handle_size )
            
            if corner_rect.contains( pos ):
                return corner_name
        
        return None

    def setImagePath( self, path ):
        supported_formats = ['.bmp', '.png', '.jpg', '.jpeg', '.jpe']
        
        if path:
            file_extension = path.lower()
            has_supported_extension = any( file_extension.endswith( ext ) for ext in supported_formats )
            
            if has_supported_extension:
                self.image_path = path
                self.original_pixmap = QPixmap( path )
                
                if self.original_pixmap.isNull():
                    self.original_pixmap = QPixmap()
                    self.pixmap = QPixmap()
                    return False
            
                self.resizePixmap()

                if not self.custom_name:
                    filename = os.path.basename( path )
                    self.custom_name = f"Image_{ os.path.splitext( filename )[ 0 ] }"
                
                self.update()

                return True

            else:
                return False
        
        return False
    
    def setSelected( self, selected ):
        self.selected = selected
        self.update()
    
    def updatePropertiesSize( self ):
        main_window = self.findMainWindow()

        if not main_window:
            return
        
        if ( hasattr( main_window, 'current_shape') and main_window.current_shape == self ):
            try:
                if hasattr( main_window, 'width_spin_image' ):
                    main_window.width_spin_image.blockSignals( True )
                    main_window.width_spin_image.setValue( self.image_width )
                    main_window.width_spin_image.blockSignals( False )
                
                if hasattr(main_window, 'height_spin_image'):
                    main_window.height_spin_image.blockSignals( True )
                    main_window.height_spin_image.setValue( self.image_height )
                    main_window.height_spin_image.blockSignals( False )

            except:
                pass
    
    def updatePropertiesPosition( self ):
        main_window = self.findMainWindow()

        if not main_window:
            return

        if ( hasattr( main_window, 'current_shape' ) and main_window.current_shape == self ):
            try:    
                if hasattr( main_window, 'pos_x_spin_image' ):
                    main_window.pos_x_spin_image.blockSignals( True )
                    main_window.pos_x_spin_image.setValue( self.x() )
                    main_window.pos_x_spin_image.blockSignals( False )

                if hasattr( main_window, 'pos_y_spin_image' ):
                    main_window.pos_y_spin_image.blockSignals( True )
                    main_window.pos_y_spin_image.setValue( self.y() )
                    main_window.pos_y_spin_image.blockSignals( False )
            except:
                pass

    def setupDataDict( self ):
        self.data_dict = {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'position_x': self.x(),
            'position_y': self.y(),
            'image_width': self.image_width,
            'image_height': self.image_height,
            'frame': self.frame_enabled,
            'frame_color': self.frame_color,
            'frame_width': self.frame_width,

            'type': 'Image',
            'id': None
        }
    
    def updateDataDict( self ):
        self.data_dict.update( {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'position_x': self.x(),
            'position_y': self.y(),
            'image_width': self.image_width,
            'image_height': self.image_height,
            'frame': self.frame_enabled,
            'frame_color': self.frame_color,
            'frame_width': self.frame_width
        } )
        return self.data_dict
    
    def getDataDict( self ):
        return self.updateDataDict()
    
    def setDataId( self, data_id ):
        self.data_dict[ 'id' ] = data_id

    def findMainWindow( self ):
        parent = self.parent()

        while parent:
            if isinstance( parent, QMainWindow ):
                return parent
            
            parent = parent.parent()

        return None
    
    def mousePressEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.findMainWindow()

            if main_window and hasattr( main_window, 'object_attached' ) and main_window.object_attached:
                event.ignore()
                return

            mouse_pos = event.pos()
            self.resize_corner = self.getCornerAt( mouse_pos )

            if self.resize_corner:
                self.resizing = True
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_size = self.size()
                self.resize_start_position = self.pos()

            else:
                self.dragging = True
                self.drag_start_pos = mouse_pos
                self.clicked.emit( self )

        event.accept()
    
    def mouseMoveEvent( self, event ):
        mouse_pos = event.pos()
        corner = self.getCornerAt( mouse_pos )

        if corner:
            if corner in [ "top_left", "bottom_right" ]:
                self.setCursor( Qt.CursorShape.SizeFDiagCursor )

            elif corner in [ "top_right", "bottom_left" ]:
                self.setCursor( Qt.CursorShape.SizeBDiagCursor )

        else:
            self.setCursor( Qt.CursorShape.ArrowCursor )

        if self.resizing and event.buttons() & Qt.MouseButton.LeftButton:
            self.handleResize( event.globalPosition().toPoint() )

        elif self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            delta = mouse_pos - self.drag_start_pos
            new_x = self.x() + delta.x()
            new_y = self.y() + delta.y()

            super().move( new_x, new_y )
            self.updatePropertiesPosition()

        event.accept()
    
    def mouseReleaseEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = False
            self.dragging = False
            self.resize_corner = None

            self.updatePropertiesSize()
            self.updatePropertiesPosition()

        self.updateDataDict()
        event.accept()

class LabelWidget( QWidget ):
    clicked = pyqtSignal( object )
    
    def __init__( self, parent = None ):
        super().__init__( parent )

        self.defaultValues()
        self.calculateAndSetSize() 
        self.setMouseTracking( True )
        self.setFocusPolicy( Qt.FocusPolicy.StrongFocus )
        self.setupDataDict()
        
    def defaultValues( self ):
        self.active = True
        self.visible = True
        self.static = False
        self.custom_name = ""
        self.stack_order = 1
        self.original_x = 0
        self.original_y = 0
        self.text_color = QColor( 0, 0, 0 ) 
        self.text = "Text"  
        self.text_size = 29 
        self.text_alignment = "Left"

        self.selected = False
        self.dragging = False
        self.drag_start_global_pos = QPoint()
        self.drag_start_original_pos = None
        
    def paintEvent( self, event ):
        if self.visible and self.active:
            self.text_color.setAlpha( 255 )

        else:
            self.text_color.setAlpha( 50 )

        painter = QPainter( self )
        painter.setRenderHint( QPainter.RenderHint.Antialiasing )

        painter.setPen( QPen( self.text_color ) )
        font = QFont()
        font.setPointSize( int( ( 23 / 5 ) * self.text_size - 548 / 5 ) )
        painter.setFont( font )
        
        text_rect = QRect( 0, 0, self.label_width, self.label_height )
        
        if self.text_alignment == "Left":
            alignment_flags = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        
        elif self.text_alignment == "Right":
            alignment_flags = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        
        elif self.text_alignment == "Center":
            alignment_flags = Qt.AlignmentFlag.AlignCenter
        
        elif self.text_alignment == "Horisontaly":
            alignment_flags = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
        
        elif self.text_alignment == "Verticaly":
            alignment_flags = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        
        painter.drawText( text_rect, alignment_flags, self.text )
        
        if self.selected:
            self.drawSelectionBorder( painter )

    def drawSelectionBorder( self, painter ):
        font = QFont()
        font.setPointSize( int( ( 23 / 5 ) * self.text_size - 548 / 5 ) )
        font_metrics = QFontMetrics(font)
        
        text_width = font_metrics.horizontalAdvance( self.text )
        text_height = font_metrics.height()
        ascent = font_metrics.ascent()
        
        if self.text_alignment == "Left":
            text_x = 0
            text_y = ascent
            
        elif self.text_alignment == "Right":
            text_x = self.width() - text_width
            text_y = ascent
            
        elif self.text_alignment == "Center":
            text_x = ( self.width() - text_width ) // 2
            text_y = ( self.height() - text_height ) // 2 + ascent
            
        elif self.text_alignment == "Horisontaly":
            text_x = ( self.width() - text_width ) // 2
            text_y = ascent
            
        elif self.text_alignment == "Verticaly":
            text_x = 0
            text_y = ( self.height() - text_height ) // 2 + ascent
            
        bbox_x = text_x
        bbox_y = text_y - ascent 
    
        
        border_rect = QRect( bbox_x, bbox_y, text_width, text_height )
    
        selection_pen = QPen( QColor( 255, 0, 0 ) )
        selection_pen.setWidth( 2 )
        selection_pen.setStyle( Qt.PenStyle.DashLine )
        selection_pen.setDashPattern( [ 4, 2 ] )
    
        painter.setPen( selection_pen )
        painter.setBrush( Qt.BrushStyle.NoBrush )
        painter.drawRect( border_rect )

    def calculateAndSetSize( self ):
        font = QFont()
        font.setPointSize( int( ( 23 / 5 ) * self.text_size - 548 / 5 ) )
        font_metrics = QFontMetrics( font )
        
        self.text_width = font_metrics.horizontalAdvance( self.text )
        self.text_height = font_metrics.height()
        self.ascent = font_metrics.ascent()
        
        margin = 10
        self.label_width = max( 50, self.text_width + 2 * margin )
        self.label_height = max( 30, self.text_height + 2 * margin )
        
        self.setFixedSize( self.label_width, self.label_height )

    def applyAlignmentOffset( self ):
        if not hasattr( self, 'text_width' ):
            return
            
        if self.text_alignment == "Left":
            offset_x = 0
            offset_y = 0
            
        elif self.text_alignment == "Right":
            offset_x = - self.text_width
            offset_y = 0
            
        elif self.text_alignment == "Center":
            offset_x = - self.text_width // 2
            offset_y = - self.text_height // 2
            
        elif self.text_alignment == "Horisontaly":
            offset_x = - self.text_width // 2
            offset_y = 0
            
        elif self.text_alignment == "Verticaly":
            offset_x = 0
            offset_y = - self.ascent // 2
            
        actual_x = self.original_x + offset_x
        actual_y = self.original_y + offset_y

        super().move(int(actual_x), int(actual_y))

    def move(self, x, y):
        self.original_x = x
        self.original_y = y
        
        self.applyAlignmentOffset()
        self.updatePropertiesPosition()

    def setSelected(self, selected):
        self.selected = selected
        self.update()

    def setSizeBasedOnText(self):
        current_original_x = getattr( self, 'original_x', self.x() )
        current_original_y = getattr( self, 'original_y', self.y() )
        
        self.calculateAndSetSize()
        
        self.original_x = current_original_x
        self.original_y = current_original_y
        self.original_x = max( 0, self.original_x )
        self.original_y = max( 0, self.original_y )        
        self.applyAlignmentOffset()
        self.update()

    def updatePropertiesPosition( self ):
        main_window = self.findMainWindow()

        if main_window and hasattr( main_window, 'current_shape' ) and main_window.current_shape == self:
            try:
                if hasattr( main_window, 'pos_x_spin_label' ):
                    main_window.pos_x_spin_label.blockSignals( True )
                    main_window.pos_x_spin_label.setValue( self.original_x )
                    main_window.pos_x_spin_label.blockSignals( False )

            except RuntimeError:
                pass
            
            try:
                if hasattr( main_window, 'pos_y_spin_label' ):
                    main_window.pos_y_spin_label.blockSignals( True )
                    main_window.pos_y_spin_label.setValue( self.original_y )
                    main_window.pos_y_spin_label.blockSignals( False )

            except RuntimeError:
                pass

    def setupDataDict( self ):
        self.data_dict = {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'position_x': self.original_x, 
            'position_y': self.original_y,  
            'text_color': self.text_color,
            'text': self.text,
            'text_size': self.text_size,
            'text_alignment': self.text_alignment,

            'type': 'Label',
            'id': None

        }
    
    def updateDataDict( self ):
        self.data_dict.update( {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'position_x': self.original_x,  
            'position_y': self.original_y,  
            'text_color': self.text_color,
            'text': self.text,
            'text_size': self.text_size,
            'text_alignment': self.text_alignment
        } )
        return self.data_dict
    
    def getDataDict( self ):
        return self.updateDataDict()
    
    def setDataId(self, data_id):
        self.data_dict[ 'id' ] = data_id

    def findMainWindow(self):
        parent = self.parent()

        while parent:
            if isinstance( parent, QMainWindow ):
                return parent
            
            parent = parent.parent()

        return None
    
    def mouseMoveEvent( self, event ):
        if self.dragging and ( event.buttons() & Qt.MouseButton.LeftButton ):
            if self.drag_start_original_pos is not None:
                current_global_pos = event.globalPosition().toPoint()
                delta = current_global_pos - self.drag_start_global_pos
                
                self.original_x = self.drag_start_original_pos[ 0 ] + delta.x()
                self.original_y = self.drag_start_original_pos[ 1 ] + delta.y()
                
                self.applyAlignmentOffset()
                self.updatePropertiesPosition()
                self.update()
        
        event.accept()

    def mousePressEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.findMainWindow()

            if main_window and hasattr( main_window, 'object_attached' ) and main_window.object_attached:
                event.ignore()
                return

            self.dragging = True
            self.drag_start_global_pos = event.globalPosition().toPoint()
            self.drag_start_original_pos = ( self.original_x, self.original_y )
            self.clicked.emit( self )

        event.accept()

    def mouseReleaseEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.drag_start_original_pos = None

        self.updateDataDict()
        event.accept()

class NumericWidget( QWidget ):
    clicked = pyqtSignal( object )
    
    def __init__(self, parent = None ):
        super().__init__( parent )

        self.defaultValues()
        self.calculateAndSetSize() 
        self.setMouseTracking( True )
        self.setFocusPolicy( Qt.FocusPolicy.StrongFocus )
        self.setupDataDict()
        
    def defaultValues( self ):
        self.active = True
        self.visible = True
        self.static = False
        self.custom_name = ""
        self.stack_order = 1
        self.original_x = 0
        self.original_y = 0
        self.number_color = QColor( 0, 0, 0 )
        self.number = 123
        self.number_size = 29
        self.number_alignment = "Left"

        self.selected = False
        self.dragging = False
        self.drag_start_global_pos = QPoint()
        self.drag_start_original_pos = None
        
    def paintEvent( self, event ):
        if self.visible and self.active:
            self.number_color.setAlpha( 255 )

        else:
            self.number_color.setAlpha( 50 )

        painter = QPainter( self )
        painter.setRenderHint( QPainter.RenderHint.Antialiasing )

        painter.setPen( QPen( self.number_color ) )
        font = QFont()
        font.setPointSize( int( ( 23 / 5 ) * self.number_size - 548 / 5 ) )
        painter.setFont(font)
        
        text_rect = QRect( 0, 0, self.numeric_width, self.numeric_height )
        
        if self.number_alignment == "Left":
            alignment_flags = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop

        elif self.number_alignment == "Right":
            alignment_flags = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop

        elif self.number_alignment == "Center":
            alignment_flags = Qt.AlignmentFlag.AlignCenter

        elif self.number_alignment == "Horisontaly":
            alignment_flags = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop

        elif self.number_alignment == "Verticaly":
            alignment_flags = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        painter.drawText( text_rect, alignment_flags, str( self.number ) )
        
        if self.selected:
            self.drawSelectionBorder( painter )

    def drawSelectionBorder( self, painter ):
        font = QFont()
        font.setPointSize( int( ( 23 / 5 ) * self.number_size - 548 / 5 ) )
        font_metrics = QFontMetrics( font )
        
        text_width = font_metrics.horizontalAdvance( str( self.number ) )
        text_height = font_metrics.height()
        ascent = font_metrics.ascent()
        
        if self.number_alignment == "Left":
            text_x = 0
            text_y = ascent

        elif self.number_alignment == "Right":
            text_x = self.width() - text_width
            text_y = ascent

        elif self.number_alignment == "Center":
            text_x = ( self.width() - text_width ) // 2
            text_y = ( self.height() - text_height ) // 2 + ascent

        elif self.number_alignment == "Horisontaly":
            text_x = ( self.width() - text_width ) // 2
            text_y = ascent

        elif self.number_alignment == "Verticaly":
            text_x = 0
            text_y = ( self.height() - text_height ) // 2 + ascent
        
        bbox_x = text_x
        bbox_y = text_y - ascent 
        
        border_rect = QRect( bbox_x, bbox_y, text_width, text_height )
    
        selection_pen = QPen( QColor( 255, 0, 0 ) )
        selection_pen.setWidth( 2 )
        selection_pen.setStyle( Qt.PenStyle.DashLine )
        selection_pen.setDashPattern( [ 4, 2 ] )
    
        painter.setPen( selection_pen )
        painter.setBrush( Qt.BrushStyle.NoBrush )
        painter.drawRect( border_rect )

    def calculateAndSetSize( self ):
        font = QFont()
        font.setPointSize( int( ( 23 / 5 ) * self.number_size - 548 / 5 ) )
        font_metrics = QFontMetrics( font )
        
        self.text_width = font_metrics.horizontalAdvance( str( self.number ) )
        self.text_height = font_metrics.height()
        self.ascent = font_metrics.ascent()
        
        margin = 10
        self.numeric_width = max( 50, self.text_width + 2 * margin )
        self.numeric_height = max( 30, self.text_height + 2 * margin )
        
        self.setFixedSize( self.numeric_width, self.numeric_height )

    def applyAlignmentOffset( self ):
        if not hasattr( self, 'text_width' ):
            return
            
        if self.number_alignment == "Left":
            offset_x = 0
            offset_y = 0

        elif self.number_alignment == "Right":
            offset_x = - self.text_width
            offset_y = 0

        elif self.number_alignment == "Center":
            offset_x = - self.text_width // 2
            offset_y = - self.text_height // 2

        elif self.number_alignment == "Horisontaly":
            offset_x = - self.text_width // 2
            offset_y = 0

        elif self.number_alignment == "Verticaly":
            offset_x = 0
            offset_y = - self.ascent // 2

        else:
            offset_x = 0
            offset_y = 0
        
        actual_x = self.original_x + offset_x
        actual_y = self.original_y + offset_y

        super().move( int( actual_x ), int( actual_y ) )

    def move( self, x, y ):
        self.original_x = x
        self.original_y = y
        
        self.applyAlignmentOffset()
        self.updatePropertiesPosition()

    def setSelected( self, selected ):
        self.selected = selected
        self.update()

    def setSizeBasedOnNumber(self):
        current_original_x = getattr( self, 'original_x', self.x() )
        current_original_y = getattr( self, 'original_y', self.y() )
        
        self.calculateAndSetSize()
        
        self.original_x = current_original_x
        self.original_y = current_original_y
        self.original_x = max( 0, self.original_x )
        self.original_y = max( 0, self.original_y )        
        self.applyAlignmentOffset()
        self.update()

    def updatePropertiesPosition( self ):
        main_window = self.findMainWindow()

        if main_window and hasattr( main_window, 'current_shape' ) and main_window.current_shape == self:
            try:
                if hasattr( main_window, 'pos_x_spin_numeric' ):
                    main_window.pos_x_spin_numeric.blockSignals( True )
                    main_window.pos_x_spin_numeric.setValue( self.original_x )
                    main_window.pos_x_spin_numeric.blockSignals( False )

            except RuntimeError:
                pass
            
            try:
                if hasattr( main_window, 'pos_y_spin_numeric' ):
                    main_window.pos_y_spin_numeric.blockSignals( True )
                    main_window.pos_y_spin_numeric.setValue( self.original_y )
                    main_window.pos_y_spin_numeric.blockSignals( False )

            except RuntimeError:
                pass


    def setupDataDict( self ):
        self.data_dict = {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'position_x': self.original_x, 
            'position_y': self.original_y, 
            'number_color': self.number_color,
            'number': self.number,
            'number_size': self.number_size,
            'number_alignment': self.number_alignment,

            'type': 'Numeric',
            'id': None

        }
    
    def updateDataDict( self ):
        self.data_dict.update( {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'stack_order': self.stack_order,
            'position_x': self.original_x, 
            'position_y': self.original_y,
            'number_color': self.number_color,
            'number': self.number,
            'number_size': self.number_size,
            'number_alignment': self.number_alignment
        } )
        return self.data_dict
    
    def getDataDict( self ):
        return self.updateDataDict()
    
    def setDataId( self, data_id ):
        self.data_dict[ 'id' ] = data_id

    def findMainWindow( self ):
        parent = self.parent()

        while parent:

            if isinstance( parent, QMainWindow ):
                return parent
            
            parent = parent.parent()

        return None
    
    def mouseMoveEvent( self, event ):
        if self.dragging and ( event.buttons() & Qt.MouseButton.LeftButton ):
            if self.drag_start_original_pos is not None:
                current_global_pos = event.globalPosition().toPoint()
                delta = current_global_pos - self.drag_start_global_pos
                
                self.original_x = self.drag_start_original_pos[ 0 ] + delta.x()
                self.original_y = self.drag_start_original_pos[ 1 ] + delta.y()
                
                self.applyAlignmentOffset()
                self.updatePropertiesPosition()
                self.update()
        
        event.accept()

    def mousePressEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.findMainWindow()

            if main_window and hasattr( main_window, 'object_attached' ) and main_window.object_attached:
                event.ignore()
                return

            self.dragging = True
            self.drag_start_global_pos = event.globalPosition().toPoint()
            self.drag_start_original_pos = ( self.original_x, self.original_y )
            self.clicked.emit( self )

        event.accept()

    def mouseReleaseEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.drag_start_original_pos = None

        self.updateDataDict()
        event.accept()