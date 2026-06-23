'use client';
import { useState, useRef, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { Send } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:8000';

export default function AvatarChat() {
  const t = useTranslations('advisor');
  const locale = useLocale();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          session_id: 'demo-session',
          language: locale,
          history: messages,
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
          <p className="text-blue-200 text-xs">IDBI Wealth Advisor · {locale.toUpperCase()}</p>
        </div>
        <span className="ml-auto w-2 h-2 rounded-full bg-green-400" />
      </div>

      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <p className="text-center text-gray-400 text-sm mt-8">
            {locale === 'hi' ? 'नमस्ते! मैं श्रेया हूं, आपकी AI वेल्थ एडवाइज़र।' :
             locale === 'mr' ? 'नमस्कार! मी श्रेया आहे, तुमची AI वेल्थ अॅडव्हायझर.' :
             locale === 'ta' ? 'வணக்கம்! நான் ஸ்ரேயா, உங்கள் AI செல்வ ஆலோசகர்.' :
             locale === 'bn' ? 'নমস্কার! আমি শ্রেয়া, আপনার AI ওয়েলথ অ্যাডভাইজার।' :
             'Hello! I\'m Shreya, your AI wealth advisor. How can I help you today?'}
          </p>
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
          disabled={loading || !input.trim()}
          className="bg-idbi-blue text-white px-4 py-2 rounded-xl hover:bg-blue-900 disabled:opacity-50 transition-colors"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
