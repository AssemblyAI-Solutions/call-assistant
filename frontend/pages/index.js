import Image from 'next/image'
import Video from '@/components/Video'
import Assistant from '@/components/Assistant'
import Transcript from '@/components/Transcript'
import aai_logo_colored from '../public/aai_logo_colored.jpeg'
import { StreamIdProvider } from '@/contexts/StreamIdContext'

export default function Home() {
  return (
    <StreamIdProvider>
    <div>
    <div className='h-full my-2 mx-14'>
        <Image src={aai_logo_colored} width={250} alt="AAI Logo"/>
    </div>
    <main
      className='flex h-screen overflow-hidden bg-custom-white mx-12 my-2'
    >
      <div className="flex flex-col w-full h-screen p-2">
        <Video />
      </div>
      <div className="flex flex-col w-1/2 p-2 bg-white shadow-xl">
        <Transcript />
        <Assistant/>
      </div>
    </main>
    </div>
    </StreamIdProvider>
  )
}
