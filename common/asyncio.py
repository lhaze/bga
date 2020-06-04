import asyncio


def run(coroutine):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coroutine)


async def gather_async_generator(generator):
    result = []
    async for item in generator:
        result.append(item)
    return result
