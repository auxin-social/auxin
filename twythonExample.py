from twython import Twython
import keys

twitter = Twython(
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret
)

message = "qwertyuiop"
twitter.update_status(status=message)
print("Tweeted: %s" % message)
