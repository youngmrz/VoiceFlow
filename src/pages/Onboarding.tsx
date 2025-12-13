import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, ArrowLeft, Check, Mic, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { AudioVisualizer } from "@/components/AudioVisualizer";
import { api } from "@/lib/api";
import type { Settings, Options } from "@/lib/types";
import { 
  MODEL_OPTIONS, 
  THEME_OPTIONS, 
  ONBOARDING_FEATURES, 
  ONBOARDING_STEPS_INFO 
} from "@/lib/constants";

// Assets
import HeroImg from "@/assets/hero-illustration.png";
import MicImg from "@/assets/onboarding-mic.png";
import ModelImg from "@/assets/onboarding-model.png";
import ThemeImg from "@/assets/onboarding-theme.png";
import SuccessImg from "@/assets/onboarding-success.png";

// --- Step Components ---

const StepWelcome = () => (
  <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
    <p className="text-xl font-light leading-relaxed text-muted-foreground">
      Dictation designed for <span className="text-foreground font-medium">privacy</span> and <span className="text-foreground font-medium">flow</span>.
    </p>

    <div className="grid gap-4">
      {ONBOARDING_FEATURES.map((feature) => (
        <div key={feature.label} className="group flex items-center gap-4 p-4 rounded-2xl bg-secondary/30 backdrop-blur-sm border border-border/30 transition-all hover:bg-secondary/50 hover:border-primary/20 hover:shadow-lg hover:shadow-primary/5">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0 text-primary transition-transform group-hover:scale-110">
            <feature.icon className="w-5 h-5" />
          </div>
          <div>
            <p className="font-medium text-foreground">{feature.label}</p>
            <p className="text-sm text-muted-foreground">{feature.desc}</p>
          </div>
        </div>
      ))}
    </div>
  </div>
);

const StepAudio = ({ 
  microphone, 
  setMicrophone, 
  options 
}: { 
  microphone: number, 
  setMicrophone: (id: number) => void, 
  options: Options 
}) => {
  const [amplitude, setAmplitude] = useState(0);
  const [isListening, setIsListening] = useState(false);

  useEffect(() => {
    let audioContext: AudioContext | null = null;
    let analyser: AnalyserNode | null = null;
    let microphoneStream: MediaStream | null = null;
    let source: MediaStreamAudioSourceNode | null = null;
    let animationFrame: number;

    const startListening = async () => {
      try {
        microphoneStream = await navigator.mediaDevices.getUserMedia({
          audio: {
            deviceId: microphone ? String(microphone) : undefined,
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          }
        });

        audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 32;
        
        source = audioContext.createMediaStreamSource(microphoneStream);
        source.connect(analyser);

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        const update = () => {
          if (!analyser) return;
          analyser.getByteFrequencyData(dataArray);
          
          // Calculate average amplitude
          const sum = dataArray.reduce((acc, val) => acc + val, 0);
          const avg = sum / bufferLength;
          // Normalize to 0-1 (approximate max for speech usually hits around 128-150 depending on gain)
          const norm = Math.min(1, avg / 100); 
          
          setAmplitude(norm);
          animationFrame = requestAnimationFrame(update);
        };

        setIsListening(true);
        update();
      } catch (error) {
        console.error("Failed to access microphone:", error);
      }
    };

    startListening();

    return () => {
      if (microphoneStream) microphoneStream.getTracks().forEach(track => track.stop());
      if (audioContext) audioContext.close();
      cancelAnimationFrame(animationFrame);
    };
  }, [microphone]);

  return (
    <div className="space-y-6 animate-in slide-in-from-bottom-4 duration-500">
      <div className="p-1 rounded-2xl bg-secondary/30 backdrop-blur-sm border border-border/30 focus-within:ring-2 focus-within:ring-primary/20 transition-all">
        <Select value={String(microphone)} onValueChange={(v) => setMicrophone(Number(v))}>
          <SelectTrigger className="h-16 text-base bg-transparent border-0 rounded-xl px-4 focus:ring-0 focus:ring-offset-0">
            <SelectValue placeholder="Select a microphone" />
          </SelectTrigger>
          <SelectContent className="border-border/50 bg-popover/95 backdrop-blur-xl shadow-2xl rounded-xl">
            {options.microphones.map((mic) => (
              <SelectItem key={mic.id} value={String(mic.id)} className="py-3 rounded-lg cursor-pointer">
                <span className="flex items-center gap-3">
                  <Mic className="w-4 h-4 text-muted-foreground" />
                  <span>{mic.name}</span>
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex items-center gap-4 px-2">
         {/* Live Visualizer */}
         <div className="h-14 w-full bg-primary/5 rounded-xl border border-primary/10 flex items-center justify-center p-3 relative overflow-hidden group transition-all hover:bg-primary/10">
            {isListening ? (
               <AudioVisualizer amplitude={amplitude} bars={25} className="gap-1 h-8 text-primary" />
            ) : (
               <div className="flex items-center gap-2 text-muted-foreground text-sm">
                  <span className="w-2 h-2 rounded-full bg-muted" /> Microphone off
               </div>
            )}
            
            {/* Status Indicator */}
            <div className={`absolute right-3 top-3 w-2 h-2 rounded-full ${isListening ? 'bg-green-500 shadow-[0_0_8px_#22c55e] animate-pulse' : 'bg-red-500/50'}`} />
         </div>
      </div>

      <p className="text-sm text-muted-foreground px-2 leading-relaxed">
        Speak now to test your input levels. Green bars indicate we can hear you clearly.
      </p>
    </div>
  );
};

const StepModel = ({ 
  language, 
  setLanguage, 
  model, 
  setModel, 
  options 
}: { 
  language: string, 
  setLanguage: (l: string) => void, 
  model: string, 
  setModel: (m: string) => void, 
  options: Options 
}) => (
  <div className="space-y-6 animate-in slide-in-from-bottom-4 duration-500">
    {/* Language */}
    <div className="p-1 rounded-2xl bg-secondary/30 backdrop-blur-sm border border-border/30 focus-within:ring-2 focus-within:ring-primary/20 transition-all">
      <Select value={language} onValueChange={setLanguage}>
        <SelectTrigger className="h-14 text-base bg-transparent border-0 rounded-xl px-4 focus:ring-0 focus:ring-offset-0">
          <span className="flex items-center gap-3 w-full">
            <span className="text-muted-foreground min-w-[80px]">Language:</span>
            <SelectValue />
          </span>
        </SelectTrigger>
        <SelectContent className="border-border/50 bg-popover/95 backdrop-blur-xl shadow-2xl rounded-xl max-h-[280px]">
          {options.languages.map((lang) => (
            <SelectItem key={lang} value={lang} className="py-2.5 rounded-lg cursor-pointer">
              {lang === "auto" ? "Auto-detect" : lang.toUpperCase()}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>

    {/* Models */}
    <div className="space-y-3">
      <div className="flex items-center justify-between px-1">
         <span className="text-sm font-medium text-muted-foreground">Processing Model</span>
         <span className="text-xs text-primary/80 bg-primary/10 px-2 py-0.5 rounded-full">Local Execution</span>
      </div>
      
      <div className="grid grid-cols-2 gap-3" role="radiogroup" aria-label="Select processing model">
        {MODEL_OPTIONS.map((m) => {
           const isActive = model === m.id;
           return (
            <button
              key={m.id}
              type="button"
              role="radio"
              aria-checked={isActive}
              className={`
                relative p-4 rounded-2xl text-left transition-all duration-200 group
                flex flex-col gap-1
                ${isActive
                  ? 'bg-primary/10 border-primary/50 shadow-lg shadow-primary/5'
                  : 'bg-secondary/30 border-border/30 hover:bg-secondary/50 hover:border-primary/20'}
                border
                focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2
              `}
              onClick={() => setModel(m.id)}
            >
              <div className="flex items-center justify-between w-full mb-1">
                <span className={`font-semibold ${isActive ? 'text-primary' : 'text-foreground'}`}>
                  {m.label}
                </span>
                {isActive && <div className="w-2 h-2 rounded-full bg-primary shadow-[0_0_8px_currentColor]" aria-hidden="true" />}
              </div>
              
              <span className="text-xs text-muted-foreground font-medium">{m.detail}</span>
              <span className="text-[10px] text-muted-foreground/60 leading-tight">{m.tradeoff}</span>
            </button>
           );
        })}
      </div>
    </div>
  </div>
);

const StepTheme = ({ 
  theme, 
  setTheme, 
  autoStart, 
  setAutoStart 
}: { 
  theme: Settings["theme"], 
  setTheme: (t: Settings["theme"]) => void, 
  autoStart: boolean, 
  setAutoStart: (b: boolean) => void 
}) => (
  <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
    <fieldset>
      <legend className="text-sm font-medium text-muted-foreground px-1 mb-4">Interface Theme</legend>
      <div className="grid grid-cols-3 gap-4" role="radiogroup" aria-label="Theme selection">
        {THEME_OPTIONS.map((opt) => {
          const isActive = theme === opt.val;
          return (
            <button
              key={opt.val}
              type="button"
              role="radio"
              aria-checked={isActive}
              className={`
                relative p-4 rounded-2xl flex flex-col items-center gap-4 transition-all duration-300
                focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2
                ${isActive
                  ? 'bg-primary/10 border-primary/50 shadow-lg shadow-primary/10 scale-105'
                  : 'bg-secondary/30 border-border/30 hover:bg-secondary/50 hover:border-primary/20'}
                border
              `}
              onClick={() => setTheme(opt.val as Settings['theme'])}
            >
              <div className={`w-10 h-10 rounded-full border-2 shadow-sm transition-transform duration-500 ${isActive ? 'rotate-12' : ''} ${
                opt.val === 'light' ? 'bg-[#f4f4f5] border-gray-200' :
                opt.val === 'dark' ? 'bg-[#18181b] border-gray-800' :
                'bg-gradient-to-br from-[#f4f4f5] to-[#18181b] border-gray-400'
              }`} />
              <span className={`text-sm font-medium ${isActive ? 'text-primary' : 'text-muted-foreground'}`}>{opt.label}</span>
            </button>
          );
        })}
      </div>
    </fieldset>

    <div className="p-5 rounded-2xl bg-secondary/30 backdrop-blur-sm border border-border/30 transition-colors hover:bg-secondary/40">
      <label className="flex items-center justify-between cursor-pointer">
        <div className="space-y-1">
          <span className="block font-medium text-foreground">Auto-start VoiceFlow</span>
          <span className="block text-sm text-muted-foreground">Launch instantly when Windows starts</span>
        </div>
        <Switch checked={autoStart} onCheckedChange={setAutoStart} className="data-[state=checked]:bg-primary" />
      </label>
    </div>
  </div>
);

const StepFinal = () => (
  <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
    <div className="p-8 rounded-3xl bg-primary/5 backdrop-blur-md border border-primary/10 text-center relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent opacity-50" />
      
      <div className="relative z-10">
        <p className="text-xs font-bold text-primary uppercase tracking-widest mb-6">Global Shortcut</p>
        <div className="flex items-center justify-center gap-4 mb-6">
          <kbd className="min-w-[80px] py-3 rounded-xl bg-background border border-border/50 text-2xl font-bold text-foreground shadow-[0_4px_0_0_rgba(0,0,0,0.1)] dark:shadow-[0_4px_0_0_rgba(255,255,255,0.05)] transition-transform active:translate-y-1 active:shadow-none">
            Ctrl
          </kbd>
          <span className="text-xl text-muted-foreground/50">+</span>
          <kbd className="min-w-[80px] py-3 rounded-xl bg-background border border-border/50 text-2xl font-bold text-foreground shadow-[0_4px_0_0_rgba(0,0,0,0.1)] dark:shadow-[0_4px_0_0_rgba(255,255,255,0.05)] transition-transform active:translate-y-1 active:shadow-none">
            Win
          </kbd>
        </div>
        <p className="text-sm text-muted-foreground">
          Hold to record, release to transcribe.
        </p>
      </div>
    </div>

    <p className="text-center text-muted-foreground text-sm">
      VoiceFlow runs quietly in the background. <br/>
      Press the shortcut anytime, anywhere to start dictating.
    </p>
  </div>
);


export function Onboarding() {
  const navigate = useNavigate();
  const [options, setOptions] = useState<Options | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState(0);

  // Form state
  const [language, setLanguage] = useState("auto");
  const [model, setModel] = useState("small");
  const [autoStart, setAutoStart] = useState(true);
  const [retention] = useState(-1);
  const [theme, setTheme] = useState<Settings["theme"]>("system");
  const [microphone, setMicrophone] = useState<number>(0);

  useEffect(() => {
    const load = async () => {
      try {
        setError(null);
        const optionsData = await api.getOptions();
        setOptions(optionsData);
        if (optionsData.microphones.length > 0) {
          setMicrophone(optionsData.microphones[0].id);
        }
      } catch (err) {
        console.error("Failed to load options:", err);
        setError("Failed to load configuration. Please restart the application.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  // Apply theme in real-time
  useEffect(() => {
    const root = document.documentElement;
    let isDark = theme === "system"
      ? window.matchMedia("(prefers-color-scheme: dark)").matches
      : theme === "dark";

    if (isDark) {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
  }, [theme]);

  const handleFinish = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.updateSettings({
        language,
        model,
        autoStart,
        retention,
        theme,
        microphone,
        onboardingComplete: true,
      });
      navigate("/dashboard");
    } catch (err) {
      console.error("Failed to save settings:", err);
      setError("Failed to save settings. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const nextStep = () => setStep((s) => s + 1);
  const prevStep = () => setStep((s) => s - 1);

  // --- Render Steps Logic ---

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden" aria-busy="true">
        <div className="absolute inset-0 overflow-hidden" aria-hidden="true">
          <div className="absolute top-1/4 -left-32 w-96 h-96 bg-primary/20 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-primary/10 rounded-full blur-3xl animate-pulse delay-1000" />
        </div>

        <div className="relative flex flex-col items-center gap-6 z-10">
          <div className="w-16 h-16 rounded-2xl bg-secondary/50 backdrop-blur-xl border border-border/50 flex items-center justify-center shadow-xl">
            <div className="w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
          <div className="text-center space-y-2">
            <p className="text-lg font-medium text-foreground">Initializing VoiceFlow</p>
            <p className="text-sm text-muted-foreground">Preparing your experience...</p>
          </div>
        </div>
      </main>
    );
  }

  if (error && !options) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden">
        <div className="absolute inset-0 overflow-hidden" aria-hidden="true">
           <div className="absolute top-1/3 left-1/4 w-64 h-64 bg-destructive/10 rounded-full blur-3xl" />
        </div>
        
        <div className="relative backdrop-blur-xl bg-card/80 border border-border/50 rounded-3xl p-8 max-w-md text-center shadow-2xl z-10" role="alert">
          <div className="w-14 h-14 rounded-2xl bg-destructive/10 flex items-center justify-center mx-auto mb-6">
            <AlertCircle className="w-7 h-7 text-destructive" aria-hidden="true" />
          </div>
          <h2 className="text-xl font-semibold text-foreground mb-2">Something went wrong</h2>
          <p className="text-muted-foreground mb-6">{error}</p>
          <Button onClick={() => window.location.reload()} className="rounded-xl w-full">
            Try Again
          </Button>
        </div>
      </main>
    );
  }

  if (!options) return null;

  const stepsData = [
    { 
      ...ONBOARDING_STEPS_INFO.welcome, 
      image: HeroImg, 
      component: <StepWelcome /> 
    },
    { 
      ...ONBOARDING_STEPS_INFO.audio, 
      image: MicImg, 
      component: <StepAudio microphone={microphone} setMicrophone={setMicrophone} options={options} /> 
    },
    { 
      ...ONBOARDING_STEPS_INFO.model, 
      image: ModelImg, 
      component: <StepModel language={language} setLanguage={setLanguage} model={model} setModel={setModel} options={options} /> 
    },
    { 
      ...ONBOARDING_STEPS_INFO.theme, 
      image: ThemeImg, 
      component: <StepTheme theme={theme} setTheme={setTheme} autoStart={autoStart} setAutoStart={setAutoStart} /> 
    },
    { 
      ...ONBOARDING_STEPS_INFO.final, 
      image: SuccessImg, 
      component: <StepFinal /> 
    },
  ];

  const currentStep = stepsData[step];
  const isLastStep = step === stepsData.length - 1;

  return (
    <main className="min-h-screen flex bg-background relative overflow-hidden selection:bg-primary/20">
      {/* Ambient background orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
        <div className="absolute -top-[10%] -left-[10%] w-[60%] h-[60%] bg-primary/5 rounded-full blur-[120px] animate-pulse" />
        <div className="absolute top-[40%] -right-[10%] w-[50%] h-[50%] bg-primary/3 rounded-full blur-[100px]" />
        <div className="absolute bottom-[-10%] left-[20%] w-[40%] h-[40%] bg-secondary/80 rounded-full blur-[80px]" />
      </div>

      {/* Error toast */}
      {error && options && (
        <div role="alert" className="fixed top-6 left-1/2 -translate-x-1/2 z-50 backdrop-blur-xl bg-destructive/10 border border-destructive/20 text-destructive px-6 py-3 rounded-full flex items-center gap-3 shadow-lg animate-in slide-in-from-top-4">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span className="text-sm font-medium">{error}</span>
        </div>
      )}

      {/* Left side: Full-bleed image (45% for better balance) */}
      <div className="hidden lg:block w-[45%] relative overflow-hidden">
        {stepsData.map((s, idx) => (
            <img
            key={s.id}
            src={s.image}
            alt=""
            role="presentation"
            className={`
                absolute inset-0 w-full h-full object-cover transition-all duration-700 ease-in-out
                ${idx === step ? 'opacity-100 scale-100' : 'opacity-0 scale-105'}
            `}
            />
        ))}
        {/* Overlay gradient for text readability if needed, though pure image is preferred usually */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent to-background/5" />
      </div>

      {/* Right side: Content */}
      <div className="flex-1 flex flex-col relative z-10">
        
        {/* Top Navigation / Progress */}
        <div className="absolute top-0 left-0 right-0 p-8 flex justify-between items-center">
             {/* Progress Dots */}
             <div className="flex gap-3">
                {stepsData.map((_, idx) => (
                    <div 
                        key={idx} 
                        className={`h-1.5 rounded-full transition-all duration-500 ease-out ${idx <= step ? 'w-8 bg-primary' : 'w-2 bg-muted-foreground/20'}`} 
                    />
                ))}
            </div>
            {/* Skip button logic could go here */}
        </div>


        <div className="flex-1 flex items-center justify-center p-8 lg:p-16">
            <section className="w-full max-w-lg space-y-8 animate-in fade-in zoom-in-95 duration-500 key={step}">
                <header className="space-y-3">
                    <span className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-primary/10 text-primary font-bold text-sm mb-4">
                        {step + 1}
                    </span>
                    <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground">
                        {currentStep.title}
                    </h1>
                    <p className="text-lg md:text-xl text-muted-foreground font-light leading-relaxed">
                        {currentStep.subtitle}
                    </p>
                </header>

                <div className="min-h-[320px]">
                    {currentStep.component}
                </div>

                <footer className="flex items-center gap-4 pt-8 border-t border-border/20">
                    <Button
                        variant="ghost"
                        size="lg"
                        onClick={prevStep}
                        disabled={step === 0}
                        className={`
                            rounded-xl text-muted-foreground hover:text-foreground hover:bg-secondary/50 px-6
                            ${step === 0 ? 'opacity-0 pointer-events-none' : 'opacity-100'}
                        `}
                    >
                        <ArrowLeft className="mr-2 w-4 h-4" />
                        Back
                    </Button>

                    <button
                        type="button"
                        onClick={isLastStep ? handleFinish : nextStep}
                        disabled={saving}
                        className="
                        ml-auto group relative h-14 px-10
                        rounded-2xl font-semibold text-base
                        bg-primary text-primary-foreground
                        shadow-[0_4px_20px_-4px_rgba(var(--primary),0.4)]
                        hover:shadow-[0_8px_30px_-4px_rgba(var(--primary),0.5)]
                        hover:-translate-y-0.5
                        active:translate-y-0
                        transition-all duration-300
                        flex items-center gap-3
                        disabled:opacity-70 disabled:cursor-not-allowed
                        overflow-hidden
                        "
                    >
                        <span className="relative z-10 flex items-center gap-2">
                            {saving ? (
                                <>
                                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                Processing...
                                </>
                            ) : isLastStep ? (
                                <>
                                Get Started
                                <Check className="w-5 h-5" />
                                </>
                            ) : (
                                <>
                                Continue
                                <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
                                </>
                            )}
                        </span>
                        
                        {/* Shimmer effect */}
                        <div className="absolute inset-0 -translate-x-[100%] group-hover:animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/20 to-transparent z-0" />
                    </button>
                </footer>
            </section>
        </div>
      </div>

      {/* Mobile Background Image Fallback */}
      <div className="lg:hidden fixed bottom-0 left-0 right-0 h-1/3 pointer-events-none z-0 opacity-20">
        <div className="absolute inset-0 bg-gradient-to-t from-background to-transparent z-10" />
        <img
          src={currentStep.image}
          alt=""
          className="w-full h-full object-cover"
        />
      </div>
    </main>
  );
}
