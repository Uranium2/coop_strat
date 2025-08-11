import random
from typing import Union

from shared.models.game_models import (
    Building,
    Enemy,
    GameState,
    Hero,
    Position,
    Unit,
)


class CombatService:
    def __init__(self):
        pass

    def apply_damage(self, attacker, target) -> bool:
        """Apply damage from attacker to target, returns True if target died"""
        # Simple damage calculation for now
        base_damage = 10  # Default damage
        
        # Get attacker damage if available
        if hasattr(attacker, 'attack_damage'):
            base_damage = attacker.attack_damage
        elif hasattr(attacker, 'combat_stats') and attacker.combat_stats:
            base_damage = attacker.combat_stats.attack_damage
        
        # Apply damage with some variance
        damage = int(base_damage * (0.8 + random.random() * 0.4))  # ±20% variance
        
        # Apply damage to target
        target.health = max(0, target.health - damage)
        
        return target.health <= 0