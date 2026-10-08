from PyQt6.QtGui import ( QPainter, QPen, QColor, QFont, QPixmap, QCursor, QPalette )
from PyQt6.QtWidgets import ( QWidget, QLabel, QApplication, QFrame, QColorDialog )
from PyQt6.QtCore import ( Qt, QPoint, QRect, pyqtSignal )

class WidgetIcon( QFrame ):

    def __init__( self, shape ):
        super().__init__()

        self.setFixedSize( 100, 100 )
        self.setFrameShape( QFrame.Shape.Box )
        self.setLineWidth( 1 )
        self.shape = shape

        self.setAutoFillBackground( True )
        self.default_color = QColor( 0, 0, 0, 0 )
        self.hover_color = QColor( 202, 230, 232, 255 )

        palette = self.palette()
        palette.setColor( QPalette.ColorRole.Window, self.default_color )
        self.setPalette( palette )

    def paintEvent( self, event ):
        super().paintEvent( event )

        pen = QPen( QColor( 255, 255, 255 ) )
        font = QFont( "Arial", 10, QFont.Weight.Normal )  

        painter = QPainter( self )
        painter.setFont( font )
        painter.setPen( pen )
        text_rect = QRect( 0, 0, self.width(), self.height() - 5 )
        painter.drawText( text_rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, self.shape )
        
        shape_drawers = {
            "Line": self.drawLine,
            "Rectangle": self.drawRectangle,
            "Circle": self.drawCircle,
            "Ellipse":self.drawEllipse,
            "Button": self.drawButton,
            "Keys": self.drawKeys,
            "Clock": self.drawClock,
            "Gauge": self.drawGauge,
            "Dial": self.drawDial,
            "Toggle": self.drawToggle,
            "Scroll bar": self.drawScrollBar,
            "Slider": self.drawSlider,
            "Progress bar": self.drawProgressBar,
            "Image": self.drawImage,
            "Label": self.drawLabel,
            "Numeric":self.drawNumeric
        }
        
        if self.shape in shape_drawers:
            shape_drawers[ self.shape ]( painter )

    def drawLine( self, painter ):
        painter.drawLine( 20, 20, 80, 80 )

    def drawRectangle( self, painter ):
        painter.drawRect( 20, 20, 60, 50 )

    def drawCircle(self, painter):
        painter.drawEllipse( QPoint( 50, 45 ), 25, 25 )

    def drawEllipse( self, painter ):
        painter.drawEllipse( QPoint( 50, 45 ), 35, 25 )

    def drawButton( self, painter ):
        painter.drawRoundedRect( 20, 30, 60, 30, 5, 5 )
        rect = QRect( 20, 30, 60, 30 )
        painter.drawText( rect, Qt.AlignmentFlag.AlignCenter, "Press" )

    def drawKeys( self, painter ):
        x, y = 25, 20
        for i in range( 2 ):
            for j in range( 4 ):
                painter.drawRoundedRect( x, y, 10, 10, 1, 1 )
                x += 13
            x = 25
            y += 13
        painter.drawRoundedRect( 30, 47, 40, 10, 1, 1 )

    def drawClock( self, painter ):
        painter.drawEllipse( QPoint( 50, 45 ), 20, 20 )
        painter.translate( 50, 45 )
        for i in range( 12 ):  
            painter.drawPoint( 0, - 15 )
            painter.rotate( 30 )
        
        painter.rotate( 55 ) 
        needle_pen = QPen(QColor( 236, 238, 241 ) )
        needle_pen.setWidth( 1 )
        painter.setPen( needle_pen )
        painter.drawLine( 0, 0, - 2, 15 ) 
        
        painter.rotate( -55 )
        needle_pen.setWidth( 2 )
        painter.setPen( needle_pen )
        painter.drawLine( 0, 0, 4, - 13 )
        
        painter.rotate( - 55 )
        needle_pen.setWidth( 3 )
        painter.setPen( needle_pen )
        painter.drawLine( 0, 0, -10, - 11 )

    def drawGauge( self, painter ):
        painter.drawEllipse( QPoint( 50, 45 ), 20, 20 )
        painter.translate( 50, 45 )
        painter.rotate( -135 )
        for i in range( 6 ):  
            painter.drawLine( 0, - 15, 0, - 12 )
            painter.rotate( 54 )
        painter.drawLine( 0, 0, 14, 10 )

    def drawDial( self, painter ):
        painter.drawEllipse( QPoint( 50, 40 ), 20, 20 )
        painter.drawLine( 50, 25, 50, 30 )

    def drawToggle( self, painter ):
        painter.drawLine( 35, 40, 65, 40 )
        painter.drawLine( 35, 60, 65, 60 )
        painter.drawArc( 25, 40, 20, 20, 90 * 16, 16 * 180 )
        painter.drawArc( 55, 40, 20, 20, 90 * 16, - 16 * 180 )
        painter.setBrush( QColor( 255, 255, 255 ) )
        painter.drawEllipse( QPoint( 63, 50 ), 8, 8 )
        rect = QRect( 25, 40, 30, 20 )
        painter.setFont( QFont( "Arial", 8, QFont.Weight.Normal ) )
        painter.drawText( rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignCenter, "ON" )

    def drawScrollBar( self, painter ):
        painter.drawLine( 25, 40, 75, 40 )
        painter.drawLine( 25, 50, 75, 50 )
        painter.drawArc( 20, 40, 10, 10, 90 * 16, 16 * 180 )
        painter.drawArc( 71, 40, 10, 10, 90 * 16, - 16 * 180 )
        painter.setBrush( QColor( 255, 255, 255 ) )
        painter.drawRect( 30, 42, 20, 6 )
        painter.drawPie( 27, 42, 6, 6, 90 * 16, 16 * 180 )
        painter.drawPie( 47, 42, 6, 6, 90 * 16, - 16 * 180 )

    def drawSlider( self, painter ):
        painter.drawLine( 17, 42, 78, 42 )
        painter.drawLine( 17, 48, 78, 48 )
        painter.drawArc( 15, 42, 6, 6, 90 * 16, 16 * 180 )
        painter.drawArc( 75, 42, 6, 6, 90 * 16, - 16 * 180 )
        painter.setBrush( QColor( 255, 255, 255 ) )
        painter.drawEllipse( QPoint( 50, 45 ), 6, 6 )

    def drawProgressBar( self, painter ):
        painter.drawLine( 25, 40, 75, 40 )
        painter.drawLine( 25, 50, 75, 50 )
        painter.drawLine( 60, 40, 60, 50 )
        painter.drawArc( 20, 40, 10, 10, 90 * 16, 16 * 180 )
        painter.drawArc( 70, 40, 10, 10, 90 * 16, - 16 * 180 )
        painter.setBrush( QColor( 255, 255, 255 ) )
        painter.drawPie( 22, 42, 6, 6, 90 * 16, 16 * 180 )
        painter.drawRect( 25, 42, 35, 6 )

    def drawImage( self, painter ):
        painter.drawRoundedRect( 25, 20, 50, 50, 5, 5 )
        painter.drawLine( 27, 68, 45, 45 )
        painter.drawLine( 45, 45, 65, 70 )
        painter.drawLine( 55, 55, 65, 45 )
        painter.drawLine( 65, 45, 75, 58 )
        painter.drawArc( 15, 10, 25, 25, 0 * 16, - 16 * 90 )
        painter.translate( 25, 20 )
        painter.rotate( 110 )

        for i in range( 3 ):  
            painter.drawLine( 0, - 20, 0, - 17 )
            painter.rotate( 25 )

    def drawLabel( self, painter ):
        painter.drawLine( 20, 40, 65, 40 )
        painter.drawLine( 20, 60, 65, 60 )
        painter.drawLine( 20, 40, 20, 60 )
        painter.drawLine( 65, 40, 80, 50 )
        painter.drawLine( 65, 60, 80, 50 )
        painter.setFont( QFont( "Arial", 8, QFont.Weight.Normal ) )
        rect = QRect( 30, 40, 30, 20 )
        painter.drawText( rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignCenter, "Text" )

    def drawNumeric( self, painter ):
        rect = QRect( 25, 35, 50, 30 )
        painter.drawText( rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignCenter, "123" )
        painter.drawRoundedRect( rect, 0, 0 )

    def createCustomCursor( self ):
        pix = QPixmap( 300, 130 )
        pix.fill( Qt.GlobalColor.transparent )
        painter = QPainter( pix )
        painter.setPen( QPen( QColor( 150, 202, 232 ), 2 ) )
        
        cursor_actions = {
            "Line": lambda: painter.drawLine( 0, 0, 100, 100 ),
            "Rectangle": lambda: painter.drawRect( 0, 0, 100, 80 ),
            "Circle": lambda: painter.drawEllipse( QPoint( 50, 50 ), 50, 50 ),
            "Ellipse":lambda: painter.drawEllipse( QPoint( 62, 42 ), 60, 40 ),
            "Button": lambda: painter.drawRoundedRect( 0, 0, 100, 50, 5, 5 ),
            "Keys": lambda: painter.drawRect( 0, 0, 286, 112 ),
            "Clock": lambda: painter.drawEllipse( QPoint( 50, 50 ), 50, 50 ),
            "Gauge": lambda: painter.drawEllipse( QPoint( 50, 50 ), 50, 50 ),
            "Dial": lambda: painter.drawEllipse( QPoint( 50, 50 ), 40, 40 ),
            "Toggle": lambda: painter.drawRoundedRect( 0, 0, 80, 30, 10, 10 ),
            "Scroll bar": lambda: painter.drawRoundedRect( 0, 0, 200, 15, 3, 3 ),
            "Slider": lambda: painter.drawRoundedRect( 0, 0, 200, 30, 3, 3 ),
            "Progress bar": lambda: painter.drawRoundedRect( 0, 0, 200, 15, 3, 3 ),
            "Image": lambda: painter.drawRect( 0, 0, 100, 100 ),
            "Label": lambda: painter.drawRect( 0, 0, 55, 42 ),
            "Numeric": lambda: painter.drawRect( 0, 0, 52, 42 )
        }
        
        if self.shape in cursor_actions:
            cursor_actions[ self.shape ]()
        
        painter.end()
        hot_spots = {

            "Line": ( 0, 0 ),  
            "Rectangle": ( 0, 0 ),
            "Circle": ( 50, 50 ),
            "Ellipse": ( 62, 42 ),             
            "Button": ( 0, 0 ),
            "Keys": ( 0, 0 ), 
            "Clock": ( 50, 50 ),                        
            "Gauge": ( 50, 50 ), 
            "Dial": ( 50, 50 ), 
            "Toggle": ( 0, 0 ), 
            "Scroll bar": ( 0, 0 ), 
            "Slider": ( 0, 0 ), 
            "Progress bar": ( 0, 0 ), 
            "Image": ( 0, 0 ), 
            "Label": ( 0, 0 ), 
            "Numeric": ( 0, 0 ), 
        }
    
        hot_spot_x, hot_spot_y = hot_spots.get( self.shape, ( 16, 16 ) )
        QApplication.setOverrideCursor( QCursor( pix, hot_spot_x, hot_spot_y ) )

    def mousePressEvent( self, event ):
        if event.button() == Qt.MouseButton.LeftButton:
            main_window = self.window()
            if getattr( main_window, "object_attached", False ):
                QApplication.restoreOverrideCursor()
                main_window.object_attached = False
                main_window.selected_shape = None
            else:
                self.createCustomCursor()
                main_window.object_attached = True
                main_window.selected_shape = self.shape

    def enterEvent( self, event ):
        super().enterEvent( event )

        palette = self.palette()
        palette.setColor( QPalette.ColorRole.Window, self.hover_color )
        self.setPalette( palette )
        
    def leaveEvent( self, event ):
        super().leaveEvent( event )

        palette = self.palette()
        palette.setColor( QPalette.ColorRole.Window, self.default_color )
        self.setPalette( palette )

class ColorRectangle( QLabel ):
    def __init__( self, initial_color = "white" ):
        super().__init__()
        self._color = initial_color
        self.setFixedSize( 20, 20 )
        self.updateDisplay()
        self.setCursor( Qt.CursorShape.PointingHandCursor )
        
    def updateDisplay( self ):
        self.setStyleSheet( f"background-color: { self._color }; border: 1px solid #383838;" )
    
    def getColor( self ):
        return self._color
        
    def setColor( self, value ):
        self._color = value
        self.updateDisplay()
        
    def mousePressEvent( self, event ):
        super().mousePressEvent( event )

        if event.button() == Qt.MouseButton.LeftButton:
            new_color = QColorDialog.getColor( QColor( self._color ) )

            if new_color.isValid():
                self._color = new_color.name()
                self.updateDisplay()

                if hasattr( self, 'colorChanged' ):
                    self.colorChanged.emit( self._color )

class Canvas( QWidget ):
    clicked = pyqtSignal( object )
    
    def __init__( self, parent = None ):
        super().__init__( parent )

        self.defaultValues()
        self.setupUI()
        self.setupDataDict()

    def defaultValues( self ):
        self.canvas_id = 0
        self.active = True
        self.visible = True
        self.static = False
        self.custom_name = ""
        self.canvas_color = QColor( 168, 168, 168 )
        self.canvas_grid_enable = False
        self.grid_color = QColor( 0, 0, 0 )
        self.grid_type = "Lines"
        self.grid_size = 20

    def setupUI( self ):
        self.setFixedSize( 480, 272 )
        
        self.container = QWidget( self )
        self.container.setGeometry ( 0, 0, 480, 272 )
        self.container.setStyleSheet( "background-color: white; border: 1px solid #ccc;" )
        
        self.widget_container = QWidget( self.container )
        self.widget_container.setGeometry( 0, 0, 480, 272 )
        self.widget_container.setStyleSheet( "background-color: transparent;" )
        
        self.canvas_label = QLabel( self.container )
        self.canvas_label.setGeometry( 0, 0, 480, 272 )
        self.canvas_label.setAlignment( Qt.AlignmentFlag.AlignCenter )
        self.canvas_label.lower()

    def paintEvent(self, event ):
        pixmap = QPixmap( 480, 272 )
        pixmap.fill(self.canvas_color)

        if self.canvas_grid_enable:
            painter = QPainter( pixmap )
            grid_color = QColor( self.grid_color )
            painter.setPen( QPen( grid_color, 1 ) )
            
            if self.grid_type == "Lines":
                for x in range( 0, 481, self.grid_size ):
                    painter.drawLine( x, 0, x, 272 )

                for y in range( 0, 273, self.grid_size ):
                    painter.drawLine( 0, y, 480, y )

            elif self.grid_type == "Dots":
                dot_size = 2

                for x in range( self.grid_size // 2, 481, self.grid_size ):

                    for y in range( self.grid_size // 2, 273, self.grid_size ):
                        painter.drawEllipse( x - dot_size // 2, y - dot_size // 2, dot_size, dot_size )

            painter.end()

        super().update()
        self.canvas_label.setPixmap( pixmap )
        self.canvas_label.lower()

    def setupDataDict( self ):
        self.data_dict = {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'background_color': self.canvas_color,
            'grid_enable': self.canvas_grid_enable,
            'grid_color': self.grid_color ,
            'grid_type': self.grid_type,
            'grid_size': self.grid_size,
            'id': self.canvas_id,
            'widgets': []
        }
    
    def updateDataDict( self ):
        self.data_dict.update( {
            'active': self.active,
            'visible': self.visible,
            'static': self.static,
            'name': self.custom_name,
            'background_color': self.canvas_color,
            'grid_enable': self.canvas_grid_enable,
            'grid_color': self.grid_color,
            'grid_type': self.grid_type,
            'grid_size': self.grid_size
        } )
        return self.data_dict
    
    def addWidgetData( self, widget_dict ):
        self.data_dict[ 'widgets' ].append( widget_dict )
    
    def removeWidgetData( self, widget_id ):
        self.data_dict['widgets'] = [ w for w in self.data_dict[ 'widgets' ] if w.get( 'id' ) != widget_id ]
    
    def getDataDict( self ):
        return self.data_dict

    def mousePressEvent( self, event ):
        super().mousePressEvent( event )
        
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit( event )