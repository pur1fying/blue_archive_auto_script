from core.geometry import triangle

class Parallelogram:
    def __init__(self, start_x, start_y, k1, dx1, k2, dx2):
        # init 2 triangles
        p_1 = (start_x, start_y)
        p_2 = (start_x + dx1, int(start_y + k1 * dx1))
        p_3 = (start_x + dx2, int(start_y + k2 * dx2))
        p_4 = (start_x + dx1 + dx2, int(start_y + k1 * dx1 + k2 * dx2))
        self.triangle1 = triangle.Triangle([p_1, p_2, p_3])
        self.triangle2 = triangle.Triangle([p_2, p_3, p_4])


    def pixels(self):
        t1_x_bound_min, t1_x_bound_max = self.triangle1.x_bounds()
        t2_x_bound_min, t2_x_bound_max = self.triangle2.x_bounds()

        y_min = min(self.triangle1.v0[1], self.triangle2.v0[1])
        y_max = max(self.triangle1.v2[1], self.triangle2.v2[1])

        x_bound_min = [float("inf")] * (y_max - y_min + 1)
        x_bound_max = [float("-inf")] * (y_max - y_min + 1)
        delta = self.triangle1.v0[1] - y_min
        for i in range(len(t1_x_bound_min)):
            y_index = i + delta
            x_bound_min[y_index] = min(x_bound_min[y_index], t1_x_bound_min[i])
            x_bound_max[y_index] = max(x_bound_max[y_index], t1_x_bound_max[i])

        delta = self.triangle2.v0[1] - y_min
        for i in range(len(t2_x_bound_min)):
            y_index = i + delta
            x_bound_min[y_index] = min(x_bound_min[y_index], t2_x_bound_min[i])
            x_bound_max[y_index] = max(x_bound_max[y_index], t2_x_bound_max[i])

        return y_min, x_bound_min, x_bound_max

