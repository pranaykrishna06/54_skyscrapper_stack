import random
import pygame
from game.block import Block


class Debris:
    """A trimmed block section that falls and rotates after a cut."""

    def __init__(self, x, y, width, height, color, velocity_x, rotation_speed):
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)
        self.color = color
        self.velocity_x = float(velocity_x)
        self.velocity_y = -1.5
        self.rotation = 0.0
        self.rotation_speed = float(rotation_speed)
        self.gravity = 0.45
        self.life = 90

    def update(self):
        self.velocity_y += self.gravity
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.rotation += self.rotation_speed
        self.life -= 1

    def render(self, surface):
        width = max(2, int(self.width))
        height = max(2, int(self.height))
        debris_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(debris_surface, self.color, debris_surface.get_rect(), border_radius=4)
        pygame.draw.rect(
            debris_surface,
            (245, 245, 250),
            debris_surface.get_rect(),
            width=2,
            border_radius=4,
        )

        rotated = pygame.transform.rotate(debris_surface, self.rotation)
        rect = rotated.get_rect(center=(int(self.x + self.width / 2), int(self.y + self.height / 2)))
        surface.blit(rotated, rect)


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.block_height = 28
        self.base_width = 180

        self.font_title = pygame.font.SysFont(None, 38)
        self.font_hud = pygame.font.SysFont(None, 28)
        self.font_big = pygame.font.SysFont(None, 46)

        # Task 2: perfect-placement settings/state.
        self.perfect_tolerance = 6
        self.perfect_bonus = 2
        self.perfect_streak = 0
        self.perfect_message_timer = 0
        self.perfect_message_duration = 45
        self.width_restore_streak = 3
        self.width_restore_amount = 5

        self.reset()

    def get_color(self, index):
        palette = [
            (230, 75, 75),   # Crimson
            (240, 140, 45),  # Orange
            (245, 210, 50),  # Gold
            (60, 195, 110),  # Green
            (50, 150, 240),  # Blue
            (165, 80, 225),  # Purple
        ]
        return palette[index % len(palette)]

    def reset(self):
        self.score = 0
        self.game_over = False
        self.perfect_streak = 0
        self.perfect_message_timer = 0

        base_x = (self.width - self.base_width) // 2
        base_y = self.height - 60
        base_block = Block(base_x, base_y, self.base_width, self.block_height, self.get_color(0), speed=0)
        self.stack = [base_block]
        self.debris = []

        self.spawn_active_block()

    def spawn_active_block(self):
        top_block = self.stack[-1]
        next_y = top_block.y - self.block_height - 4
        speed = min(10.0, 4.5 + (len(self.stack) * 0.35))
        color = self.get_color(len(self.stack))

        start_x = 25 if random.choice([True, False]) else self.width - 25 - top_block.width
        self.active_block = Block(start_x, next_y, top_block.width, self.block_height, color, speed=speed)

    def create_debris(self, x, y, width, color, direction):
        if width <= 0:
            return

        velocity_x = 1.2 * direction
        rotation_speed = 5.0 * direction
        self.debris.append(
            Debris(
                x,
                y,
                width,
                self.block_height,
                color,
                velocity_x,
                rotation_speed,
            )
        )

    def drop_block(self):
        if self.game_over:
            return

        top_block = self.stack[-1]
        act = self.active_block

        left = max(act.x, top_block.x)
        right = min(act.x + act.width, top_block.x + top_block.width)
        overlap = right - left

        is_successful_drop = overlap > 0

        if is_successful_drop:
            # Task 2: a placement is perfect when the active block is
            # almost flush with either horizontal edge of the tower top.
            left_alignment = abs(act.x - top_block.x)
            right_alignment = abs(
                (act.x + act.width) - (top_block.x + top_block.width)
            )
            is_perfect = min(left_alignment, right_alignment) <= self.perfect_tolerance

            if is_perfect:
                # Snap to the tower edge and keep the active block's full width.
                snapped_x = top_block.x if left_alignment <= right_alignment else (
                    top_block.x + top_block.width - act.width
                )
                new_block = Block(
                    snapped_x,
                    act.y,
                    act.width,
                    self.block_height,
                    act.color,
                    speed=0,
                )

                self.perfect_streak += 1
                self.perfect_message_timer = self.perfect_message_duration
                self.score += 1 + self.perfect_bonus

                # Restore a small amount of width after several consecutive
                # perfect placements, up to the original base width.
                if self.perfect_streak % self.width_restore_streak == 0:
                    restored_width = min(
                        self.base_width,
                        new_block.width + self.width_restore_amount,
                    )
                    width_gain = restored_width - new_block.width
                    if width_gain > 0:
                        new_block.width = restored_width
                        new_block.x -= width_gain / 2
            else:
                # Task 3: animate the sections cut away from the active block.
                left_offcut = left - act.x
                right_offcut = (act.x + act.width) - right

                if left_offcut > 0:
                    self.create_debris(act.x, act.y, left_offcut, act.color, -1)
                if right_offcut > 0:
                    self.create_debris(right, act.y, right_offcut, act.color, 1)

                trimmed_width = max(10.0, overlap)
                new_block = Block(
                    left,
                    act.y,
                    trimmed_width,
                    self.block_height,
                    act.color,
                    speed=0,
                )
                self.perfect_streak = 0
                self.score += 1

            self.stack.append(new_block)

            if new_block.y < 180:
                shift_amount = self.block_height + 4
                for b in self.stack:
                    b.y += shift_amount

            self.spawn_active_block()
        else:
            self.perfect_streak = 0
            self.perfect_message_timer = 0
            self.game_over = True

    def handle_event(self, event):
        if self.game_over:
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_r) or                (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                self.reset()
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.drop_block()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.drop_block()

    def update(self):
        if not self.game_over:
            self.active_block.update(self.width)

        if self.perfect_message_timer > 0:
            self.perfect_message_timer -= 1

        for debris in self.debris:
            debris.update()
        self.debris = [
            debris
            for debris in self.debris
            if debris.life > 0 and debris.y < self.height + 60
        ]

    def get_atmospheric_colors(self):
        """Return top/bottom sky colors based on the current tower height."""
        # Use actual stack height rather than score so perfect-placement bonuses
        # do not make the sky advance faster than the tower.
        height = max(0, len(self.stack) - 1)

        # Gradually move through atmospheric stages as the tower climbs.
        stages = [
            ((24, 27, 36), (58, 72, 105)),    # ground: night blue
            ((34, 43, 78), (98, 74, 128)),    # lower climb: violet
            ((62, 47, 105), (170, 92, 125)),  # mid climb: dusk
            ((96, 62, 104), (222, 139, 105)), # high climb: warm horizon
            ((54, 76, 118), (165, 196, 220)), # upper climb: pale atmosphere
        ]

        stage_position = min(height / 6.0, len(stages) - 1)
        stage_index = min(int(stage_position), len(stages) - 2)
        fraction = stage_position - stage_index

        top_a, bottom_a = stages[stage_index]
        top_b, bottom_b = stages[stage_index + 1]

        def blend(a, b, t):
            return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

        return blend(top_a, top_b, fraction), blend(bottom_a, bottom_b, fraction)

    def draw_atmospheric_background(self, screen):
        """Draw a vertical sky gradient whose colors change with tower height."""
        top_color, bottom_color = self.get_atmospheric_colors()
        max_y = max(1, self.height - 1)

        for y in range(self.height):
            t = y / max_y
            color = tuple(
                int(top_color[i] + (bottom_color[i] - top_color[i]) * t)
                for i in range(3)
            )
            pygame.draw.line(screen, color, (0, y), (self.width, y))

    def render(self, screen):
        # Task 4: replace the static sky with a height-driven atmospheric gradient.
        self.draw_atmospheric_background(screen)

        title_surf = self.font_title.render("Skyscraper Stack", True, (245, 245, 245))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 16))

        score_surf = self.font_hud.render(f"Height: {self.score}", True, (255, 220, 80))
        screen.blit(score_surf, (self.width // 2 - score_surf.get_width() // 2, 54))

        for debris in self.debris:
            debris.render(screen)

        for b in self.stack:
            b.render(screen)

        if not self.game_over:
            self.active_block.render(screen)

        # Task 2: show the temporary perfect-placement prompt.
        if self.perfect_message_timer > 0 and not self.game_over:
            perfect_surf = self.font_big.render("PERFECT!", True, (255, 220, 80))
            screen.blit(
                perfect_surf,
                (
                    self.width // 2 - perfect_surf.get_width() // 2,
                    95,
                ),
            )

        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 195))
            screen.blit(overlay, (0, 0))

            over_surf = self.font_big.render("TOWER COLLAPSED!", True, (240, 75, 75))
            screen.blit(over_surf, (self.width // 2 - over_surf.get_width() // 2, self.height // 2 - 40))

            final_surf = self.font_hud.render(f"Final Height: {self.score}", True, (255, 255, 255))
            screen.blit(final_surf, (self.width // 2 - final_surf.get_width() // 2, self.height // 2 + 10))

            restart_surf = self.font_hud.render("Press [Space] or [R] to Play Again", True, (200, 200, 200))
            screen.blit(restart_surf, (self.width // 2 - restart_surf.get_width() // 2, self.height // 2 + 50))
