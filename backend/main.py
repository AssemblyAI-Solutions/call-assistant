import os
import requests
import subprocess
import time
import redis
from glob import glob
import ngrok
from flask import Flask, request
from threading import Thread
from pydub import AudioSegment
from datetime import datetime

r = redis.Redis(host='localhost', port=6379, db=0)

webhook_url = r.get('ngrok_url').decode() + '/'
assembly_key = "AAI KEY HERE"

# create Flask app
app = Flask(__name__)

def has_audio(filename):
    audio = AudioSegment.from_file(filename)
    return len(audio) > 0


# Function to upload a file to AssemblyAI for transcription
def upload_to_assemblyai(filename):
    headers = {'authorization': assembly_key}
    response = requests.post(
        'https://api.assemblyai.com/v2/upload',
        headers=headers,
        data=open(filename, 'rb')
    )
    return response.json()['upload_url']

# Function to transcribe an uploaded file with AssemblyAI
def transcribe_with_assemblyai(upload_url, stream_id):
    headers = {'authorization': assembly_key}
    response = requests.post(
        'https://api.assemblyai.com/v2/transcript',
        json={'audio_url': upload_url, 'speech_threshold': 0.2, 'webhook_url': f'{webhook_url}/?streamid={stream_id}'}, 
        headers=headers
    )
    return response.json()['id']


def upload_and_transcribe(filename, stream_id):
    upload_url = upload_to_assemblyai(filename)
    transcript_id = transcribe_with_assemblyai(upload_url, stream_id)
    return transcript_id


def process_video(data):
    rtmp_url = data.get('url', '')  # extract the URL from the data
    session_id = data.get('session_id', '')
    print('rtmp_url: ' + rtmp_url)
    print("waiting for stream to sync")
    # Start consuming the RTMP livestream and segmenting it into 1-minute chunks
    time.sleep(3)
    start_time = int(time.time())  # Get the current time in seconds since the Epoch
    r.hset('sessions', session_id, start_time) #store the session in redis. this will associate the front end session with the stream id (start time)
    counter = 0
    while True:
        # Define the output filename based on the counter
        filename = f'stream_{start_time}_{counter:04d}.mp3'

        # Start consuming the RTMP livestream and segmenting it into 5s chunks
        command = ['ffmpeg', '-i', rtmp_url, '-f', 'mp3', '-t', '5', filename]

        # Run the ffmpeg command and wait for it to complete
        ffmpeg_process = subprocess.run(command)

        print(f'Processing {filename}...')
        transcript_id = upload_and_transcribe(filename, start_time) #use start time as stream id
        print(f'Transcription started with id {transcript_id}...')

        # Increment the counter for the next loop
        counter += 1

@app.route('/', methods=['POST'])
def app_handler():
    data = request.get_json()
    thread = Thread(target=process_video, args=(data,))
    thread.start()
    return {"status": "processing started"}

@app.route('/stream_id', methods=['GET'])
def get_stream_id():
    session_id = request.args.get('session_id')  # get the session_id from the query parameters
    stream_id = r.hget('sessions', session_id)  # retrieve the stream_id from Redis
    if stream_id is None:
        return {'error': 'No stream associated with this session'}, 404
    return {'stream_id': stream_id.decode()}, 200

if __name__ == "__main__":

    # start the Flask app
    app.run(port=5001)