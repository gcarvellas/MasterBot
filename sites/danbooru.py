import json
import sys

import aiohttp as aiohttp
import requests
import threading
import asyncio

from aiohttp import ClientSession


class Danbooru:

    def __init__(self):
        self.downloaded_images = []  # TODO replace this with photo cache once it's implemented
        self._DANBOORU_URL = "http://www.danbooru.donmai.us"

    async def download_random_images(self, size):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for _ in range(size):
                task = asyncio.create_task(self.download_random_image(session=session))
                tasks.append(task)
            await asyncio.gather(*tasks)

    async def download_random_image(self, session : ClientSession = None):

        #Use the same session if set as an optional arg
        get = None
        if session is None:
            get = requests.get
        else:
            get = session.get

        #HTTP Get Request
        response = await get(f"{self._DANBOORU_URL}/posts/random.json")
        if response.status < 200 or response.status > 399:
            raise Exception(f"Error in getting danbooru post: {requests.codes[response.status]}")
        response = json.loads(await response.text())

        # Check if image is in another site
        if "id" not in response and "source" in response:  # TODO add support to site redirects (twitter, pawoo, etc.)
            print(f"Redirect link detected! Retrying random image search: {response['source']}",
                  file=sys.stderr)  # TODO How do you print console errors in python???
            return await self.download_random_image()

        # Checks if there's no image in danbooru post
        elif "id" not in response and "source" not in response:
            print(f"No image found! Retrying random image search: {response['source']}", file=sys.stderr)  # TODO How do you print console errors in python???
            return await self.download_random_image()

        # Check if image has already been downloaded
        if response["id"] in self.downloaded_images:
            return await self.download_random_image()
        else:
            self.downloaded_images.append(response["id"])

        # Check if danbooru post has image
        url = ""
        if "large_file_url" in response:
            url = response["large_file_url"]
        elif "file_url" in response:
            url = response["file_url"]
        else:
            return await self.download_random_image()

        img_response = await get(url)
        if img_response.status < 200 or img_response.status > 399:
            raise Exception(f"Error in downloading image from danbooru: {requests.codes[img_response.status]}")

        with open(f"temp/danbooru{response['id']}.jpg", "wb") as image_file:  # TODO redirect photos to photo cache when implemented
            image_file.write(await img_response.read())
        return True

