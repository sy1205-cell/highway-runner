import pyxel
import random
import time

# 画面サイズ
WIDTH, HEIGHT = 160, 120
LANE_COUNT = 10  
LANE_WIDTH = WIDTH // LANE_COUNT

class Game:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT)
        pyxel.load("/Users/sasajimayuuya/Documents/選択項目から作成したフォルダ/my_resource.pyxres")
        self.reset_game()
        self.is_game_started = False  # ゲーム開始フラグを追加
        pyxel.run(self.update, self.draw)

    def reset_game(self):
        self.player = Car(WIDTH // 2, HEIGHT - 20)
        self.enemies = []
        self.enemy_speed = 1
        self.collision_count = 0
        self.avoid_count = 0
        self.road_offset = 0
        self.patrol_car = None
        self.congratulations_x = None
        self.arrest_x = None
        self.lane_count = LANE_COUNT
        self.movement_limit_x = 0  # 初期制限なし
        self.powerup = None
        self.powerup_start_time = None
        self.next_powerup_time = time.time() + random.randint(5, 10)
        self.score = 0  # スコアを追加
        self.is_game_over = False  # ゲームオーバーフラグを追加

    def update(self):
        if not self.is_game_started:
            if pyxel.btnp(pyxel.KEY_SPACE):
                self.is_game_started = True
            return

        if pyxel.btnp(pyxel.KEY_R):
            self.reset_game()
            self.is_game_started = False
            return

        if self.is_game_over:
            return

        if self.score >= 3:
            if self.congratulations_x is None:
                self.congratulations_x = WIDTH
            self.congratulations_x -= 1
            return

        self.player.move(self.movement_limit_x)
        self.road_offset = (self.road_offset + 2) % 16

        # 車線の減少
        if self.score > 0:
            self.movement_limit_x = min(WIDTH // 2, self.score * 20)  

        # パワーアップの生成
        if self.powerup is None and time.time() >= self.next_powerup_time:
            self.powerup = [random.randint(self.movement_limit_x, WIDTH - self.movement_limit_x - 8), random.randint(10, HEIGHT - 10)]
            self.next_powerup_time = time.time() + random.randint(5, 10)

        # パワーアップの適用
        if self.powerup and abs(self.player.x - self.powerup[0]) < 15 and abs(self.player.y - self.powerup[1]) < 15:
            self.score += 1
            self.powerup = None

        powerup_active = self.powerup_start_time and time.time() - self.powerup_start_time < 20

        # 敵の追加
        if random.randint(1, 10) == 1:
            available_lanes = [i * (WIDTH // self.lane_count) for i in range(self.lane_count)]
            available_lanes = [x for x in available_lanes if self.movement_limit_x <= x <= WIDTH - self.movement_limit_x - 8]
            possible_lanes = available_lanes

            if possible_lanes:
                enemy_x = random.choice(possible_lanes)
                self.enemies.append(EnemyCar(enemy_x, 0))       
        for enemy in self.enemies[:]:
            enemy.move(self.enemy_speed)
            if enemy.y > HEIGHT:
                self.enemies.remove(enemy)
                if not powerup_active:
                    self.avoid_count += 1
                if self.avoid_count % 5 == 0 and self.patrol_car is None:
                    self.patrol_car = PatrolCar(self.player.x, HEIGHT) 
                if self.avoid_count % 20 == 0:
                    self.enemy_speed += 1  
        if self.patrol_car:
            self.patrol_car.move(-self.enemy_speed)
            if self.patrol_car.y < 0:
                self.patrol_car = None
            for enemy in self.enemies[:]:
                if self.patrol_car and abs(self.patrol_car.x - enemy.x) < 12 and abs(self.patrol_car.y - enemy.y) < 12:
                    self.enemies.remove(enemy)
                    self.patrol_car = None
                    break
            if self.patrol_car and abs(self.player.x - self.patrol_car.x) < 12 and abs(self.player.y - self.patrol_car.y) < 12:
                self.is_game_over = True
                self.arrest_x = WIDTH

        # 衝突判定
        for enemy in self.enemies[:]:
            if not powerup_active and abs(self.player.x - enemy.x) < 12 and abs(self.player.y - enemy.y) < 12:
                self.collision_count += 1
                self.enemies.remove(enemy)
                if self.collision_count >= 10:
                    self.is_game_over = True
                    self.arrest_x = WIDTH

    def draw(self):
        pyxel.cls(13)

        if not self.is_game_started:
            pyxel.text(WIDTH // 2 - 65, HEIGHT // 2, "Press space key to start this game", 7)
            pyxel.text(WIDTH // 2 - 50, HEIGHT // 4, "You can operate your car", 7)
            pyxel.text(WIDTH // 2 - 40, HEIGHT // 3, "using arrow keys!", 7)
            return

        if self.is_game_over:
            if self.arrest_x is not None:
                pyxel.text(self.arrest_x, HEIGHT // 2, "Keep your eyes on the road! press R to restart", 8)
                self.arrest_x -= 1
            return

        for i in range(1, self.lane_count):
            x = i * (WIDTH // self.lane_count)
            if self.movement_limit_x <= x <= WIDTH - self.movement_limit_x:
                for j in range(0, HEIGHT, 16):
                    pyxel.rect(x, (j + self.road_offset) % HEIGHT, 2, 8, 7)

        self.player.draw()
        for enemy in self.enemies:
            enemy.draw()

        if self.patrol_car:
            self.patrol_car.draw()

        if self.powerup:
            pyxel.rect(self.powerup[0], self.powerup[1], 16, 8, 2)
            pyxel.text(self.powerup[0]+2, self.powerup[1]+1, "ETC", 7)

        pyxel.text(5, 5, f"your life: {10-self.collision_count}", 7)
        pyxel.text(5, 15, f"points: {self.avoid_count}", 7)
        pyxel.text(5, 25, f"ETC: {self.score}/3", 2)

        if self.congratulations_x is not None:
            pyxel.text(self.congratulations_x, HEIGHT // 2, "Congratulations! Press R to restart the game", 8)

        if self.arrest_x is not None and not self.is_game_over:
            pyxel.text(self.arrest_x, HEIGHT // 2, ":( Press R to reset the game", 8)

class Car:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.h = 16
        self.w = 16

    def draw(self):
        pyxel.blt(self.x, self.y, 1, 0, 0, 16, 16, 0)

    def move(self, limit_x):
        left_bound = limit_x
        right_bound = WIDTH - limit_x - self.w

        if pyxel.btn(pyxel.KEY_RIGHT) and self.x < right_bound:
            self.x += 1
        if pyxel.btn(pyxel.KEY_LEFT) and self.x > left_bound:
            self.x -= 1
        if pyxel.btn(pyxel.KEY_UP) and self.y > 0:
            self.y -= 1
        if pyxel.btn(pyxel.KEY_DOWN) and self.y < HEIGHT - self.h:
            self.y += 1

class EnemyCar:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.h = 16
        self.w = 16

    def draw(self):
        pyxel.blt(self.x, self.y, 2, 0, 0, 16, 16, 0)

    def move(self, speed):
        self.y += speed

class PatrolCar(EnemyCar):
    def draw(self):
        pyxel.blt(self.x, self.y, 0, 0, 0, 16, 16, 0)

    def move(self, speed):
        self.y += speed

Game()
