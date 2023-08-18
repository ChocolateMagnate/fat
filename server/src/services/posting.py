import os
import jwt
import datetime
import bson

from flask import Response
from mongoengine import ObjectIdField
from .authentication import algorithm, jwt_sing_key, audience

from ..models.User import User
from ..models.Post import Post


async def get_user_id_from_jwt(token: str) -> ObjectIdField | None:
    subject = jwt.decode(token, jwt_sing_key, algorithms=algorithm, audience=audience)
    user = User.objects.get(id=subject["sub"])
    if not user:
        raise jwt.DecodeError()
    return user.id


async def make_post(title: str, content: str, access: str, refresh: str) -> Response:
    try:
        author = await get_user_id_from_jwt(access)
    except jwt.ExpiredSignatureError:
        author = await get_user_id_from_jwt(refresh)
    except jwt.DecodeError:
        return Response("JWT is invalid, user is logged out", 401)

    if author is None:
        return Response("User does not exist", 401)

    post = Post()
    post.title = title
    post.content = content
    post.created_at = datetime.datetime.today()
    post.timestamp = datetime.datetime.utcnow()
    post.author = author
    post.likes = []
    post.save()
    return Response(str(post.id))


async def upvote(postId: bson.ObjectId, userId: bson.ObjectId) -> Response:
    post = Post.objects(id=postId).first()
    user = User.objects(id=userId).first()
    if not post:
        return Response("The post does not exist: " + str(postId), 404)
    elif not user:
        return Response("The user does not exist: " + str(userId), 404)
    post.likes.append(user)
    post.save()
    user.last_service_request = datetime.datetime.utcnow()
    user.save()
    return Response()


async def downvote(postId: ObjectIdField, userId: ObjectIdField) -> Response:
    post = Post.objects(id=postId).first()
    user = User.objects(id=userId).first()
    if not post:
        return Response("The post does not exist: " + str(postId), 404)
    elif not user:
        return Response("The user does not exist: " + str(userId), 404)
    post.likes.pop()
    user.last_service_request = datetime.datetime.utcnow()
    user.save()
    return Response()


async def get_post_likes(postId: ObjectIdField) -> Response:
    post = Post.objects(id=postId).first()
    if not post:
        return Response("The post does not exist: " + str(postId), 404)
    response = Response()
    response.likes = post.likes
    return response


async def aggregate_posts(start: datetime.datetime, end: datetime.datetime) -> Response:
    analytics = dict()
    posts = Post.objects(created_at__gte=start, created_at__lte=end).order_by('created_at')
    if not posts:
        return Response("There are no posts in the time interval between " + str(start) + " to " + str(end), 404)

    for post in posts:
        date = post.created_at
        if date in analytics:
            analytics[date] += len(post.likes)
        else:
            analytics[date] = len(post.likes)
    print(analytics)
    return Response(str(analytics))
