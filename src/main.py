import asyncio
from pong import main as _pong_main

# Definir main() localmente para compatibilidad con pygbag
# (pygbag necesita ver async def main() en este archivo)
async def main():
    await _pong_main()

asyncio.run(main())
