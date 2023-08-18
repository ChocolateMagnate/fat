import mongoengine as mongo


class User(mongo.Document):
    """Represents a single user in the social network demo."""
    username = mongo.StringField(required=True)
    password = mongo.BinaryField(required=True)
    last_login = mongo.DateTimeField()
    last_service_request = mongo.DateTimeField()
    likes = mongo.IntField(default=0, required=True)
    posts = mongo.IntField(default=0, required=True)

