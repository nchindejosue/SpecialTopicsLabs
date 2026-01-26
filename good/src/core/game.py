import tkinter as tk
import random
import src.config.settings as settings
from src.entities.player import Player
from src.entities.obstacle import Obstacle
class Game(tk.Toplevel):
    def __init__(self, launcher):
        super().__init__(launcher)
        self.launcher = launcher
        self.title(settings.TITLE)
        self.geometry(f"{settings.SCREEN_WIDTH}x{settings.SCREEN_HEIGHT}")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.canvas = tk.Canvas(self, bg=settings.BACKGROUND_COLOR, width=settings.SCREEN_WIDTH, height=settings.SCREEN_HEIGHT)
        self.canvas.pack()
        # Game state
        self.score = 0
        self.game_over_flag = False
        self.obstacles = []
        self.obstacle_speed = settings.INITIAL_OBSTACLE_SPEED
        self.road_x_start = (settings.SCREEN_WIDTH - settings.ROAD_WIDTH) / 2
        # Create game elements
        self.player = Player(self.canvas, self.road_x_start)
        self.score_label = self.canvas.create_text(
            70, 30, text=f"Score: {self.score}", font=("Arial", 16, "bold"), fill=settings.SCORE_COLOR
        )
        # Back Button
        back_button = tk.Button(self, text="Back to Menu", command=self.on_close)
        self.canvas.create_window(settings.SCREEN_WIDTH - 70, 30, window=back_button)
        # Bind keyboard events
        self.bind("<Left>", self.player.move_left)
        self.bind("<Right>", self.player.move_right)
        self.focus_set()
        # Start game loops
        self.draw_road()
        self.update_game()
        self.spawn_obstacle()
    def on_close(self):
        self.destroy()
        self.launcher.show_launcher()
    def draw_road(self):
        road_x_end = self.road_x_start + settings.ROAD_WIDTH
        # Draw road boundaries
        self.canvas.create_line(self.road_x_start, 0, self.road_x_start, settings.SCREEN_HEIGHT, fill=settings.LANE_COLOR, width=5)
        self.canvas.create_line(road_x_end, 0, road_x_end, settings.SCREEN_HEIGHT, fill=settings.LANE_COLOR, width=5)
        # Draw lane markers
        for i in range(1, settings.LANE_COUNT):
            x = self.road_x_start + i * settings.LANE_WIDTH
            for y in range(0, settings.SCREEN_HEIGHT, settings.LANE_MARKER_HEIGHT + settings.LANE_MARKER_GAP):
                self.canvas.create_line(x, y, x, y + settings.LANE_MARKER_HEIGHT, fill=settings.LANE_COLOR, width=2, dash=(4, 4))
    def spawn_obstacle(self):
        if self.game_over_flag:
            return
        lane = random.randint(0, settings.LANE_COUNT - 1)
        obstacle = Obstacle(self.canvas, lane, self.road_x_start, self.obstacle_speed)
        self.obstacles.append(obstacle)
        self.after(settings.SPAWN_INTERVAL_MS, self.spawn_obstacle)
    def check_collision(self, obstacle):
        p_coords = self.player.get_coords()
        o_coords = obstacle.get_coords()
        if p_coords and o_coords: # Check if objects exist
            if p_coords[2] > o_coords[0] and p_coords[0] < o_coords[2] and \
               p_coords[3] > o_coords[1] and p_coords[1] < o_coords[3]:
                self.game_over()
    def game_over(self):
        self.game_over_flag = True
        self.canvas.create_text(
            settings.SCREEN_WIDTH / 2,
            settings.SCREEN_HEIGHT / 2,
            text="GAME OVER",
            font=("Arial", 50, "bold"),
            fill=settings.GAMEOVER_COLOR
        )
    def update_game(self):
        if self.game_over_flag:
            return
        for obstacle in self.obstacles[:]:
            obstacle.move()
            self.check_collision(obstacle)
            coords = obstacle.get_coords()
            if coords and coords[1] > settings.SCREEN_HEIGHT:
                obstacle.destroy()
                self.obstacles.remove(obstacle)
                self.update_score()
        self.after(settings.GAME_UPDATE_MS, self.update_game)
    def update_score(self):
        self.score += 1
        self.canvas.itemconfig(self.score_label, text=f"Score: {self.score}")
        # Increase difficulty
        if self.score > 0 and self.score % settings.SCORE_TO_INCREASE_SPEED == 0:
            self.obstacle_speed += settings.SPEED_INCREASE_RATE
