import json
import sys
import aiohttp as aiohttp
import requests
import asyncio
from http.client import responses

from aiohttp import ClientSession

#asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
#asyncio.run(Danbooru().download_random_images(50))

class Danbooru:

    def __init__(self):
        self.downloaded_images = []  # TODO replace this with photo cache once it's implemented
        self._DANBOORU_URL = f"http://danbooru.donmai.us"
        self._RATE_LIMIT = 25

    async def download_random_images(self, size):
        limit = asyncio.Semaphore(self._RATE_LIMIT)
        async with aiohttp.ClientSession() as session:
            tasks = []
            for _ in range(size):
                task = asyncio.ensure_future(self.download_random_image(session=session, semaphore=limit))
                tasks.append(task)
            await asyncio.gather(*tasks)

    async def _semaphore_get_request(self, url: str, session: ClientSession, semaphore: asyncio.Semaphore):
        async with semaphore:
            response = await session.get(url)

            if semaphore.locked():
                await asyncio.sleep(1)

            if response.status == 429:
                raise Exception(f"Error in getting danbooru post: {responses[response.status]}. Try lowering the rate limit.")
            else:
                return response

    async def download_random_image(self, session: ClientSession, semaphore: asyncio.Semaphore):

        #HTTP Get Request
        response = await self._semaphore_get_request(f"{self._DANBOORU_URL}/posts/random.json", session, semaphore)

        if response.status < 200 or response.status > 399:
            raise Exception(f"Error in getting danbooru post: {responses[response.status]}")
        response = json.loads(await response.text())

        # Checks if there's no image in danbooru post
        if "id" not in response and "source" not in response:
            print(f"No image found! Retrying random image search: {response['source']}", file=sys.stderr)  # TODO How do you print console errors in python???
            return await self.download_random_image(session=session, semaphore=semaphore)

        # Check if image is in another site
        if "id" not in response and "source" in response:  # TODO add support to site redirects (twitter, pawoo, etc.)
            print(f"Redirect link detected! Retrying random image search: {response['source']}",
                  file=sys.stderr)  # TODO How do you print console errors in python???
            return await self.download_random_image(session=session, semaphore=semaphore)

        # Check if image has already been downloaded
        if response["id"] in self.downloaded_images:
            return await self.download_random_image(session=session, semaphore=semaphore)
        else:
            self.downloaded_images.append(response["id"])

        # Check if danbooru post has image
        url = ""
        if "large_file_url" in response:
            url = response["large_file_url"]
        elif "file_url" in response:
            url = response["file_url"]
        else:
            return await self.download_random_image(session=session, semaphore=semaphore)

        img_response = await self._semaphore_get_request(url, session, semaphore)
        if img_response.status < 200 or img_response.status > 399:
            raise Exception(f"Error in downloading image from danbooru: {requests.codes[img_response.status]}")

        with open(f"temp/danbooru{response['id']}.jpg", "wb") as image_file:  # TODO redirect photos to photo cache when implemented
            image_file.write(await img_response.read())

