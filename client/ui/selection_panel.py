from typing import Union

import pygame

from shared.constants.game_constants import COLORS
from shared.models.game_models import Building, Enemy, Hero


class SelectionPanel:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

    def render(
        self, screen: pygame.Surface, selected_entity: Union[Hero, Building, Enemy]
    ):
        pygame.draw.rect(screen, COLORS["BLACK"], self.rect)
        pygame.draw.rect(screen, COLORS["WHITE"], self.rect, 2)

        if hasattr(selected_entity, "hero_type"):
            self._render_hero_info(screen, selected_entity)
        elif hasattr(selected_entity, "building_type"):
            self._render_building_info(screen, selected_entity)
        elif (
            hasattr(selected_entity, "id")
            and not hasattr(selected_entity, "hero_type")
            and not hasattr(selected_entity, "building_type")
        ):
            self._render_enemy_info(screen, selected_entity)

    def _render_hero_info(self, screen: pygame.Surface, hero: Hero):
        title = self.font.render(f"Hero: {hero.hero_type}", True, COLORS["WHITE"])
        screen.blit(title, (self.rect.x + 5, self.rect.y + 5))

        y_offset = 30
        health_text = f"Health: {hero.health}/{hero.max_health}"
        health_surface = self.small_font.render(health_text, True, COLORS["WHITE"])
        screen.blit(health_surface, (self.rect.x + 5, self.rect.y + y_offset))

        y_offset += 20
        damage_text = f"Attack Damage: {hero.attack_damage}"
        damage_surface = self.small_font.render(damage_text, True, COLORS["WHITE"])
        screen.blit(damage_surface, (self.rect.x + 5, self.rect.y + y_offset))

        y_offset += 20
        range_text = f"Attack Range: {hero.attack_range}"
        range_surface = self.small_font.render(range_text, True, COLORS["WHITE"])
        screen.blit(range_surface, (self.rect.x + 5, self.rect.y + y_offset))

        y_offset += 20
        speed_text = f"Move Speed: {hero.speed}"
        speed_surface = self.small_font.render(speed_text, True, COLORS["WHITE"])
        screen.blit(speed_surface, (self.rect.x + 5, self.rect.y + y_offset))

        y_offset += 20
        attack_speed_text = f"Attack Speed: {hero.attack_speed}"
        attack_speed_surface = self.small_font.render(
            attack_speed_text, True, COLORS["WHITE"]
        )
        screen.blit(attack_speed_surface, (self.rect.x + 5, self.rect.y + y_offset))

    def _render_building_info(self, screen: pygame.Surface, building: Building):
        title = self.font.render(
            f"Building: {building.building_type}", True, COLORS["WHITE"]
        )
        screen.blit(title, (self.rect.x + 5, self.rect.y + 5))

        health_text = f"Health: {building.health}/{building.max_health}"
        health_surface = self.small_font.render(health_text, True, COLORS["WHITE"])
        screen.blit(health_surface, (self.rect.x + 5, self.rect.y + 30))

        pos_text = f"Position: ({building.position.x}, {building.position.y})"
        pos_surface = self.small_font.render(pos_text, True, COLORS["WHITE"])
        screen.blit(pos_surface, (self.rect.x + 5, self.rect.y + 50))

    def _render_enemy_info(self, screen: pygame.Surface, enemy: Enemy):
        title = self.font.render("Enemy", True, COLORS["RED"])
        screen.blit(title, (self.rect.x + 5, self.rect.y + 5))

        y_offset = 30
        health_text = f"Health: {enemy.health}/{enemy.max_health}"
        health_surface = self.small_font.render(health_text, True, COLORS["WHITE"])
        screen.blit(health_surface, (self.rect.x + 5, self.rect.y + y_offset))

        y_offset += 20
        damage_text = f"Attack Damage: {enemy.attack_damage}"
        damage_surface = self.small_font.render(damage_text, True, COLORS["WHITE"])
        screen.blit(damage_surface, (self.rect.x + 5, self.rect.y + y_offset))

        y_offset += 20
        range_text = f"Attack Range: {enemy.attack_range}"
        range_surface = self.small_font.render(range_text, True, COLORS["WHITE"])
        screen.blit(range_surface, (self.rect.x + 5, self.rect.y + y_offset))

        y_offset += 20
        speed_text = f"Move Speed: {enemy.speed}"
        speed_surface = self.small_font.render(speed_text, True, COLORS["WHITE"])
        screen.blit(speed_surface, (self.rect.x + 5, self.rect.y + y_offset))

        y_offset += 20
        attack_speed_text = f"Attack Speed: {enemy.attack_speed}"
        attack_speed_surface = self.small_font.render(
            attack_speed_text, True, COLORS["WHITE"]
        )
        screen.blit(attack_speed_surface, (self.rect.x + 5, self.rect.y + y_offset))
