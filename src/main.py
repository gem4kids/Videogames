import asyncio

async def main():
    # Importar dentro de la corrutina para que ocurra después de que
    # pygbag haya inicializado el entorno WASM completamente
    from pong import main as _pong_main
    await _pong_main()

asyncio.run(main())
