def tab_stylesheet(stylesheet):
    """
        Loads the stylesheet for the tab area of the gui.

        :param stylesheet: Not used.

        :return: String containing stylesheet.
        """
    stylesheet = """
            QTabBar::tab { 
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                            stop: 0 rgb(00, 113, 188), stop: 1.0 rgb(00, 113, 188));
                min-width: 150px;       /* Sets the width of the tabs */
                height: 30px;           /* Sets the height of the tabs */
                padding-top : 0px;      /* Sets extra space at the top of the tabs */
                padding-bottom : 0px;   /* Sets extra space at the bottom of the tabs */
                color: white;            /* Sets the text color and frame color of the tabs */
                font: 12pt "Arial";     /* Sets the font for the tabs */
                }
            QTabBar::tab:hover { 
                font: bold;
                }    
            QTabWidget::tab-bar { 
                left: 15px;             /* Moves the tabs to the right */
                }    
            QTabWidget::pane {
                border-top: 4px solid gray;     /* Sets the border color and thickness of the tab area */
                border-left: 4px solid gray;
                border-right: 4px solid gray;
                border-bottom: 4px solid gray;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 rgb(00, 113, 188), stop: 1.0 rgb(00, 113, 188));
                }  
            QTabBar::tab:!selected {
                margin-top: 2px; /* Shrinks non-selected tabs */
                }
            QTabWidget {
                background: rgb(32,84,147);  /* Sets the color of the unselected tabs */
                }
            """
    return stylesheet


def background_stylesheet(stylesheet):
    """
        Loads the stylesheet for the main window of the gui.

        :param stylesheet: Not used.

        :return: String containing stylesheet.
        """
    stylesheet = """
        QWidget {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 rgb(00, 113, 188), stop: 1.0 rgb(00, 113, 188));
            }
     """
    return stylesheet


def button_stylesheet(stylesheet):
    """
        Loads the stylesheet for buttons contained in the gui.

        :param stylesheet: Not used.

        :return: String containing stylesheet.
        """
    stylesheet = """
        QPushButton {
        background-color: rgb(32,84,147);
        border: 1px solid white;
        border-radius: 6px;
        }
        QPushButton:enabled {
        background-color: rgb(32,84,147); 
        border: 1px solid white;
        color: white;
        }
        QPushButton:hover {
        border: 2px solid white;
        border-radius: 6px;
        font: bold;
        color: white;
        }
        QPushButton:pressed {
        border: 4px solid rgb(60,60,60);
        border-radius: 6px;
        font: bold;
        color: white;
        }
     """
    return stylesheet


def label_stylesheet(stylesheet):
    """
        Loads the stylesheet for labels contained in the gui.

        :param stylesheet: Not used.

        :return: String containing stylesheet.
        """
    stylesheet = """
        QLabel { color : white; }
     """
    return stylesheet


def checkbox_stylesheet(stylesheet):
    """
        Loads the stylesheet for checkboxes contained in the gui.

        :param stylesheet: Not used.

        :return: String containing stylesheet.
        """
    stylesheet = """
        QCheckBox { color : white; }
     """
    return stylesheet


def test1(stylesheet):
    stylesheet = """
        QTabBar::tab { 
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 rgb(181, 232, 181), stop: 1.0 rgb(147, 188, 147));
            min-width: 150px;       /* Sets the width of the tabs */
            height: 30px;           /* Sets the height of the tabs */
            padding-top : 0px;      /* Sets extra space at the top of the tabs */
            padding-bottom : 0px;   /* Sets extra space at the bottom of the tabs */
            color: rgb(0,0,0);            /* Sets the text color and frame color of the tabs */
            font: 12pt "Arial";     /* Sets the font for the tabs */
            }
        QTabBar::tab:hover { 
            font: bold;
            }    
        QTabWidget::tab-bar { 
            left: 15px;             /* Moves the tabs to the right */
            }    
        QTabWidget::pane {
            border-top: 4px solid gray;     /* Sets the border color and thickness of the tab area */
            border-left: 4px solid gray;
            border-right: 4px solid gray;
            border-bottom: 4px solid gray;
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgb(181, 232, 181), stop: 1.0 rgb(147, 188, 147));
            }  
        QTabBar::tab:!selected {
            margin-top: 2px; /* Shrinks non-selected tabs */
            }
        QTabWidget {
            background: rgb(170,170,170);  /* Sets the color of the unselected tabs */
            }
        """
    return stylesheet

