import tkinter

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