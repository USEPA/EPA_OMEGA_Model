def tab_stylesheet(stylesheet):
    """
        Loads the stylesheet for the tab area of the gui.

        :param stylesheet: Not used.

        :return: String containing stylesheet.
        """
    stylesheet = """
                QTabBar::tab { 
                    background: #bae3c0;    /* Sets the color of the selected tab */
                    min-width: 150px;       /* Sets the width of the tabs */
                    height: 30px;           /* Sets the height of the tabs */
                    }
                QTabWidget::tab-bar { 
                    left: 15px;             /* Moves the tabs to the right */
                    }    
                QTabWidget {
                    background: lightgray;  /* Sets the color of the unselected tabs */
                    }
                """
    return stylesheet
