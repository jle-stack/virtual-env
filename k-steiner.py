import numpy as np
import math
import copy
import time
import gurobipy as gp
from gurobipy import GRB
import matplotlib.pyplot as plt

def find(lst, a):
    return [i for i, x in enumerate(lst) if x == a]

def rotate(origin, point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    The angle should be given in radians.
    """
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return [qx, qy]

def angle(b, a):
    """
    finds the angle of vertex b from vertex a (measured anticlockwise between 0 and 2 * pi)
    """
    eps = 0.00001

    if abs(b[0] - a[0]) < eps and b[1] > a[1]:
        angle = np.pi / 2
    elif abs(b[0] - a[0]) < eps and b[1] < a[1]:
        angle = 3 * np.pi / 2

    else:
        angle = math.atan((b[1] - a[1]) / (b[0] - a[0]))

        if b[0] - a[0] < 0:
            angle += np.pi
        elif b[1] - a[1] < 0:
            angle += 2 * np.pi

    return angle

def dist(a, b):
    """
    Calculates the Euclidean distance between two points
    """
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def eqpoint(a, b):
    """
    Calculates the equilateral point of a and b (ordered)
    """
    x_a, y_a = a
    x_b, y_b = b

    x_ab = x_a + 1 / 2 * (x_b - x_a) - math.sqrt(3) / 2 * (y_b - y_a)
    y_ab = y_a + math.sqrt(3) / 2 * (x_b - x_a) + 1 / 2 * (y_b - y_a)

    return [x_ab, y_ab]

def line_arc_intersection(point1, point2, line_type, arc):
    # finds the intersection point(s) between a line (defined by pseudo1 and pseudo2) and an arc

    # line_type = 0 for a line segment (want one solution)
    #           = 0.5 for a line segment (want two solutions)
    #           = 1 for a ray with initial point point1 (intersection counts if it is beyond point2)
    #           = 2 for a line

    eps = 0.0001
    # solving aax^2 + bbx + cc = 0 gives the intersection point(s)
    if point2[0] - point1[0] != 0:
        # y = mx + c is the equation of the line going through the two pseudoterminals
        m = (point2[1] - point1[1]) / (point2[0] - point1[0])
        c = point1[1] - m * point1[0]

        aa = m ** 2 + 1
        bb = 2 * m * c - 2 * arc[0] - 2 * arc[1] * m
        cc = arc[0] ** 2 + arc[1] ** 2 + c ** 2 - 2 * arc[1] * c - arc[2] ** 2

        if bb ** 2 - 4 * aa * cc < 0:
            return 0
        elif bb ** 2 - 4 * aa * cc == 0:
            x_soln = -bb / (2 * aa)
            y_soln = m * x_soln + c
            potential_solns = [[x_soln, y_soln]]

        # bb ** 2 - 4 * aa * cc > 0
        else:
            sqrt_term = math.sqrt(bb ** 2 - 4 * aa * cc)
            x_soln1 = (-bb + sqrt_term) / (2 * aa)
            y_soln1 = m * x_soln1 + c
            x_soln2 = (-bb - sqrt_term) / (2 * aa)
            y_soln2 = m * x_soln2 + c
            potential_solns = [[x_soln1, y_soln1], [x_soln2, y_soln2]]

        actual_solns = []

        # line segment (one solution)
        if line_type == 0:
            for soln in potential_solns:
                # check whether this intersection point is between the two angles
                soln_angle = angle(soln, [arc[0], arc[1]])

                if arc[4] >= soln_angle >= arc[3]:
                    if (soln[0] - point1[0]) * (soln[0] - point2[0]) <= 0 and (soln[1] - point1[1]) * (soln[1] - point2[1]) <= 0:
                        if dist(soln, point1) > eps:
                            actual_solns.append(soln)
                elif arc[3] > arc[4] and (soln_angle <= arc[4] or soln_angle >= arc[3]):
                    if (soln[0] - point1[0]) * (soln[0] - point2[0]) <= 0 and (soln[1] - point1[1]) * (soln[1] - point2[1]) <= 0:
                        if dist(soln, point1) > eps:
                            actual_solns.append(soln)

            if len(actual_solns) == 1:
                return actual_solns[0]
            else:
                return 0

        # line segment (two solutions)
        if line_type == 0.5:
            for soln in potential_solns:
                # check whether this intersection point is between the two angles
                soln_angle = angle(soln, [arc[0], arc[1]])

                if arc[3] == arc[4]:
                    if (soln[0] - point1[0]) * (soln[0] - point2[0]) <= 0 and (soln[1] - point1[1]) * (soln[1] - point2[1]) <= 0:
                        actual_solns.append(soln)
                elif arc[4] >= soln_angle >= arc[3]:
                    if (soln[0] - point1[0]) * (soln[0] - point2[0]) <= 0 and (soln[1] - point1[1]) * (soln[1] - point2[1]) <= 0:
                        actual_solns.append(soln)
                elif arc[3] > arc[4] and (soln_angle <= arc[4] or soln_angle >= arc[3]):
                    if (soln[0] - point1[0]) * (soln[0] - point2[0]) <= 0 and (soln[1] - point1[1]) * (soln[1] - point2[1]) <= 0:
                        actual_solns.append(soln)

            if len(actual_solns) == 0:
                return 0
            else:
                return actual_solns

        # ray with initial point point1
        elif line_type == 1:
            for soln in potential_solns:
                # check whether this intersection point is between the two angles
                soln_angle = angle(soln, [arc[0], arc[1]])

                if arc[4] >= soln_angle >= arc[3]:
                    if (soln[0] - point1[0]) * (soln[0] - point2[0]) >= 0 or (soln[1] - point1[1]) * (soln[1] - point2[1]) >= 0:
                        if dist(soln, point1) > eps:
                            actual_solns.append(soln)
                elif arc[3] > arc[4] and (soln_angle <= arc[4] or soln_angle >= arc[3]):
                    if (soln[0] - point1[0]) * (soln[0] - point2[0]) >= 0 or (soln[1] - point1[1]) * (soln[1] - point2[1]) >= 0:
                        if dist(soln, point1) > eps:
                            actual_solns.append(soln)

            if len(actual_solns) == 1:
                return actual_solns[0]
            else:
                return 0

        # line
        else:
            for soln in potential_solns:
                # check whether this intersection point is between the two angles
                soln_angle = angle(soln, [arc[0], arc[1]])

                if arc[3] == arc[4]:
                    actual_solns.append(soln)
                elif arc[4] >= soln_angle >= arc[3]:
                    actual_solns.append(soln)
                elif arc[3] > arc[4] and (soln_angle <= arc[4] or soln_angle >= arc[3]):
                    actual_solns.append(soln)

            if len(actual_solns) == 0:
                return 0
            else:
                return actual_solns

    else:
        x_soln = point1[0]

        if x_soln < arc[0] - arc[2] or x_soln > arc[0] + arc[2]:
            return 0

        sqrt_term = math.sqrt(arc[2] ** 2 - (x_soln - arc[0]) ** 2)

        if sqrt_term == 0:
            potential_solns = [[x_soln, arc[1]]]
        else:
            potential_solns = [[x_soln, arc[1] + sqrt_term], [x_soln, arc[1] - sqrt_term]]

        actual_solns = []

        # line segment (one solution)
        if line_type == 0:
            for soln in potential_solns:
                # check whether this intersection point is between the two angles
                soln_angle = angle(soln, [arc[0], arc[1]])

                if arc[4] >= soln_angle >= arc[3]:
                    if (soln[1] - point1[1]) * (soln[1] - point2[1]) <= 0:
                        actual_solns.append(soln)
                elif arc[3] > arc[4] and (soln_angle <= arc[4] or soln_angle >= arc[3]):
                    if (soln[1] - point1[1]) * (soln[1] - point2[1]) <= 0:
                        actual_solns.append(soln)

            if len(actual_solns) == 1:
                return actual_solns[0]
            else:
                return 0

        # line segment (two solutions)
        if line_type == 0.5:
            for soln in potential_solns:
                # check whether this intersection point is between the two angles
                soln_angle = angle(soln, [arc[0], arc[1]])

                if arc[3] == arc[4]:
                    if (soln[0] - point1[0]) * (soln[0] - point2[0]) <= 0 and (soln[1] - point1[1]) * (soln[1] - point2[1]) <= 0:
                        actual_solns.append(soln)
                elif arc[4] >= soln_angle >= arc[3]:
                    if (soln[0] - point1[0]) * (soln[0] - point2[0]) <= 0 and (soln[1] - point1[1]) * (soln[1] - point2[1]) <= 0:
                        actual_solns.append(soln)
                elif arc[3] > arc[4] and (soln_angle <= arc[4] or soln_angle >= arc[3]):
                    if (soln[0] - point1[0]) * (soln[0] - point2[0]) <= 0 and (soln[1] - point1[1]) * (soln[1] - point2[1]) <= 0:
                        actual_solns.append(soln)

            if len(actual_solns) == 0:
                return 0
            else:
                return actual_solns

        # ray with initial point point1
        elif line_type == 1:
            for soln in potential_solns:
                # check whether this intersection point is between the two angles
                soln_angle = angle(soln, [arc[0], arc[1]])

                if arc[4] >= soln_angle >= arc[3]:
                    if (soln[0] - point1[0]) * (soln[0] - point2[0]) >= 0 or (soln[1] - point1[1]) * (soln[1] - point2[1]) >= 0:
                        if dist(soln, point1) > eps:
                            actual_solns.append(soln)
                elif arc[3] > arc[4] and (soln_angle <= arc[4] or soln_angle >= arc[3]):
                    if (soln[0] - point1[0]) * (soln[0] - point2[0]) >= 0 or (soln[1] - point1[1]) * (soln[1] - point2[1]) >= 0:
                        if dist(soln, point1) > eps:
                            actual_solns.append(soln)

            if len(actual_solns) == 1:
                return actual_solns[0]
            else:
                return 0

        # line
        else:
            for soln in potential_solns:
                # check whether this intersection point is between the two angles
                soln_angle = angle(soln, [arc[0], arc[1]])

                if arc[3] == arc[4]:
                    actual_solns.append(soln)
                elif arc[4] >= soln_angle >= arc[3]:
                    actual_solns.append(soln)
                elif arc[3] > arc[4] and (soln_angle <= arc[4] or soln_angle >= arc[3]):
                    actual_solns.append(soln)

            if len(actual_solns) == 0:
                return 0
            else:
                return actual_solns

def line_intersection(line1, line2, type1, type2):
    # line1 = [point1, point2]
    # type1 = 0 if line1 is a line segment,
    #       = 1 if line1 is a ray with initial point point1
    #       = 2 if line1 is a line
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
        return 0

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div

    if type1 == 0:
        if (x - line1[0][0]) * (x - line1[1][0]) > 0 or (y - line1[0][1]) * (y - line1[1][1]) > 0:
            return 0
    elif type1 == 1:
        if (x - line1[0][0]) * (line1[1][0] - line1[0][0]) < 0 or (y - line1[0][1]) * (line1[1][1] - line1[0][1]) < 0:
            return 0

    if type2 == 0:
        if (x - line2[0][0]) * (x - line2[1][0]) > 0 or (y - line2[0][1]) * (y - line2[1][1]) > 0:
            return 0
    elif type2 == 1:
        if (x - line2[0][0]) * (line2[1][0] - line2[0][0]) < 0 or (y - line2[0][1]) * (line2[1][1] - line2[0][1]) < 0:
            return 0

    return [x, y]

def MST(points):
    mst = []
    intree = [0]
    outtree = list(range(1, len(points)))

    for i in range(len(points) - 1):
        mindist = 99

        for qi in range(len(intree)):
            for qj in range(len(outtree)):
                a = intree[qi]
                b = outtree[qj]
                if dist(points[a], points[b]) < mindist:
                    mina = a
                    minb = b
                    mindist = dist(points[a], points[b])

        intree = np.append(intree, minb)
        outtree.remove(minb)
        mst.append([mina, minb])
    return mst

def intersect(arc1, arc2):
    """
    finds all intersection point(s) between arc1 and arc2
    arc = [centrex, centrey, radius, angle1, angle2]
    """

    d = dist([arc1[0], arc1[1]], [arc2[0], arc2[1]])

    if arc1[2] + arc2[2] > d and -d < arc1[2] - arc2[2] < d:
        parasoln = (arc1[2] ** 2 - arc2[2] ** 2 + d ** 2) / (2 * d)
        perpsoln = math.sqrt(arc1[2] ** 2 - parasoln ** 2)

        x2 = arc1[0] + parasoln / d * (arc2[0] - arc1[0])
        y2 = arc1[1] + parasoln / d * (arc2[1] - arc1[1])

        x31 = x2 + perpsoln / d * (arc2[1] - arc1[1])
        x32 = x2 - perpsoln / d * (arc2[1] - arc1[1])

        y31 = y2 - perpsoln / d * (arc2[0] - arc1[0])
        y32 = y2 + perpsoln / d * (arc2[0] - arc1[0])

        solutions = [[x31, y31], [x32, y32]]

    elif arc1[2] + arc2[2] == d:
        x3 = arc1[0] + arc1[2] / d * (arc2[0] - arc1[0])
        y3 = arc1[1] + arc1[2] / d * (arc2[1] - arc1[1])
        solutions = [[x3, y3]]

    elif arc1[2] - arc2[2] == d:
        x3 = arc1[0] + arc1[2] / d * (arc2[0] - arc1[0])
        y3 = arc1[1] + arc1[2] / d * (arc2[1] - arc1[1])
        solutions = [[x3, y3]]

    elif arc2[2] - arc1[2] == d:
        x3 = arc2[0] + arc2[2] / d * (arc1[0] - arc2[0])
        y3 = arc2[1] + arc2[2] / d * (arc1[1] - arc2[1])
        solutions = [[x3, y3]]

    else:
        return 0

    # """

    feasiblesolutions = []
    for solution in solutions:
        arc1angle = angle(solution, [arc1[0], arc1[1]])
        arc2angle = angle(solution, [arc2[0], arc2[1]])

        if arc1[4] < arc1[3]:
            if arc1[3] > arc1angle > arc1[4]:
                continue

        elif arc1[3] < arc1[4]:
            if arc1angle < arc1[3] or arc1angle > arc1[4]:
                continue

        if arc2[4] < arc2[3]:
            if arc2[3] > arc2angle > arc2[4]:
                continue

        elif arc2[3] < arc2[4]:
            if arc2angle < arc2[3] or arc2angle > arc2[4]:
                continue

        feasiblesolutions.append(solution)

    if len(feasiblesolutions) == 1:
        return feasiblesolutions[0]
    elif len(feasiblesolutions) > 1:
        return feasiblesolutions
    else:
        return 0

def double_projection_arc(a_or_b, b1, b2, circle):

    if a_or_b == "a":
        arc = b1[2]
        # if radius of arc a is not 0, then a is not a terminal
        if arc[2] != 0:

            r_a = [arc[0] + arc[2] * math.cos(arc[3]),
                   arc[1] + arc[2] * math.sin(arc[3])]

            l_a = [arc[0] + arc[2] * math.cos(arc[4]),
                   arc[1] + arc[2] * math.sin(arc[4])]

            # l_a is outside the circle
            if dist(l_a, [circle[0], circle[1]]) > circle[2]:
                return 0

            # l_a is inside the circle and r_a is outside
            elif dist(r_a, [circle[0], circle[1]]) > circle[2]:

                p = line_arc_intersection(b1[1], l_a, 1, circle)
                q = intersect(circle, b1[2])

                if q == 0:
                    return 0

                # p does not lie on arc ab
                if p == 0:
                    angle1 = angle(q, [circle[0], circle[1]])
                    angle2 = angle(b2[1], [circle[0], circle[1]])

                    return [angle1, angle2]

                # p does lie on arc ab
                else:
                    angle1 = angle(q, [circle[0], circle[1]])
                    angle2 = angle(p, [circle[0], circle[1]])

                    return [angle1, angle2]

            # l_a is inside the circle and r_a is inside
            else:
                p = line_arc_intersection(b1[1], l_a, 1, circle)
                q = line_arc_intersection(b1[1], r_a, 1, circle)

                if q == 0:
                    return 0

                # q lies on arc ab, p does not
                if p == 0:
                    angle1 = angle(q, [circle[0], circle[1]])
                    angle2 = angle(b2[1], [circle[0], circle[1]])

                    return [angle1, angle2]

                # both p and q lies on arc ab
                else:
                    angle1 = angle(q, [circle[0], circle[1]])
                    angle2 = angle(p, [circle[0], circle[1]])

                    return [angle1, angle2]

        # a is a terminal
        else:
            return [circle[3], circle[4]]

    # a_or_b == "b"
    else:
        arc = b2[2]
        # if radius of arc b is not 0, then b is not a terminal
        if arc[2] != 0:

            r_a = [arc[0] + arc[2] * math.cos(arc[3]),
                   arc[1] + arc[2] * math.sin(arc[3])]

            l_a = [arc[0] + arc[2] * math.cos(arc[4]),
                   arc[1] + arc[2] * math.sin(arc[4])]

            # r_b is outside the circle
            if dist(r_a, [circle[0], circle[1]]) > circle[2]:
                return 0

            # r_b is inside the circle and l_b is outside
            elif dist(l_a, [circle[0], circle[1]]) > circle[2]:

                q = line_arc_intersection(b2[1], r_a, 1, circle)
                p = intersect(circle, b2[2])

                if p == 0:
                    return 0

                # q does not lie on arc ab
                if q == 0:
                    angle1 = angle(b1[1], [circle[0], circle[1]])
                    angle2 = angle(p, [circle[0], circle[1]])

                    return [angle1, angle2]

                # q does lie on arc ab
                else:
                    angle1 = angle(q, [circle[0], circle[1]])
                    angle2 = angle(p, [circle[0], circle[1]])

                    return [angle1, angle2]

            # r_b is inside the circle and l_b is inside
            else:
                p = line_arc_intersection(b2[1], l_a, 1, circle)
                q = line_arc_intersection(b2[1], r_a, 1, circle)

                if p == 0:
                    return 0

                # p lies on arc ab, q does not
                if q == 0:
                    angle1 = angle(b1[1], [circle[0], circle[1]])
                    angle2 = angle(p, [circle[0], circle[1]])


                    return [angle1, angle2]

                # both p and q lies on arc ab
                else:
                    angle1 = angle(q, [circle[0], circle[1]])
                    angle2 = angle(p, [circle[0], circle[1]])

                    return [angle1, angle2]

        # a is a terminal
        else:
            return [circle[3], circle[4]]


def double_projection_seg(a_or_b, b1, b2, circle):

    if a_or_b == "a":
        segarc_ints = line_arc_intersection([b1[2][2], b1[2][3]], [b1[2][0], b1[2][1]], 0.5, circle)

        r_a = [b1[2][0], b1[2][1]]
        l_a = [b1[2][2], b1[2][3]]

        # no intersections
        if segarc_ints == 0:
            q = line_arc_intersection(b1[1], r_a, 1, circle)

            if q == 0:
                return 0
            else:
                p = line_arc_intersection(b1[1], l_a, 1, circle)
                if p == 0:
                    return [angle(q, [circle[0], circle[1]]), circle[4]]
                else:
                    return [angle(q, [circle[0], circle[1]]), angle(p, [circle[0], circle[1]])]

        # one intersection
        elif len(segarc_ints) == 1:
            q = segarc_ints[0]
            tangent_checker = len(line_arc_intersection(l_a, r_a, 2, [circle[0], circle[1], circle[2], 0, 0]))

            # tangent
            if tangent_checker == 1:
                return 0
            else:
                p = line_arc_intersection(b1[1], l_a, 1, circle)
                if p == 0:
                    return [angle(q, [circle[0], circle[1]]), circle[4]]
                else:
                    return [angle(q, [circle[0], circle[1]]), angle(p, [circle[0], circle[1]])]

        # two intersections
        else:
            angle1 = angle(segarc_ints[0], [circle[0], circle[1]])
            angle2 = angle(segarc_ints[1], [circle[0], circle[1]])

            if circle[4] >= circle[3]:
                if angle2 >= angle1:
                    return [angle1, angle2]
                else:
                    return [angle2, angle1]
            else:
                if angle1 <= circle[4] and angle2 >= circle[3]:
                    return [angle2, angle1]
                elif angle2 <= circle[4] and angle1 >= circle[3]:
                    return [angle1, angle2]
                elif angle2 >= angle1:
                    return [angle1, angle2]
                else:
                    return [angle2, angle1]

    # a_or_b == "b":
    else:
        segarc_ints = line_arc_intersection([b2[2][2], b2[2][3]], [b2[2][0], b2[2][1]], 0.5, circle)

        r_b = [b2[2][0], b2[2][1]]
        l_b = [b2[2][2], b2[2][3]]

        # no intersections
        if segarc_ints == 0:
            p = line_arc_intersection(b2[1], l_b, 1, circle)

            if p == 0:
                return 0
            else:
                q = line_arc_intersection(b2[1], r_b, 1, circle)
                if q == 0:
                    return [circle[3], angle(p, [circle[0], circle[1]])]
                else:
                    return [angle(q, [circle[0], circle[1]]), angle(p, [circle[0], circle[1]])]

        # one intersection
        elif len(segarc_ints) == 1:
            p = segarc_ints[0]
            tangent_checker = len(line_arc_intersection(l_b, r_b, 2, [circle[0], circle[1], circle[2], 0, 0]))

            # tangent
            if tangent_checker == 1:
                return 0
            else:
                q = line_arc_intersection(b2[1], r_b, 1, circle)
                if q == 0:
                    return [circle[3], angle(p, [circle[0], circle[1]])]
                else:
                    return [angle(q, [circle[0], circle[1]]), angle(p, [circle[0], circle[1]])]

        # two intersections
        else:
            angle1 = angle(segarc_ints[0], [circle[0], circle[1]])
            angle2 = angle(segarc_ints[1], [circle[0], circle[1]])

            if circle[4] >= circle[3]:
                if angle2 >= angle1:
                    return [angle1, angle2]
                else:
                    return [angle2, angle1]
            else:
                if angle1 <= circle[4] and angle2 >= circle[3]:
                    return [angle2, angle1]
                elif angle2 <= circle[4] and angle1 >= circle[3]:
                    return [angle1, angle2]
                elif angle2 >= angle1:
                    return [angle1, angle2]
                else:
                    return [angle2, angle1]




def double_projection(b1, b2, circle):

    # interval a is an arc
    if len(b1[2]) == 5:
        a_interval = double_projection_arc("a", b1, b2, circle)
        if a_interval == 0:
            return 0

    # interval a is a segment
    else:
        a_interval = double_projection_seg("a", b1, b2, circle)
        if a_interval == 0:
            return 0

    # interval b is an arc
    if len(b2[2]) == 5:
        b_interval = double_projection_arc("b", b1, b2, circle)
        if b_interval == 0:
            return 0

    # interval b is a segment
    else:
        b_interval = double_projection_seg("b", b1, b2, circle)
        if b_interval == 0:
            return 0

    # now find intersection of a_interval and b_interval
    fullarc_angle1 = angle(b1[1], [circle[0], circle[1]])
    fullarc_angle2 = angle(b2[1], [circle[0], circle[1]])

    if fullarc_angle2 >= fullarc_angle1:
        angle1 = max(a_interval[0], b_interval[0])
        angle2 = min(a_interval[1], b_interval[1])

        if angle2 >= angle1:
            return [angle1, angle2]
        else:
            return 0

    else:
        for index, endpoint_angle in enumerate(a_interval):
            if endpoint_angle <= fullarc_angle2:
                a_interval[index] += 2 * np.pi

        for index, endpoint_angle in enumerate(b_interval):
            if endpoint_angle <= fullarc_angle2:
                b_interval[index] += 2 * np.pi

        angle1 = max(a_interval[0], b_interval[0])
        angle2 = min(a_interval[1], b_interval[1])

        if angle2 > angle1:
            return [angle1 % (2*np.pi), angle2 % (2*np.pi)]
        else:
            return 0


def double_merge(b1, b2):
    new_pseudo = eqpoint(b1[1], b2[1])
    new_arc_centre = [(b1[1][0] + b2[1][0] + new_pseudo[0]) / 3,
                      (b1[1][1] + b2[1][1] + new_pseudo[1]) / 3]

    new_arc_radius = dist(b1[1], new_arc_centre)
    new_arc_angle1 = angle(b1[1], new_arc_centre)
    new_arc_angle2 = angle(b2[1], new_arc_centre)

    circle = [new_arc_centre[0], new_arc_centre[1], new_arc_radius, new_arc_angle1, new_arc_angle2]
    newangles = double_projection(b1, b2, circle)

    if newangles == 0:
        return 0

    newarc = [new_arc_centre[0], new_arc_centre[1], new_arc_radius, newangles[0], newangles[1]]

    b1vertices = copy.deepcopy(b1[0])
    b2vertices = copy.deepcopy(b2[0])

    for i in range(len(b2vertices) - 1):
        b2vertices[i][3] += len(b1vertices)

    b1vertices[-1][3] = len(b1vertices) + len(b2vertices)
    b2vertices[-1][3] = len(b1vertices) + len(b2vertices)

    new_vertex_list = b1vertices + b2vertices + [[-1, -1, -1, -1]]

    new_arc = newarc
    new_terminal_list = list(set(b1[3]) | set(b2[3]))

    return [new_vertex_list, new_pseudo, new_arc, new_terminal_list, b1[4] + b2[4]]


def triple_merge_checker(b1, b2, b3):
    pseudo_1 = b1[1]
    pseudo_2 = b2[1]
    pseudo_3 = b3[1]

    vector_12 = [pseudo_2[x] - pseudo_1[x] for x in range(2)]
    vector_13 = [pseudo_3[x] - pseudo_1[x] for x in range(2)]

    sign = np.cross(vector_12, vector_13).tolist()

    # pseudoterminals 1, 2 and 3 are collinear and cannot be triple merged
    if sign == 0:
        return 0

    elif sign > 0:
        order = [[0, 2, 1], [2, 1, 0], [1, 0, 2]]

    else:
        order = [[0, 1, 2], [1, 2, 0], [2, 0, 1]]

    return order

def triple_projection(b1, b2, b3):
    # checks whether two branches can be termination merged

    # interval a is an arc
    if len(b1[2]) == 5:
        # b1 is a terminal
        if b1[2][2] == 0:
            steiner_location_1 = b1[1]
        else:
            steiner_location_1 = line_arc_intersection(b1[1], b3[1], 0, b1[2])
        if steiner_location_1 == 0:
            return 0

    # interval a is a segment
    else:
        steiner_location_1 = line_intersection([b1[1], b3[1]], [[b1[2][0], b1[2][1]], [b1[2][2], b1[2][3]]], 0, 0)
        if steiner_location_1 == 0:
            return 0

    # interval b is an arc
    if len(b3[2]) == 5:
        # b3 is a terminal
        if b3[2][2] == 0:
            steiner_location_2 = b3[1]
        else:
            steiner_location_2 = line_arc_intersection(b3[1], b1[1], 0, b3[2])
        if steiner_location_2 == 0:
            return 0

    # interval b is a segment
    else:
        steiner_location_2 = line_intersection([b1[1], b3[1]], [[b3[2][0], b3[2][1]], [b3[2][2], b3[2][3]]], 0, 0)
        if steiner_location_2 == 0:
            return 0

    angle_1 = angle(steiner_location_1, b2[1])
    angle_2 = angle(steiner_location_2, b2[1])

    # if source interval is a segment
    if len(b2[2]) == 4:
        source_angle_1 = angle([b2[2][0], b2[2][1]], b2[1])
        source_angle_2 = angle([b2[2][2], b2[2][3]], b2[1])
    # if source interval is an arc
    else:
        if b2[2][2] == 0:
            return [steiner_location_1[0], steiner_location_1[1], steiner_location_2[0], steiner_location_2[1]]

        source_angle_1 = angle([b2[2][0] + b2[2][2] * math.cos(b2[2][3]), b2[2][1] + b2[2][2] * math.sin(b2[2][3])], b2[1])
        source_angle_2 = angle([b2[2][0] + b2[2][2] * math.cos(b2[2][4]), b2[2][1] + b2[2][2] * math.sin(b2[2][4])], b2[1])

    if source_angle_2 >= source_angle_1 and angle_2 >= angle_1:
        lower = max(angle_1, source_angle_1)
        upper = min(angle_2, source_angle_2)
        if lower > upper:
            return 0
        else:
            final_1 = lower
            final_2 = upper

    elif source_angle_2 >= source_angle_1:
        lower_1 = max(source_angle_1, angle_1)
        upper_1 = min(source_angle_2, angle_2 + 2 * np.pi)
        if upper_1 >= lower_1:
            final_1 = lower_1
            final_2 = upper_1
        else:
            lower_2 = max(source_angle_1, angle_1 - 2 * np.pi)
            upper_2 = min(source_angle_2, angle_2)

            if lower_2 > upper_2:
                return 0
            else:
                final_1 = lower_2
                final_2 = upper_2

    elif angle_2 >= angle_1:
        lower_1 = max(angle_1, source_angle_1)
        upper_1 = min(angle_2, source_angle_2 + 2 * np.pi)
        if upper_1 >= lower_1:
            final_1 = lower_1
            final_2 = upper_1
        else:
            lower_2 = max(angle_1, source_angle_1 - 2 * np.pi)
            upper_2 = min(angle_2, source_angle_2)

            if lower_2 > upper_2:
                return 0
            else:
                final_1 = lower_2
                final_2 = upper_2

    else:
        final_1 = max(angle_1, source_angle_1)
        final_2 = min(angle_2, source_angle_2)

    final_1_projection = [b2[1][0] + math.cos(final_1), b2[1][1] + math.sin(final_1)]
    final_2_projection = [b2[1][0] + math.cos(final_2), b2[1][1] + math.sin(final_2)]

    int_1 = line_intersection([steiner_location_1, steiner_location_2], [b2[1], final_1_projection], 2, 1)
    int_2 = line_intersection([steiner_location_1, steiner_location_2], [b2[1], final_2_projection], 2, 1)

    return [int_1[0], int_1[1], int_2[0], int_2[1]]


def triple_merge(b1, b2, b3):

    new_segment = triple_projection(b1, b2, b3)
    if new_segment == 0:
        return 0

    b1vertices = copy.deepcopy(b1[0])
    b2vertices = copy.deepcopy(b2[0])
    b3vertices = copy.deepcopy(b3[0])

    for i in range(len(b2vertices) - 1):
        b2vertices[i][3] += len(b1vertices)

    for i in range(len(b3vertices) - 1):
        b3vertices[i][3] += len(b1vertices) + len(b2vertices)

    b1vertices[-1][3] = len(b1vertices) + len(b2vertices) + len(b3vertices)
    b2vertices[-1][3] = len(b1vertices) + len(b2vertices) + len(b3vertices)
    b3vertices[-1][3] = len(b1vertices) + len(b2vertices) + len(b3vertices)

    new_vertex_list = b1vertices + b2vertices + b3vertices + [[-1, -1, -2, -1]]

    new_pseudo = b2[1]

    new_terminal_list = list(set(b1[3]) | set(b2[3]) | set(b3[3]))

    partial_length = dist(b1[1], b3[1])

    return [new_vertex_list, new_pseudo, new_segment, new_terminal_list, b1[4] + b2[4] + b3[4] + partial_length]

def termination_check(b1, terminal):
    # checks whether b1 can be terminated with t

    # arc
    if len(b1[2]) == 5:

        centre = [b1[2][0], b1[2][1]]

        if dist(centre, terminal) <= b1[2][2]:
            return 0

        terminal_angle = angle(terminal, centre)

        if b1[2][4] >= terminal_angle >= b1[2][3]:
            x_steiner_location = centre[0] + b1[2][2] * math.cos(terminal_angle)
            y_steiner_location = centre[1] + b1[2][2] * math.sin(terminal_angle)
            return [x_steiner_location, y_steiner_location]

        elif b1[2][3] > b1[2][4] and (terminal_angle <= b1[2][4] or terminal_angle >= b1[2][3]):
            x_steiner_location = centre[0] + b1[2][2] * math.cos(terminal_angle)
            y_steiner_location = centre[1] + b1[2][2] * math.sin(terminal_angle)
            return [x_steiner_location, y_steiner_location]

        else:
            return 0

    #segment
    else:
        soln = line_intersection([b1[1], terminal], [[b1[2][0],b1[2][1]], [b1[2][2], b1[2][3]]], 0, 0)
        if soln == 0:
            return 0
        else:
            return soln


def termination_merge(b1, N, t):
    # b1 is the branch, t is the index of the terminal, N is the list of terminals
    terminal = N[t]
    result = termination_check(b1, terminal)

    # cannot be terminated
    if result == 0:
        return 0

    else:
        b1vertices = copy.deepcopy(b1[0])
        b1vertices[-1][3] = len(b1vertices)

        FST_vertices = b1vertices + [[terminal[0], terminal[1], t, -1]]
        # no pseudoterminal
        pseudo = 0
        # no arc/segment
        arcseg = 0
        new_terminal_list = list(set(b1[3]) | {t})

        length = dist(b1[1], terminal)

        FST = [FST_vertices, pseudo, arcseg, new_terminal_list, b1[4] + length]

    return FST


def concatenation(FST_set, terminal_no, max_steiner_no):
    concat_start = time.perf_counter()

    FST_no = 0

    for i in range(max_steiner_no + 1):
        FST_no += len(FST_set[i])

    # number of Steiner points in each hyperedge
    S = [0 for i in range(FST_no)]
    # length of each hyperedge
    L = [0 for i in range(FST_no)]
    # terminals in each hyperedge
    T = [0 for i in range(FST_no)]

    FST_index = 0
    for i in range(max_steiner_no + 1):
        for fst in FST_set[i]:
            S[FST_index] = len(fst[0]) - len(fst[3])
            L[FST_index] = fst[4]
            T[FST_index] = fst[3]
            FST_index += 1


    # number of iterations
    iter = 1
    # number of cut-constraints implemented
    cutno = 0

    milp_model = gp.Model("milp")
    milp_model.Params.LogToConsole = 0

    x = milp_model.addVars(FST_no, vtype=GRB.BINARY)

    milp_model.setObjective(sum(L[i] * x[i] for i in range(FST_no)), GRB.MINIMIZE)
    c2 = milp_model.addConstr(sum(S[i] * x[i] for i in range(FST_no)) <= max_steiner_no)

    milp_model.optimize()

    xvalues = np.zeros((FST_no), dtype=int)
    for i in range(FST_no):
        xvalues[i] = x[i].x

    print("Number of iterations is " + str(iter))
    print("Number of cut-constraints implemented is " + str(cutno) + " out of a possible " + str(2 ** (terminal_no - 1) - 1))
    components = [i for i in range(terminal_no)]

    hypertree = find(xvalues, 1)
    for i in range(len(hypertree)):
        currenthyper = hypertree[i]
        vincurrenthyper = T[currenthyper]

        comps = [components[i] for i in vincurrenthyper]
        aa = len(comps)
        compsnodouble = list(set(comps))
        ab = len(compsnodouble)

        nextitcomp = np.min(compsnodouble)

        for j in range(ab):
            if nextitcomp != compsnodouble[j]:
                tempind = find(components, compsnodouble[j])
                for k in tempind:
                    components[k] = nextitcomp

    # number of comps in the current graph
    noofcomps = len(list(set(components)))

    print(components)

    while noofcomps > 1.5:

        if noofcomps == 2:
            # labels of different components
            dfjeqns = np.zeros((1, FST_no), dtype=int)
            cutno = cutno + 1

            for i in range(FST_no):
                currenth = T[i]

                # currentcompv denotes all vertices in the current component
                currentcompv = find(components, 0)
                # notcurrentcompv denotes all vertices not in the current component
                notcurrentcompv = list(set(range(terminal_no)) - set(currentcompv))

                if len(set(currentcompv) - set(currenth)) < len(currentcompv) and \
                        len(set(notcurrentcompv) - set(currenth)) < len(notcurrentcompv):
                    dfjeqns[0, i] = 1

            milp_model.addConstr(sum(x[i] * dfjeqns[0, i] for i in range(FST_no)) >= 1)

        elif noofcomps >= 3:
            # labels of different components
            l = list(set(components))
            p = len(l)
            dfjeqns = np.zeros((p, FST_no), dtype=int)
            cutno = cutno + noofcomps

            for i in range(FST_no):
                currenth = T[i]

                for j in range(p):
                    # currentcompv denotes all vertices in the current component
                    currentcompv = find(components, l[j])
                    # notcurrentcompv denotes all vertices not in the current component
                    notcurrentcompv = list(set(range(terminal_no)) - set(currentcompv))

                    if len(set(currentcompv) - set(currenth)) < len(currentcompv) and \
                            len(set(notcurrentcompv) - set(currenth)) < len(notcurrentcompv):
                        dfjeqns[j, i] = 1

            milp_model.addConstrs(sum(x[i] * dfjeqns[j, i] for i in range(FST_no)) >= 1 for j in range(p))

        iter = iter + 1
        milp_model.optimize()

        xvalues = np.zeros((FST_no), dtype=int)
        for i in range(FST_no):
            xvalues[i] = x[i].x

        print("Number of iterations is " + str(iter))
        print("Number of cut-constraints implemented is " + str(cutno) + " out of a possible " + str(2 ** (terminal_no - 1) - 1))
        components = [i for i in range(terminal_no)]

        hypertree = find(xvalues, 1)
        for i in range(len(hypertree)):
            currenthyper = hypertree[i]
            vincurrenthyper = T[currenthyper]

            comps = [components[i] for i in vincurrenthyper]
            aa = len(comps)
            compsnodouble = list(set(comps))
            ab = len(compsnodouble)

            nextitcomp = np.min(compsnodouble)

            for j in range(ab):
                if nextitcomp != compsnodouble[j]:
                    tempind = find(components, compsnodouble[j])
                    for k in tempind:
                        components[k] = nextitcomp

        # number of comps in the current graph
        noofcomps = len(list(set(components)))

    htree = find(xvalues, 1)
    F_star = []
    for htree_index in htree:

        i = 0
        update_index = htree_index

        while update_index + 1 > len(FST_set[i]):
            update_index -= len(FST_set[i])
            i += 1

        fst = FST_set[i][update_index]
        print(f"one fst of the optimal soln is {fst}")
        F_star.append(fst)
    return F_star

def interval_plot(b1):
    # given a branch b1, this function plots its pseudoterminal and its arc or segment

    colour = list(np.random.uniform(0, 1, 3))

    # pseudoterminal
    plt.plot(b1[1][0], b1[1][1], marker='o', markersize=6,
             markeredgecolor=colour, markerfacecolor=colour)
    # arc
    if len(b1[2]) == 5:
        if b1[2][4] >= b1[2][3]:
            angles = np.linspace(b1[2][3], b1[2][4])
        else:
            angles = np.linspace(b1[2][3], b1[2][4] + 2*np.pi)

        x = [b1[2][0] + b1[2][2] * math.cos(theta) for theta in angles]
        y = [b1[2][1] + b1[2][2] * math.sin(theta) for theta in angles]
        plt.scatter(x, y, color=colour, marker='o', s=5)

        x_r = np.linspace(b1[1][0], 3 * (b1[2][0] + b1[2][2] * math.cos(b1[2][3]) - b1[1][0]) + b1[1][0])
        y_r = np.linspace(b1[1][1], 3 * (b1[2][1] + b1[2][2] * math.sin(b1[2][3]) - b1[1][1]) + b1[1][1])
        x_l = np.linspace(b1[1][0], 3 * (b1[2][0] + b1[2][2] * math.cos(b1[2][4]) - b1[1][0]) + b1[1][0])
        y_l = np.linspace(b1[1][1], 3 * (b1[2][1] + b1[2][2] * math.sin(b1[2][4]) - b1[1][1]) + b1[1][1])
        plt.scatter(x_r, y_r, color=colour, marker='o', s=5)
        plt.scatter(x_l, y_l, color=colour, marker='o', s=5)

    # segment
    else:
        x = np.linspace(b1[2][0], b1[2][2])
        y = np.linspace(b1[2][1], b1[2][3])
        plt.scatter(x, y, color=colour, marker='o', s=15)

        x_r = np.linspace(b1[1][0], b1[1][0] + 3 * (b1[2][0] - b1[1][0]))
        y_r = np.linspace(b1[1][1], b1[1][1] + 3 * (b1[2][1] - b1[1][1]))
        x_l = np.linspace(b1[1][0], b1[1][0] + 3 * (b1[2][2] - b1[1][0]))
        y_l = np.linspace(b1[1][1], b1[1][1] + 3 * (b1[2][3] - b1[1][1]))
        plt.scatter(x_r, y_r, color=colour, marker='o', s=5)
        plt.scatter(x_l, y_l, color=colour, marker='o', s=5)

    plt.axis('scaled')
    return


def cluster_plot(cluster, N):
    vertexlist = cluster[0]
    vertexno = len(cluster[0])

    for terminal_index in range(len(N)):
        plt.plot(N[terminal_index][0], N[terminal_index][1], marker='o', markersize=5,
                 markeredgecolor="k", markerfacecolor='k')

    for i in range(vertexno):
        if vertexlist[i][2] == -1:
            plt.plot(vertexlist[i][0], vertexlist[i][1],
                     marker='o', markersize=5, markeredgecolor="r", markerfacecolor='r')
        elif vertexlist[i][2] == -2:
            plt.plot(vertexlist[i][0], vertexlist[i][1],
                     marker='o', markersize=5, markeredgecolor="m", markerfacecolor='m')

    for j in range(vertexno - 1):
        plt.plot([vertexlist[j][0], vertexlist[vertexlist[j][3]][0]],
                 [vertexlist[j][1], vertexlist[vertexlist[j][3]][1]], color='b')

    plt.axis('scaled')
    plt.axis([0, 1, 0, 1])
    plt.show()
    return



def steiner(N):
    n = len(N)


    return n





def k_steiner(N, k):

    algstart = time.perf_counter()
    n = len(N)

    # B is the set of branches where B[0] is the set of branches with 0 steiner pt, ...
    B = [[] for i in range(k + 1)]

    # F is the set of FSTs where F[0] is the set of FSTs with 0 steiner pt, ...
    F = [[] for i in range(k + 1)]

    # Generate branches of size 0 (terminals)
    for terminal_no in range(n):
        B[0].append([[[N[terminal_no][0], N[terminal_no][1], terminal_no, -1]], N[terminal_no],
                     [N[terminal_no][0], N[terminal_no][1], 0, 0, 0], [terminal_no], 0])

    # Generate the MST and FSTs of size 0 (edges of the MST)
    mst = MST(N)
    for [u, v] in mst:
        edge_length = dist(N[u], N[v])
        F[0].append([[[N[u][0], N[u][1], u, 1], [N[v][0], N[v][1], v, -1]], -1, -1, [u, v], edge_length])

    # Generate branches and FSTs of size current_k
    for current_k in range(1, k + 1):
        print(f"Starting {current_k} Steiner pt generation - double merge")
        # double merging
        for k_1 in range(math.floor((current_k-1)/2) + 1):
            for index_1, branch_1 in enumerate(B[k_1]):

                # branch_1 and branch_2 have the same number of steiner pts
                if k_1 == current_k - k_1 - 1:
                    for index_2 in range(index_1):
                        branch_2 = B[current_k - k_1 - 1][index_2]
                        if any(x in branch_1[3] for x in branch_2[3]) is False:
                            branch_12 = double_merge(branch_1, branch_2)
                            if branch_12 != 0:
                                B[current_k].append(branch_12)
                            branch_21 = double_merge(branch_2, branch_1)
                            if branch_21 != 0:
                                B[current_k].append(branch_21)

                # branch_1 and branch_2 have a different number of steiner pts
                else:
                    for index_2, branch_2 in enumerate(B[current_k - k_1 - 1]):
                        if any(x in branch_1[3] for x in branch_2[3]) is False:
                            branch_12 = double_merge(branch_1, branch_2)
                            if branch_12 != 0:
                                B[current_k].append(branch_12)
                            branch_21 = double_merge(branch_2, branch_1)
                            if branch_21 != 0:
                                B[current_k].append(branch_21)


        # triple merging
        print(f"Starting {current_k} Steiner pt generation - triple merge")
        for k_3 in range(math.ceil((current_k - 1)/3), k):
            for index_3, branch_3 in enumerate(B[k_3]):
                for k_1 in range(math.floor((current_k - 1 - k_3)/2) + 1):
                    k_2 = current_k - 1 - k_3 - k_1

                    if k_3 > k_2 > k_1:
                        for index_2, branch_2 in enumerate(B[k_2]):
                            for index_1, branch_1 in enumerate(B[k_1]):
                                if len(list(set(branch_1[3])|set(branch_2[3])|set(branch_3[3]))) == len(branch_1[3]) + len(branch_2[3]) + len(branch_3[3]):
                                    order_triple = triple_merge_checker(branch_1, branch_2, branch_3)
                                    if order_triple != 0:
                                        branches = [branch_1, branch_2, branch_3]
                                        for order in order_triple:
                                            temp_branch = triple_merge(branches[order[0]], branches[order[1]], branches[order[2]])
                                            if temp_branch != 0:
                                                B[current_k].append(temp_branch)
                    elif k_3 == k_2 > k_1:
                        for index_2 in range(index_3):
                            branch_2 = B[k_2][index_2]
                            for index_1, branch_1 in enumerate(B[k_1]):
                                if len(list(set(branch_1[3])|set(branch_2[3])|set(branch_3[3]))) == len(branch_1[3]) + len(branch_2[3]) + len(branch_3[3]):
                                    order_triple = triple_merge_checker(branch_1, branch_2, branch_3)
                                    if order_triple != 0:
                                        branches = [branch_1, branch_2, branch_3]
                                        for order in order_triple:
                                            temp_branch = triple_merge(branches[order[0]], branches[order[1]], branches[order[2]])
                                            if temp_branch != 0:
                                                B[current_k].append(temp_branch)
                    elif k_3 > k_2 == k_1:
                        for index_2, branch_2 in enumerate(B[k_2]):
                            for index_1 in range(index_2):
                                branch_1 = B[k_1][index_1]
                                if len(list(set(branch_1[3])|set(branch_2[3])|set(branch_3[3]))) == len(branch_1[3]) + len(branch_2[3]) + len(branch_3[3]):
                                    order_triple = triple_merge_checker(branch_1, branch_2, branch_3)
                                    if order_triple != 0:
                                        branches = [branch_1, branch_2, branch_3]
                                        for order in order_triple:
                                            temp_branch = triple_merge(branches[order[0]], branches[order[1]], branches[order[2]])
                                            if temp_branch != 0:
                                                B[current_k].append(temp_branch)

                    # k_3 == k_2 == k_1
                    else:
                        for index_2 in range(index_3):
                            for index_1 in range(index_2):
                                branch_2 = B[k_2][index_2]
                                branch_1 = B[k_1][index_1]
                                if len(list(set(branch_1[3])|set(branch_2[3])|set(branch_3[3]))) == len(branch_1[3]) + len(branch_2[3]) + len(branch_3[3]):
                                    order_triple = triple_merge_checker(branch_1, branch_2, branch_3)
                                    if order_triple != 0:
                                        branches = [branch_1, branch_2, branch_3]
                                        for order in order_triple:
                                            temp_branch = triple_merge(branches[order[0]], branches[order[1]], branches[order[2]])
                                            if temp_branch != 0:
                                                B[current_k].append(temp_branch)

        # termination
        print(f"Starting {current_k} Steiner pt generation - termination")
        for branch_1 in B[current_k]:

            temp_list = [i for i in range(n)]
            max_index = max(branch_1[3])
            unvisited = [x for

                         x in temp_list if x > max_index]

            for terminal in unvisited:
                result = termination_merge(branch_1, N, terminal)

                # result != 0 when termination can occur
                if result != 0:
                    F[current_k].append(result)

    for i in range(k+1):
        print("number of branches with", i, "steiner pts is", len(B[i]))

        #for branch in B[i]:
            #print("branch", branch)

        print("number of FSTs with", i, "steiner pts is", len(F[i]))

        #for fst in F[i]:
            #print("fst", fst)

    half_time = time.perf_counter()
    gen_time = half_time - algstart
    print(f"time taken for generation phase is {gen_time}")
    opt = concatenation(F, n, k)

    algend = time.perf_counter()
    total_time = algend - algstart
    print(f"total time taken is {total_time}")

    return opt




"""
N = [[0,0], [1, 1], [3, 1]]
a1 = [[[0, 0, 0, -1]], [0, 0], [1, 0, 1, 0, 5*np.pi/6], [0]]
a2 = [[[10, 0, 3, -1]], [10, 0], [8.5, 0.5, 8, 0], [3]]
a3 = double_merge(a2, a1)
print("a3", a3)
interval_plot(a1)
interval_plot(a2)
interval_plot(a3)
plt.axis('scaled')
plt.axis([-1, 11, -9, 5])
plt.show()

N = [[0,0], [1, 1], [3, 1]]
a1 = [[[0, 0, 0, -1]], [0, 0], [1, 1, math.sqrt(2), 5*np.pi/3, 3*np.pi/4], [0]]
a2 = [[[5, 4, 3, -1]], [6, 5], [5, 4, math.sqrt(2), 2*np.pi/3, 11*np.pi/6], [1]]
a3 = [[[5, 0, 3, -1]], [5, 0], [5, 1, 4, 0], [3]]
a4 = triple_merge(a2, a3, a1)
print("a4", a4)
interval_plot(a1)
interval_plot(a2)
interval_plot(a3)
interval_plot(a4)
plt.axis('scaled')
plt.axis([-1, 8, -4, 12])
plt.show()


N = [[0, 0], [1, 0], [0.5, 1]]
k = 1
x,t = k_steiner(N, k)
print(f"final answer is {x}")
print(f"time taken is {t}")

print(f"----------------------------")


N = [[0, 0], [1, 0], [0, 1], [1, 1]]
k = 2
x = k_steiner(N, k)
print(f"final answer is {x}")

print(f"----------------------------")

N = [[0, 0], [1, 0], [0, 1], [1, 1]]
k = 1
x = k_steiner(N, k)
print(f"final answer is {x}")
"""

print(f"----------------------------")


#N = [list(np.random.rand(2)) for i in range(20)]
#N = [[0.5185623941380034, 0.7053107125100567], [0.873344638285359, 0.9710019268237062], [0.8214503228987976, 0.5821230887660225], [0.4664543438423039, 0.5665134514381938], [0.8390526301199909, 0.6085339132686411], [0.816253562998671, 0.9813002146133665], [0.16127715870813641, 0.6181883266735895], [0.4775177411297019, 0.3690834277451992], [0.13130832825729932, 0.17268508932015558], [0.8349090650381271, 0.4280693134538306]]
#N = [[0.322430303999917, 0.638173507897649], [0.9760978083424661, 0.7539716767670575], [0.873988256490949, 0.13478355192488745], [0.682540381208859, 0.011749902318472949], [0.34390188296344604, 0.016141823063221317], [0.013016918641762132, 0.9921280635953252], [0.8202491079042633, 0.16249404071429385], [0.04840941473867466, 0.9555437917110807], [0.806529710580405, 0.28929003418286225], [0.1541396025730991, 0.34455607289682555], [0.512298577275337, 0.9883878255309243], [0.02768987078543428, 0.6792517957922066], [0.035701999108259885, 0.7556401936281025], [0.8828565928992487, 0.4437667180474618], [0.06797994980697641, 0.23591012291444202], [0.6535722524916702, 0.40314899361935885], [0.7044373264017667, 0.08923322928278699], [0.8481877990606772, 0.23878450538946716], [0.052298106392798416, 0.5056945066401706], [0.28385939363769974, 0.9214290695223673]]
N = [[0.821789251378946, 0.8507998160605801], [0.7067269633162914, 0.6526528658032125], [0.4062911068215014, 0.10749918688844096], [0.4084099423853943, 0.9100170027928908], [0.6390657391408231, 0.9607090630394356], [0.2874605962448229, 0.08926277971803276], [0.8602946679731229, 0.24362869720536107], [0.5354584639794022, 0.27243369454794786], [0.10128120236137983, 0.9148209822084301], [0.026491943644951, 0.2834167252305779], [0.24171601521636343, 0.5462763442461642], [0.11541344979339585, 0.4500609593932362]]
# n = 12
N = [list(np.random.rand(2)) for i in range(5)]
print(f"N is {N}")
k = 3
x = k_steiner(N, k)
print(f"final answer is {x}")