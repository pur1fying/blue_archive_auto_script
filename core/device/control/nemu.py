from core.device.nemu_client import NemuClient, NemuIpcIncompatible, NemuIpcError
import time
import numpy as np
import os.path


def random_normal_distribution(a, b, n=5):
    output = np.mean(np.random.uniform(a, b, size=n))
    return output


def random_theta():
    theta = np.random.uniform(0, 2 * np.pi)
    return np.array([np.sin(theta), np.cos(theta)])


def random_rho(dis):
    return random_normal_distribution(-dis, dis)


def insert_swipe(p0, p3, speed=15, min_distance=10):
    """
    Insert way point from start to end.
    First generate a cubic bézier curve

    Args:
        p0: Start point.
        p3: End point.
        speed: Average move speed, pixels per 10ms.
        min_distance:

    Returns:
        list[list[int]]: List of points.

    Examples:
        > insert_swipe((400, 400), (600, 600), speed=20)
        [[400, 400], [406, 406], [416, 415], [429, 428], [444, 442], [462, 459], [481, 478], [504, 500], [527, 522],
        [545, 540], [560, 557], [573, 570], [584, 582], [592, 590], [597, 596], [600, 600]]
    """
    p0 = np.array(p0)
    p3 = np.array(p3)

    # Random control points in Bézier curve
    distance = np.linalg.norm(p3 - p0)
    p1 = 2 / 3 * p0 + 1 / 3 * p3 + random_theta() * random_rho(distance * 0.1)
    p2 = 1 / 3 * p0 + 2 / 3 * p3 + random_theta() * random_rho(distance * 0.1)

    # Random `t` on Bézier curve, sparse in the middle, dense at start and end
    segments = max(int(distance / speed) + 1, 5)
    lower = random_normal_distribution(-85, -60)
    upper = random_normal_distribution(80, 90)
    theta = np.arange(lower + 0., upper + 0.0001, (upper - lower) / segments)
    ts = np.sin(theta / 180 * np.pi)
    ts = np.sign(ts) * abs(ts) ** 0.9
    ts = (ts - min(ts)) / (max(ts) - min(ts))

    # Generate cubic Bézier curve
    points = []
    prev = (-100, -100)
    for t in ts:
        point = p0 * (1 - t) ** 3 + 3 * p1 * t * (1 - t) ** 2 + 3 * p2 * t ** 2 * (1 - t) + p3 * t ** 3
        point = point.astype(int).tolist()
        if np.linalg.norm(np.subtract(point, prev)) < min_distance:
            continue

        points.append(point)
        prev = point

    # Delete nearing points
    if len(points[1:]):
        distance = np.linalg.norm(np.subtract(points[1:], points[0]), axis=1)
        mask = np.append(True, distance > min_distance)
        points = np.array(points)[mask].tolist()
        if len(points) <= 1:
            points = [p0, p3]
    else:
        points = [p0, p3]
    return points


class NemuControl:
    def __init__(self, conn):
        self.config_set = conn.config_set
        self.config = conn.config
        self.logger = conn.logger
        self.serial = conn.serial

        self.nemu_folder = self.config_set.get("program_address")
        self.nemu_folder = os.path.dirname(self.nemu_folder)
        self.nemu_folder = os.path.dirname(self.nemu_folder)    # C:/Program Files/Netease/MuMu Player 12
        self.instance_id = NemuClient.serial_to_id(self.serial)
        if self.instance_id is not None:
            try:
                self.nemu_client = NemuClient.get_instance(self.nemu_folder, self.instance_id, self.logger)
            except (NemuIpcIncompatible, NemuIpcError) as e:
                self.logger.warning(e.__str__())
                self.logger.info("Emulator info incorrect. Try to auto detect mumu player path.")
                path = NemuClient.get_possible_mumu12_folder()
                self.logger.info(f"Auto detect mumu player path: {str(path)}")
                if path is not None:
                    self.logger.info(f"Set new config program_address.")
                    self.config_set.set("program_address", path)
                    self.nemu_folder = os.path.dirname(path)
                    self.nemu_folder = os.path.dirname(self.nemu_folder)
                    try:
                        self.nemu_client = NemuClient.get_instance(self.nemu_folder, self.instance_id, self.logger)
                    except (NemuIpcIncompatible, NemuIpcError) as e:
                        self.logger.error(e.__str__())
                        raise Exception("Unable to init NemuControl with auto detected path.")
                else:
                    self.logger.error("MuMu Player 12 not found.")
                    raise Exception("Unable to use Init NemuControl.")
        else:
            self.logger.error('Can\'t convert serial to instance id.')
            raise Exception("Invalid serial. Unable to use Init NemuControl.")

    def click(self, x, y):
        self.nemu_client.down(x, y)
        time.sleep(0.015)
        self.nemu_client.up()
        time.sleep(0.035)

    def swipe(self, x1, y1, x2, y2, duration):
        points = insert_swipe(p0=(x1, y1), p3=(x2, y2))

        for point in points:
            self.nemu_client.down(*point)
            time.sleep(0.010)

        self.nemu_client.up()
        time.sleep(0.050)

    def long_click(self, x, y, duration):
        self.nemu_client.down(x, y)
        time.sleep(duration)
        self.nemu_client.up()
        time.sleep(0.050)



