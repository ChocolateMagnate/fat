import json
import random
import string
import secrets
import asyncio
import logging as log

from typing import Self
from pathlib import Path
from httpx import AsyncClient, Response, Timeout

timeout = Timeout(10.0)
host = "http://127.0.0.1:5000"


def generate_2_random_strings() -> tuple[str, str]:
    alpha = string.ascii_letters
    key1 = key2 = []
    for i in range(100):
        key1 += secrets.choice(alpha)
        key2 += secrets.choice(alpha)
    return "".join(key1), "".join(key2)


class UserActivityBot:
    def __init__(self, path: Path):
        self.users = []
        self.posts = []
        try:
            with open(path) as file:
                contents = file.read()
                self.configurations = json.loads(contents)
        except FileNotFoundError:
            self.status = "file-not-found"
        except IsADirectoryError:
            self.status = "is-a-directory"
        except PermissionError:
            self.status = "permission-error"
        except OSError as e:
            self.status = "os-error: " + str(e)
        else:
            self.status = "open"

    def status(self):
        return self.status

    async def run(self) -> Self:
        if self.status != "open":
            log.error("Error: config file could not be read: " + self.status)
            return self

        async with AsyncClient() as client:
            await self.create_users(client)
            await self.create_posts(client)
            await self.like_posts(client)
        log.info("Bot script exited with status 0")
        return self

    async def gather_tasks(self, client: AsyncClient, task, size: int, message: str) -> None:
        tasks = [task(client) for _ in range(size)]
        responses = await asyncio.gather(*tasks)
        self.process_responses(responses)
        log.info(message)

    async def create_users(self, client: AsyncClient) -> None:
        user_count = self.configurations["number_of_users"]
        await self.gather_tasks(client, self.create_user, user_count, "Created users: " + str(user_count))

    def process_responses(self, responses: list[Response]) -> None:
        for response in responses:
            if response.status_code != 200:
                log.error(f"An error occurred while making a request: {response.text}")

    async def create_user(self, client: AsyncClient) -> Response:
        username, password = generate_2_random_strings()
        self.users.append((username, password))
        form = {
            "username": username,
            "password": password
        }
        response = await client.post(host + "/register", data=form, timeout=timeout)
        return response

    async def create_posts(self, client: AsyncClient) -> None:
        users = self.configurations["number_of_users"]
        max_posts = self.configurations["max_posts_per_user"]
        posts = random.randint(1, users * max_posts)
        await self.gather_tasks(client, self.create_single_post, posts, "Created posts: " + str(posts))

    async def create_single_post(self, client: AsyncClient) -> Response:
        title, content = generate_2_random_strings()
        form = {
            "title": title,
            "content": content
        }
        response = await client.post(host + "/create-post", data=form, timeout=timeout)
        self.posts.append(response.text)
        return response

    async def like_posts(self, client: AsyncClient) -> None:
        max_likes = self.configurations["max_likes_per_user"]
        users = self.configurations["number_of_users"]
        likes = random.randint(1, users * max_likes)
        await self.gather_tasks(client, self.like_post, likes, "Liked the posts: " + str(likes))

    async def like_post(self, client: AsyncClient) -> Response:
        postId = secrets.choice(self.posts)
        form = {
            "post-id": postId
        }
        response = await client.post(host + "/upvote-post", data=form, timeout=timeout)
        return response


async def main():
    config = Path("client/config.json")
    bot = await UserActivityBot(config).run()


if __name__ == "__main__":
    asyncio.run(main())
