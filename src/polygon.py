"""
EUCLIDES
A geometric shooter
"""

import math
import point


class Polygon:
    """ Class to create and handle convex regular polygons """

    def __init__(self, radius, n):
        """ A polygon is defined with
            radius: radius of its outer circle
            n: will be an n-sided polygon
        """
        self.__radius = radius
        self.__setup(n)

    def __str__(self):
        """ List the poligons tipical points (center and corners) """
        center = "The polygon's center is at {}.\n".format(self.__center)
        coords = ", ".join([str(p) for p in self.__corners])
        coord = "Its coordinates are: {}.".format(coords)
        return center + coord

    def create(self, canvas):
        """ Create a tkinter-polygon using the coordinates """
        self.__poly = canvas.create_polygon(*self.__coords, fill="", outline="white")

    def draw(self, canvas):
        """ Draw this polygon on the canvas """
        canvas.coords(self.__poly, *self.__coords)

    def __setup(self, n):
        """ Set up the polygon. 
            Begin with its center point, then the top corner and proceed clockwise.
            n: n-sided polygon
        """
        p = point.Point()  # working variable
        self.__center = p.next(p.x, p.y)  # looks better than point.Point(p.x, p.y)
        self.__corners = []
        half = math.pi / n  # half of the interior angle (in radians: 2pi/n/2)
        edge = 2 * self.__radius * math.sin(half)
        angle = half  # starting angle
        p.move(0, -self.__radius)  # move point to the top
        for i in range(n):
            self.__corners.append(p.next(p.x, p.y))
            p.shift(edge, angle)
            angle += half * 2
        self.__coords = [(corner.x, corner.y) for corner in self.__corners]


def test():
    """ Testing this class """
    p = Polygon(5, 7)
    print(p)


if __name__ == "__main__":
    test()
