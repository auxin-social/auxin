import requests, json, os
import keys
from werkzeug.utils import secure_filename

def uploadImageToLinkedIn(app, owner_urn, data, access_token):
    # Find out how to upload media content
    upload_context = {
        "registerUploadRequest": {
            "owner": owner_urn,
            "recipes": [
                keys.LINKEDIN_IMAGE_RECIPE
            ],
            "supportedUploadMechanism": [
                "SYNCHRONOUS_UPLOAD"
            ]
        }
    }

    # Prepare for upload Image vs Video
    upload_context_response = app.make_request("POST", "https://api.linkedin.com/v2/assets?action=registerUpload", data=json.dumps(upload_context))
    upload_context_response = upload_context_response.json()

    upload_url = upload_context_response["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    asset_urn = upload_context_response["value"]["asset"]

    upload_response = requests.put(upload_url, data=data, headers={
        "Authorization": f"Bearer {access_token}"
    })

    return upload_response, asset_urn

def uploadVideoToLinkedIn(app, owner, data):
    upload_context = {
        "registerUploadRequest": {
            "owner": owner,
            "recipes": [
                keys.LINKEDIN_VIDEO_RECIPE
            ],
            "serviceRelationships": [
                {
                    "identifier": "urn:li:userGeneratedContent",
                    "relationshipType": "OWNER"
                }
            ]
        }
    }

    upload_context_response = app.make_request("POST", "https://api.linkedin.com/v2/assets?action=registerUpload", data=json.dumps(upload_context))
    upload_context_response = upload_context_response.json()

    upload_url = upload_context_response["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    asset_urn = upload_context_response["value"]["asset"]
    header = upload_context_response["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["headers"]
    print(f"{upload_url} {asset_urn} {header}")

    upload_response = requests.put(upload_url, data=data, headers=header)
    print(upload_response)

    return upload_response, asset_urn

def linkedInMediaFilterLogic(file, allowed_media_extension):
    filename = secure_filename(file.filename)
    if filename == "":
        return False
    _, extension = os.path.splitext(filename)
    if extension not in allowed_media_extension:
        return False
    return True
