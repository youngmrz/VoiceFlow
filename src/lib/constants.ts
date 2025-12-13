
import { Lock, Gauge, Wand2 } from "lucide-react";

export const APP_VERSION = "0.4.2"; // Example version, should ideally come from package.json

export const THEME_OPTIONS = [
  { val: 'light', label: 'Light' },
  { val: 'dark', label: 'Dark' },
  { val: 'system', label: 'System' },
] as const;

export const MODEL_OPTIONS = [
  { id: 'tiny', label: 'Tiny', desc: 'Fastest', detail: '39M params', tradeoff: 'Basic accuracy' },
  { id: 'base', label: 'Base', desc: 'Fast', detail: '74M params', tradeoff: 'Good for simple audio' },
  { id: 'small', label: 'Small', desc: 'Balanced', detail: '244M params', tradeoff: 'Recommended' },
  { id: 'turbo', label: 'Turbo', desc: 'Fast + Accurate', detail: '809M params', tradeoff: 'Best value' },
  { id: 'medium', label: 'Medium', desc: 'Accurate', detail: '769M params', tradeoff: 'High quality' },
  { id: 'large-v3', label: 'Large', desc: 'Most Accurate', detail: '1.5B params', tradeoff: 'Slower, best quality' },
] as const;

export const ONBOARDING_FEATURES = [
  { icon: Lock, label: "100% Local", desc: "Never leaves your device" },
  { icon: Gauge, label: "Lightning Fast", desc: "Real-time transcription" },
  { icon: Wand2, label: "AI Powered", desc: "State-of-the-art accuracy" },
];

export const ONBOARDING_STEPS_INFO = {
  welcome: {
    id: "welcome",
    title: "Welcome to VoiceFlow",
    subtitle: "Your AI-powered dictation assistant",
  },
  audio: {
    id: "audio",
    title: "Select Microphone",
    subtitle: "Choose your input device",
  },
  model: {
    id: "model",
    title: "AI Configuration",
    subtitle: "Balance speed and accuracy",
  },
  theme: {
    id: "theme",
    title: "Appearance",
    subtitle: "Make it yours",
  },
  final: {
    id: "final",
    title: "You're All Set",
    subtitle: "Start dictating anywhere",
  }
};
