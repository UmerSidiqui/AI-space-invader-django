# game/views.py

from django.shortcuts import render
import os
import pygame
import random
import cv2
import mediapipe as mp
import math
from django.http import StreamingHttpResponse

def game_view(request):
    if request.method == "GET":
        pygame.init()
        pygame.font.init()

        WIDTH, HEIGHT = 750, 750
        WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.display.set_caption("Space Shooter Gesture Control")

        # Load images
        base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/game')
        RED_SPACE_SHIP = pygame.image.load(os.path.join(base_path, "pixel_ship_red_small.png"))
        GREEN_SPACE_SHIP = pygame.image.load(os.path.join(base_path, "pixel_ship_green_small.png"))
        BLUE_SPACE_SHIP = pygame.image.load(os.path.join(base_path, "pixel_ship_blue_small.png"))
        YELLOW_SPACE_SHIP = pygame.image.load(os.path.join(base_path, "pixel_ship_yellow.png"))
        RED_LASER = pygame.image.load(os.path.join(base_path, "pixel_laser_red.png"))
        GREEN_LASER = pygame.image.load(os.path.join(base_path, "pixel_laser_green.png"))
        BLUE_LASER = pygame.image.load(os.path.join(base_path, "pixel_laser_blue.png"))
        YELLOW_LASER = pygame.image.load(os.path.join(base_path, "pixel_laser_yellow.png"))
        BG = pygame.transform.scale(pygame.image.load(os.path.join(base_path, "background-black.png")), (WIDTH, HEIGHT))
        
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.8, min_tracking_confidence=0.5)
        mp_draw = mp.solutions.drawing_utils

        # Initialize webcam
        cap = cv2.VideoCapture(0)
        cap.set(3, 500)
        cap.set(4, 500)
        # Define game classes and functions (Laser, Ship, Player, Enemy, collide, etc.)
        def get_direction(lm_list):
    
            if not lm_list or len(lm_list) < 9:
                return "Unknown"

            index_tip = lm_list[8]
            index_mcp = lm_list[5]
            thumb_tip = lm_list[4]
            thumb_mcp = lm_list[2]

            distance = math.sqrt((thumb_tip[1] - thumb_mcp[1]) ** 2 + (thumb_tip[2] - thumb_mcp[2]) ** 2)

            if index_tip[1] > index_mcp[1] + 30 and distance > 125:
                return "Rt"
            elif index_tip[1] < index_mcp[1] - 30 and distance > 125:
                return "Lt"
            elif index_tip[2] < index_mcp[2] - 30 and distance > 125:
                return "Ut"
            elif index_tip[2] > index_mcp[2] + 30 and distance > 125:
                return "Dt"
            elif index_tip[1] > index_mcp[1] + 30:
                return "Right"
            elif index_tip[1] < index_mcp[1] - 30:
                return "Left"
            elif index_tip[2] < index_mcp[2] - 30:
                return "Up"
            elif index_tip[2] > index_mcp[2] + 30:
                return "Down"
            else:
                return "t"
            
        class Laser:
            def __init__(self, x, y, img):
                self.x = x
                self.y = y
                self.img = img
                self.mask = pygame.mask.from_surface(self.img)

            def draw(self, window):
                window.blit(self.img, (self.x, self.y))

            def move(self, vel):
                self.y += vel

            def off_screen(self, height):
                return not (0 <= self.y <= height)

            def collision(self, obj):
                return collide(self, obj)

        class Ship:
            COOLDOWN = 30

            def __init__(self, x, y, health=100):
                self.x = x
                self.y = y
                self.health = health
                self.ship_img = None
                self.laser_img = None
                self.lasers = []
                self.cool_down_counter = 0

            def draw(self, window):
                window.blit(self.ship_img, (self.x, self.y))
                for laser in self.lasers:
                    laser.draw(window)

            def move_lasers(self, vel, obj):
                self.cooldown()
                for laser in self.lasers:
                    laser.move(vel)
                    if laser.off_screen(HEIGHT):
                        self.lasers.remove(laser)
                    elif laser.collision(obj):
                        obj.health -= 10
                        self.lasers.remove(laser)

            def cooldown(self):
                if self.cool_down_counter >= self.COOLDOWN:
                    self.cool_down_counter = 0
                elif self.cool_down_counter > 0:
                    self.cool_down_counter += 1

            def shoot(self):
                if self.cool_down_counter == 0:
                    laser = Laser(self.x + self.get_width() // 2 - self.laser_img.get_width() // 2, self.y, self.laser_img)
                    self.lasers.append(laser)
                    self.cool_down_counter = 1

            def get_width(self):
                return self.ship_img.get_width()

            def get_height(self):
                return self.ship_img.get_height()

        class Player(Ship):
            def __init__(self, x, y, health=100):
                super().__init__(x, y, health)
                self.ship_img = YELLOW_SPACE_SHIP
                self.laser_img = YELLOW_LASER
                self.mask = pygame.mask.from_surface(self.ship_img)
                self.max_health = health

            def move_lasers(self, vel, objs):
                self.cooldown()
                for laser in self.lasers:
                    laser.move(vel)
                    if laser.off_screen(HEIGHT):
                        self.lasers.remove(laser)
                    else:
                        for obj in objs:
                            if laser.collision(obj):
                                objs.remove(obj)
                                if laser in self.lasers:
                                    self.lasers.remove(laser)

            def draw(self, window):
                super().draw(window)
                self.healthbar(window)

            def healthbar(self, window):
                pygame.draw.rect(window, (255, 0, 0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width(), 10))
                pygame.draw.rect(window, (0, 255, 0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width() * (self.health / self.max_health), 10))

            def move(self, direction, vel):
                if direction == "Left" and self.x - vel > 0:
                    self.x -= vel
                if direction == "Right" and self.x + vel + self.get_width() < WIDTH:
                    self.x += vel
                if direction == "Up" and self.y - vel > 0:
                    self.y -= vel
                if direction == "Down" and self.y + vel + self.get_height() < HEIGHT:
                    self.y += vel

        class Enemy(Ship):
            COLOR_MAP = {
                "red": (RED_SPACE_SHIP, RED_LASER),
                "green": (GREEN_SPACE_SHIP, GREEN_LASER),
                "blue": (BLUE_SPACE_SHIP, BLUE_LASER)
            }

            def __init__(self, x, y, color, health=100):
                super().__init__(x, y, health)
                self.ship_img, self.laser_img = self.COLOR_MAP[color]
                self.mask = pygame.mask.from_surface(self.ship_img)

            def move(self, vel):
                self.y += vel

            def shoot(self):
                if self.cool_down_counter == 0:
                    laser = Laser(self.x - 20, self.y, self.laser_img)
                    self.lasers.append(laser)
                    self.cool_down_counter = 1

        def collide(obj1, obj2):
            offset_x = obj2.x - obj1.x
            offset_y = obj2.y - obj1.y
            return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) is not None
        
        
        def main():
            run = True
            FPS = 60
            level = 0
            lives = 5
            main_font = pygame.font.SysFont("comicsans", 50)
            lost_font = pygame.font.SysFont("comicsans", 60)

            enemies = []
            wave_length = 5
            enemy_vel = 1

            player_vel = 5
            laser_vel = 5

            player = Player(300, 630)

            clock = pygame.time.Clock()

            lost = False
            lost_count = 0

            def redraw_window():
                WIN.blit(BG, (0, 0))
                lives_label = main_font.render(f"Lives: {lives}", 1, (255, 255, 255))
                level_label = main_font.render(f"Level: {level}", 1, (255, 255, 255))

                WIN.blit(lives_label, (10, 10))
                WIN.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))

                for enemy in enemies:
                    enemy.draw(WIN)

                player.draw(WIN)

                if lost:
                    lost_label = lost_font.render("You Lost!!", 1, (255, 255, 255))
                    WIN.blit(lost_label, (WIDTH / 2 - lost_label.get_width() / 2, 350))

                pygame.display.update()

            while run:
                clock.tick(FPS)
                redraw_window()

                if lives <= 0 or player.health <= 0:
                    lost = True
                    lost_count += 1

                if lost:
                    if lost_count > FPS * 3:
                        run = False
                    continue

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        cap.release()
                        cv2.destroyAllWindows()
                        pygame.quit()
                        quit()

                success, img = cap.read()
                if not success:
                    continue

                img = cv2.flip(img, 1)
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                results = hands.process(img_rgb)
                lm_list = []

                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                        for id, lm in enumerate(hand_landmarks.landmark):
                            h, w, _ = img.shape
                            cx, cy = int(lm.x * w), int(lm.y * h)
                            lm_list.append([id, cx, cy])

                    gesture = get_direction(lm_list)
                    # cv2.putText(img, f"Gesture: {gesture}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

                    if gesture == "Lt":
                        player.move("Left", player_vel)
                        player.shoot()
                    elif gesture == "Rt":
                        player.move("Right", player_vel)
                        player.shoot()
                    elif gesture == "Ut":
                        player.move("Up", player_vel)
                        player.shoot()
                    elif gesture == "Dt":
                        player.move("Down", player_vel)
                        player.shoot()
                    elif gesture == "t":
                        player.shoot()
                    elif gesture == "Left":
                        player.move("Left", player_vel)
                    elif gesture == "Right":
                        player.move("Right", player_vel)
                    elif gesture == "Up":
                        player.move("Up", player_vel)
                    elif gesture == "Down":
                        player.move("Down", player_vel)
                
                # cv2.imshow("Hand Gesture Detection", img)

                for enemy in enemies[:]:
                    enemy.move(enemy_vel)
                    enemy.move_lasers(laser_vel, player)

                    if random.randrange(0, 2 * 60) == 1:
                        enemy.shoot()

                    if collide(enemy, player):
                        player.health -= 10
                        enemies.remove(enemy)
                    elif enemy.y + enemy.get_height() > HEIGHT:
                        lives -= 1
                        enemies.remove(enemy)

                player.move_lasers(-laser_vel, enemies)

                if len(enemies) == 0:
                    level += 1
                    wave_length += 5
                    for i in range(wave_length):
                        enemy = Enemy(random.randrange(50, WIDTH - 100), random.randrange(-1500, -100), random.choice(["red", "blue", "green"]))
                        enemies.append(enemy)


            # Game logic and rendering here
        
        def main_menu():
            title_font = pygame.font.SysFont("comicsans", 70)
            run = True
            while run:
                WIN.blit(BG, (0, 0))
                title_label = title_font.render("Press the mouse to begin...", 1, (255, 255, 255))
                WIN.blit(title_label, (WIDTH / 2 - title_label.get_width() / 2, 350))
                pygame.display.update()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        run = False
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        main()
            pygame.quit()



            

        # Start the game
        main_menu()

    return render(request, 'game/game.html')


def video_feed(request):
    return StreamingHttpResponse(game_view(), content_type='multipart/x-mixed-replace; boundary=frame')
