#!/usr/bin/env python3.6
"""
EUCLIDES
A geometric shooter
main executable script
"""

import tkinter as tk
from tkinter import ttk
import polygon

WIDTH = 640
HEIGHT = 480
BG_COLOR = "black"


class Euclides(tk.Canvas):
    """ Main game application """

    def __init__(self, root=None):
        """ Init game field """
        super().__init__(root)
        self["height"] = HEIGHT
        self["width"] = WIDTH
        self["bg"] = BG_COLOR
        self.grid()

        p = polygon.Polygon(100, 12)
        p.create(self)


def main():
    """ Run game """
    Euclides().mainloop()


if __name__ == "__main__":
    main()
