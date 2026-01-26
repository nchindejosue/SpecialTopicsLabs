import src.config.settings as settings
class Player:
    """ Manages the player's car. """
    def __init__(self, canvas, road_x_start):
        self.canvas = canvas
        self.road_x_start = road_x_start
        self.current_lane = 1  # Start in the middle lane (0, 1, 2)
        x = self.get_lane_center_x(self.current_lane)
        y = settings.SCREEN_HEIGHT - settings.PLAYER_CAR_HEIGHT - 20
        self.rect = self.canvas.create_rectangle(
            x - settings.PLAYER_CAR_WIDTH / 2,
            y - settings.PLAYER_CAR_HEIGHT / 2,
            x + settings.PLAYER_CAR_WIDTH / 2,
            y + settings.PLAYER_CAR_HEIGHT / 2,
            fill=settings.PLAYER_CAR_COLOR,
            outline="black"
        )
    def get_lane_center_x(self, lane_index):
        """ Calculates the center x-coordinate for a given lane index. """
        return self.road_x_start + (lane_index * settings.LANE_WIDTH) + (settings.LANE_WIDTH / 2)
    def move_left(self, event=None):
        if self.current_lane > 0:
            self.current_lane -= 1
            self.update_position()
    def move_right(self, event=None):
        if self.current_lane < settings.LANE_COUNT - 1:
            self.current_lane += 1
            self.update_position()
    def update_position(self):
        new_x = self.get_lane_center_x(self.current_lane)
        current_coords = self.canvas.coords(self.rect)
        current_y = (current_coords[1] + current_coords[3]) / 2
        self.canvas.coords(
            self.rect,
            new_x - settings.PLAYER_CAR_WIDTH / 2,
            current_y - settings.PLAYER_CAR_HEIGHT / 2,
            new_x + settings.PLAYER_CAR_WIDTH / 2,
            current_y + settings.PLAYER_CAR_HEIGHT / 2,
        )
    def get_coords(self):
        return self.canvas.coords(self.rect)
