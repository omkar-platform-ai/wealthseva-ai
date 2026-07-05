'use client';
import { useState, useRef, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { Mic, Send, Volume2, VolumeX, X } from 'lucide-react';
import { motion } from 'framer-motion';
import { speak, createRecognizer, SpeakHandle, Recognizer } from '@/lib/voice';
import { useRouter, usePathname } from '../navigation';

interface Message {
  // 'divider' entries mark a mid-conversation language switch; they are
  // rendered as a thread separator and never sent to the backend.
  role: 'user' | 'assistant' | 'divider';
  content: string;
}

const NATIVE_NAMES: Record<string, string> = {
  en: 'English',
  hi: 'हिंदी',
  mr: 'मराठी',
  ta: 'தமிழ்',
  bn: 'বাংলা',
};
interface HealthStatus {
  healthy: boolean;
  loading: boolean;
}
type AvatarState = 'idle' | 'listening' | 'speaking';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:8000';

export default function AvatarChat() {
  const t = useTranslations('advisor');
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const [messages, setMessages] = useState<Message[]>([]);
  const [suggestedLocale, setSuggestedLocale] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState<HealthStatus>({ healthy: true, loading: false });
  const [showChips, setShowChips] = useState(true);
  const [avatarState, setAvatarState] = useState<AvatarState>('idle');
  const [voiceOn, setVoiceOn] = useState(true);
  const [sttSupported, setSttSupported] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
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

  useEffect(() => {
    const w = window as unknown as Record<string, unknown>;
    setSttSupported(typeof (w.SpeechRecognition ?? w.webkitSpeechRecognition) === 'function');
  }, []);

  // Keep the conversation across locale switches — switching language
  // mid-conversation must NOT lose context (demo priority #1). Only the
  // audio stops; a divider marks where the language changed.
  const prevLocaleRef = useRef(locale);
  useEffect(() => {
    if (prevLocaleRef.current === locale) return;
    prevLocaleRef.current = locale;
    setSuggestedLocale(null);
    speakRef.current?.stop();
    speakRef.current = null;
    recognizerRef.current?.stop();
    const divider = t('continuity_divider', { language: NATIVE_NAMES[locale] ?? locale });
    setMessages(prev => (prev.length === 0 ? prev : [...prev, { role: 'divider', content: divider }]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locale]);

  useEffect(() => {
    return () => {
      speakRef.current?.stop();
      recognizerRef.current?.stop();
    };
  }, []);

  // ---- Backend wiring: streaming POST /api/chat ----
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
          history: updatedMessages
            .filter(m => m.role !== 'divider')
            .slice(-10)
            .map(m => ({ role: m.role, content: m.content })),
        }),
      });

      // The language Shreya actually replied in (may differ from the UI
      // locale when the user typed in another language) — drives the TTS
      // voice and the "switch app language?" continuity chip.
      const detected = response.headers.get('X-Detected-Language');
      const replyLang = detected && NATIVE_NAMES[detected] ? detected : locale;

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

      setSuggestedLocale(replyLang !== locale ? replyLang : null);

      if (voiceOnRef.current && reply) {
        setAvatarState('speaking');
        speakRef.current = await speak(reply, replyLang, () => setAvatarState('idle'));
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

  const statusLabel =
    avatarState === 'listening' ? t('listening' as never)
    : avatarState === 'speaking' ? t('speaking' as never)
    : loading ? 'Typing…'
    : (
      <>IDBI Wealth Advisor · {locale.toUpperCase()} · {NATIVE_NAMES[locale] ?? locale.toUpperCase()}</>
    );

  return (
    <div className="flex flex-col bg-white rounded-[22px] border border-idbi-line shadow-pop overflow-hidden h-[600px]">
      {/* Avatar header */}
      <div className="bg-gradient-to-br from-idbi-green to-idbi-deep px-5 py-4 flex items-center gap-3.5">
        <div className="relative w-[46px] h-[46px] shrink-0">
          {avatarState !== 'idle' && (
            <motion.span
              className={`absolute inset-0 rounded-full ${avatarState === 'speaking' ? 'bg-idbi-orange' : 'bg-emerald-400'}`}
              animate={{ scale: [1, 1.6], opacity: [0.6, 0] }}
              transition={{ duration: 1.2, repeat: Infinity, ease: 'easeOut' }}
            />
          )}
          <div className="relative w-[46px] h-[46px] rounded-full bg-gradient-to-br from-idbi-orange to-[#F79B5E] flex items-center justify-center text-white font-bold text-lg">
            S
          </div>
        </div>
        <div>
          <p className="text-white font-bold text-base leading-tight">Shreya</p>
          <p className="text-[#BFE6DC] text-xs font-medium mt-0.5">{statusLabel}</p>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <button
            onClick={toggleVoice}
            className="text-[#BFE6DC] hover:text-white transition-colors"
            aria-label={voiceOn ? t('voice_off' as never) : t('voice_on' as never)}
            title={voiceOn ? t('voice_off' as never) : t('voice_on' as never)}
          >
            {voiceOn ? <Volume2 size={18} /> : <VolumeX size={18} />}
          </button>
          <span className={`w-2 h-2 rounded-full ${health.healthy ? 'bg-emerald-400 shadow-[0_0_0_3px_rgba(93,217,168,.25)]' : 'bg-red-500'}`} />
          {!health.healthy && <span className="text-[11px] text-red-100">{t('reconnecting' as never)}</span>}
        </div>
      </div>

      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-3.5">
        {messages.length === 0 && (
          <div className="text-center pt-6">
            <p className="text-idbi-slate text-lg font-semibold max-w-md mx-auto mb-5 leading-snug text-balance">
              {t('welcomeMessage' as never)}
            </p>
            {showChips && (
              <div className="flex flex-wrap gap-2.5 justify-center">
                {[
                  { key: 'chip1', text: t('chip1' as never) },
                  { key: 'chip2', text: t('chip2' as never) },
                  { key: 'chip3', text: t('chip3' as never) },
                ].map(chip => (
                  <button
                    key={chip.key}
                    onClick={() => sendMessage(chip.text)}
                    className="text-[13px] font-semibold bg-idbi-light text-idbi-green px-4 py-2.5 rounded-full hover:bg-idbi-green hover:text-white transition-colors"
                  >
                    {chip.text}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
        {messages.map((msg, i) => (
          msg.role === 'divider' ? (
            <div key={i} className="flex items-center gap-3 py-1" role="separator">
              <span className="flex-1 h-px bg-idbi-line" />
              <span className="text-[11px] font-medium text-idbi-faint">{msg.content}</span>
              <span className="flex-1 h-px bg-idbi-line" />
            </div>
          ) : (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[76%] px-4 py-3 rounded-[18px] text-sm leading-relaxed ${
              msg.role === 'user'
                ? 'bg-idbi-green text-white rounded-br-[5px]'
                : 'bg-[#F1F5F3] text-idbi-slate rounded-bl-[5px]'
            }`}>
              {msg.content || (
                <span className="inline-flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-idbi-green" style={{ animation: 'ws-dot 1.2s infinite' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-idbi-green" style={{ animation: 'ws-dot 1.2s infinite .2s' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-idbi-green" style={{ animation: 'ws-dot 1.2s infinite .4s' }} />
                </span>
              )}
            </div>
          </div>
          )
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Language-continuity chip: Shreya replied in a language other than the
          UI locale — offer a one-tap switch (conversation is preserved). */}
      {suggestedLocale && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mx-3.5 mb-2 flex items-center gap-2.5 bg-idbi-light rounded-[13px] px-3.5 py-2.5"
        >
          <p className="flex-1 text-[12.5px] font-medium text-idbi-slate">
            {t('continuity_prompt', { language: NATIVE_NAMES[suggestedLocale] })}
          </p>
          <button
            onClick={() => router.push(pathname, { locale: suggestedLocale })}
            className="shrink-0 text-[12.5px] font-bold text-white bg-idbi-green px-3.5 py-1.5 rounded-full hover:bg-idbi-dark transition-colors"
          >
            {t('continuity_switch')}
          </button>
          <button
            onClick={() => setSuggestedLocale(null)}
            aria-label={t('continuity_dismiss')}
            className="shrink-0 text-idbi-faint hover:text-idbi-slate transition-colors"
          >
            <X size={14} />
          </button>
        </motion.div>
      )}

      {/* Input */}
      <div className="border-t border-idbi-line p-3.5 flex gap-2.5 items-center bg-white">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendMessage()}
          placeholder={t('placeholder')}
          className="flex-1 min-w-0 border-[1.5px] border-idbi-line rounded-[14px] px-4 py-3 text-sm bg-[#FAFCFB] focus:outline-none focus:border-idbi-green focus:bg-white transition-colors"
          disabled={loading}
        />
        {sttSupported && (
          <button
            onClick={toggleMic}
            disabled={loading}
            className={`shrink-0 w-11 h-11 rounded-[13px] flex items-center justify-center transition-colors disabled:opacity-50 ${
              avatarState === 'listening'
                ? 'bg-red-500 text-white animate-pulse'
                : 'border-[1.5px] border-idbi-line text-idbi-green hover:bg-idbi-light'
            }`}
            aria-label={t('mic_label' as never)}
            title={t('mic_label' as never)}
          >
            <Mic size={18} />
          </button>
        )}
        <button
          onClick={() => sendMessage()}
          disabled={loading || !input.trim() || !health.healthy}
          className="shrink-0 w-11 h-11 rounded-[13px] bg-idbi-green text-white flex items-center justify-center hover:bg-idbi-dark disabled:opacity-50 transition-colors shadow-[0_8px_16px_-8px_rgba(0,131,108,.8)]"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
