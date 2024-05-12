import ngrok
import redis
from flask import Flask, request, stream_with_context, Response
import logging
import requests
from flask_cors import CORS, cross_origin
import time
import json
from datetime import datetime

r = redis.Redis(host='localhost', port=6379, db=0)

ngrok_tunnel = "PORT 5000 NGROK URL HERE"  #note to update this every time you restart server... this is port 5000
r.set('ngrok_url', ngrok_tunnel)

assembly_key = "AAI KEY HERE"

def get_transcript(id):
    headers = {'authorization': assembly_key}
    response = requests.get(
        'https://api.assemblyai.com/v2/transcript/' + id,
        json={},
        headers=headers
    )
    return response.json()

first_transcript_flag = True

# create Flask app
app = Flask(__name__)

lemur_feedback_format = "<HEADLINE> \n\n <ul><NOTE><NOTE><NOTE></ul>"

def lemur_call(previous_responses, transcript_ids):
    print("CALLING...")
    formatted_previous_responses = "\n\n".join(previous_responses)
    lemur_prompt = f"""
    You are a helpful assistant that is aiding me in taking notes on this live stream. Please create formatted notes based on what has happened so far.

    Here is the is the feedback you have given me so far:

    {formatted_previous_responses}

    I need quick, actionable notes that can fit in 3 sentences.
    """
    headers = {'authorization': assembly_key}
    response = requests.post(
        'https://api.assemblyai.com/lemur/v3/generate/task',
        json={'prompt': lemur_prompt, 'context': lemur_feedback_format, 'transcript_ids': transcript_ids},
        headers=headers
    )
    return response.json()

lemur_notes_format = "Bullet points"
def lemur_notes(previous_notes, transcript_ids):
    print("CALLING")
    formatted_previous_notes = "\n\n".join(previous_notes)
    lemur_prompt = f"""
    You are a helpful assistant that is aiding me in taking notes on this live stream. Imagine that I am hosting a live workshop about AssemblyAI's new products.

    Imagine that you are taking notes on behalf of the speaker, and trying to help the speaker to understand what they've discussed so far in the presentation. Think of this as an outline of what has already been spoken. Don't be afraid to include other context that was not explicitly spoken in conversation so far!

    I will review these notes as I present, and use them for encouragement and guidance.

    Here are the notes you have taken so far:

    {formatted_previous_notes}
    
    Your job is to add to these notes so that they are accurate, relevant, and up to date without being too verbose or hard to read.

    New Notes:
    """
    headers = {'authorization': assembly_key}
    response = requests.post(
        'https://api.assemblyai.com/v2/generate/summary',
        json={'context': lemur_prompt, 'answer_format': lemur_notes_format, 'transcript_ids': transcript_ids, 'final_model': 'basic'},
        headers=headers
    )
    return response.json()

ids = []
@app.route('/', methods=['POST'])
def webhook_handler():
    try:
        stream_id = request.args.get('streamid')
        print('Stream ID: ' + stream_id)
        job_id = request.json.get('transcript_id')
        job_id_response = requests.get('https://api.assemblyai.com/v2/transcript/' + job_id, headers={'authorization': assembly_key})
        if job_id_response.json()['status'] == 'error':
            #note - need to return 200 here to prevent AssemblyAI from retrying
            return {'message': 'Webhook received, but transcript had an error: perhaps it contained no audio or text'}, 200
        print('job_id: ' + job_id)
        r.rpush(stream_id, job_id) #store the transcript ids in a list named after the stream id

        #get existing transcripts so far
        existing_trancript = r.hget(f'{stream_id}_transcript', 'transcript')
        if existing_trancript == None:
            existing_trancript = ""
        else: 
            existing_trancript = existing_trancript.decode()
        # print("TRANSCRIPT SO FAR:", existing_trancript)
        existing_trancript += f" {get_transcript(job_id)['text']}"
        # print("UPDATED TRANSCRIPT:", existing_trancript)
        r.hset(f'{stream_id}_transcript', 'transcript', existing_trancript)

        # read the results from redis
        assistant_completion_values = r.hvals('lemur_assistant_results')
        assistant_completion_values = [value.decode('utf-8') for value in assistant_completion_values]
        if len(assistant_completion_values) == 0:
            assistant_completion_values.append("")

        # read last 10 ids from redis and convert them into the format we need... note that at any point in time we're only bringing in the last 10 ids
        # if we are sending off 5s chunks for transcription at a time, then this means we have about 1min worth of sliding window we are working with
        ids = r.lrange(stream_id, -10, -1)
        ids = [id.decode('utf-8') for id in ids]
        ids = list(set(ids))

        print("TRANSCRIPT IDS", ids)
        print("ASSISTANT COMPLETIONS SO FAR", assistant_completion_values)
        #call lemur using the previous responses and the most recent 10 ids - note that this number of ids could be expanded dramatically to ~100
        lemur_assistant_response = lemur_call(assistant_completion_values, ids)
        print(lemur_assistant_response)

        assistant_payload = lemur_assistant_response["response"]
        if job_id and assistant_payload:
            r.hset(f'{stream_id}_assistant_results', job_id, assistant_payload)  # store the payload in a hash specific to the stream id

        return {'message': 'Webhook received'}, 200
    except Exception as e:
        print("Error: ", e)
        # Even if there's an error, we send back a '200 OK' status to prevent retries from AssemblyAI.
        return {'message': 'Webhook received, but an internal error occurred.'}, 200

@app.route('/stream')
def stream():
    def event_stream():
        stream_id = request.args.get('streamid')
        print('Stream ID: ' + stream_id)
        while True:
            # Get the last key in the list which represents the most recent results
            last_key = r.lindex(stream_id, -1)
            if last_key:
                # Get the corresponding hash entry and send it as an update
                assistant_update = r.hget(stream_id + '_assistant_results', last_key.decode())

                if assistant_update:
                    yield f"data: {json.dumps({'assistant': {last_key.decode(): assistant_update.decode()}})}\n\n"  # SSE data format

            # Sleep for a short period to prevent CPU overload
            time.sleep(30)
    headers = {
        'Content-Type': 'text/event-stream',
        'Access-Control-Allow-Origin': 'http://localhost:3000',
        'Access-Control-Allow-Credentials': 'true'
    }
    
    response = Response(stream_with_context(event_stream()), headers=headers, mimetype="text/event-stream")
    print(response.headers)
    return response

@app.route('/transcript_stream')
def transcript_stream():
    def event_stream():
        stream_id = request.args.get('streamid')
        print('Stream ID: ' + stream_id)
        while True:
            # Get the last key in the list which represents the most recent results
            transcript = r.hget(f'{stream_id}_transcript', 'transcript')
            print("TRANSCRIPT", transcript)
            if transcript is not None:
                transcript = transcript.decode()
                print(f"data: {json.dumps({'transcript': transcript})}\n\n")
                yield f"data: {json.dumps({'transcript': transcript})}\n\n"  # SSE data format
    headers = {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': 'http://localhost:3000',
        'Access-Control-Allow-Credentials': 'true'
    }
    
    response = Response(stream_with_context(event_stream()), headers=headers, mimetype="text/event-stream")
    print(response.headers)
    return response

if __name__ == "__main__":

    # start the Flask app
    app.run(port=5000)