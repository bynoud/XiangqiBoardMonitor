# import sys
# if sys.version_info[0] == 2:  # Just checking your Python version to import Tkinter properly.
#     import Tkinter as tk
# else:
#     import tkinter as tk
# import numpy as np
# import ctypes, cv2
from PIL import Image, ImageTk, ImageGrab

# ctypes.windll.shcore.SetProcessDpiAwareness(1)

# def screen_cap():
#     npimg = ImageGrab.grab()
#     # npimg = cv2.cvtColor(np.array(npimg), cv2.COLOR_BGR2GRAY)
#     return npimg
#     # return ImageTk.PhotoImage(image=Image.fromarray(npimg))


# # class Fullscreen_Window:

# #     def __init__(self):
# #         self.tk = Tk.Tk()
# #         # self.tk.attributes('-zoomed', True)  # This just maximizes it so we can see the window. It's nothing to do with fullscreen.
# #         # self.frame = Tk.Frame(self.tk)
# #         # self.frame.pack()
# #         self.state = False
# #         self.tk.bind("<F11>", self.toggle_fullscreen)
# #         self.tk.bind("<Escape>", self.end_fullscreen)

# #         img = Tk.PhotoImage(file='board.png')
# #         label = Tk.Label(self.tk, image=img)
# #         label.pack()

# #     def toggle_fullscreen(self, event=None):
# #         self.state = not self.state  # Just toggling the boolean
# #         self.tk.attributes("-fullscreen", self.state)
# #         # if self.state:
# #         #     img = Tk.PhotoImage(file='board.png')
# #         #     label = Tk.Label(self.tk, image=img)
# #         #     label.pack()
# #         return "break"

# #     def end_fullscreen(self, event=None):
# #         self.state = False
# #         self.tk.attributes("-fullscreen", False)
# #         return "break"

# # if __name__ == '__main__':
# #     w = Fullscreen_Window()
# #     w.tk.mainloop()

# class Window:

#     def __init__(self, image):
#         self.image = image

#         self.root = tk.Tk()
#         self.widgets()
#         # self.root.attributes("-fullscreen", True)
#         self.root.bind("<Escape>", self.end_fullscreen)
#         self.root.mainloop()
#     def widgets(self):
#         # img = tk.PhotoImage(file=self.image) #.subsample(2,2)
#         # img = ImageGrab.grab()
#         img = ImageTk.PhotoImage(image=self.image) #Image.fromarray(self.sc))
#         label = tk.Label(self.root, image=img)
#         label.pack()
#     def end_fullscreen(self, event=None):
#         self.root.attributes("-fullscreen", False)

# if __name__ == "__main__":
#     image = "board.png"
#     Window(ImageGrab.grab())

# # Import the required libraries
# from tkinter import *
import pyautogui
# from PIL import ImageTk, Image

# # Create an instance of tknter frame or window
# win = Tk()

# # Set the size of the window
# win.geometry("700x350")


# # Define a function to take the screenshot
# def take_screenshot():
#     import time
#     #    x = 500
#     #    y = 500
#     #    # Take the screenshot in the given corrds
#     # win.withdraw()
#     # time.sleep(0.2)

#     im1 = pyautogui.screenshot()  # region=(x, y, 700, 300))

#     # Create a toplevel window
#     top = Toplevel(win)
#     canvas = Canvas(top,bg='black')
#     im1 = ImageTk.PhotoImage(im1)

#     # Add the image in the label widget
#     # image1 = Label(top, image=im1)
#     # image1.image = im1
#     # image1.place(x=0, y=0)

#     canvas.create_image(0,0,image=im1,anchor='nw')

#     # canvas.bind("<ButtonPress-1>", lambda ev=None: print('mouse down', ev.x, ev.y))
#     # canvas.bind("<ButtonRelease-1>", lambda ev=None: print('mouse up', ev.x, ev.y))
#     # canvas.bind("<B1-Motion>", lambda ev=None: print('mouse move', ev.x, ev.y))

#     canvas.pack(expand=YES)

#     # top.attributes("-fullscreen", True)
#     # top.bind("<Escape>", show_mainwin(top))

# def show_mainwin(top):
#     def fn(ev=None):
#         top.attributes("-fullscreen", False)
#         win.deiconify()
#     return fn


# Button(win, text='Take ScreenShot',
#        command=take_screenshot).pack(padx=10, pady=10)

# win.mainloop()


try:
    import tkinter as tk
    from tkinter.constants import *
except ImportError:  # Python 2.x
    import Tkinter as tk
    from Tkconstants import *

# Create the canvas, size in pixels.
canvas = tk.Canvas(width=300, height=200, bg='black')

# Pack the canvas into the Frame.
canvas.pack(expand=YES, fill=BOTH)

# Load the .gif image file.
# gif1 = tk.PhotoImage(file='board.png')
gif1 = ImageTk.PhotoImage(pyautogui.screenshot())

# Put gif image on canvas.
# Pic's upper-left corner (NW) on the canvas is at x=50 y=10.
canvas.create_image(50, 10, image=gif1, anchor=NW)

# Run it...
tk.mainloop()
