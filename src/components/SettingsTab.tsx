import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Globe, Mic, Cpu, Zap, Clock, Palette, FolderOpen, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import type { Settings, Options } from "@/lib/types";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

export function SettingsTab() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [options, setOptions] = useState<Options | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      const [settingsData, optionsData] = await Promise.all([
        api.getSettings(),
        api.getOptions(),
      ]);
      setSettings(settingsData);
      setOptions(optionsData);
    } catch (error) {
      console.error("Failed to load settings:", error);
      setError("Failed to load settings. Please try again.");
      toast.error("Failed to load settings");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const updateSetting = async <K extends keyof Settings>(
    key: K,
    value: Settings[K]
  ) => {
    if (!settings) return;

    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);

    try {
      await api.updateSettings({ [key]: value });
      toast.success("Settings saved");
    } catch (error) {
      console.error("Failed to update setting:", error);
      toast.error("Failed to save settings");
      // Revert on error
      setSettings(settings);
    }
  };

  // Apply theme
  useEffect(() => {
    if (!settings) return;

    const root = document.documentElement;
    let isDark = false;

    if (settings.theme === "system") {
      isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    } else {
      isDark = settings.theme === "dark";
    }

    if (isDark) {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
  }, [settings?.theme]);

  if (loading) {
    return <div className="text-center py-8 text-muted-foreground">Loading...</div>;
  }

  if (error || !settings || !options) {
    return (
      <div className="p-4 md:p-8 max-w-5xl mx-auto">
        <div className="text-center py-20 border-2 border-dashed border-destructive/30 rounded-xl bg-destructive/5" role="alert">
          <p className="text-destructive font-medium">{error || "Failed to load settings"}</p>
          <button
            className="mt-4 px-4 py-2 text-sm font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
            onClick={loadSettings}
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  const retentionEntries = Object.entries(options.retentionOptions);

  return (
    <div className="p-4 md:p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-foreground/90">Settings</h1>
        <p className="text-muted-foreground mt-1">Configure your transcription experience</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Language */}
          <Card className="border-none shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="pb-3 flex flex-row items-center gap-4 space-y-0">
                <div className="p-2 bg-primary/10 rounded-lg">
                    <Globe className="h-5 w-5 text-primary" />
                </div>
                <div>
                    <CardTitle className="text-base">Language</CardTitle>
                    <CardDescription>Target language for transcription</CardDescription>
                </div>
            </CardHeader>
            <CardContent>
              <Select
                value={settings.language}
                onValueChange={(value) => updateSetting("language", value)}
              >
                <SelectTrigger className="h-11 rounded-lg border-input/50 bg-background/50 backdrop-blur-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {options.languages.map((lang) => (
                    <SelectItem key={lang} value={lang}>
                      {lang === "auto" ? "Auto-detect" : lang.toUpperCase()}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          {/* Model */}
          <Card className="border-none shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="pb-3 flex flex-row items-center gap-4 space-y-0">
                <div className="p-2 bg-primary/10 rounded-lg">
                    <Cpu className="h-5 w-5 text-primary" />
                </div>
                <div>
                    <CardTitle className="text-base">AI Model</CardTitle>
                    <CardDescription>Balance between speed and accuracy</CardDescription>
                </div>
            </CardHeader>
            <CardContent>
              <Select
                value={settings.model}
                onValueChange={(value) => updateSetting("model", value)}
              >
                <SelectTrigger className="h-11 rounded-lg border-input/50 bg-background/50 backdrop-blur-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {options.models.map((model) => (
                    <SelectItem key={model} value={model}>
                      {model.charAt(0).toUpperCase() + model.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          {/* Microphone */}
          <Card className="border-none shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="pb-3 flex flex-row items-center gap-4 space-y-0">
                <div className="p-2 bg-primary/10 rounded-lg">
                    <Mic className="h-5 w-5 text-primary" />
                </div>
                <div>
                    <CardTitle className="text-base">Microphone</CardTitle>
                    <CardDescription>Input device for voice capture</CardDescription>
                </div>
            </CardHeader>
            <CardContent>
              <Select
                value={String(settings.microphone)}
                onValueChange={(value) => updateSetting("microphone", Number(value))}
              >
                <SelectTrigger className="h-11 rounded-lg border-input/50 bg-background/50 backdrop-blur-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="-1">Default System Mic</SelectItem>
                  {options.microphones.map((mic) => (
                    <SelectItem key={mic.id} value={String(mic.id)}>
                      {mic.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          {/* Theme */}
          <Card className="border-none shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="pb-3 flex flex-row items-center gap-4 space-y-0">
                <div className="p-2 bg-primary/10 rounded-lg">
                    <Palette className="h-5 w-5 text-primary" />
                </div>
                <div>
                    <CardTitle className="text-base">Appearance</CardTitle>
                    <CardDescription>Customize UI theme</CardDescription>
                </div>
            </CardHeader>
            <CardContent>
              <Select
                value={settings.theme}
                onValueChange={(value) => updateSetting("theme", value as Settings["theme"])}
              >
                <SelectTrigger className="h-11 rounded-lg border-input/50 bg-background/50 backdrop-blur-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {options.themeOptions.map((theme) => (
                    <SelectItem key={theme} value={theme}>
                      {theme.charAt(0).toUpperCase() + theme.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          {/* History Retention */}
          <Card className="border-none shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="pb-3 flex flex-row items-center gap-4 space-y-0">
                <div className="p-2 bg-primary/10 rounded-lg">
                    <Clock className="h-5 w-5 text-primary" />
                </div>
                <div>
                    <CardTitle className="text-base">History</CardTitle>
                    <CardDescription>Data retention period</CardDescription>
                </div>
            </CardHeader>
            <CardContent>
              <Select
                value={String(settings.retention)}
                onValueChange={(value) => updateSetting("retention", Number(value))}
              >
                <SelectTrigger className="h-11 rounded-lg border-input/50 bg-background/50 backdrop-blur-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {retentionEntries.map(([label, days]) => (
                    <SelectItem key={days} value={String(days)}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

           {/* Auto-start */}
          <Card className="border-none shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="pb-3 flex flex-row items-center gap-4 space-y-0">
                <div className="p-2 bg-primary/10 rounded-lg">
                    <Zap className="h-5 w-5 text-primary" />
                </div>
                <div>
                    <CardTitle className="text-base">System</CardTitle>
                    <CardDescription>Startup behavior</CardDescription>
                </div>
            </CardHeader>
            <CardContent className="flex items-center justify-between pt-1">
                 <Label htmlFor="auto-start" className="font-normal text-muted-foreground">Start with Windows</Label>
                 <Switch
                  id="auto-start"
                  checked={settings.autoStart}
                  onCheckedChange={(checked) => updateSetting("autoStart", checked)}
                />
            </CardContent>
          </Card>

           {/* Data Management */}
           <Card className="border-none shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="pb-3 flex flex-row items-center gap-4 space-y-0">
                <div className="p-2 bg-primary/10 rounded-lg">
                    <FolderOpen className="h-5 w-5 text-primary" />
                </div>
                <div>
                    <CardTitle className="text-base">Data Management</CardTitle>
                    <CardDescription>Access local application data</CardDescription>
                </div>
            </CardHeader>
            <CardContent>
                <button
                    onClick={() => api.openDataFolder()}
                    className="w-full flex items-center justify-center gap-2 h-11 rounded-lg border-2 border-dashed border-input/50 hover:border-primary/50 hover:bg-primary/5 transition-all text-sm font-medium text-muted-foreground hover:text-primary"
                >
                    <FolderOpen className="w-4 h-4" />
                    Open Data Folder
                </button>
            </CardContent>
          </Card>

          {/* Delete All Data */}
          <Card className="border-none shadow-sm hover:shadow-md transition-shadow border-destructive/20">
            <CardHeader className="pb-3 flex flex-row items-center gap-4 space-y-0">
                <div className="p-2 bg-destructive/10 rounded-lg">
                    <Trash2 className="h-5 w-5 text-destructive" />
                </div>
                <div>
                    <CardTitle className="text-base text-destructive">Danger Zone</CardTitle>
                    <CardDescription>Permanently delete all data</CardDescription>
                </div>
            </CardHeader>
            <CardContent>
                <AlertDialog>
                    <AlertDialogTrigger asChild>
                        <button
                            className="w-full flex items-center justify-center gap-2 h-11 rounded-lg border-2 border-dashed border-destructive/30 hover:border-destructive hover:bg-destructive/5 transition-all text-sm font-medium text-destructive/70 hover:text-destructive"
                        >
                            <Trash2 className="w-4 h-4" />
                            Delete All Data
                        </button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                        <AlertDialogHeader>
                            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                            <AlertDialogDescription>
                                This will permanently delete all your transcription history, settings, and preferences.
                                You will need to complete the onboarding process again. This action cannot be undone.
                            </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                onClick={async () => {
                                    try {
                                        await api.resetAllData();
                                        toast.success("All data deleted - returning to setup");
                                        // Reload - the router will redirect to onboarding since onboardingComplete is now false
                                        setTimeout(() => {
                                            window.location.hash = "/";
                                            window.location.reload();
                                        }, 500);
                                    } catch (error) {
                                        console.error("Failed to delete data:", error);
                                        toast.error("Failed to delete data");
                                    }
                                }}
                            >
                                Delete Everything
                            </AlertDialogAction>
                        </AlertDialogFooter>
                    </AlertDialogContent>
                </AlertDialog>
            </CardContent>
          </Card>
      </div>
    </div>
  );
}
