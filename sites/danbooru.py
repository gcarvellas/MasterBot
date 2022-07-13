import json
import sys
import aiohttp as aiohttp
import requests
import asyncio

from aiohttp import ClientSession


class Danbooru:

    def __init__(self):
        self.downloaded_images = []  # TODO replace this with photo cache once it's implemented
        self._api_key = "API_KEY_HERE" #TODO grab api_key and username from yaml file
        self._username = "USERNAME_HERE"
        self._DANBOORU_URL = f"http://{self._username}:{self._api_key}@danbooru.donmai.us"
        self._RATE_LIMIT = 1

    async def _gather_with_concurrency(self, n, *tasks):
        """
        https://stackoverflow.com/questions/48483348/how-to-limit-concurrency-with-python-asyncio/61478547#61478547
        """
        semaphore = asyncio.Semaphore(n)

        async def sem_task(task):
            async with semaphore:
                return await task
        return await asyncio.gather(*(sem_task(task) for task in tasks))

    async def download_random_images(self, size):
        connector = aiohttp.TCPConnector(limit=size)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for _ in range(size):
                task = asyncio.create_task(self.download_random_image(session=session))
                tasks.append(task)
            await self._gather_with_concurrency(self._RATE_LIMIT, *tasks)

    async def download_random_image(self, session: ClientSession):

        #HTTP Get Request
        response = await session.get(f"{self._DANBOORU_URL}/posts/random.json")

        if response.status < 200 or response.status > 399:
            raise Exception(f"Error in getting danbooru post: {requests.codes[response.status]}")
        response = json.loads(await response.text())

        # Check if image is in another site
        if "id" not in response and "source" in response:  # TODO add support to site redirects (twitter, pawoo, etc.)
            print(f"Redirect link detected! Retrying random image search: {response['source']}",
                  file=sys.stderr)  # TODO How do you print console errors in python???
            return await self.download_random_image(session=session)

        # Checks if there's no image in danbooru post
        elif "id" not in response and "source" not in response:
            print(f"No image found! Retrying random image search: {response['source']}", file=sys.stderr)  # TODO How do you print console errors in python???
            return await self.download_random_image(session=session)

        # Check if image has already been downloaded
        if response["id"] in self.downloaded_images:
            return await self.download_random_image(session=session)
        else:
            self.downloaded_images.append(response["id"])

        # Check if danbooru post has image
        url = ""
        if "large_file_url" in response:
            url = response["large_file_url"]
        elif "file_url" in response:
            url = response["file_url"]
        else:
            return await self.download_random_image(session=session)

        img_response = await session.get(url)
        if img_response.status < 200 or img_response.status > 399:
            raise Exception(f"Error in downloading image from danbooru: {requests.codes[img_response.status]}")

        with open(f"temp/danbooru{response['id']}.jpg", "wb") as image_file:  # TODO redirect photos to photo cache when implemented
            image_file.write(await img_response.read())
        return True

