from PyQt6.QtGui import QColor

def widgetStructureMapping():
    return {
        'Line': 'ft800_designer_line',
        'Rectangle': 'ft800_designer_rectangle',
        'Circle': 'ft800_designer_circle',
        'Ellipse': 'ft800_designer_ellipse',
        'Button': 'ft800_designer_button',
        'Keys': 'ft800_designer_keys',
        'Clock': 'ft800_designer_clock',
        'Gauge': 'ft800_designer_gauge',
        'Dial': 'ft800_designer_dial',
        'Toggle': 'ft800_designer_toggle',
        'ScrollBar': 'ft800_designer_scroll_bar',
        'Slider': 'ft800_designer_slider',
        'ProgressBar': 'ft800_designer_progress_bar',
        'Image': 'ft800_designer_image',
        'Label': 'ft800_designer_label',
        'Numeric': 'ft800_designer_numeric'
    }

def widgetFunctionMapping():
    return {
            'Line': 'ft800_line_designer',
            'Rectangle': 'ft800_rectangle_designer',
            'Circle': 'ft800_circle_designer',
            'Ellipse': 'ft800_ellipse_designer',
            'Button': 'ft800_button_designer',
            'Keys': 'ft800_keys_designer',
            'Clock': 'ft800_clock_designer',
            'Gauge': 'ft800_gauge_designer',
            'Dial': 'ft800_dial_designer',
            'Toggle': 'ft800_toggle_designer',
            'ScrollBar': 'ft800_scroll_bar_designer',
            'Slider': 'ft800_slider_designer',
            'ProgressBar': 'ft800_progress_bar_designer',
            'Image': 'ft800_image_designer',
            'Label': 'ft800_label_designer',
            'Numeric': 'ft800_numeric_designer'
    }


def convertColorToHex( color ):
    if isinstance( color, QColor ):
        return f"0x{color.red():02X}{color.green():02X}{color.blue():02X}"
    
    elif isinstance( color, str ):
        try:
            qcolor = QColor( color )

            return f"0x{qcolor.red():02X}{qcolor.green():02X}{qcolor.blue():02X}"
        
        except:
            return color
        
    else:
        return color

def convertBool( value ):
    if value:
        return 'true'  
    
    else: 
        return 'false'

def convertGridType( grid_type ) :
    if grid_type == 'Dots':
        return 'FT800_GRID_DOTS'
    
    elif grid_type == 'Lines':
        return 'FT800_GRID_LINE'

def convert3dEnabled( value ):
    if value:
        return 'FT800_3D'
      
    else: 
        return 'FT800_FLAT'

def convertAlignment( alignment ):
    mapping = {
        'Left': 'FT800_ALIGN_LEFT',
        'Right': 'FT800_ALIGN_RIGHT',
        'Center': 'FT800_ALIGN_CENTER',
        'Horisontaly': 'FT800_ALIGN_HORISONTALY',
        'Verticaly': 'FT800_ALIGN_VERTICALY',
    }

    return mapping.get( alignment, 'FT800_ALIGN_LEFT' )

def convertGradientType( gradient_type ):
    mapping = {
        'Top-Bottom': 'FT800_TOP_BOTTOM_GRADIENT',
        'Bottom-Top': 'FT800_BOTTOM_TOP_GRADIENT',
        'Left-Right': 'FT800_LEFT_RIGHT_GRADIENT',
        'Right-Left': 'FT800_RIGHT_LEFT_GRADIENT',
    }

    return mapping.get( gradient_type, 'FT800_TOP_BOTTOM_GRADIENT' )

def convertKeyboardType( key_type ):
    mapping = {
        'NUM': 'FT800_KEYBOARD_NUM',
        'QUERTZ': 'FT800_KEYBOARD_QUERTZ',
    }

    return mapping.get( key_type, 'FT800_KEYBOARD_NUM' )

def convertToggleState( state ):
    if state:
        return 'FT800_ON'  
        
    else: 
        return 'FT800_OFF'
    
def scaleValue( value ):
    return int( value * 65535 / 100 )