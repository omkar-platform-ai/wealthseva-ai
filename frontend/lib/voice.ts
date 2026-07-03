// Voice v1: speak replies via backend /api/tts (ElevenLabs proxy) with
// browser speechSynthesis fallback, plus Web Speech API mic input.

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:8000';

// BCP-47 tags for browser speech APIs (Indian regional variants)
export const SPEECH_LOCALE: Record<string, string> = {
  en: 'en-IN',
  hi: 'hi-IN',
  mr: 'mr-IN',
  ta: 'ta-IN',
  bn: 'bn-IN',
};

export interface SpeakHandle {
  stop: () => void;
}

export async function speak(
  text: string,
  locale: string,
  onEnd: () => void,
): Promise<SpeakHandle> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/tts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text.slice(0, 2000), language: locale }),
    });
    if (res.ok && res.headers.get('content-type')?.includes('audio')) {
      const url = URL.createObjectURL(await res.blob());
      const audio = new Audio(url);
      const finish = () => {
        URL.revokeObjectURL(url);
        onEnd();
      };
      audio.onended = finish;
      audio.onerror = finish;
      await audio.play();
      return {
        stop: () => {
          audio.pause();
          finish();
        },
      };
    }
  } catch {
    // Backend unreachable or autoplay blocked — browser fallback below.
  }
  return speakWithBrowser(text, locale, onEnd);
}

function speakWithBrowser(text: string, locale: string, onEnd: () => void): SpeakHandle {
  if (typeof window === 'undefined' || !window.speechSynthesis) {
    onEnd();
    return { stop: () => {} };
  }
  const synth = window.speechSynthesis;
  synth.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  const lang = SPEECH_LOCALE[locale] ?? 'en-IN';
  utterance.lang = lang;
  // getVoices() can be empty before voices load; utterance.lang alone still
  // lets the engine pick — the explicit match just improves voice quality.
  const voices = synth.getVoices();
  const voice =
    voices.find(v => v.lang === lang) ??
    voices.find(v => v.lang.startsWith(lang.split('-')[0]));
  if (voice) utterance.voice = voice;
  utterance.onend = onEnd;
  utterance.onerror = onEnd;
  synth.speak(utterance);
  return {
    stop: () => {
      synth.cancel();
      onEnd();
    },
  };
}

export interface Recognizer {
  start: () => void;
  stop: () => void;
}

export function createRecognizer(
  locale: string,
  onResult: (transcript: string, isFinal: boolean) => void,
  onEnd: () => void,
): Recognizer | null {
  if (typeof window === 'undefined') return null;
  // Chrome/Edge expose the API as webkitSpeechRecognition; not in TS lib.dom
  const Ctor =
    (window as unknown as Record<string, unknown>).SpeechRecognition ??
    (window as unknown as Record<string, unknown>).webkitSpeechRecognition;
  if (typeof Ctor !== 'function') return null;

  const recognition = new (Ctor as new () => {
    lang: string;
    interimResults: boolean;
    continuous: boolean;
    onresult: (event: { results: ArrayLike<{ 0: { transcript: string }; isFinal: boolean }> }) => void;
    onend: () => void;
    onerror: () => void;
    start: () => void;
    stop: () => void;
  })();
  recognition.lang = SPEECH_LOCALE[locale] ?? 'en-IN';
  recognition.interimResults = true;
  recognition.continuous = false;
  recognition.onresult = event => {
    const result = event.results[event.results.length - 1];
    onResult(result[0].transcript, result.isFinal);
  };
  recognition.onend = onEnd;
  recognition.onerror = onEnd;
  return {
    start: () => recognition.start(),
    stop: () => recognition.stop(),
  };
}
