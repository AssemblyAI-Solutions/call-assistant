import React, { useEffect, useState, useContext } from 'react';
import StreamIdContext from '@/contexts/StreamIdContext';

const Transcript = () => {
    const [transcript, setTranscript] = useState("")
    const { streamId } = useContext(StreamIdContext);

    useEffect(() => {
        console.log(streamId)

        const transcriptSource = new EventSource(`https://PORT 5000 NGROK URL/transcript_stream?streamid=${streamId}`, { //update url here... should be webhook server/app.py
            withCredentials: true,
        });

        transcriptSource.onmessage = (event) => {
            console.log(event.data);
            const data = JSON.parse(event.data)
            console.log(data);

            setTranscript(data.transcript);
        }
    
        return () => transcriptSource.close();
      }, [streamId]);

    return (

        <div className="flex flex-col h-2/3 text-custom-white bg-custom-off-blue rounded-md">
            <h2 className="text-xl p-2 font-bold mb-2">Transcript</h2>
            <div className="flex-grow overflow-auto bg-gray-200 p-2 rounded-sm shadow-inner text-black">
                <div>
                    {transcript}
                </div>
            </div>
            </div>
    )
}

export default Transcript;