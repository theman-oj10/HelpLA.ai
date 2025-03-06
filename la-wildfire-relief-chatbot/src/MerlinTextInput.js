import React, { useState } from 'react';
import { MessageSquare } from 'lucide-react';

const MerlinTextInput = () => {
  const [prompt, setPrompt] = useState('');

  return (
    <div style={{
      width: '100%',
      padding: '16px',
      backgroundColor: '#121212',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100px'
    }}>
      <div style={{
        backgroundColor: '#1F2937',
        borderRadius: '8px',
        padding: '8px',
        display: 'flex',
        alignItems: 'center',
        width: '100%',
        maxWidth: '800px'
      }}>
        <button style={{
          padding: '8px',
          color: '#A0AEC0',
          background: 'none',
          border: 'none',
          cursor: 'pointer'
        }}>
          <MessageSquare size={20} />
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
        />
        
        <button style={{
          backgroundColor: 'white',
          color: 'black',
          padding: '4px 12px',
          borderRadius: '6px',
          fontWeight: 500,
          marginRight: '8px',
          border: 'none',
          cursor: 'pointer'
        }}>
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
    </div>
  );
};

export default MerlinTextInput;