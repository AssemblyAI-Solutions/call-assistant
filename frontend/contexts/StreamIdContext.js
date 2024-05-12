import { createContext, useState } from 'react';

const StreamIdContext = createContext({
  streamId: null,
  setStreamId: () => {},
});

export const StreamIdProvider = ({ children }) => {
  const [streamId, setStreamId] = useState(null);

  return (
    <StreamIdContext.Provider value={{ streamId, setStreamId }}>
      {children}
    </StreamIdContext.Provider>
  );
};

export default StreamIdContext;
