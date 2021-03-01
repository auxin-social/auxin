def video_allowed_file(name):
    valid_extensions = [
        '.mp4', '.mov', 
        '.jpg', 'jpeg',
    ]
    return any([name.endswith(e) for e in valid_extensions])
