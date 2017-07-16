"""
EUCLIDES
A geometric shooter
"""

import math
import itertools
import point


class Polygon:
    """ Class to create and handle convex regular polygons """

    def __init__(self, radius, n):
        """ A polygon is defined with
            radius: radius of its outer circle
            n: will be an n-sided polygon
        """
        self.__tkid = None
        self.__setup(radius, n)

    def __str__(self):
        """ List the polygons typical points (center and corners) """
        center = "The polygon's center is at {}.\n".format(self.__center)
        coords = ", ".join([str(p) for p in self.__corners])
        coord = "Its coordinates are: {}.".format(coords)
        return center + coord

    @property
    def tkid(self):
        """ Return this polygon's tkinter object id """
        return self.__tkid

    @tkid.setter
    def tkid(self, tkid):
        """ Set this polygons tkinter object id """
        self.__tkid = tkid

    def coords(self):
        """ Return the polygon's coordinates as a tuple
            Tkinter needs this format in .coords() """
        coord = [(corner.x, corner.y) for corner in self.__corners]
        return tuple(itertools.chain.from_iterable(coord))

    def move(self, x, y):
        """ Set this polygon's center points and corners as well.
            x: new horizontal coordinate of polygons center point
            y: new vertical coordinate of polygons center point
        """
        offset_x = x - self.__center.x
        offset_y = y - self.__center.y
        self.__center.move(offset_x, offset_y)
        for corner in self.__corners:
            corner.move(offset_x, offset_y)

    def __setup(self, radius, n):
        """ Set up the polygon. 
            Begin with its center point, then the top corner and proceed clockwise.
            radius: radius of 
            n: n-sided polygon
        """
        p = point.Point()  # working variable
        # looks better than point.Point(p.x, p.y)
        self.__center = p.next(p.x, p.y)
        self.__corners = []
        half = math.pi / n  # half of the interior angle (in radians: 2pi/n/2)
        edge = 2 * radius * math.sin(half)
        angle = half  # starting angle
        p.move(0, -radius)  # move point to the top
        for i in range(n):
            self.__corners.append(p.next(p.x, p.y))
            p.shift(edge, angle)
            angle += half * 2


def test():
    """ Testing this class """
    p = Polygon(5, 7)
    print(p)
    print(p.coords())
    p.move(2, 2)
    print(p)


if __name__ == "__main__":
    test()
