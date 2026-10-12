import random
import pygame


class GameEngine:
    FPS = 60
    PLAYER_PUSH_STRENGTH = 4.2
    PUSH_STAMINA_COST = 2.0
    EXHAUSTED_THRESHOLD = 10.0
    LOW_STAMINA_THRESHOLD = 25.0
    NORMAL_STAMINA_REGEN_PER_SECOND = 4.0
    COUNTER_STAMINA_REGEN_PER_SECOND = 12.0
    AI_SURGE_DURATION = 2.0
    AI_COOLDOWN_DURATION = 4.0
    AI_SURGE_MULTIPLIER = 2.1
    AI_COOLDOWN_MULTIPLIER = 0.45
    COUNTER_WINDOW_SECONDS = 1.0
    COUNTER_BONUS_SECONDS = 1.5
    COUNTER_BONUS_MULTIPLIER = 2.0
    AI_STRENGTH = 0.35

    def __init__(self, width, height):
        self.width, self.height = width, height
        self.target_limit = 100.0
        self.reset()
        self.font_big = pygame.font.SysFont(None, 44)
        self.font_med = pygame.font.SysFont(None, 26)
        self.font_small = pygame.font.SysFont(None, 22)

    def reset(self):
        self.arm_position = 0.0
        self.last_key = None
        self.stamina = self.max_stamina = 100.0
        self.winner = None
        self.game_state = "PLAYING"
        self.ai_phase = "SURGE"
        self.ai_phase_elapsed = 0.0
        self.counter_window_remaining = 0.0
        self.counter_bonus_remaining = 0.0

    @property
    def ai_surge_active(self):
        return self.ai_phase == "SURGE"

    @property
    def exhausted(self):
        return self.stamina <= self.EXHAUSTED_THRESHOLD

    def _check_winner(self):
        if self.arm_position <= -self.target_limit:
            self.winner, self.game_state = "PLAYER", "GAME_OVER"
        elif self.arm_position >= self.target_limit:
            self.winner, self.game_state = "COMPUTER", "GAME_OVER"

    def handle_event(self, event):
        if self.game_state != "PLAYING":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()
            return
        if event.type != pygame.KEYDOWN or event.key not in (pygame.K_LEFT, pygame.K_RIGHT):
            return
        if self.last_key == event.key or self.exhausted:
            return

        # Press RIGHT in the short cooldown window to counter the surge.
        if (event.key == pygame.K_RIGHT and self.ai_phase == "COOLDOWN"
                and self.counter_window_remaining > 0.0):
            self.counter_window_remaining = 0.0
            self.counter_bonus_remaining = self.COUNTER_BONUS_SECONDS
            self.stamina = min(self.max_stamina, self.stamina + 10.0)

        multiplier = self.COUNTER_BONUS_MULTIPLIER if self.counter_bonus_remaining > 0 else 1.0
        # Negative arm positions are the player's winning direction; both alternating keys push left.
        self.arm_position -= self.PLAYER_PUSH_STRENGTH * multiplier
        self.stamina = max(0.0, self.stamina - self.PUSH_STAMINA_COST)
        self.last_key = event.key
        self._check_winner()

    def _advance_ai_phase(self, dt):
        self.ai_phase_elapsed += dt
        changed = False
        if self.ai_phase == "SURGE" and self.ai_phase_elapsed >= self.AI_SURGE_DURATION:
            overflow = self.ai_phase_elapsed - self.AI_SURGE_DURATION
            self.ai_phase, self.ai_phase_elapsed = "COOLDOWN", overflow
            self.counter_window_remaining = self.COUNTER_WINDOW_SECONDS
            changed = True
        elif self.ai_phase == "COOLDOWN" and self.ai_phase_elapsed >= self.AI_COOLDOWN_DURATION:
            overflow = self.ai_phase_elapsed - self.AI_COOLDOWN_DURATION
            self.ai_phase, self.ai_phase_elapsed = "SURGE", overflow
            self.counter_window_remaining = 0.0
            changed = True
        if not changed:
            self.counter_window_remaining = max(0.0, self.counter_window_remaining - dt)
        self.counter_bonus_remaining = max(0.0, self.counter_bonus_remaining - dt)

    def update(self, dt=1.0 / FPS):
        """Advance state by elapsed seconds; defaults to one 60-FPS frame."""
        if self.game_state != "PLAYING":
            return
        dt = max(0.0, float(dt))
        if dt == 0.0:
            return
        self._advance_ai_phase(dt)
        pressure = self.AI_SURGE_MULTIPLIER if self.ai_surge_active else self.AI_COOLDOWN_MULTIPLIER
        self.arm_position += self.AI_STRENGTH * random.uniform(0.3, 1.0) * pressure * dt * self.FPS
        regen = self.COUNTER_STAMINA_REGEN_PER_SECOND if self.counter_bonus_remaining > 0 else self.NORMAL_STAMINA_REGEN_PER_SECOND
        self.stamina = min(self.max_stamina, self.stamina + regen * dt)
        self._check_winner()

    def render(self, screen):
        screen.fill((25, 28, 35))
        title = self.font_big.render("ARM WRESTLE SHOWDOWN", True, (240, 240, 240))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 12))
        screen.blit(self.font_med.render("PLAYER", True, (80, 160, 255)), (60, 55))
        screen.blit(self.font_med.render("COMPUTER", True, (255, 100, 80)), (self.width - 150, 55))

        table = pygame.Rect(40, 100, self.width - 80, 310)
        pygame.draw.rect(screen, (110, 50, 15), table, border_radius=14)
        pygame.draw.rect(screen, (70, 30, 8), table, width=5, border_radius=14)
        pygame.draw.line(screen, (45, 18, 4), (self.width // 2, 100), (self.width // 2, 410), 4)
        hand_x = self.width // 2 + int((self.arm_position / self.target_limit) * 95)
        hand_y = 235
        p_shoulder, p_elbow = (70, 330), (140, 215)
        c_shoulder, c_elbow = (self.width - 70, 330), (self.width - 140, 215)
        pygame.draw.line(screen, (200, 145, 110), p_shoulder, p_elbow, 32)
        pygame.draw.line(screen, (215, 160, 125), p_elbow, (hand_x, hand_y), 26)
        pygame.draw.circle(screen, (185, 130, 95), p_elbow, 18)
        pygame.draw.line(screen, (170, 110, 85), c_shoulder, c_elbow, 32)
        pygame.draw.line(screen, (185, 125, 95), c_elbow, (hand_x, hand_y), 26)
        pygame.draw.circle(screen, (150, 95, 70), c_elbow, 18)
        pygame.draw.circle(screen, (225, 175, 140), (hand_x, hand_y), 24)
        pygame.draw.circle(screen, (160, 115, 85), (hand_x, hand_y), 24, width=3)

        screen.blit(self.font_med.render("STAMINA", True, (220, 220, 220)), (40, 445))
        pygame.draw.rect(screen, (45, 50, 60), pygame.Rect(140, 448, 240, 22), border_radius=6)
        fill_width = max(0, int(240 * self.stamina / self.max_stamina))
        if fill_width:
            color = (60, 210, 100) if self.stamina > self.LOW_STAMINA_THRESHOLD else (220, 60, 60)
            pygame.draw.rect(screen, color, pygame.Rect(140, 448, fill_width, 22), border_radius=6)

        if self.ai_surge_active:
            status, status_color = "AI POWER SURGE! Brace yourself", (255, 95, 80)
        else:
            status, status_color = "AI COOLDOWN - push to recover", (100, 230, 150)
        surf = self.font_small.render(status, True, status_color)
        screen.blit(surf, (self.width // 2 - surf.get_width() // 2, 482))

        if self.counter_bonus_remaining > 0:
            info, info_color = "COUNTER-SURGE BONUS! 2x push + fast recovery", (100, 220, 255)
        elif self.counter_window_remaining > 0:
            info, info_color = "COUNTER WINDOW: press RIGHT now!", (255, 215, 90)
        elif self.exhausted:
            info, info_color = "EXHAUSTED - wait for stamina to recover", (255, 90, 90)
        elif self.stamina <= self.LOW_STAMINA_THRESHOLD:
            info, info_color = "LOW STAMINA - pace your pushes", (255, 185, 85)
        else:
            info, info_color = "Alternate LEFT and RIGHT to push", (210, 210, 210)
        surf = self.font_small.render(info, True, info_color)
        screen.blit(surf, (self.width // 2 - surf.get_width() // 2, 510))

        if self.game_state == "GAME_OVER":
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            message = "PLAYER WINS THE MATCH!" if self.winner == "PLAYER" else "COMPUTER WINS!"
            color = (80, 240, 100) if self.winner == "PLAYER" else (240, 80, 80)
            surf = self.font_big.render(message, True, color)
            screen.blit(surf, (self.width // 2 - surf.get_width() // 2, self.height // 2 - 45))
            surf = self.font_med.render("Press [R] to Rematch", True, (240, 240, 240))
            screen.blit(surf, (self.width // 2 - surf.get_width() // 2, self.height // 2 + 10))
