"""TK_Example
   ----------"""

import tkinter


def function_with_types_in_docstring(param1, param2):
    """
    Document a function using a docstring.

    Parameters
    ----------
    param1 : int
        The first input.
    param2 : str
        The second input.

    Returns
    -------
    param3 : str
        The first output.
    param4 : str
        The second output.
    """


def function_with_types_in_docstring1(param1, param2):
    """
    Document a function using a docstring.

    Parameters
    ----------
    param1 : int
        The first input.
    param2 : str
        The second input.

    Returns
    -------
    param3 : str
        The first output.
    param4 : str
        The second output.
    """


"""
    This is a test
    Hello"""



"""TK_Example2
   -----------"""

window = tkinter.Tk()
window.title("Welcome to LikeGeeks app")
window.geometry('350x200')

# lbl = Label(window, text="Hello", font=("Arial Bold", 50))
lbl = tkinter.Label(window, text="Hello")
lbl.grid(column=0, row=0)

"""This Defines Click
   =================="""


def clicked():
    lbl.configure(text="Button was clicked !!")


btn = tkinter.Button(window, text="Click Me", command=clicked)

btn.grid(column=1, row=0)

window.mainloop()
