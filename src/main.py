import asyncio
import pygame

async def main():
    pygame.display.init()
    screen = pygame.display.set_mode((400, 300))
    clock = pygame.time.Clock()
    while True:
        screen.fill((0, 100, 0))
        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(60)

asyncio.run(main())
