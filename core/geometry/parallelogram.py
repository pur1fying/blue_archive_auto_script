

class Parallelogram:
    def __init__(self, x, y, k1, dx1, k2, dx2):
        self.x = x
        self.y = y
        self.k1 = k1
        self.dx1 = dx1
        self.k2 = k2
        self.dx2 = dx2


    def pixels(self):
        """
            (start_y, y_cnt, [[x_start, x_end]])
        """
        start_y = self.y
        y_cnt = round(self.dx1 * self.k1)
        x_list = []
        for y in range(y_cnt):

