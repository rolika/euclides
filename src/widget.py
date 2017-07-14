"""
EUCLIDES
A geometric shooter
"""

import tkinter as tk
from tkinter import ttk

WIDTH = 640
HEIGHT = 480
BG_COLOR = "black"


class GameField(tk.Canvas):
    """ This will hold the game """

    def __init__(self, root=None):
        """ Init game field """
        super().__init__(root)
        self["height"] = HEIGHT
        self["width"] = WIDTH
        self["bg"] = BG_COLOR
        self.grid()


def test():
    """ Testing this class """
    import polygon
    p = polygon.Polygon(50, 9)
    g = GameField()
    p.create(g)
    g.mainloop()


if __name__ == "__main__":
    test()
