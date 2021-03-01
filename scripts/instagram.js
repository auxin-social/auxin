FB.init({
  appId      : '443237566917005',
  cookie     : true,                     // Enable cookies to allow the server to access the session.
  xfbml      : true,                     // Parse social plugins on this webpage.
  version    : 'v9.0'           // Use this Graph API version for this call.
});

function getInstagramLoginStatus(callback) {
  FB.getLoginStatus(callback(response));
}

function connectToInstagram() {
  FB.login(function(response) {
    if (response.authResponse) {
     console.log('Welcome!  Fetching your information.... ');
     FB.api('/me', function(response) {
       console.log('Good to see you, ' + response.name + '.');
     });
    } else {
     console.log('User cancelled login or did not fully authorize.');
    }
  }, {"scope": "instagram_basic,instagram_content_publish"});
}

function postMediaToInstagram(payload) {
  FB.getLoginStatus(function(response) {
    if (response.status === 'connected') {
      user_id = response.authResponse.userID;
      user_access_token = response.authResponse.accessToken;
      postToInstagramCallback(user_id, user_access_token, payload, postMediaToInstagramCallback);
    }
  });
}

function postToInstagramCallback(user_id, user_access_token, payload, postingCallback) {
  FB.api(
    '/' + user_id + '/accounts',
    'GET',
    {
      "fields": "name,access_token,instagram_business_account",
      "access_token": user_access_token
    },
    function(response) {
        console.log(response.data[0]);
        // page_access_token = response.data[0].access_token
        instagram_id = response.data[0].instagram_business_account.id
        // page_id = response.data[0].id
        // page_name = response.data[0].name
        postingCallback(
          payload = payload,
          instagram_id = instagram_id,
          access_token = user_access_token
        );
    }
  );
}

function postMediaToInstagramCallback(payload, instagram_id, access_token) { 
  document.getElementById("instagram_status").innerHTML = "Posting...";

  let extension = payload['file_url'].split('.').pop();
  if (extension === 'mp4' || extension === 'mov') {
    FB.api(
      '/' + instagram_id + '/media',
      'POST',
      {
        "media_type": "VIDEO",
        "video_url": payload['file_url'],
        "caption": payload['description'],
        "access_token": access_token,
      },
      function(response) {
        monitorContainerUploadStatus(response.id, payload, instagram_id, access_token)
      }
    );
  } else if (extension === 'jpg' || extension === 'jpeg') {
    FB.api(
      '/' + instagram_id + '/media',
      'POST',
      {
        "image_url": payload['file_url'],
        "caption": payload['description'],
        "access_token": access_token,
      },
      function(response) {
        monitorContainerUploadStatus(response.id, payload, instagram_id, access_token)
      }
    );
  } else {
    document.getElementById("instagram_status").innerHTML = "Unsupported file format :(";
  }
}

function monitorContainerUploadStatus(container_id, payload, instagram_id, access_token) {
  FB.api(
    '/' + container_id,
    'GET',
    {
      "fields": "status_code"
    },
    function(response) {
      if (response.status_code == 'FINISHED') {
        instagramUploadContainer(container_id, access_token)
      } else if (response.status_code == 'IN_PROGRESS') {
        // preparing, try again in a bit
        setTimeout(function () {
          monitorContainerUploadStatus(container_id, payload, instagram_id, access_token);
        }, 5000);
      } else {
        document.getElementById("instagram_status").innerHTML = "Failed :(";
      }
    }
  );
}

function instagramUploadContainer(container_id, access_token) {
  FB.api(
    '/' + instagram_id + '/media_publish',
    'POST',
    {
      'creation_id': container_id,
      'access_token': access_token
    },
    function(response) {
      console.log(response);
      instagramPostSuccessCallback();
    }
  );
}

function instagramPostSuccessCallback() {
  document.getElementById("instagram_status").innerHTML = "Post successful!";
}