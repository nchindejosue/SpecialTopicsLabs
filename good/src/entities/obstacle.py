import src.config.settings as settings
class Obstacle:
    """ Manages a single obstacle car. """
    def __init__(self, canvas, lane, road_x_start, speed):
        self.canvas = canvas
        self.speed = speed
        lane_center_x = road_x_start + (lane * settings.LANE_WIDTH) + (settings.LANE_WIDTH / 2)
        self.rect = self.canvas.create_rectangle(
            lane_center_x - settings.OBSTACLE_WIDTH / 2,
            -settings.OBSTACLE_HEIGHT, # Start above the screen
            lane_center_x + settings.OBSTACLE_WIDTH / 2,
            0,
            fill=settings.OBSTACLE_CAR_COLOR,
            outline="black"
        )
    def move(self):
        self.canvas.move(self.rect, 0, self.speed)
    def get_coords(self):
        return self.canvas.coords(self.rect)
    def destroy(self):
        self.canvas.delete(self.rect)
