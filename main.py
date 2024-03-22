import pygame
import random

class Monster(pygame.sprite.Sprite):
    def __init__(self, image, width, height):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, width - self.rect.width)
        self.rect.y = random.randint(0, height - self.rect.height)
        self.velocity_x = random.choice([-1, 1])  # Random initial x-direction velocity
        self.velocity_y = random.choice([-1, 1])  # Random initial y-direction velocity

    def update(self):
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y

        if self.rect.x < 0 or self.rect.x > 800 - self.rect.width:
            self.velocity_x *= -1  # Reverse monster velocity in the x-direction
        if self.rect.y < 0 or self.rect.y > 600 - self.rect.height:
            self.velocity_y *= -1  # Reverse monster velocity in the y-direction

class Knockback:
    def __init__(self):
        pygame.init()
        self.lataa_kuvat()
        self.paused = False

        # Font
        self.smallfont = pygame.font.Font(None, 35)
        self.bigfont = pygame.font.Font(None, 100)

        # Screen
        self.korkeus = 600
        self.leveys = 800
        nayton_korkeus = self.korkeus
        nayton_leveys = self.leveys
        self.naytto = pygame.display.set_mode((nayton_leveys, nayton_korkeus))

        self.clock = pygame.time.Clock()

        # Robot
        self.robot_image = pygame.image.load("robo.png")
        self.robot_rect = self.robot_image.get_rect()
        self.robot_rect.center = (nayton_leveys // 2, nayton_korkeus // 2)

        # Monster group
        self.monsters = pygame.sprite.Group()

        # Coin
        self.coin_image = pygame.image.load("kolikko.png")
        self.coin_rect = self.coin_image.get_rect()
        self.coins = []
        self.coin_counter = 0

        # Projectile parameters
        self.PROJECTILE_SPEED = 10
        self.VPROJECTILE_SIZE = (30, 12)  # Vertical projectile
        self.HPROJECTILE_SIZE = (12, 30)  # Horizontal projectile
        self.PROJECTILE_COLOR = (200, 0, 0)
        self.projectile_velocity = [2, 2]
        self.projectiles = []

        self.monster_spawn_threshold = 3
        self.monster_counter = 0
        self.monster_exists = False

        self.acceleration = 4
        self.friction = 0.02

        # Robot velocity
        self.velocity_x = 0
        self.velocity_y = 0

        self.last_coin_spawn = pygame.time.get_ticks()  # Get the current time in milliseconds

        self.collision_margin = 10  # Set the collision margin to 10 pixels

        self.play_again_text = self.smallfont.render("Press Enter to play again", True, (0, 0, 0))
        self.play_again_rect = self.play_again_text.get_rect(center=(self.leveys // 2, self.korkeus // 2 + 100))
        self.play_again = False

        pygame.display.set_caption("Knockback")

        self.silmukka()

    def lataa_kuvat(self):
        self.kuvat = []
        for nimi in ["robo", "kolikko", "hirvio"]:
            self.kuvat.append(pygame.image.load(nimi + ".png"))

    def silmukka(self):
        while True:
            self.tutki_tapahtumat()
            self.piirra_naytto()
            
            # Apply friction
            self.velocity_x *= (1 - self.friction)
            self.velocity_y *= (1 - self.friction)

            # Update position
            self.robot_rect.x += self.velocity_x
            self.robot_rect.y += self.velocity_y

            # Update monsters
            self.monsters.update()

            # Limit velocity to prevent continuous movement
            max_velocity = 20  # Adjust as needed
            self.velocity_x = max(min(self.velocity_x, max_velocity), -max_velocity)
            self.velocity_y = max(min(self.velocity_y, max_velocity), -max_velocity)

            # Update projectiles
            for self.projectile, self.velocity in self.projectiles:
                self.projectile.x += self.velocity[0]
                self.projectile.y += self.velocity[1]

            # Spawn a coin every two seconds
            current_time = pygame.time.get_ticks()
            if current_time - self.last_coin_spawn >= 1200:  # Coin spawn rate
                self.spawn_coin()
                self.last_coin_spawn = current_time

            if self.monster_counter >= self.monster_spawn_threshold:
                self.spawn_monster()
                self.monster_counter = 0

            self.coin_collision()
            self.wall_collision()
            self.check_collision_with_monster()

            self.clock.tick(60)  # 60 frames per second

    def tutki_tapahtumat(self):
        for tapahtuma in pygame.event.get():
            if tapahtuma.type == pygame.QUIT:
                exit()
            elif tapahtuma.type == pygame.KEYDOWN:
                if tapahtuma.key == pygame.K_RETURN and self.paused:
                    self.restart_game()

                elif tapahtuma.key == pygame.K_LEFT:
                    # Shoot projectile left
                    projectile_rect = pygame.Rect(self.robot_rect.centerx - self.VPROJECTILE_SIZE[0], self.robot_rect.centery - self.VPROJECTILE_SIZE[1] // 2, *self.VPROJECTILE_SIZE)
                    self.projectiles.append((projectile_rect, (-self.PROJECTILE_SPEED, 0)))
                    self.velocity_x += self.acceleration
                elif tapahtuma.key == pygame.K_RIGHT:
                    # Shoot projectile right
                    projectile_rect = pygame.Rect(self.robot_rect.centerx, self.robot_rect.centery - self.VPROJECTILE_SIZE[1] // 2, *self.VPROJECTILE_SIZE)
                    self.projectiles.append((projectile_rect, (self.PROJECTILE_SPEED, 0)))
                    self.velocity_x -= self.acceleration
                elif tapahtuma.key == pygame.K_UP:
                    # Shoot projectile up
                    projectile_rect = pygame.Rect(self.robot_rect.centerx - self.HPROJECTILE_SIZE[0] // 2, self.robot_rect.centery - self.HPROJECTILE_SIZE[1], *self.HPROJECTILE_SIZE)
                    self.projectiles.append((projectile_rect, (0, -self.PROJECTILE_SPEED)))
                    self.velocity_y += self.acceleration
                elif tapahtuma.key == pygame.K_DOWN:
                    # Shoot projectile down
                    projectile_rect = pygame.Rect(self.robot_rect.centerx - self.HPROJECTILE_SIZE[0] // 2, self.robot_rect.centery, *self.HPROJECTILE_SIZE)
                    self.projectiles.append((projectile_rect, (0, self.PROJECTILE_SPEED)))
                    self.velocity_y -= self.acceleration

    def wall_collision(self):
        if self.robot_rect.left < 0:
            self.robot_rect.left = 0
            self.velocity_x = self.velocity_x * -1
        elif self.robot_rect.right > self.leveys:
            self.robot_rect.right = self.leveys
            self.velocity_x = self.velocity_x * -1
        if self.robot_rect.top < 0:
            self.robot_rect.top = 0
            self.velocity_y = self.velocity_y * -1
        elif self.robot_rect.bottom > self.korkeus:
            self.robot_rect.bottom = self.korkeus
            self.velocity_y = self.velocity_y * -1

    def coin_collision(self):
        for projectile, _ in self.projectiles:
            for coin in self.coins:
                if projectile.colliderect(coin) or self.robot_rect.colliderect(coin):
                    self.coins.remove(coin)
                    self.monster_counter += 1
                    if not self.paused:
                        self.coin_counter += 1
                    if self.monster_counter >= self.monster_spawn_threshold:
                        self.spawn_monster()
                        self.monster_counter = 0

    def spawn_monster(self):
        # Calculate minimum distance between player and monster spawn position
        min_distance = max(self.kuvat[2].get_width(), self.kuvat[2].get_height()) + max(self.robot_image.get_width(), self.robot_image.get_height())

        # Choose a random spawn position for the monster
        max_attempts = 100  # Maximum number of attempts to spawn a monster
        for _ in range(max_attempts):
            monster = Monster(self.kuvat[2], self.leveys, self.korkeus)
            distance = ((self.robot_rect.centerx - monster.rect.centerx) ** 2 +
                        (self.robot_rect.centery - monster.rect.centery) ** 2) ** 0.5

            if distance >= min_distance:
                self.monsters.add(monster)
                break
        else:
            print("Failed to spawn monster after maximum attempts.")

    def spawn_coin(self):
        coin_rect = self.coin_image.get_rect()
        min_distance = max(coin_rect.width, coin_rect.height) + max(self.robot_rect.width, self.robot_rect.height)

        # Choose a random spawn position for the coin
        max_attempts = 100  # Maximum number of attempts to spawn a coin
        for _ in range(max_attempts):
            coin_rect.x = random.randint(0, self.leveys - coin_rect.width)
            coin_rect.y = random.randint(0, self.korkeus - coin_rect.height)

            coin_collides = any(coin_rect.colliderect(existing_coin) for existing_coin in self.coins)
            projectile_collides = any(projectile.colliderect(coin_rect) for projectile, _ in self.projectiles)

            if not coin_collides and not projectile_collides:
                # If no collision with existing coins or projectiles, spawn the coin
                self.coins.append(coin_rect)
                break
        else:
            print("Failed to spawn coin after maximum attempts.")

    def check_collision_with_monster(self):
        for monster in self.monsters:
            # Create smaller rectangles for player and monster collisions
            player_rect_smaller = self.robot_rect.inflate(-self.collision_margin, -self.collision_margin)
            monster_rect_smaller = monster.rect.inflate(-self.collision_margin, -self.collision_margin)

            if player_rect_smaller.colliderect(monster_rect_smaller):
                self.paused = True

    def restart_game(self):
        # Reset game variables to their initial states
        self.monsters.empty()
        self.coins.clear()
        self.projectiles.clear()
        self.coins_collected = 0
        self.coin_counter = 0
        self.paused = False
        self.play_again = False

        self.robot_rect.center = (self.leveys // 2, self.korkeus // 2)
        self.last_coin_spawn = pygame.time.get_ticks()

        self.spawn_coin()

    def piirra_naytto(self):
        self.naytto.fill((200, 200, 200))

        # Draw game elements
        if not self.paused:
            self.naytto.blit(self.robot_image, self.robot_rect)
            for monster in self.monsters:
                self.naytto.blit(monster.image, monster)
            for projectile, _ in self.projectiles:
                pygame.draw.rect(self.naytto, self.PROJECTILE_COLOR, projectile)
            for coin in self.coins:
                self.naytto.blit(self.coin_image, coin)

            # Draw coin counter
            coin_text = self.smallfont.render("Coins: " + str(self.coin_counter), True, (0, 0, 0))
            self.naytto.blit(coin_text, (10, 10))

        # Draw "YOU LOST" text in the middle of the screen if paused
        if self.paused:
            lost_text = self.bigfont.render("YOU LOST", True, (0, 0, 0))
            text_rect = lost_text.get_rect(center=(self.leveys // 2, self.korkeus // 2 - 80))
            self.naytto.blit(lost_text, text_rect)

            # Display the number of coins collected
            collected_text = self.smallfont.render("Coins collected: " + str(self.coin_counter), True, (0, 0, 0))
            collected_text_rect = collected_text.get_rect(center=(self.leveys // 2, self.korkeus // 2 + 50))
            self.naytto.blit(collected_text, collected_text_rect)

            # Draw "Press Enter to play again" text
            self.naytto.blit(self.play_again_text, self.play_again_rect)
            self.play_again = True

        pygame.display.flip()

if __name__ == "__main__":
    Knockback()
