import { useEffect } from 'react';
import { TeletextPanel, TeletextText, NodeBadge } from '../components';
import useNavigationStore from '../store/navigationStore';
import useMeshStore from '../store/meshStore';

/**
 * P300 - Messages Page
 * LXMF message inbox with unread indicators
 */
const P300 = () => {
  const setBreadcrumbs = useNavigationStore((state) => state.setBreadcrumbs);
  
  const messages = useMeshStore((state) => state.messages);
  const messagesLoading = useMeshStore((state) => state.messagesLoading);
  const messagesError = useMeshStore((state) => state.messagesError);
  const loadMessages = useMeshStore((state) => state.loadMessages);
  const connectWS = useMeshStore((state) => state.connectWS);
  const disconnectWS = useMeshStore((state) => state.disconnectWS);
  const nodes = useMeshStore((state) => state.nodes);
  
  useEffect(() => {
    setBreadcrumbs(['MESSAGES', 'P300']);
    loadMessages();
    connectWS();

    return () => {
      disconnectWS();
    };
  }, [setBreadcrumbs, loadMessages, connectWS, disconnectWS]);

  const getNodeById = (nodeId: string) => {
    return nodes.find((n) => n.id === nodeId);
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
  };

  return (
    <div style={{ 
      padding: '20px', 
      backgroundColor: '#000', 
      minHeight: '100vh',
      fontFamily: 'IBM VGA, monospace'
    }}>
      <TeletextPanel title={`INBOX ● ${messages.length} MESSAGES`} color="cyan">
        {messagesLoading && (
          <TeletextText color="yellow">LOADING MESSAGES...</TeletextText>
        )}

        {messagesError && (
          <div>
            <TeletextText color="red">ERROR: {messagesError}</TeletextText>
            <br />
            <TeletextText color="gray">Press R to retry</TeletextText>
          </div>
        )}

        {!messagesLoading && !messagesError && messages.length === 0 && (
          <TeletextText color="gray">NO MESSAGES</TeletextText>
        )}

        {!messagesLoading && !messagesError && messages.length > 0 && (
          <div>
            {messages.map((msg) => {
              const sender = getNodeById(msg.sender_id);
              const recipient = msg.recipient_id ? getNodeById(msg.recipient_id) : null;
              
              return (
                <div key={msg.id} style={{ marginBottom: '16px', borderBottom: '1px solid #333', paddingBottom: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <TeletextText color="cyan">FROM: </TeletextText>
                      {sender ? (
                        <NodeBadge node={{
                          id: sender.id,
                          callsign: sender.callsign,
                          type: sender.type,
                          status: sender.status.toUpperCase() as 'ONLINE' | 'DEGRADED' | 'OFFLINE'
                        }} />
                      ) : (
                        <TeletextText color="gray">{msg.sender_id.slice(0, 12)}</TeletextText>
                      )}
                    </div>
                    <TeletextText color="yellow">{formatTime(msg.timestamp)}</TeletextText>
                  </div>

                  <div style={{ marginTop: '4px' }}>
                    <TeletextText color="cyan">TO: </TeletextText>
                    {recipient ? (
                      <NodeBadge node={{
                        id: recipient.id,
                        callsign: recipient.callsign,
                        type: recipient.type,
                        status: recipient.status.toUpperCase() as 'ONLINE' | 'DEGRADED' | 'OFFLINE'
                      }} />
                    ) : (
                      <TeletextText color="magenta">
                        {msg.recipient_id ? msg.recipient_id.slice(0, 12) : 'BROADCAST'}
                      </TeletextText>
                    )}
                    {' '}
                    <TeletextText color="gray">● HOPS: {msg.hops}</TeletextText>
                  </div>

                  <div style={{ marginTop: '8px', paddingLeft: '16px' }}>
                    <TeletextText color="white">{msg.content}</TeletextText>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </TeletextPanel>

      <div style={{ marginTop: '16px' }}>
        <TeletextText color="gray">[100] MENU • [301] COMPOSE • [ESC] CLEAR</TeletextText>
      </div>
    </div>
  );
};

export default P300;
