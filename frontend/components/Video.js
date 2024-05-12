import React, { useEffect, useRef, useContext } from 'react';
import StreamIdContext from '@/contexts/StreamIdContext';
import DailyIframe from '@daily-co/daily-js';

function showEvent(e) {
  console.log('callFrame event', e);
}

//note - this daily.co token and joinCall() are probably best to be moved into server side. 
//this app is for demo purposes only 
const token = "DAILY TOKEN HERE"
const Video = () => {
  const callFrame = useRef(null);
  const containerRef = useRef(null);
  const { setStreamId } = useContext(StreamIdContext);

  const CALL_OPTIONS = {
    showLeaveButton: true,
    isOwner: true,
    room_name: 'lemur-assistant-room',
  }

  const getStreamId = async (id) => {
    const response = await fetch(`/api/get_stream_id?session_id=${id}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    } else if (response.headers.get('content-type').includes('application/json')) {
      return response.json();
    } else {
      throw new Error(`Expected JSON but received ${response.headers.get('content-type')}`);
    }
  }

  const startProcessing = async () => {
    let session_id = Date.now()
    const response = await fetch('/api/begin_processing', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: 'rtmp://NGROK TCP PATH/live/foo', session_id: session_id }), // /live/foo is the correct path, but need to update root 
    });

    if (response.ok) {
      console.log('processing started for session', session_id)
      await new Promise(resolve => setTimeout(resolve, 7000));
      console.log("7 seconds have passed");
      
      const stream_id = await getStreamId(session_id);
      // set the stream id here for context
      setStreamId(stream_id.stream_id);
      console.log(stream_id);
    }
    
    else if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    } else if (response.headers.get('content-type').includes('application/json')) {
      return response.json();
    } else {
      throw new Error(`Expected JSON but received ${response.headers.get('content-type')}`);
    }
  }  

  async function joinCall() {
    callFrame.current = DailyIframe.createFrame(containerRef.current);
      console.log('joining stream now')
      //url should be your daily.co url
      callFrame.current.join({ url: 'https://your-daily-domain-here/lemur-assistant-room', token, theme: { //update daily.co domain
        colors: {
          accent: '#1C0644',
          accentText: '#ffffff',
        }} 
      });
  }

  function startLiveStream() {
    callFrame.current.startLiveStreaming({ rtmpUrl: "rtmp://NGROK TCP PATH/live/foo" }); //remember to change every time we updat this
    callFrame.current.on('live-streaming-started', showEvent)

    startProcessing()
  }

  useEffect(() => {
    // Only create a new DailyIframe if one doesn't already exist
    if (containerRef.current && callFrame.current === null) {
      joinCall();
      console.log(callFrame)
      
      callFrame.current.on('live-streaming-error', showEvent)
    }

    
    return () => {
      
      if (callFrame.current) {
        // Properly destroy the existing DailyIframe on unmount
        callFrame.current.leave().then(() => {
          callFrame.current.stopLiveStreaming();
          callFrame.current = null;
        });
      }
    };
  }, [containerRef]);

  return (
    <div className="relative">
      <div ref={containerRef} className="w-80% h-[700px] rounded-xl overflow-hidden shadow" /> 
      <button className="absolute bottom-2 right-4 py-2 px-4 font-semibold rounded-lg shadow-md text-white bg-custom-blue hover:bg-custom-blue-700" onClick={startLiveStream}>
        Activate LeMUR Agent
      </button>
    </div>
  );

};

export default Video;