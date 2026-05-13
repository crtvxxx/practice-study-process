import asyncio
import asyncpg as pg

async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info('peername')
    print(f'Подключен {addr}')

    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break
           
            message = data.decode().strip()
            print(f'Получено: {message!r} от {addr}')

            response = f"Эхо: {message}\n".encode()
            writer.write(response)
            await writer.drain()
    except ConnectionResetError:
        print(f'Клиент {addr} разорвал соединение')
    finally:
        writer.close()
        await writer.wait_closed()
        print(f'Соединение с {addr} закрыто')

async def main():
    server = await asyncio.start_server(
        handle_client,
        host='0.0.0.0',
        port=28735,
        start_serving=True,  
        backlog=100          
    )
    print(f'Сервер запущен на {server.sockets[0].getsockname()}')

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())