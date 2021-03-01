import os
import moviepy.editor as mpy

"""
Takes an audio file and convert to an video file with a static image. 
"""
def audio_to_video_with_static_image(image_path, image_name, audio_path, audio_name, 
                                     video_path, video_name):

    audio = mpy.AudioFileClip(os.path.join(audio_path, f'{audio_name}.mp3'))
    clip = mpy.ImageClip(os.path.join(image_path, f'{image_name}.jpg'))
    clip = clip.set_duration(audio.duration)
    clip = clip.set_audio(audio)
    
    video_path = os.path.join(video_path, f'{video_name}.mp4')
    # has to have audio_codec='aac', otherwise no sound
    # see https://stackoverflow.com/questions/40445885/no-audio-when-adding-mp3-to-videofileclip-moviepy
    clip.write_videofile(video_path, audio_codec='aac', fps=24)
    return video_path
