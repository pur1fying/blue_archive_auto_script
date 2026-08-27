
# Determinate a triangle by three vertexes in a screen

class Triangle:
    def __init__(self, p):
        self.p = p
        assert len(p) == 3

        self.p.sort(key=lambda pt: pt[1])
        self.v0, self.v1, self.v2 = self.p

    def x_bounds(self):
        """
            Calculate the minimum and maximum x coordinates for each y coordinate
        """

        y_cnt = self.v2[1] - self.v0[1] + 1
        x_min_list = [float('inf')] * y_cnt
        x_max_list = [float('-inf')] * y_cnt

        # scan from lowest to middle vertex
        if self.v0[1] != self.v1[1]:
            dx_dy_10 = (self.v1[0] - self.v0[0]) / (self.v1[1] - self.v0[1])
            dx_dy_20 = (self.v2[0] - self.v0[0]) / (self.v2[1] - self.v0[1])
            d_l = min(dx_dy_10, dx_dy_20)
            d_r = max(dx_dy_10, dx_dy_20)
            x_left = self.v0[0]
            x_right = self.v0[0]

            for y in range(0, self.v1[1] + 1 - self.v0[1]):
                x_min_list[y] = min(x_min_list[y], round(x_left))
                x_max_list[y] = max(x_max_list[y], round(x_right))

                x_left  += d_l
                x_right += d_r
        else:
            self._check_single_horizontal_line(self.v0, self.v1, x_min_list, x_max_list)

        # scan from highest to middle vertex
        if self.v1[1] != self.v2[1]:
            dx_dy_21 = (self.v2[0] - self.v1[0]) / (self.v2[1] - self.v1[1])
            dx_dy_20 = (self.v2[0] - self.v0[0]) / (self.v2[1] - self.v0[1])
            d_l = max(dx_dy_20, dx_dy_21)
            d_r = min(dx_dy_20, dx_dy_21)
            x_left = self.v2[0]
            x_right = self.v2[0]

            for y in range(self.v2[1] - self.v0[1], self.v1[1] - 1 - self.v0[1], -1):
                x_min_list[y] = min(x_min_list[y], round(x_left))
                x_max_list[y] = max(x_max_list[y], round(x_right))

                x_left -= d_l
                x_right -= d_r
        else:
            self._check_single_horizontal_line(self.v1, self.v2, x_min_list, x_max_list)

        return x_min_list, x_max_list

    def _check_single_horizontal_line(self, v0, v1, x_min_list, x_max_list):
        idx = v0[1] - self.v0[1]
        x_min_list[idx] = min(x_min_list[idx], min(v0[0], v1[0]))
        x_max_list[idx] = max(x_max_list[idx], max(v0[0], v1[0]))

    def pixels(self):
        return self.v0[1], self.x_bounds()
