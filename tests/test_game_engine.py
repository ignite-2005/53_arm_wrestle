import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from game.game_engine import GameEngine


class GameEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.game = GameEngine(600, 620)

    def key(self, key):
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))

    def test_alternating_inputs_move_toward_player(self):
        self.key(pygame.K_LEFT)
        self.key(pygame.K_RIGHT)
        self.assertAlmostEqual(self.game.arm_position, -8.4)

    def test_repeating_same_key_does_not_add_force(self):
        self.key(pygame.K_LEFT)
        self.key(pygame.K_LEFT)
        self.assertAlmostEqual(self.game.arm_position, -4.2)

    def test_surge_transitions_to_cooldown_and_opens_counter_window(self):
        with patch("game.game_engine.random.uniform", return_value=0.5):
            for _ in range(201):
                self.game.update(0.01)
        self.assertEqual(self.game.ai_phase, "COOLDOWN")
        self.assertGreater(self.game.counter_window_remaining, 0.0)

    def test_right_during_counter_window_activates_bonus(self):
        self.game.ai_phase = "COOLDOWN"
        self.game.counter_window_remaining = 0.8
        start = self.game.arm_position
        self.key(pygame.K_RIGHT)
        self.assertAlmostEqual(self.game.arm_position - start, -8.4)
        self.assertGreater(self.game.counter_bonus_remaining, 0.0)
        self.assertEqual(self.game.counter_window_remaining, 0.0)

    def test_ai_force_is_lower_during_cooldown_than_surge(self):
        with patch("game.game_engine.random.uniform", return_value=1.0):
            surge, cooldown = GameEngine(600, 620), GameEngine(600, 620)
            cooldown.ai_phase = "COOLDOWN"
            surge.update(0.01)
            cooldown.update(0.01)
        self.assertGreater(surge.arm_position, cooldown.arm_position)

    def test_exhaustion_blocks_input_until_stamina_recovers(self):
        self.game.stamina = 9.0
        self.key(pygame.K_LEFT)
        self.assertEqual(self.game.arm_position, 0.0)
        with patch("game.game_engine.random.uniform", return_value=0.0):
            self.game.update(1.0)
        self.assertGreater(self.game.stamina, self.game.EXHAUSTED_THRESHOLD)
        self.key(pygame.K_LEFT)
        self.assertLess(self.game.arm_position, 0.0)

    def test_counter_window_message_is_hidden_while_exhausted(self):
        self.game.ai_phase = "COOLDOWN"
        self.game.counter_window_remaining = 0.5
        self.game.stamina = self.game.EXHAUSTED_THRESHOLD
        surface = pygame.Surface((600, 620))

        rendered_text = []

        def capture_render(text, antialias, color):
            rendered_text.append(text)
            return pygame.Surface((1, 1))

        with patch.object(self.game.font_small, "render", side_effect=capture_render):
            self.game.render(surface)

        self.assertIn("EXHAUSTED - wait for stamina to recover", rendered_text)
        self.assertNotIn("COUNTER WINDOW: press RIGHT now!", rendered_text)

    def test_invalid_key_does_not_change_game_state(self):
        self.key(pygame.K_SPACE)
        self.assertEqual(self.game.arm_position, 0.0)
        self.assertEqual(self.game.stamina, 100.0)

    def test_player_win_is_detected(self):
        self.game.arm_position = -99.0
        self.key(pygame.K_LEFT)
        self.assertEqual(self.game.winner, "PLAYER")
        self.assertEqual(self.game.game_state, "GAME_OVER")

    def test_cycle_returns_to_surge_after_cooldown(self):
        self.game.ai_phase = "COOLDOWN"
        self.game.ai_phase_elapsed = 0.0
        with patch("game.game_engine.random.uniform", return_value=0.0):
            self.game.update(4.01)
        self.assertEqual(self.game.ai_phase, "SURGE")

    def test_render_smoke_test(self):
        surface = pygame.Surface((600, 620))
        self.game.render(surface)
        self.assertEqual(surface.get_size(), (600, 620))

    def test_reset_restores_match_and_timed_states(self):
        self.game.ai_phase = "COOLDOWN"
        self.game.counter_window_remaining = 0.5
        self.game.counter_bonus_remaining = 1.0
        self.game.arm_position = -30.0
        self.game.stamina = 35.0
        self.game.reset()
        self.assertEqual(self.game.arm_position, 0.0)
        self.assertEqual(self.game.stamina, 100.0)
        self.assertEqual(self.game.game_state, "PLAYING")
        self.assertEqual(self.game.ai_phase, "SURGE")
        self.assertEqual(self.game.counter_window_remaining, 0.0)
        self.assertEqual(self.game.counter_bonus_remaining, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
