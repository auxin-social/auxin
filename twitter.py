import keys
import audio_video_utils as av

from twython import Twython


'''
Take defined file and upload to twitter
'''
def tweet_audio_as_video(twitter_obj, file_path, file_name, message=""):
  try:
    video_path = av.audio_to_video_with_static_image(
      image_path = '',
      image_name = 'cover',
      audio_path = file_path,
      audio_name = file_name,
      video_path = file_path,
      video_name = file_name,
    )
    with open(video_path, 'rb') as video:
      response = twitter_obj.upload_video(media=video, media_type='video/mp4')
      twitter_obj.update_status(status=message, media_ids=[response['media_id']])

    return str(200)
  except Exception as err:
    print(err)
    return str(400)

"""
Get the redirect url to Twitter login page. 
Also gets the oauth token and secret. 
"""
def authenticate():
  twitter = Twython(
    keys.CONSUMER_KEY,
    keys.CONSUMER_SECRET
  )

  auth = twitter.get_authentication_tokens(callback_url='https://young-stream-53529.herokuapp.com/loginToTwitterCallback')
  oauth_token = auth['oauth_token']
  oauth_token_secret = auth['oauth_token_secret']

  return auth['auth_url'], oauth_token, oauth_token_secret

"""
Takes the oauth token and secret from the authenticate step, 
as well as oauth_verifier from callback. 
Returns the final oauth token and secret for the user. 
"""
def login(oauth_token, oauth_token_secret, oauth_verifier):
  twitter = Twython(keys.CONSUMER_KEY,
                    keys.CONSUMER_SECRET,
                    oauth_token,
                    oauth_token_secret)
  final_step = twitter.get_authorized_tokens(oauth_verifier)
  oauth_token = final_step['oauth_token']
  oauth_token_secret = final_step['oauth_token_secret']
  return oauth_token, oauth_token_secret

"""
Gets a twython object with oauth token and secret. 
"""
def get_twitter_obj(oauth_token, oauth_token_secret):
  return Twython(keys.CONSUMER_KEY,
                 keys.CONSUMER_SECRET,
                 oauth_token,
                 oauth_token_secret)
