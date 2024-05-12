## LeMUR + RealTime Assistant

### Loom Video

[Loom Video Link](https://www.loom.com/embed/8d57564f628d482e91191c2cfaf72437?sid=57d13da5-bc7d-4d6e-8456-ab3bada53278")

### TL;DR

This implementation demonstrates how AssemblyAI's asynchronous transcription API can be used along with LeMUR to provide a near real time 'agent assistant' experience.

##### The core logic is inside of `main.py` and `app.py`

- `main.py` holds the logic for chunking a live stream & sending files off for transcription
- `app.py` is a webhook server which handles the LeMUR completions & LLM logic.

#### There are several steps you need to run this app.

1. Start docker container (be sure pull the pluot/nginx-rtmp container from docker hub first if you don't have it)

```bash
docker run \
 --rm -it \
 -p 1935:1935 \
 -p 9090:80 \
 --name nginx-rtmp \
 pluot/nginx-rtmp
```

2. Start ngrok to make sure that all ports you'll use are available
`ngrok start --all` is what you can use for this.

Note that, if you want to use ngrok like this, you'll need to make sure that your ./ngrok.yml file has port 5000, 5001, and 1935 configured correctly. I.e. you should find your ngrok.yml file on your machine and make it look something like this:
```
tunnels:
  rtmp:
    proto: tcp
    addr: 1935
  hls:
    proto: http
    addr: 9090
  webhook:
    proto: http
    addr: 5000
  segmentation:
    proto: http
    addr: 5001
```

Port 5000 and 5001 should be there by default, but you may need to add rtmp. From here, you need to add the correct ngrok URLs in several areas of your application:

- the ngrok URL associated with localhost 5001 (or main.py) needs to be inputted in /api/begin_processing.js and /api/get_stream_id.js
- everything after tcp:// (i.e. the URL pointing to localhost 1935) should be inputted in Video.js
- the ngrok URL associated with localhost 5000 (or app.py) should be placed within app.py at the top of the file & it should also be the url that our EventSource object listens to in Assistant.js on the client side

[OPTIONAL]
- open OBS or VLC to see the live stream. 
- for example, if using VLC, use CMD + N then enter the live stream url there i.e. rtmp://ngrok_tcp_address:PORT/live/lemur-assistant-room

3. `cd` into the frontend repo, install deps the next app with `npm run dev` or `yarn dev.` At this step you'll also need to go into Assistant.js and Video.js and ensure that the rtmp stream url and webhook server url are correct. The webhook server should correspond to port 5000, and the rtmp server will correspond to the tcp url you see in ngrok. 

The rtmp server is a bit more complicated to identify, but it is required for the Video.js component. 

If your tcp url exposed via ngrok is: tcp://8.tcp.ngrok.io:18834, then the rtmp url you should use is rtmp://8.tcp.ngrok.io:18834/live/foo. See an example of a url in that component (just note that the one there now won't work out of the gate)
 
4. Join the live stream and click 'Activate LeMUR Agent'

5. `cd` into the backend app, and install python deps via `pip install requirements.txt`

6. Make sure that you add your AssemblyAI key and webhook server url where needed in main.py and app.py

7. `cd` into `backend` and run app.py, then main.py (app.py will set the webhook url which is used by main.py). Note that if you want to modify the prompt or core LeMUR logic, app.py is the place to do it.

8. On your frontend, make sure you've joined the live stream, and click 'Activate LeMUR Agent' at the bottom right hand of the screen to begin processing.

If everything worked correctly, you should see lemur write notes and provide coaching as you talk into your live stream feed!

Here's what's happening under the hood:
- A live stream is created when you click 'activate lemur agent.' We are using the Daily.co sdk for video streaming, but any rtmp stream should work here
- Our server running main.py uses ffmpeg to slice the stream into 20 second chunks and sends each chunk off to assemblyai for processing, along with a webhook url which is associated with the current session
- Our webhook server receives the results of the transcription from assembly, then takes those results, stores the ids in Redis, and then uses the ids, the historical lemur results, and a custom prompt to generate a new assistant response
- Using SSE, we stream that response to the client.