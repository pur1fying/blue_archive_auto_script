class Triangle:
    def __init__(self, p):
        self.p = p
        assert len(p) == 3

        self.p.sort(key=lambda pt: pt[1])
        self.v0, self.v1, self.v2 = self.p

    def x_bounds(self):
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

            for y in range(self.v2[1], self.v1[1] - 1, -1):
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

if __name__ == "__main__":
    triangle = Triangle([(719, 1279), (360, 0), (0, 1279)])

    x_min_list, x_max_list = triangle.x_bounds()

    print("y坐标 | 最小x | 最大x")
    print("-------------------")
    for i in range(len(x_min_list)):
        y = i + int(triangle.v0[1])
        min_x = x_min_list[i]
        max_x = x_max_list[i]

        if min_x == float('inf') or max_x == float('-inf'):
            continue

        print(f"{y:4d} | {min_x:6.2f} | {max_x:6.2f}")

    # draw pixels with opencv
    import cv2
    import numpy as np
    img = np.zeros((1280, 720, 3), dtype=np.uint8)
    for y in range(len(x_min_list)):
        min_x = x_min_list[y]
        max_x = x_max_list[y]
        if min_x == float('inf') or max_x == float('-inf'):
            continue
        for x in range(int(min_x), int(max_x) + 1):
            img[y, x] = [255, 255, 255]  # white pixel

    cv2.imshow("Triangle Pixels", img)
    cv2.waitKey(0)

