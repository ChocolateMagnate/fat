import os
import asyncio
import datetime
from logging import log

import bson
import mongoengine as mongo
from flask import Flask, Response, request

from .services import authentication as auth
from .services import posting


server = Flask(__name__)
host = "http://127.0.0.1:5000"


def these_are_empty_strings(*args) -> bool:
    for string in args:
        if string is None:
            return True
        if not string.strip():
            return True
    return False


@server.route("/register", methods=["POST"])
async def register() -> Response:
    """Registers a new user in the database using JWT authentication. The appropriate
        access and refresh tokens are then attached to the client's cookies."""
    username = request.form.get("username")
    password = request.form.get("password")
    if these_are_empty_strings(username, password):
        return Response("Incorrect username or password", 400)
    response = await auth.signup(username, password)
    return response


@server.route("/login", methods=["POST"])
async def login() -> Response:
    """Authenticates user when refresh token is expired. For all other tasks, when access token
        expires, as long as refresh token is valid, user will be automatically authenticated."""
    username = request.form.get("username")
    password = request.form.get("password")
    if these_are_empty_strings(username, password):
        return Response("Incorrect username or password", 400)
    response = await auth.login(username, password)
    return response


@server.route("/logout", methods=["POST"])
async def logout() -> Response:
    """Logs user out by invalidating their refresh token and clearing the access token cookies."""
    refreshToken = request.cookies.get("refresh")
    if not refreshToken:
        return Response("Invalid refresh token, the user is already logged out.")

    return await auth.logout(refreshToken)


@server.route("/create-post", methods=["POST"])
async def create_post() -> Response:
    title = request.form.get("title")
    content = request.form.get("content")
    access = request.cookies.get("access")
    refresh = request.cookies.get("refresh")
    if these_are_empty_strings(title, content, access, refresh):
        return Response("Some of the post metadata are not valid.", 400)

    response = await posting.make_post(title, content, access, refresh)
    return response


@server.route("/upvote-post", methods=["POST"])
async def upvote_post() -> Response:
    post_id_string = request.form.get("post-id").strip()
    access = request.cookies.get("access")
    refresh = request.cookies.get("refresh")
    if these_are_empty_strings(post_id_string):
        return Response("User or post cannot be empty.", 404)
    if not auth.user_tokens_are_valid(access, refresh):
        return Response("Post cannot be upvoted because user is logged out", 401)

    payload = await auth.extract_user_details_from(access, refresh)
    if not payload:
        return Response("Invalid JWT tokens, user is logged out.", 400)
    postId = bson.ObjectId(post_id_string)
    userId = bson.ObjectId(payload["sub"])
    return await posting.upvote(postId, userId)


@server.route("/downvote-post", methods=["POST"])
async def downvote_post() -> Response:
    post_id_string = request.form.get("post-id")
    user_id_string = request.form.get("user-id")
    if these_are_empty_strings(post_id_string, user_id_string):
        return Response("User or post cannot be empty.", 404)

    postId = mongo.ObjectIdField(post_id_string)
    userId = mongo.ObjectIdField(user_id_string)
    return await posting.upvote(postId, userId)


@server.route("/aggregate", methods=["GET"])
async def aggregate() -> Response:
    start_param = request.args.get("from")
    end_param = request.args.get("to")
    date_format = "%Y-%m-%d"
    start = datetime.datetime.strptime(start_param, date_format)
    end = datetime.datetime.strptime(end_param, date_format).replace(hour=23, minute=59, second=59)
    if start > end:
        return Response("Request is ill-formed: start date " + str(start) +
                        " is after the end date " + str(end), 400)
    return await posting.aggregate_posts(start, end)


@server.route("/report-activity", methods=["GET"])
async def report_activity() -> Response:
    access = request.cookies.get("access")
    refresh = request.cookies.get("refresh")
    if not auth.user_tokens_are_valid(access, refresh):
        return Response("User is not logged in, permission denied.", 401)

    user_details = await auth.extract_user_details_from(access, refresh)
    userId = user_details["sub"]
    return await auth.report_user_activity(userId)


async def create_app() -> Flask:
    return server


def main():
    log(0, "================== SERVER START ==================")
    log(0, "Started at " + str(datetime.datetime.now()))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_app())
    username = os.environ['DB_USERNAME']
    password = os.environ['DB_PASSWORD']
    database = f"mongodb://{username}:{password}@mongo:27017/fat-database?authSource=admin"
    mongo.connect(host=database)
    server.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
