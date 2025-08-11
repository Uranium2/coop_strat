import random
import time
import uuid

from shared.models.game_models import (
    AttackEffect,
    AttackEffectType,
    Position,
)


class CombatService:
    def __init__(self):
        pass

    def create_attack_effect(
        self,
        attacker_id: str,
        target_id: str,
        attacker_pos: Position,
        target_pos: Position,
        damage: int,
        effect_type: str = None,
        attacker=None,
        target=None,
    ) -> AttackEffect:
        """Create an attack effect for visual representation"""
        # If attacker and target objects are provided, use the old interface for compatibility
        if attacker is not None and target is not None:
            return self._create_attack_effect_legacy(attacker, target, damage)

        # Determine effect type
        attack_effect_type = AttackEffectType.MELEE
        if effect_type:
            if effect_type == "RANGED":
                attack_effect_type = AttackEffectType.RANGED
            elif effect_type == "MAGIC":
                attack_effect_type = AttackEffectType.MAGIC

        # Duration based on effect type
        duration = 0.3  # Melee attacks are quick
        if attack_effect_type == AttackEffectType.RANGED:
            duration = 0.8  # Arrows take time to travel
        elif attack_effect_type == AttackEffectType.MAGIC:
            duration = 0.6  # Magic spells have medium duration

        return AttackEffect(
            id=str(uuid.uuid4()),
            attacker_id=attacker_id,
            target_id=target_id,
            effect_type=attack_effect_type,
            start_position=attacker_pos,
            end_position=target_pos,
            start_time=time.time(),
            duration=duration,
            damage=damage,
        )

    def _create_attack_effect_legacy(
        self, attacker, target, damage: int
    ) -> AttackEffect:
        """Legacy method for backward compatibility"""
        # Determine effect type based on attacker
        effect_type = AttackEffectType.MELEE
        if hasattr(attacker, "hero_type"):
            if attacker.hero_type.value == "ARCHER":
                effect_type = AttackEffectType.RANGED
            elif attacker.hero_type.value == "MAGE":
                effect_type = AttackEffectType.MAGIC

        # Duration based on effect type
        duration = 0.3  # Melee attacks are quick
        if effect_type == AttackEffectType.RANGED:
            duration = 0.8  # Arrows take time to travel
        elif effect_type == AttackEffectType.MAGIC:
            duration = 0.6  # Magic spells have medium duration

        return AttackEffect(
            id=str(uuid.uuid4()),
            attacker_id=attacker.id,
            target_id=target.id,
            effect_type=effect_type,
            start_position=Position(x=attacker.position.x, y=attacker.position.y),
            end_position=Position(x=target.position.x, y=target.position.y),
            start_time=time.time(),
            duration=duration,
            damage=damage,
        )

    def apply_damage(self, attacker, target) -> tuple[bool, AttackEffect]:
        """Apply damage from attacker to target, returns (target_died, attack_effect)"""
        # Simple damage calculation for now
        base_damage = 10  # Default damage

        # Get attacker damage if available
        if hasattr(attacker, "attack_damage"):
            base_damage = attacker.attack_damage
        elif hasattr(attacker, "combat_stats") and attacker.combat_stats:
            base_damage = attacker.combat_stats.attack_damage

        # Apply damage with some variance
        damage = int(base_damage * (0.8 + random.random() * 0.4))  # ±20% variance

        # Apply damage to target
        target.health = max(0, target.health - damage)

        # Create attack effect using legacy method
        attack_effect = self._create_attack_effect_legacy(attacker, target, damage)

        return target.health <= 0, attack_effect
