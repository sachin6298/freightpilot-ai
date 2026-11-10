import { useState, type FormEvent } from 'react';
import { Bot, CornerDownLeft, LoaderCircle, Send, Sparkles, UserRound } from 'lucide-react';
import { sendAiSupportChat } from '../../api';

type Message = { id: number; role: 'user' | 'assistant'; text: string };

export function AiCopilotChat({ shipmentId, role }: { shipmentId?: string; role?: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [disclaimer, setDisclaimer] = useState('');

  const send = async (event: FormEvent) => {
    event.preventDefault();
    const text = draft.trim();
    if (!text || busy) return;
    setError('');
    setDraft('');
    const userMessage: Message = { id: Date.now(), role: 'user', text };
    setMessages((current) => [...current, userMessage]);
    setBusy(true);
    try {
      const response = await sendAiSupportChat(text, shipmentId, role || 'GUEST');
      setMessages((current) => [...current, { id: Date.now() + 1, role: 'assistant', text: response.reply }]);
      setDisclaimer(response.disclaimer || 'AI responses are decision support and should be checked against the source records.');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'The AI service could not answer this request.');
      setDraft(text);
    } finally {
      setBusy(false);
    }
  };

  return <section className="fp-ai-chat-card">
    <div className="fp-ai-chat-heading"><div className="fp-ai-avatar"><Sparkles size={18}/></div><div><span>GEMINI AI ASSISTANT</span><h3>Ask Freight Copilot</h3><p>Ask about shipping workflows, quote terms, risk signals or your selected shipment.</p></div><span className="fp-ai-live"><i/> BACKEND-CONFIGURED</span></div>
    <div className="fp-ai-chat-body">
      {messages.length === 0 ? <div className="fp-ai-empty"><div className="fp-ai-empty-icon"><Bot size={27}/></div><strong>What would you like to understand?</strong><p>Start with a question. Responses are returned by your configured backend AI provider.</p><div className="fp-ai-suggestions">{['Summarise the key risks in my selected shipment','What should I compare before choosing a carrier?','Explain the PayPal Sandbox payment flow'].map((suggestion) => <button key={suggestion} onClick={() => setDraft(suggestion)}>{suggestion}</button>)}</div></div> : <div className="fp-ai-messages">{messages.map((message) => <div className={`fp-ai-message ${message.role}`} key={message.id}><span className="fp-ai-message-icon">{message.role === 'user' ? <UserRound size={15}/> : <Bot size={15}/>}</span><div><small>{message.role === 'user' ? 'YOU' : 'COPILOT'}</small><p>{message.text}</p></div></div>)}{busy && <div className="fp-ai-thinking"><LoaderCircle size={15}/> Copilot is preparing a response…</div>}</div>}
    </div>
    {error && <div className="fp-ai-error">{error}</div>}
    <form className="fp-ai-chat-form" onSubmit={send}><textarea value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Ask a freight or shipment question…" rows={2} disabled={busy}/><div><span><CornerDownLeft size={13}/> Enter to send · Responses depend on backend provider configuration</span><button type="submit" disabled={busy || !draft.trim()}>{busy ? <LoaderCircle size={16} className="spin"/> : <Send size={16}/>} Send</button></div></form>
    {disclaimer && <p className="fp-ai-disclaimer">{disclaimer}</p>}
  </section>;
}
