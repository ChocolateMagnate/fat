import mongoengine as mongo


class Post(mongo.Document):
    """Represents a single post made in the social network demo."""
    title = mongo.StringField(required=True)
    content = mongo.StringField(required=True)
    author = mongo.ObjectIdField(required=True)
    likes = mongo.ListField(default=[])
    created_at = mongo.DateTimeField(required=True)
    timestamp = mongo.DateTimeField()
