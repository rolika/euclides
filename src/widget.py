"""
EUCLIDES
A geometric shooter
"""

import tkinter as tk
from tkinter import ttk
import const


class GameField(tk.Canvas):
    """ This will hold the game """

    def __init__(self, root=None):
        """ Init game field """
        super().__init__(root)
        self["height"] = const.GAME_HEIGHT
        self["width"] = const.GAME_WIDTH
        self["bg"] = const.BG_COLOR
        self.grid()

    def add_poly(self, polygon):
        """ Add a polygon to the canvas and set its tkinter id.
            polygon: a Polygon-object
        """
        polygon.tkid = self.create_polygon(
            polygon.coords(), fill="", outline=const.FG_COLOR)

    def move_poly(self, polygon, x, y):
        """ Relocate polygon on the canvas.
            polygon: a Polygon-object
            x: new horizontal coordinate of polygons center point
            y: new vertical coordinate of polygons center point
        """
        polygon.move(x, y)
        self.coords(polygon.tkid, *polygon.coords())


def test():
    """ Testing this class """
    import polygon
    g = GameField()
    p = polygon.Polygon(20, 3)
    p.move(320, 200)
    g.add_poly(p)
    g.bind("<Motion>", lambda event: g.move_poly(p, event.x, event.y))
    g.mainloop()


if __name__ == "__main__":
    test()
