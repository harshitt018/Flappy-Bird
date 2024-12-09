import pygame
import random
import sqlite3

# Initialize pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
GROUND_HEIGHT = 100
BIRD_WIDTH = 40
BIRD_HEIGHT = 30
PIPE_WIDTH = 60
PIPE_GAP = 150
FPS = 60

# Load assets and resize images
bg_image = pygame.image.load('bg.png')
bg_image = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

bird_image = pygame.image.load('bird.png')
bird_image = pygame.transform.scale(bird_image, (BIRD_WIDTH, BIRD_HEIGHT))

pipe_image = pygame.image.load('pipe.png')
pipe_image = pygame.transform.scale(pipe_image, (PIPE_WIDTH, pipe_image.get_height()))

ground_image = pygame.image.load('ground.png')
ground_image = pygame.transform.scale(ground_image, (SCREEN_WIDTH, GROUND_HEIGHT))

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird")

# Game clock
clock = pygame.time.Clock()

# Database setup
conn = sqlite3.connect('scores.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_name TEXT,
        score INTEGER
    )
''')
conn.commit()

# Function to insert score into database
def insert_score(player_name, score):
    c.execute('INSERT INTO scores (player_name, score) VALUES (?, ?)', (player_name, score))
    conn.commit()

# Function to get highest score
def get_high_score():
    c.execute('SELECT MAX(score) FROM scores')
    result = c.fetchone()[0]
    return result if result is not None else 0

# Function to get player history
def get_player_history():
    c.execute('SELECT player_name, MAX(score) FROM scores GROUP BY player_name')
    return c.fetchall()

# Bird class
class Bird:
    def __init__(self):
        self.x = 50
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.gravity = 0.5
        self.jump = -10
        self.image = bird_image
        self.rect = pygame.Rect(self.x, self.y, BIRD_WIDTH, BIRD_HEIGHT)

    def move(self):
        self.velocity += self.gravity
        self.y += self.velocity
        self.rect.y = self.y

    def flap(self):
        self.velocity = self.jump

    def draw(self):
        screen.blit(self.image, (self.rect.x, self.rect.y))

# Pipe class
class Pipe:
    def __init__(self):
        self.x = SCREEN_WIDTH
        self.height = random.randint(100, SCREEN_HEIGHT - PIPE_GAP - GROUND_HEIGHT)
        self.top_rect = pygame.Rect(self.x, 0, PIPE_WIDTH, self.height)
        self.bottom_rect = pygame.Rect(self.x, self.height + PIPE_GAP, PIPE_WIDTH, SCREEN_HEIGHT - self.height - PIPE_GAP)

    def move(self):
        self.x -= 5
        self.top_rect.x = self.x
        self.bottom_rect.x = self.x

    def draw(self):
        screen.blit(pipe_image, (self.x, self.height - pipe_image.get_height()))
        screen.blit(pipe_image, (self.x, self.height + PIPE_GAP))

# Function to display Game Over and restart instructions
def display_game_over(score, player_name):
    insert_score(player_name, score)
    font = pygame.font.Font(None, 50)
    text = font.render(f"Game Over! Score: {score}", True, BLACK)
    restart_text = font.render("Press R to Restart", True, BLACK)
    high_score_text = font.render(f"High Score: {get_high_score()}", True, BLACK)
    screen.blit(text, (50, 200))
    screen.blit(high_score_text, (50, 250))
    screen.blit(restart_text, (50, 300))
    pygame.display.flip()

# Function to display player history
def display_player_history():
    history = get_player_history()
    screen.fill(WHITE)

    # Title
    font_title = pygame.font.Font(None, 48)
    title_text = font_title.render("Player History", True, BLACK)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
    screen.blit(title_text, title_rect)

    # Semi-transparent rectangle for the scores
    history_rect = pygame.Rect(50, 100, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 200)
    pygame.draw.rect(screen, (0, 0, 0, 150), history_rect)

    # Draw history
    font = pygame.font.Font(None, 36)
    for index, (player_name, high_score) in enumerate(history):
        name_text = font.render(player_name, True, (100, 200, 255))
        score_text = font.render(str(high_score), True, (255, 255, 100))

        # Calculate positions for centered alignment
        name_rect = name_text.get_rect(center=(SCREEN_WIDTH // 2 - 50, 120 + index * 30))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2 + 50, 120 + index * 30))

        screen.blit(name_text, name_rect)
        screen.blit(score_text, score_rect)

    pygame.display.flip()

    # Wait for user to press any key to return to the game
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                waiting = False

# Main game function
def game_loop(player_name):
    bird = Bird()
    pipes = [Pipe()]
    score = 0
    running = True
    game_over = False

    while running:
        screen.blit(bg_image, (0, 0))

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over:
                    bird.flap()
                if event.key == pygame.K_r and game_over:
                    game_loop(player_name)
                if event.key == pygame.K_h and not game_over:
                    display_player_history()

        if not game_over:
            bird.move()

            # Pipe movement and generation
            for pipe in pipes:
                pipe.move()
                if pipe.x + PIPE_WIDTH < 0:
                    pipes.remove(pipe)
                    pipes.append(Pipe())
                    score += 1

                # Collision detection
                if (bird.rect.colliderect(pipe.top_rect) or 
                    bird.rect.colliderect(pipe.bottom_rect) or 
                    bird.y <= 0 or 
                    bird.y >= SCREEN_HEIGHT - GROUND_HEIGHT):
                    game_over = True

            # Ground collision
            if bird.y >= SCREEN_HEIGHT - GROUND_HEIGHT:
                game_over = True

            # Draw pipes
            for pipe in pipes:
                pipe.draw()

        bird.draw()
        screen.blit(ground_image, (0, SCREEN_HEIGHT - GROUND_HEIGHT))

        # Draw score
        font = pygame.font.Font(None, 36)
        text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(text, (10, 10))

        if game_over:
            display_game_over(score, player_name)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

# Function to display start screen and get player name
def start_screen():
    player_name = ''
    input_box = pygame.Rect(100, 250, 200, 50)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    text = ''
    font = pygame.font.Font(None, 32)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        return text
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode

        screen.fill((255, 255, 255))
        pygame.draw.rect(screen, color, input_box, 2)
        txt_surface = font.render(text, True, color)
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        start_text = font.render("Enter your name and press Enter to start:", True, BLACK)
        screen.blit(start_text, (20, 200))
        pygame.display.flip()

# Start the game
if __name__ == "__main__":
    player_name = start_screen()
    game_loop(player_name)
