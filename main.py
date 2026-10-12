import sys
import pygame
from game.game_engine import GameEngine

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 620
FPS = 60


def main():
    pygame.init()
    pygame.display.set_caption("Arm Wrestle Showdown")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    engine = GameEngine(SCREEN_WIDTH, SCREEN_HEIGHT)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                engine.handle_event(event)
        dt = clock.tick(FPS) / 1000.0
        engine.update(dt)
        engine.render(screen)
        pygame.display.flip()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
