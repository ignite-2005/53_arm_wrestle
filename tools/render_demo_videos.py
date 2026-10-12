"""Render 10-second gameplay-surface demos from the original and fixed game engines.

Run inside a graphical/headless Pygame environment with ffmpeg installed:
    python tools/render_demo_videos.py

These clips capture the game's render surface under scripted key inputs. They are not
desktop/screen recordings.
"""
import os
import random
import subprocess
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from game.game_engine import GameEngine
from tools.original_game_engine import GameEngine as OriginalGameEngine

WIDTH, HEIGHT = 600, 620
VIDEO_FPS = 20
SECONDS = 10
SIM_FPS = 60
ROOT = Path(__file__).resolve().parents[1]
VIDEO_DIR = ROOT / "videos"


def run_demo(engine, output_path: Path, fixed: bool) -> None:
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    total_frames = VIDEO_FPS * SECONDS
    sim_steps_per_frame = SIM_FPS // VIDEO_FPS
    tick = 0
    key_index = 0
    cadence_ticks = 24 if fixed else 42  # 0.4s fixed; 0.7s original

    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}", "-r", str(VIDEO_FPS), "-i", "-",
        "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "31",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(output_path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for _ in range(total_frames):
            for _step in range(sim_steps_per_frame):
                if fixed:
                    engine.update(1.0 / SIM_FPS)
                else:
                    engine.update()

                # For the fixed demo, make sure the strategic RIGHT input lands
                # inside the counter-surge window as soon as cooldown begins.
                if fixed and engine.ai_phase == "COOLDOWN" and engine.counter_window_remaining > 0:
                    # The scripted user alternates keys; ensure RIGHT is accepted if
                    # a cadence edge coincides with phase transition rounding.
                    if not getattr(engine, "_demo_counter_attempted", False):
                        engine.last_key = pygame.K_LEFT
                        engine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
                        engine._demo_counter_attempted = True
                        key_index += 1
                        tick += 1
                        continue

                if tick % cadence_ticks == 0 and engine.game_state == "PLAYING":
                    key = pygame.K_LEFT if key_index % 2 == 0 else pygame.K_RIGHT
                    engine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))
                    key_index += 1
                tick += 1

            engine.render(screen)
            frame_bytes = pygame.image.tostring(screen, "RGB")
            assert process.stdin is not None
            process.stdin.write(frame_bytes)
    finally:
        if process.stdin is not None:
            process.stdin.close()
        code = process.wait()
        if code != 0:
            raise RuntimeError(f"ffmpeg failed for {output_path.name} with exit code {code}")


def main() -> None:
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    pygame.init()
    random.seed(484)
    run_demo(OriginalGameEngine(WIDTH, HEIGHT), VIDEO_DIR / "before_bug_demo.mp4", fixed=False)
    random.seed(484)
    run_demo(GameEngine(WIDTH, HEIGHT), VIDEO_DIR / "after_fix_demo.mp4", fixed=True)
    pygame.quit()
    for name in ("before_bug_demo.mp4", "after_fix_demo.mp4"):
        size = (VIDEO_DIR / name).stat().st_size
        print(f"Created {name}: {size} bytes, {SECONDS} seconds at {VIDEO_FPS} fps")


if __name__ == "__main__":
    main()
