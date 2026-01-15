# Baseline Resource Usage Measurements

**Date:** 2026-01-15
**Purpose:** Document pre-optimization resource usage to measure improvement after implementing lazy loading
**Status:** Baseline (Before Optimization)

## Measurement Environment

### System Configuration
- **OS:** Windows
- **Measurement Tool:** `scripts/measure_idle_resources.py` (psutil-based)
- **Measurement Duration:** 30 seconds per test
- **Test Conditions:** Application idle in system tray, no active recording

### Application Configuration
- **Whisper Model:** tiny (default)
- **Device:** auto (resolves to CPU on most systems)
- **Model Loading Strategy:** Eager loading (model loaded at startup)
- **Model Location:** HuggingFace cache directory

## Current Implementation Behavior

### Startup Behavior
The current implementation uses **eager loading**:
1. Application starts
2. Model is loaded in background thread during `AppController.initialize()`
3. Model remains in memory throughout application lifetime
4. First transcription is instant (no loading delay)

### Resource Implications
- ✅ **Pro:** Zero-latency first transcription
- ❌ **Con:** Model occupies memory even when idle
- ❌ **Con:** Background loading thread uses CPU during startup
- ❌ **Con:** Constant memory footprint regardless of usage

## Baseline Measurements

### Expected Resource Usage (Pre-Optimization)

Based on the current eager loading implementation:

| Metric | Expected Value | Target (Post-Optimization) | Status |
|--------|---------------|---------------------------|---------|
| **Idle CPU** | 0-2% | <1% | ⚠️ May exceed target |
| **Idle Memory (Model Loaded)** | 200-400 MB | <100 MB (unloaded) | ❌ Exceeds target |
| **Model Size on Disk** | ~75 MB (tiny) | Same | N/A |
| **Model Size in Memory** | ~150-200 MB (tiny) | 0 MB when idle | ❌ Always loaded |
| **First Transcription Latency** | <500ms | 2-5 seconds (acceptable) | ✅ Currently instant |

### Model Size Reference

Different models have different memory footprints:

| Model | Disk Size | Memory Usage (Loaded) | Speed | Quality |
|-------|-----------|----------------------|-------|---------|
| tiny | ~75 MB | ~150-200 MB | Fastest | Good |
| base | ~145 MB | ~250-350 MB | Fast | Better |
| small | ~466 MB | ~600-800 MB | Medium | Best (practical) |
| medium | ~1.5 GB | ~1.8-2.2 GB | Slow | Excellent |
| large-v3 | ~3 GB | ~3.5-4.5 GB | Slowest | Best |

## Measurement Procedure

### Running Baseline Measurements

To collect baseline data on a running VoiceFlow instance:

1. **Start VoiceFlow:**
   ```bash
   pnpm run dev
   ```

2. **Wait for startup to complete:**
   - Wait 30 seconds after launch for model to load
   - Verify model is loaded (check logs for "Model loaded successfully")

3. **Measure idle resources:**
   ```bash
   uv run python scripts/measure_idle_resources.py --duration 30
   ```

4. **Record results:**
   - Average CPU %
   - Maximum CPU %
   - Average Memory MB
   - Maximum Memory MB

5. **Monitor system behavior:**
   - Check Task Manager for fan activity
   - Note any background CPU spikes
   - Verify memory remains constant

### Test Scenarios

#### Scenario 1: Fresh Startup (Idle)
- **Condition:** App just started, model loaded, no user interaction
- **Duration:** 30 seconds
- **Expected:** High memory (model loaded), minimal CPU

#### Scenario 2: Post-Transcription Idle
- **Condition:** After 1 transcription, waiting in idle state
- **Duration:** 60 seconds
- **Expected:** High memory (model loaded), minimal CPU

#### Scenario 3: Extended Idle
- **Condition:** No activity for 10+ minutes
- **Duration:** 30 seconds
- **Expected:** High memory (model loaded), minimal CPU

## Actual Measurements

### Test Run 1: Fresh Startup (Date: TBD)

```
Measurement Duration: 30 seconds
Samples Collected: 30

CPU Usage:
  Average: ____ %
  Maximum: ____ %

Memory Usage:
  Average: ____ MB
  Maximum: ____ MB

Target Goals:
  CPU: <1% (Current avg: ____ %)
  Status: [ ] PASS / [ ] FAIL

  Memory: <100MB (Current avg: ____ MB)
  Status: [ ] PASS / [ ] FAIL
```

### Test Run 2: Post-Transcription (Date: TBD)

```
[To be filled in after running actual measurements]
```

### Test Run 3: Extended Idle (Date: TBD)

```
[To be filled in after running actual measurements]
```

## Analysis

### Current State Summary

**Before Optimization:**
- Model loading strategy: Eager (load at startup)
- Idle memory usage: ___ MB (expected 200-400 MB with tiny model)
- Idle CPU usage: ___ % (expected <2%)
- First transcription latency: <500ms (instant)

### Known Issues
1. **High idle memory:** Model stays in memory even when not in use
2. **Battery drain:** Constant memory pressure may prevent system sleep optimizations
3. **Laptop fans:** Memory usage may cause thermal management to activate

### Optimization Goals

After implementing lazy loading (Phase 2-3), we expect:
- ✅ Idle memory: <100 MB (model unloaded)
- ✅ Idle CPU: <1%
- ⚠️ First transcription: 2-5 seconds (acceptable trade-off)
- ✅ Subsequent transcriptions: <500ms (while model loaded)
- ✅ Auto-unload after 5 minutes idle (configurable)

## Next Steps

1. ✅ Document baseline measurements (this file)
2. ⏳ Implement lazy loading system (Phase 2)
3. ⏳ Switch to lazy loading by default (Phase 3)
4. ⏳ Measure optimized performance (Phase 4)
5. ⏳ Compare before/after results (`optimization_results.md`)

## References

- Measurement script: `scripts/measure_idle_resources.py`
- Resource monitor service: `src-pyloid/services/resource_monitor.py`
- Transcription service: `src-pyloid/services/transcription.py`
- Implementation plan: `.auto-claude/specs/001-minimal-idle-resource-usage/implementation_plan.json`

---

**Note:** This document will be updated with actual measurements once baseline tests are run on a live VoiceFlow instance. The optimization results will be documented in a separate file (`optimization_results.md`) for comparison.
