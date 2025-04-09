import React, { useState } from 'react';

const MerlinApp = () => {
  const [messages, setMessages] = useState([]);

  // Function to handle new messages from the input component
  const handleSendMessage = (message) => {
    if (message.trim()) {
      // Add user message to the chat
      setMessages([...messages, { text: message, isUser: true }]);
      
      // Process the user message through the API
      processUserMessage(message);
    }
  };
  
  // This function processes user messages and generates responses via the API
  const processUserMessage = async (message) => {
    // Show loading state
    setMessages(prev => [...prev, { 
      text: "Thinking...", 
      isUser: false,
      isLoading: true
    }]);
    
    try {
      // Make API call to the FastAPI backend
      const response = await fetch('http://localhost:8000/query_services', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_query: message }) // Match the expected field name in backend
      });
      
      if (!response.ok) {
        throw new Error(`API responded with status: ${response.status}`);
      }
      
      const data = await response.json();
      const aiResponse = data.formatted_response; // Use the field from ServiceResponse model
      
      // Remove loading message and add the actual response
      setMessages(prev => {
        const filteredMessages = prev.filter(msg => !msg.isLoading);
        return [...filteredMessages, { 
          text: aiResponse, 
          isUser: false 
        }];
      });
    } catch (error) {
      console.error("API Error:", error);
      // Handle errors
      setMessages(prev => {
        const filteredMessages = prev.filter(msg => !msg.isLoading);
        return [...filteredMessages, { 
          text: "Sorry, I encountered an error connecting to the service. Please try again.", 
          isUser: false,
          isError: true
        }];
      });
    }
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      backgroundColor: '#121212',
      color: 'white',
      fontFamily: 'Inter, sans-serif'
    }}>
      {/* Top navigation bar */}
      <div style={{
        height: '56px',
        borderBottom: '1px solid #2D3748',
        display: 'flex',
        alignItems: 'center',
        padding: '0 24px'
      }}>
        <h1 style={{ fontWeight: 'bold', fontSize: '20px' }}>LA Help.ai</h1>
      </div>

      {/* Chat area - will show messages when there are any */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px'
      }}>
        {messages.length === 0 ? (
          // Welcome screen when no messages
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
            height: '100%',
            padding: '0 24px'
          }}>
            <h1 style={{ fontSize: '36px', fontWeight: 'bold', marginBottom: '24px' }}>
              Welcome to LA Help.ai
            </h1>
            <p style={{ fontSize: '24px', color: '#A0AEC0', marginBottom: '16px' }}>
              How can we help you today?
            </p>
            {/* <p style={{ fontSize: '20px', marginBottom: '8px' }}>
              I can help you <span style={{ color: '#A0AEC0' }}>summarise, code, create images</span> & more.
            </p> */}
          </div>
        ) : (
          // Display messages
          messages.map((msg, index) => (
            <div 
              key={index}
              style={{
                alignSelf: msg.isUser ? 'flex-end' : 'flex-start',
                maxWidth: '70%',
                backgroundColor: msg.isUser ? '#3B82F6' : (msg.isError ? '#B91C1C' : '#2D3748'),
                padding: '12px 16px',
                borderRadius: '12px',
                borderBottomRightRadius: msg.isUser ? '4px' : '12px',
                borderBottomLeftRadius: msg.isUser ? '12px' : '4px'
              }}
            >
              {msg.isLoading ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>{msg.text}</span>
                  <div style={{ 
                    width: '12px', 
                    height: '12px', 
                    borderRadius: '50%', 
                    backgroundColor: '#A0AEC0',
                    animation: 'pulse 1.5s infinite ease-in-out' 
                  }} />
                </div>
              ) : (
                msg.text
              )}
            </div>
          ))
        )}
      </div>

      {/* The custom text input component */}
      <div style={{ padding: '16px', borderTop: '1px solid #2D3748' }}>
        <MerlinTextInputWrapper onSendMessage={handleSendMessage} />
      </div>
    </div>
  );
};

// Wrapper for our MerlinTextInput that adds the message sending functionality
const MerlinTextInputWrapper = ({ onSendMessage }) => {
  const [prompt, setPrompt] = useState('');

  const handleSend = () => {
    onSendMessage(prompt);
    setPrompt('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{
      backgroundColor: '#1F2937',
      borderRadius: '8px',
      padding: '8px',
      display: 'flex',
      alignItems: 'center',
      width: '100%'
    }}>
      <button style={{
        padding: '8px',
        color: '#A0AEC0',
        background: 'none',
        border: 'none',
        cursor: 'pointer'
      }}>
        <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
        </svg>
      </button>
      
      <input
        type="text"
        placeholder="Type your prompt here"
        style={{
          flex: 1,
          backgroundColor: 'transparent',
          border: 'none',
          outline: 'none',
          padding: '8px 12px',
          color: 'white',
          fontSize: '16px'
        }}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        onKeyDown={handleKeyDown}
      />
      
      <button 
        style={{
          backgroundColor: prompt.trim() ? 'white' : '#4B5563',
          color: prompt.trim() ? 'black' : '#9CA3AF',
          padding: '4px 12px',
          borderRadius: '6px',
          fontWeight: 500,
          marginRight: '8px',
          border: 'none',
          cursor: prompt.trim() ? 'pointer' : 'default'
        }}
        onClick={handleSend}
        disabled={!prompt.trim()}
      >
        Ask
      </button>
      
      <button style={{
        padding: '4px',
        color: '#A0AEC0',
        background: 'none',
        border: 'none',
        cursor: 'pointer'
      }}>
        <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 2L11 13"></path>
          <path d="M22 2l-7 20-4-9-9-4 20-7z"></path>
        </svg>
      </button>
    </div>
  );
};

export default MerlinApp;