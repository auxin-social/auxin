from pydub import AudioSegment

files_path = ''
file_name = 'Courage_episode_3'

startMin = 9
startSec = 50

endMin = 10
endSec = 30

def splice(file_name, file_path, startMin, startSec, endMin, endSec):

  # Time to miliseconds
  startTime = startMin*60*1000+startSec*1000
  endTime = endMin*60*1000+endSec*1000
  try:
    # Opening file and extracting segment
    song = AudioSegment.from_mp3( files_path+file_name+'.mp3' )
    extract = song[startTime:endTime]

    # Saving
    extract.export( file_name+'-extract.mp3', format="mp3")

    return str(200) #200 for success
  except:
    print("error")
    return str(400) # 400 for generic errors
