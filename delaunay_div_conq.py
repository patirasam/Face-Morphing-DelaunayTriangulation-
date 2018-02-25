import cv2


class Point(object):
    def __init__(self, x, y):
        self.x = x+0.0
        self.y = y+0.0
        self.incoming_edge = None

    def __str__(self):
        return "(" + str(self.x) + "," + str(self.y) + ")"

    def get_tuple(self):
        return int(self.x), int(self.y)

    def __lt__(self, other):
        return self.y < other.y if self.x == other.x else self.x < other.x


left = 1
right = 0


class Edge(object):
    def __init__(self, org, dest):
        self.origin = org
        self.destination = dest
        if not self.origin.incoming_edge:
            self.origin.incoming_edge = self
        if not self.destination.incoming_edge:
            self.destination.incoming_edge = self
        self.origin_next = self.origin_prev = self.dest_next = self.dest_prev = self

    def __str__(self):
        return str(self.origin) + "--->" + str(self.destination)


def splice(a, b, v):
    if a.origin == v:
        next = a.origin_next
        a.origin_next = b
    else:
        next = a.dest_next
        a.dest_next = b

    if next.origin == v:
        next.origin_prev = b
    else:
        next.dest_prev = b

    if b.origin == v:
        b.origin_next = next
        b.origin_prev = a
    else:
        b.dest_next = next
        b.dest_prev = a


def join(edge_a, pt1, edge_b, pt2, direction):
    e = Edge(pt1, pt2)
    if direction == left:
        if edge_a.origin == pt1:
            splice(edge_a.origin_prev, e, pt1)
        else:
            splice(edge_a.dest_prev, e, pt1)
        splice(edge_b, e, pt2)
    else:
        splice(edge_a, e, pt1)
        if edge_b.origin == pt2:
            splice(edge_b.origin_prev, e, pt2)
        else:
            splice(edge_b.dest_prev, e, pt2)
    return e


def delete_edge(edge):
    u = edge.origin
    v = edge.destination

    if u.incoming_edge == edge:
        u.incoming_edge = edge.origin_next
    if v.incoming_edge == edge:
        v.incoming_edge = edge.dest_next

    if edge.origin_next.origin == u:
        edge.origin_next.origin_prev = edge.origin_prev
    else:
        edge.origin_next.dest_prev = edge.origin_prev

    if edge.origin_prev.origin == u:
        edge.origin_prev.origin_next = edge.origin_next
    else:
        edge.origin_prev.dest_next = edge.origin_next

    if edge.dest_next.origin == v:
        edge.dest_next.origin_prev = edge.dest_prev
    else:
        edge.dest_next.dest_prev = edge.dest_prev

    if edge.dest_prev.origin == v:
        edge.dest_prev.origin_next = edge.dest_next
    else:
        edge.dest_prev.dest_next = edge.dest_next


def Other_point(edge, pt):
    return edge.destination if edge.origin == pt else edge.origin


def Next(edge, pt):
    return edge.origin_next if edge.origin == pt else edge.dest_next


def Prev(edge, pt):
    return edge.origin_prev if edge.origin == pt else edge.dest_prev


def get_vector(pt1, pt2):
    return pt2.x - pt1.x, pt2.y - pt1.y


def Cross_product_3p(pt1, pt2, pt3):
    return (pt2.x - pt1.x) * (pt3.y - pt1.y) - (pt2.y - pt1.y) * (pt3.x - pt1.x)


def Cross_product_2v(u1, v1, u2, v2):
    return u1 * v2 - v1 * u2


def Dot_product_2v(u1, v1, u2, v2):
    return u1 * u2 + v1 * v2


def lower_tangent(r_cw_l, s, l_ccw_r, u):
    l = r_cw_l
    r = l_ccw_r
    o_l = s
    d_l = Other_point(l, s)
    o_r = u
    d_r = Other_point(r, u)
    finished = False
    while not finished:
        if Cross_product_3p(o_l, d_l, o_r) > 0:
            l = Prev(l, d_l)
            o_l = d_l
            d_l = Other_point(l, o_l)
        elif Cross_product_3p(o_r, d_r, o_l) < 0:
            r = Next(r, d_r)
            o_r = d_r
            d_r = Other_point(r, o_r)
        else:
            finished = True
    l_lower = l
    r_lower = r
    org_l_lower = o_l
    org_r_lower = o_r
    return l_lower, org_l_lower, r_lower, org_r_lower


def merge(r_cw_l, s, l_ccw_r, u):
    l_lower, org_l_lower, r_lower, org_r_lower = lower_tangent(r_cw_l, s, l_ccw_r, u)
    base = join(l_lower, org_l_lower, r_lower, org_r_lower, right)
    org_base = org_l_lower
    dest_base = org_r_lower
    l_tangent = base
    while True:
        # Initialise l_cand and r_cand
        l_cand = Next(base, org_base)
        r_cand = Prev(base, dest_base)
        dest_l_cand = Other_point(l_cand, org_base)
        dest_r_cand = Other_point(r_cand, dest_base)

        # Vectors for above and "in_circle" tests.
        u_l_c_o_b, v_l_c_o_b = get_vector(dest_l_cand, org_base)
        u_l_c_d_b, v_l_c_d_b = get_vector(dest_l_cand, dest_base)
        u_r_c_o_b, v_r_c_o_b = get_vector(dest_r_cand, org_base)
        u_r_c_d_b, v_r_c_d_b = get_vector(dest_r_cand, dest_base)

        # Above tests.
        c_p_l_cand = Cross_product_2v(u_l_c_o_b, v_l_c_o_b, u_l_c_d_b, v_l_c_d_b)
        c_p_r_cand = Cross_product_2v(u_r_c_o_b, v_r_c_o_b, u_r_c_d_b, v_r_c_d_b)
        above_l_cand = c_p_l_cand > 0.0
        above_r_cand = c_p_r_cand > 0.0
        if not above_l_cand and not above_r_cand:
            break  # Finished.

        if above_l_cand:

            d_p_l_cand = Dot_product_2v(u_l_c_o_b, v_l_c_o_b, u_l_c_d_b, v_l_c_d_b)
            cot_l_cand = d_p_l_cand / c_p_l_cand

            while True:
                next = Next(l_cand, org_base)
                dest_next = Other_point(next, org_base)
                u_n_o_b, v_n_o_b = get_vector(dest_next, org_base)
                u_n_d_b, v_n_d_b = get_vector(dest_next, dest_base)
                c_p_next = Cross_product_2v(u_n_o_b, v_n_o_b, u_n_d_b, v_n_d_b)
                above_next = c_p_next > 0.0

                if not above_next:
                    break  # Finished.

                d_p_next = Dot_product_2v(u_n_o_b, v_n_o_b, u_n_d_b, v_n_d_b)
                cot_next = d_p_next / c_p_next

                if cot_next > cot_l_cand:
                    break  # Finished.

                delete_edge(l_cand)
                l_cand = next
                cot_l_cand = cot_next

        # Now do the symmetrical for r_cand
        if above_r_cand:

            d_p_r_cand = Dot_product_2v(u_r_c_o_b, v_r_c_o_b, u_r_c_d_b, v_r_c_d_b)
            cot_r_cand = d_p_r_cand / c_p_r_cand

            while True:
                prev = Prev(r_cand, dest_base)
                dest_prev = Other_point(prev, dest_base)
                u_p_o_b, v_p_o_b = get_vector(dest_prev, org_base)
                u_p_d_b, v_p_d_b = get_vector(dest_prev, dest_base)
                c_p_prev = Cross_product_2v(u_p_o_b, v_p_o_b, u_p_d_b, v_p_d_b)
                above_prev = c_p_prev > 0.0

                if not above_prev:
                    break  # Finished.

                d_p_prev = Dot_product_2v(u_p_o_b, v_p_o_b, u_p_d_b, v_p_d_b)
                cot_prev = d_p_prev / c_p_prev

                if cot_prev > cot_r_cand:
                    break  # Finished.

                delete_edge(r_cand)
                r_cand = prev
                cot_r_cand = cot_prev

        dest_l_cand = Other_point(l_cand, org_base)
        dest_r_cand = Other_point(r_cand, dest_base)
        if not above_l_cand or (above_l_cand and above_r_cand and cot_r_cand < cot_l_cand):
            base = join(base, org_base, r_cand, dest_r_cand, right)
            dest_base = dest_r_cand
        else:
            base = join(l_cand, dest_l_cand, base, dest_base, right)
            org_base = dest_l_cand
    return l_tangent


def divide(pts, l, r):
    n = r - l + 1
    # print "n =", n
    if n == 2:
        # Bottom of the recursion. Make an edge
        l_ccw = r_cw = Edge(pts[l], pts[r])
    elif n == 3:
        a = Edge(pts[l], pts[l + 1])
        b = Edge(pts[l + 1], pts[r])
        splice(a, b, pts[l + 1])
        c_p = Cross_product_3p(pts[l], pts[l + 1], pts[r])
        if c_p > 0.0:
            # c = join(a, pts[l], b, pts[r], right)
            l_ccw = a
            r_cw = b
        elif c_p < 0.0:
            c = join(a, pts[l], b, pts[r], left)
            l_ccw = c
            r_cw = c
        else:
            l_ccw = a
            r_cw = b
    else:
        split = (l + r) / 2
        # print "Divide at", 0, split
        (l_ccw_l, r_cw_l) = divide(pts, l, split)
        # print_incoming_edges(pts)
        # print "Divide at", split+1, r
        (l_ccw_r, r_cw_r) = divide(pts, split + 1, r)
        # print_incoming_edges(pts)
        # print "Merging at", split
        l_tangent = merge(r_cw_l, pts[split], l_ccw_r, pts[split + 1])
        # print_incoming_edges(pts)
        # print "l_tangent", l_tangent
        if l_tangent.origin == pts[l]:
            l_ccw_l = l_tangent
        if l_tangent.destination == pts[r]:
            r_cw_r = l_tangent
        l_ccw = l_ccw_l
        r_cw = r_cw_r
        # print l_ccw, r_cw
    return l_ccw, r_cw


def get_edges(pts):
    edge_set = set()
    for point in pts:
        start_e = point.incoming_edge
        if start_e:
            if point == start_e.origin:
                edge_set.add(start_e)
                e = Next(start_e, start_e.origin)
                print "here"
                while not start_e == e:
                    edge_set.add(e)
                    e = Next(e, start_e.origin)
            else:
                edge_set.add(start_e)
                e = Next(start_e, start_e.destination)
                print "here"
                while not start_e == e:
                    edge_set.add(e)
                    e = Next(e, start_e.destination)
    return edge_set


def delaunay(pts_file, src_img):
    img = src_img  # .copy()
    # Create an array of points.
    points = []

    # Read in the points from a text file
    with open(pts_file) as file:
        for line in file:
            x, y = line.split()
            points.append(Point(int(x), int(y)))

    points.sort()
    divide(points, 0, len(points) - 1)

    for point in points:
        cv2.circle(img, point.get_tuple(), 2, (0, 0, 255), cv2.FILLED, cv2.LINE_AA, 0)

    edge_set = get_edges(points)
    for edge in edge_set:
        cv2.line(img, edge.origin.get_tuple(),
                 edge.destination.get_tuple(), (255, 255, 255), 1, cv2.LINE_AA, 0)
    namedWindow( "Display window", WINDOW_AUTOSIZE );// Create a window for display.
    imshow( "Orignal Photo", src_img ); 
    namedWindow( "Display window", WINDOW_AUTOSIZE );// Create a window for display.
    imshow( "After Delaunay triangulation", img ); 
    return img


if __name__ == '__main__':
    triangulated_img = delaunay("samkit_2/obama.txt", cv2.imread("samkit_2/obama.jpg"))
    cv2.imshow("Div_Conq Delaunay Triangulation", triangulated_img)
    cv2.waitKey(0)