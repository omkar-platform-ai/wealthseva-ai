'use client';
import { useState, useRef, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { Send } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface HealthStatus {
  healthy: boolean;
  loading: boolean;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:8000';
const ELEVENLABS_AGENT_ID = process.env.NEXT_PUBLIC_ELEVENLABS_AGENT_ID;

export default function AvatarChat() {
  const t = useTranslations('advisor');
  const locale = useLocale();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState<HealthStatus>({ healthy: true, loading: false });
  const [showChips, setShowChips] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Health check every 30 seconds
  useEffect(() => {
    const checkHealth = async () => {
      setHealth(prev => ({ ...prev, loading: true }));
      try {
        const res = await fetch(`${BACKEND_URL}/health`);
        setHealth({ healthy: res.ok, loading: false });
      } catch {
        setHealth({ healthy: false, loading: false });
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  // Clear chat and show welcome message on locale change
  useEffect(() => {
    setMessages([]);
    setShowChips(true);
  }, [locale]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setShowChips(false);
    setLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          session_id: 'demo-session',
          language: locale,
          history: messages.slice(-10), // Send last 10 messages for context
        }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let reply = '';

      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        reply += decoder.decode(value);
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: 'assistant', content: reply };
          return updated;
        });
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: t('error' as never) }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col bg-white rounded-2xl shadow-lg overflow-hidden h-[600px]">
      {/* Avatar header */}
      <div className="bg-idbi-blue p-4 flex items-center gap-3">
        <div className="w-12 h-12 rounded-full bg-idbi-gold flex items-center justify-center text-white font-bold text-lg">
          S
        </div>
        <div>
          <p className="text-white font-semibold">Shreya</p>
          <p className="text-blue-200 text-xs">IDBI Wealth Advisor · {locale.toUpperCase()} · {
            locale === 'en' ? 'English' :
            locale === 'hi' ? 'हिंदी' :
            locale === 'mr' ? 'मराठी' :
            locale === 'ta' ? 'தமிழ்' :
            locale === 'bn' ? 'বাংলা' : locale.toUpperCase()
          }</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${health.healthy ? 'bg-green-400' : 'bg-red-500'}`} />
          {health.loading && <span className="text-xs text-blue-200">...</span>}
          {!health.healthy && <span className="text-xs text-red-200">{t('reconnecting' as never)}</span>}
        </div>
      </div>

      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center mt-8">
            <p className="text-gray-600 text-lg mb-2">{t('welcomeMessage' as never)}</p>
            {!ELEVENLABS_AGENT_ID && (
              <p className="text-xs text-amber-600 bg-amber-50 px-3 py-1 rounded-full inline-block">
                Voice preview — add ElevenLabs agent ID to enable avatar
              </p>
            )}
            {showChips && (
              <div className="flex flex-wrap gap-2 justify-center mt-4">
                {[
                  { key: 'chip1', text: t('chip1' as never) },
                  { key: 'chip2', text: t('chip2' as never) },
                  { key: 'chip3', text: t('chip3' as never) },
                ].map(chip => (
                  <button
                    key={chip.key}
                    onClick={() => {
                      setInput(chip.text);
                      setTimeout(() => {
                        const event = new KeyboardEvent('keydown', { key: 'Enter' });
                        (document.activeElement as HTMLInputElement)?.dispatchEvent(event);
                      }, 100);
                    }}
                    className="text-xs bg-idbi-light text-idbi-blue px-4 py-2 rounded-full hover:bg-idbi-blue hover:text-white transition-colors"
                  >
                    {chip.text}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
              msg.role === 'user'
                ? 'bg-idbi-blue text-white rounded-br-sm'
                : 'bg-gray-100 text-gray-800 rounded-bl-sm'
            }`}>
              {msg.content || <span className="animate-pulse">●●●</span>}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t p-4 flex gap-3">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendMessage()}
          placeholder={t('placeholder')}
          className="flex-1 border rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-idbi-blue"
          disabled={loading}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim() || !health.healthy}
          className="bg-idbi-blue text-white px-4 py-2 rounded-xl hover:bg-blue-900 disabled:opacity-50 transition-colors"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
