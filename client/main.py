import pygame
import asyncio
import websockets
import json
import sys
import logging
from client.scenes.game_scene import GameScene
from client.scenes.menu_scene import MenuScene
from client.utils.network_manager import NetworkManager
from shared.constants.game_constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('client.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GameClient:
    def __init__(self):
        logger.info("Initializing game client")
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Co-op Survival RTS")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.network_manager = NetworkManager()
        self.current_scene = MenuScene(self.screen, self.network_manager)
        logger.info("Game client initialized successfully")
        
    async def run(self):
        logger.info("Starting main game loop")
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    logger.info("Quit event received")
                    self.running = False
                else:
                    self.current_scene.handle_event(event)
            
            self.current_scene.update(dt)
            
            self.screen.fill((0, 0, 0))
            self.current_scene.render(self.screen)
            pygame.display.flip()
            
            new_scene = self.current_scene.get_next_scene()
            if new_scene:
                logger.info(f"Switching to new scene: {type(new_scene).__name__}")
                self.current_scene = new_scene
            
            await asyncio.sleep(0)
        
        logger.info("Shutting down client")
        await self.network_manager.disconnect()
        pygame.quit()

async def main():
    logger.info("Starting Co-op Survival RTS Client")
    try:
        client = GameClient()
        await client.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        logger.info("Client shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())