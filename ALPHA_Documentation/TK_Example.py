from tkinter import *

window = Tk()
window.title("Welcome to LikeGeeks app")
window.geometry('350x200')

# lbl = Label(window, text="Hello", font=("Arial Bold", 50))
lbl = Label(window, text="Hello")
lbl.grid(column=0, row=0)


def clicked():
    lbl.configure(text="Button was clicked !!")


btn = Button(window, text="Click Me", command=clicked)

btn.grid(column=1, row=0)

window.mainloop()
