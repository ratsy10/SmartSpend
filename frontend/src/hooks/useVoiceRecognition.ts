import { useState, useEffect, useCallback, useRef } from 'react';

// For TypeScript compatibility with Web Speech API
interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionResultList {
  [index: number]: SpeechRecognitionResult;
  length: number;
}

interface SpeechRecognitionResult {
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
  length: number;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionInstance {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: (event: SpeechRecognitionEvent) => void;
  onerror: (event: any) => void;
  onend: () => void;
  start: () => void;
  stop: () => void;
  abort: () => void;
}

declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export function useVoiceRecognition() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const manualStopRef = useRef(false);
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const hasSupport = useRef(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        hasSupport.current = true;
        const recog = new SpeechRecognition();
        recog.continuous = true;
        recog.interimResults = true;
        recog.lang = 'en-US';

        recog.onresult = (event: SpeechRecognitionEvent) => {
          // Build the full transcript from all results (final + interim)
          let finalTranscript = '';
          let interimTranscript = '';

          for (let i = 0; i < event.results.length; i++) {
            const result = event.results[i];
            if (result.isFinal) {
              finalTranscript += result[0].transcript + ' ';
            } else {
              interimTranscript += result[0].transcript;
            }
          }

          const combinedTranscript = (finalTranscript + interimTranscript).trim();
          setTranscript(combinedTranscript);

          // Reset silence timer on every speech event
          if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
          }
          // Auto-stop after 3 seconds of silence (no new results)
          silenceTimerRef.current = setTimeout(() => {
            if (!manualStopRef.current) {
              console.log('Auto-stopping after 3s silence');
              manualStopRef.current = true;
              recog.stop();
            }
          }, 3000);
        };

        recog.onerror = (event: any) => {
          console.error('Speech recognition error:', event.error);
          // 'no-speech' and 'aborted' are not real errors
          if (event.error === 'no-speech' || event.error === 'aborted') {
            return;
          }
          setError(event.error);
          setIsListening(false);
        };

        recog.onend = () => {
          setIsListening(false);
          if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
          }
        };

        recognitionRef.current = recog;
      } else {
        setError("Speech recognition is not supported in this browser.");
      }
    }

    return () => {
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }
    };
  }, []);

  const startListening = useCallback(() => {
    if (recognitionRef.current) {
      setTranscript('');
      setError(null);
      manualStopRef.current = false;
      setIsListening(true);
      try {
        recognitionRef.current.start();
      } catch (e) {
        // Recognition might already be started
        console.error(e);
      }
    }
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      manualStopRef.current = true;
      recognitionRef.current.stop();
      setIsListening(false);
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }
    }
  }, []);

  return {
    isListening,
    transcript,
    error,
    startListening,
    stopListening,
    hasSupport: hasSupport.current || !!(typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition))
  };
}
