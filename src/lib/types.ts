export interface Settings {
  language: string;
  model: string;
  autoStart: boolean;
  retention: number;
  theme: "system" | "light" | "dark";
  onboardingComplete: boolean;
  microphone: number;
}

export interface HistoryEntry {
  id: number;
  text: string;
  char_count: number;
  word_count: number;
  created_at: string;
}

export interface Stats {
  totalTranscriptions: number;
  totalWords: number;
  totalCharacters: number;
  streakDays: number;
}

export interface Microphone {
  id: number;
  name: string;
  channels: number;
}

export interface Options {
  models: string[];
  languages: string[];
  retentionOptions: Record<string, number>;
  themeOptions: string[];
  microphones: Microphone[];
}

export interface ModelInfo {
  name: string;
  sizeBytes: number;
  cached: boolean;
}

export interface DownloadProgress {
  model: string;
  percent: number;
  downloadedBytes: number;
  totalBytes: number;
  speedBps: number;
  etaSeconds: number;
}

export interface DownloadComplete {
  model: string;
  success: boolean;
  cancelled?: boolean;
  alreadyCached?: boolean;
  error?: string;
}
