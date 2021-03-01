from flask import Flask, request, jsonify, redirect, session, render_template, send_from_directory, flash
from flask_login import LoginManager, login_user, login_required, current_user
from werkzeug.utils import secure_filename

from waitress import serve
from error import InvalidUsage
from splice_audio import splice
from file_utils import video_allowed_file
from linkedin_v2 import linkedin
import linkedin_utils
import keys
import json
import imghdr
import urllib
import time
import random
import requests
import os
import glob
import json

from login import User

import twitter

app = Flask(__name__)
app.secret_key = "CHANGE_ME"
login_manager = LoginManager()
login_manager.init_app(app)
app.config['UPLOAD_FOLDER'] = 'user_assets'


def has_args(iterable, args):
    """Verify that all args are in the iterable."""

    try:
        return all(x in iterable for x in args)

    except TypeError:
        return False

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route("/", methods=["GET"])
@login_required
def main():
    return render_template('current_test.html')

@app.route("/spliceAudio", methods=["GET"])
def runSplice():
    # get params with: request.json['dialSetting']
    if not has_args(request.json, ['file_name', 'file_path', 'startMin', 'startSec', 'endMin', 'endSec']):
      raise InvalidUsage("Mising necessary parameters.")

    return splice(request.json['file_name'],
                  request.json['file_path'],
                  request.json['startMin'],
                  request.json['startSec'],
                  request.json['endMin'],
                  request.json['endSec'])

"""
Prompts the user to Twitter log in.
"""
@app.route("/loginToTwitter", methods=["GET"])
def authenticateTwitter():
    auth_url, oauth_token, oauth_token_secret = twitter.authenticate()
    session['oauth_token_manual_login'] = oauth_token
    session['oauth_token_secret_manual_login'] = oauth_token_secret
    return redirect(auth_url, code=302)

"""
Callback from Twitter log in. 
"""
@app.route("/loginToTwitterCallback", methods=["GET"])
def loginToTwitterCallback():
    if not has_args(session, ['oauth_token_manual_login', 'oauth_token_secret_manual_login']):
        raise InvalidUsage("Log in to Twitter first.")

    oauth_token, oauth_token_secret = twitter.login(session['oauth_token_manual_login'], 
                                                    session['oauth_token_secret_manual_login'], 
                                                    request.args.get('oauth_verifier'))
    session['oauth_token'] = oauth_token
    session['oauth_token_secret'] = oauth_token_secret
    return str(200)

@app.route("/sendToTwitter", methods=["GET"])
def sendToTwitter():
    # get params with: request.json['dialSetting']
    if not has_args(request.args, ['file_name', 'file_path']):
      raise InvalidUsage("Mising necessary parameters.")
    twitter_obj = twitter.get_twitter_obj(session['oauth_token'], session['oauth_token_secret'])
    return twitter.tweet_audio_as_video(twitter_obj, request.args['file_path'], request.args['file_name'])

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect("./", code=302)

    is_login_failed = request.args.get("login_failed") is not None
    
    return render_template(
        'login.html',
        is_login_failed=is_login_failed
    )

@app.route('/authenticate', methods=['POST'])
def authenticate():
    if not has_args(request.form, ['username', 'password']):
      raise InvalidUsage("Bad request. Please use the proper login page.")
    username = request.form['username'].lower()
    # our password is NOT encrypted in transit..
    # we need to implement client slide encryption
    password = request.form['password']
    user = User.login_user(username, password)

    if not user:
        return redirect("./login?login_failed=true", code=302)
    else:
        login_user(user)
        return redirect("./", code=302)

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/login')

@app.route("/uploadContent", methods=["POST"])
def recieveContent():
    if 'file' not in request.files:
        flash('No file part')
        return str(200)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return str(200)
    if file and video_allowed_file(file.filename):
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        message = request.form['message']
        title = "title" #request.form['title']
        filename = secure_filename(file.filename)
        basename = os.path.splitext(filename)[0]
        meta_data_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{basename}.json')
        with open(meta_data_path, 'w') as f:
            f.write(json.dumps({
                "message": message,
                "title": title,
                "file": filename,
            }))
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return str(200)
    else:
        flash('Unsupported file type')
        return str(400)

@app.route("/getContent/<path:filename>", methods=["GET"])
def downloadFile(filename):
    print(filename)
    return send_from_directory("", filename, as_attachment=True)

@app.route("/listUserContent", methods=["GET"])
def listUserContent():
    return jsonify({
        "files": [
            os.path.splitext(os.path.basename(path))[0] for path in
            glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], "*.json"))
        ]
    })


"""
LinkedIn Login
"""
@app.route("/loginToLinkedInAsUser", methods=["GET"])
def linkedAuthenticate():
    return linkedAuthenticateAs(["w_member_social"])

def linkedAuthenticateAs(permissions):
    auth = linkedin.LinkedInAuthentication(keys.LINKEDIN_CLIENT_ID, keys.LINKEDIN_CLIENT_SECRET, keys.LINKEDIN_CALLBACK, permissions=["w_member_social", "r_liteprofile"])
    auth.state = f"{hex(random.getrandbits(128))}"
    session["linkedin-hash"] = auth.state
    return redirect(auth.authorization_url)

@app.route("/linkedin-authen", methods=["GET"])
def loginToLinkedInCallback():
    code = request.args.get("code")
    csrf_state = request.args.get("state")
    error = request.args.get("error")

    if session["linkedin-hash"] != csrf_state:
        raise InvalidUsage("401 Unauthorized")
    if error is not None:
        raise InvalidUsage("Error occured")

    auth = linkedin.LinkedInAuthentication(keys.LINKEDIN_CLIENT_ID, keys.LINKEDIN_CLIENT_SECRET, keys.LINKEDIN_CALLBACK, permissions=["w_member_social", "r_liteprofile"])
    print(keys.LINKEDIN_CALLBACK)
    auth.state = csrf_state
    auth.authorization_code = code
    session["linkedin-access-token"] = auth.get_access_token()

    return redirect("https://auxin-app.herokuapp.com/")
    
@app.route("/post-content-image", methods=["POST"])
def linkedInContentPost():
    if session["linkedin-access-token"] is None:
        return redirect("loginToLinkedInAsUser")

    # Set up linkedin applicatiom
    auth = linkedin.LinkedInAuthentication(keys.LINKEDIN_CLIENT_ID, keys.LINKEDIN_CLIENT_SECRET, keys.LINKEDIN_CALLBACK, permissions=["w_member_social", "r_liteprofile"])
    print(keys.LINKEDIN_CALLBACK)
    auth.token = linkedin.AccessToken(session["linkedin-access-token"][0], session["linkedin-access-token"][1])
    app = linkedin.LinkedInApplication(auth)

    # Get User ID
    response = app.make_request("GET", "https://api.linkedin.com/v2/me", params={"fields" : "id"})
    user_id = response.json()['id']
    owner_urn = f"urn:li:person:{user_id}"

    def filter_logic(file):
        filename = secure_filename(file.filename)
        if filename == "":
            return False
        _, extension = os.path.splitext(filename)
        if extension not in keys.LINKEDIN_ALLOWED_EXTENSION:
            return False
        return True

    upload_response_context = []
    for file in request.files.getlist("file"):
        if linkedin_utils.linkedInMediaFilterLogic(file, keys.LINKEDIN_ALLOWED_IMAGE_EXTENSION):
            data = file.read()
            upload_response_context.append(linkedin_utils.uploadImageToLinkedIn(app, owner_urn=owner_urn, data=data, access_token=auth.token.access_token))

    text = request.form["message"]
    context = {
        "owner": owner_urn,
        "text": {
            "text": text
        },
        "content": {
            "contentEntities" : [
                # Iterate through the media contents here
                {"entity" : f"{asset_urn}"} for (upload_response, asset_urn) in upload_response_context
            ],
            # Add media category here for it to work!
            "shareMediaCategory": "IMAGE"
        },
    }

    response = app.make_request("POST", "https://api.linkedin.com/v2/shares", data=json.dumps(context))

    return str(200)

# @app.route("/post-content-video", methods=["POST"])
def linkedInContentPostVideo():
    if "linkedin-access-token" not in session or session["linkedin-access-token"] is None:
        return redirect("/loginToLinkedInAsUser")

    auth = linkedin.LinkedInAuthentication(keys.LINKEDIN_CLIENT_ID, keys.LINKEDIN_CLIENT_SECRET, keys.LINKEDIN_CALLBACK, permissions=["w_member_social", "r_liteprofile"])
    print(keys.LINKEDIN_CALLBACK)
    auth.token = linkedin.AccessToken(session["linkedin-access-token"][0], session["linkedin-access-token"][1])
    app = linkedin.LinkedInApplication(auth)

    # Get User ID
    response = app.make_request("GET", "https://api.linkedin.com/v2/me", params={"fields" : "id"})
    user_id = response.json()['id']
    owner_urn = f"urn:li:person:{user_id}"


    upload_response_context = []
    for file in request.files.getlist("file"):
        if linkedin_utils.linkedInMediaFilterLogic(file, keys.LINKEDIN_ALLOWED_VIDEO_EXTENSION):
            response, asset_urn = linkedin_utils.uploadVideoToLinkedIn(app, owner=owner_urn, data=file.read())
            # Check if error occured in response
            response.raise_for_status()
            upload_response_context.append((response, asset_urn))

    # Make sure video content is uploaded and ready to serve
    # remaining_request = upload_response_context.copy()
    # remaining_request_next = []
    # while (len(remaining_request) > 0) :
    #     for response, asset_urn in remaining_request:
    #         status_response = app.make_request("GET", f"https://api.linkedin.com/v2/assets/{asset_urn}")
    #         status_response.raise_for_status()
    #         status_response = status_response.json()
    #         upload_status = status_response["recipes"]["status"]
    #         if upload_status == "AVAILABLE":
    #             continue
    #         elif upload_status == "PROCESSING" or upload_status == "NEW" or upload_status == "MUTATING" or upload_status == "WAITING_UPLOAD" or :
    #             remaining_request_next.append((response, asset_urn))
    #         else:
    #             raise InvalidUsage("Upload Error Occured")
    #     remaining_request = remaining_request_next.copy()
    #     remaining_request_next = []
    #     time.sleep(5)

    text = "VIDEO UPLOAD WORK2222!"
    context = {
        "author": owner_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "media": [
                    {
                        "media": assert_urn,
                        "status": "READY",
                        "title": {
                            "attributes": [],
                            "text": "Sample Video Create"
                        }
                    }
                    for upload_response, assert_urn in upload_response_context
                ],
                "shareCommentary": {
                    "attributes": [],
                    "text": text
                },
                "shareMediaCategory": "VIDEO"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    response = app.make_request("POST", "https://api.linkedin.com/v2/ugcPosts", data=json.dumps(context))

    print(f"{response} {response.headers} {response.json()}")

    return "Post-Content-2"


if __name__ == "__main__":
    app.run(port=3000)


# serve(app, host="0.0.0.0", port=3000)
