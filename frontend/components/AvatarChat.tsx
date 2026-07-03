'use client';
import { useState, useRef, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { Mic, Send, Volume2, VolumeX } from 'lucide-react';
import { motion } from 'framer-motion';
import { speak, createRecognizer, SpeakHandle, Recognizer } from '@/lib/voice';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface HealthStatus {
  healthy: boolean;
  loading: boolean;
}

type AvatarState = 'idle' | 'listening' | 'speaking';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:8000';

export default function AvatarChat() {
  const t = useTranslations('advisor');
  const locale = useLocale();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState<HealthStatus>({ healthy: true, loading: false });
  const [showChips, setShowChips] = useState(true);
  const [avatarState, setAvatarState] = useState<AvatarState>('idle');
  const [voiceOn, setVoiceOn] = useState(true);
  const [sttSupported, setSttSupported] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  // Ref mirror so an in-flight reply respects a mid-stream mute
  const voiceOnRef = useRef(true);
  const speakRef = useRef<SpeakHandle | null>(null);
  const recognizerRef = useRef<Recognizer | null>(null);

  const stopSpeaking = () => {
    speakRef.current?.stop();
    speakRef.current = null;
  };

  const toggleVoice = () => {
    const next = !voiceOnRef.current;
    voiceOnRef.current = next;
    setVoiceOn(next);
    if (!next) stopSpeaking();
  };

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

  // Web Speech API availability is only knowable client-side
  useEffect(() => {
    const w = window as unknown as Record<string, unknown>;
    setSttSupported(typeof (w.SpeechRecognition ?? w.webkitSpeechRecognition) === 'function');
  }, []);

  // Clear chat, silence voice, and show welcome message on locale change
  useEffect(() => {
    setMessages([]);
    setShowChips(true);
    speakRef.current?.stop();
    speakRef.current = null;
    recognizerRef.current?.stop();
  }, [locale]);

  // Silence voice + mic on unmount
  useEffect(() => {
    return () => {
      speakRef.current?.stop();
      recognizerRef.current?.stop();
    };
  }, []);

  const sendMessage = async (chipInput?: string) => {
    const messageToSend = chipInput || input;
    if (!messageToSend?.trim() || loading) return;

    stopSpeaking();
    const userMsg: Message = { role: 'user', content: messageToSend };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInput('');
    setShowChips(false);
    setLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageToSend,
          session_id: 'demo-session',
          language: locale,
          history: updatedMessages.slice(-10).map(m => ({ role: m.role, content: m.content })),
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

      if (voiceOnRef.current && reply) {
        setAvatarState('speaking');
        speakRef.current = await speak(reply, locale, () => setAvatarState('idle'));
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: t('error' as never) }]);
    } finally {
      setLoading(false);
    }
  };

  const toggleMic = () => {
    if (avatarState === 'listening') {
      recognizerRef.current?.stop();
      return;
    }
    stopSpeaking();
    const recognizer = createRecognizer(
      locale,
      (transcript, isFinal) => {
        setInput(transcript);
        if (isFinal) sendMessage(transcript);
      },
      () => setAvatarState('idle'),
    );
    if (!recognizer) return;
    recognizerRef.current = recognizer;
    setAvatarState('listening');
    recognizer.start();
  };

  return (
    <div className="flex flex-col bg-white rounded-2xl shadow-lg overflow-hidden h-[600px]">
      {/* Avatar header */}
      <div className="bg-idbi-blue p-4 flex items-center gap-3">
        <div className="relative w-12 h-12 flex-shrink-0">
          {avatarState !== 'idle' && (
            <motion.span
              className={`absolute inset-0 rounded-full ${
                avatarState === 'speaking' ? 'bg-idbi-gold' : 'bg-green-400'
              }`}
              animate={{ scale: [1, 1.5], opacity: [0.7, 0] }}
              transition={{ duration: 1.1, repeat: Infinity, ease: 'easeOut' }}
            />
          )}
          <div className="relative w-12 h-12 rounded-full bg-idbi-gold flex items-center justify-center text-white font-bold text-lg">
            S
          </div>
        </div>
        <div>
          <p className="text-white font-semibold">Shreya</p>
          <p className="text-blue-200 text-xs">
            {avatarState === 'listening' ? t('listening' as never)
              : avatarState === 'speaking' ? t('speaking' as never)
              : <>IDBI Wealth Advisor · {locale.toUpperCase()} · {
                  locale === 'en' ? 'English' :
                  locale === 'hi' ? 'हिंदी' :
                  locale === 'mr' ? 'मराठी' :
                  locale === 'ta' ? 'தமிழ்' :
                  locale === 'bn' ? 'বাংলা' : locale.toUpperCase()
                }</>}
          </p>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <button
            onClick={toggleVoice}
            className="text-blue-200 hover:text-white transition-colors"
            aria-label={voiceOn ? t('voice_off' as never) : t('voice_on' as never)}
            title={voiceOn ? t('voice_off' as never) : t('voice_on' as never)}
          >
            {voiceOn ? <Volume2 size={18} /> : <VolumeX size={18} />}
          </button>
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
            {showChips && (
              <div className="flex flex-wrap gap-2 justify-center mt-4">
                {[
                  { key: 'chip1', text: t('chip1' as never) },
                  { key: 'chip2', text: t('chip2' as never) },
                  { key: 'chip3', text: t('chip3' as never) },
                ].map(chip => (
                  <button
                    key={chip.key}
                    onClick={() => sendMessage(chip.text)}
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
      <div className="border-t p-3 flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendMessage()}
          placeholder={t('placeholder')}
          className="flex-1 min-w-0 border rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-idbi-blue"
          disabled={loading}
        />
        {sttSupported && (
          <button
            onClick={toggleMic}
            disabled={loading}
            className={`flex-shrink-0 p-2 rounded-xl transition-colors disabled:opacity-50 ${
              avatarState === 'listening'
                ? 'bg-red-500 text-white animate-pulse'
                : 'border border-idbi-blue text-idbi-blue hover:bg-idbi-light'
            }`}
            aria-label={t('mic_label' as never)}
            title={t('mic_label' as never)}
          >
            <Mic size={16} />
          </button>
        )}
        <button
          onClick={() => sendMessage()}
          disabled={loading || !input.trim() || !health.healthy}
          className="flex-shrink-0 bg-idbi-blue text-white p-2 rounded-xl hover:bg-blue-900 disabled:opacity-50 transition-colors"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
