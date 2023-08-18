import os
import jwt
import bcrypt
import datetime

from flask import Response, jsonify
from mongoengine import ObjectIdField


from ..models.User import User

encoding = "utf-8"
algorithm = "HS256"
audience = "flask-authentication-task-server"
jwt_sing_key: str = os.environ["JWT_SIGN_KEY"]
expired_refresh_tokens = set()


def respond_with_jwt_tokens(access: str, refresh: str) -> Response:
    response = Response()
    now = datetime.datetime.utcnow()
    response.set_cookie("access", access, expires=now + datetime.timedelta(minutes=5))
    response.set_cookie("refresh", refresh, expires=now + datetime.timedelta(weeks=4))
    return response


def generate_access_and_refresh_tokens(subject: ObjectIdField) -> Response:
    """The common routine used to regenerate a new pair of access and refresh tokens after each time
        the access token si refreshed.
        :param subject ID of the user in the MongoDB database who the tokens belong to.
        :returns A new pair of access and refresh tokens, while the previous one is discarded."""

    timestamp = datetime.datetime.utcnow()
    issuer = "flask-authentication-server"
    access = {
        "sub": str(subject),
        "aud": audience,
        "iss": issuer,
        "exp": timestamp + datetime.timedelta(minutes=5)
    }

    refresh = {
        "sub": str(subject),
        "aud": audience,
        "iss": issuer,
        "exp": timestamp + datetime.timedelta(weeks=4)
    }

    accessToken = jwt.encode(access, jwt_sing_key)
    refreshToken = jwt.encode(refresh, jwt_sing_key)
    return respond_with_jwt_tokens(accessToken, refreshToken)


async def extract_user_details_from(access: str, refresh: str) -> dict[str, object]:
    try:
        return jwt.decode(access, jwt_sing_key, audience=audience, algorithms=algorithm)
    except jwt.ExpiredSignatureError:
        return jwt.decode(refresh, jwt_sing_key, audience=audience, algorithms=algorithm)
    except jwt.DecodeError:
        return {}


async def signup(username: str, password: str) -> Response:
    user = User()
    user.username = username
    user.password = bcrypt.hashpw(password.encode(encoding), bcrypt.gensalt())
    user.save()

    return generate_access_and_refresh_tokens(user.id)


async def login(username: str, password: str) -> Response:
    claimed_user = User.objects(username=username).first()
    if not claimed_user:
        return Response("User does not exist: " + username, 404)
    if not bcrypt.checkpw(password.encode(encoding), claimed_user.password):
        return Response("Password does not match: " + password, 400)

    now = datetime.datetime.utcnow()
    claimed_user.last_login = now
    claimed_user.last_service_request = now

    return generate_access_and_refresh_tokens(claimed_user.id)


async def logout(refresh: str) -> Response:
    try:
        user_details = jwt.decode(refresh, jwt_sing_key)
        userId = user_details.id
        user = User.objects(id=userId).first()
        if not user:
            return Response("User doesn't exist: " + userId, 404)
        user.last_service_request = datetime.datetime.utcnow()
    except jwt.DecodeError:
        return Response("Incorrect refresh token.", 401)

    expired_refresh_tokens.add(refresh)
    return respond_with_jwt_tokens("", "")


async def user_id_is_valid(subject: ObjectIdField) -> bool:
    user = User.objects(id=subject).first()
    if user:
        return True
    return False


async def update_last_service_used(userId: ObjectIdField) -> None:
    user = User.objects(id=userId).first()
    if not user:
        raise RuntimeError("User does not exist: " + str(id))
    user.last_service_request = datetime.datetime.utcnow()
    user.save()


async def fetch_user_activity(userId: ObjectIdField) -> Response:
    user = User.objects(id=userId).first()
    if not user:
        return Response("User does not exist: " + str(userId), 404)
    response = {
        "message": "Request completed",
        "last-login": user.last_login,
        "last-service-request": user.last_service_request
    }
    return jsonify(response)


async def handle_access_token_timeout(refresh: str, now: datetime.datetime) -> Response:
    """Is invoked every time when access token expires. The refresh token then is used to make
        sure the user is logged in, and if they are, a new pair of access and refresh tokens is
        generated. Otherwise, the Unauthorised HTTP error is returned to the client.
        :param refresh The refresh token string.
        :param now Timestamp for the current time.
        :raise ExpiredRefreshTokenError, UserSessionExpiredError, jwt.DecodeError
        :return A pair of new access and refresh tokens."""
    if refresh in expired_refresh_tokens:
        return Response("The refresh token is expired.", 401)
    try:
        refresh_token = jwt.decode(refresh, jwt_sing_key)
        if refresh_token["exp"] > now:
            return Response("The refresh token is expired.", 401)
    except jwt.DecodeError:
        return Response("Refresh token has expired, please log in again.", 401)

    return generate_access_and_refresh_tokens(refresh_token.id)


async def user_tokens_are_valid(access: str, refresh: str) -> bool:
    # Decode method will raise jwt.DecodeError if the token is invalid and the
    # secret key doesn't match the signature, and the exception will propagate
    # to the controller where it will be caught and the error will be sent.
    try:
        claims = jwt.decode(access, jwt_sing_key)
    except jwt.ExpiredSignatureError:
        claims = jwt.decode(refresh, jwt_sing_key)
    except jwt.DecodeError:
        return False

    now = datetime.datetime.utcnow()
    if claims["exp"] < now:
        return True

    response = await handle_access_token_timeout(refresh, now)
    if response.status_code != 200:
        return False
    return True


async def report_user_activity(userId: ObjectIdField) -> Response:
    user = User.objects(id=userId).first()
    if not user:
        return Response("User does not exist", 404)
    message = f"Last login: {user.last_login}, last time user used service: {user.last_service_request}"
    return Response(message)
