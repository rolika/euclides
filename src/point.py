"""
EUCLIDES
A geometric shooter
"""

import math


class Point:
    """ Class to create and move 2-dimensional points """

    def __init__(self, x=0, y=0):
        """ A point is defined by its x and y coordinates """
        self.__x = x
        self.__y = y

    def __str__(self):
        """ String representation of a point: (x,y) """
        return "({:.2f},{:.2f})".format(self.__x, self.__y)

    @property
    def x(self):
        """ Return the x coordinate in pixels, always as integer """
        return round(self.__x)

    @property
    def y(self):
        """ Return the y coordinate in pixels, always as integer """
        return round(self.__y)

    @x.setter
    def x(self, x):
        """ Set the x coordinate in pixels """
        self.__x = x

    @y.setter
    def y(self, y):
        """ Set the y coordinate in pixels """
        self.__y = y

    @classmethod
    def next(cls, x, y):
        """ Create a new instance with these coordinates """
        return cls(x, y)

    def distance(self, other):
        """ Return the distance between this and other point """
        return math.sqrt((self.__x - other.x)**2 + (self.__y - other.y)**2)

    def move(self, offset_x, offset_y):
        """ Offset this point by offset_y and offset_y pixels """
        self.__x += offset_x
        self.__y += offset_y

    def shift(self, distance, angle):
        """ Shift this point at angle to distance
        If angle is float, threat it as radians, if integer, as degrees """
        if isinstance(angle, int):
            angle = math.radians(angle)
        offset_x = distance * math.cos(angle)
        offset_y = distance * math.sin(angle)
        self.move(offset_x, offset_y)

    def rotate(self, center, angle):
        """ Rotate this point around centerpoint at angle
        If angle is float, threat it as radians, if integer, as degrees """
        if isinstance(angle, int):
            angle = math.radians(angle)
        # translate point to origin (0, 0)
        self.move(-center.x, -center.y)
        # rotate point
        x = self.__x * math.cos(angle) - self.__y * math.sin(angle)
        y = self.__x * math.sin(angle) + self.__y * math.cos(angle)
        # translate point back
        self.__x = x + center.x
        self.__y = y + center.y


def test():
    """ Testing this class """
    o = Point()
    p = Point(2, 2)
    print(p)
    p.x = 3
    p.y = 4
    print(p)
    q = Point(9, 10)
    print(q.distance(p))
    p.shift(2, 0)  # push point horizontally by 2 pixels
    print(p)
    p.shift(math.sqrt(2), 45)
    print(p)
    q.move(0, -10)
    print(q)
    q.rotate(o, 90)
    print(q)


if __name__ == "__main__":
    test()
