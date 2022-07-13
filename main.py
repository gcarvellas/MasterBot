import asyncio
import time

from sites.danbooru import Danbooru


def main():
    pass  # TODO call sites and init bot

start_time = time.time()
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.new_event_loop().run_until_complete(Danbooru().download_random_images(100))
print(f"Multi Threaded: {time.time() - start_time}")
