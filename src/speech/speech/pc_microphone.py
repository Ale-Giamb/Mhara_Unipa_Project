"""
Modulo per la registrazione audio dal microfono del PC.
Utilizza sounddevice e soundfile per catturare l'audio.
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
from pathlib import Path
from .audio_config import AudioConfig
import logging

class PCMicrophoneRecorder:
    """
    Registra audio dal microfono del PC in formato WAV.
    """
    
    def __init__(self, logger=None):
        """
        Inizializza il registratore audio del PC.
        
        Args:
            logger: Logger ROS (opzionale, per logging)
        """
        self.logger = logger
        self.config = AudioConfig()
        self.is_recording = False
        self.recording_data = None
        
    def log(self, message: str, level: str = "info"):
        """Log message appropriato"""
        if self.logger:
            if level == "info":
                self.logger.info(f"[PC_MIC] {message}")
            elif level == "warn":
                self.logger.warn(f"[PC_MIC] {message}")
            elif level == "error":
                self.logger.error(f"[PC_MIC] {message}")
        else:
            print(f"[PC_MIC] {message}")
    
    def record_audio(self, duration: int = None, output_file: Path = None) -> Path:
        """
        Registra audio dal microfono del PC.
        
        Args:
            duration: Durata della registrazione in secondi (default: DURATION)
            output_file: Path del file di output (default: PC_RECORDING_FILE)
            
        Returns:
            Path del file WAV registrato
        """
        if duration is None:
            duration = AudioConfig.DURATION
        
        if output_file is None:
            output_file = AudioConfig.PC_RECORDING_FILE
        else:
            output_file = Path(output_file)
        
        try:
            self.log(f"Avvio registrazione da microfono PC ({duration}s)...")
            self.is_recording = True
            
            # Registra audio
            audio_data = sd.rec(
                int(duration * AudioConfig.SAMPLE_RATE),
                samplerate=AudioConfig.SAMPLE_RATE,
                channels=AudioConfig.CHANNELS,
                dtype=np.int16,
                blocksize=AudioConfig.CHUNK_SIZE
            )
            
            # Attendi la fine della registrazione
            sd.wait()
            
            # Salva il file
            sf.write(str(output_file), audio_data, AudioConfig.SAMPLE_RATE)
            
            self.is_recording = False
            self.recording_data = audio_data
            
            self.log(f"✓ Registrazione completata: {output_file}", "info")
            
            return output_file
            
        except Exception as e:
            self.is_recording = False
            self.log(f"✗ Errore nella registrazione: {str(e)}", "error")
            raise
    
    def record_with_detection(self, max_duration: int = None, 
                             silence_threshold: float = 0.02) -> Path:
        """
        Registra audio fino al rilevamento del silenzio.
        Simile al comportamento di Pepper che si ferma quando non sente più audio.
        
        Args:
            max_duration: Durata massima in secondi
            silence_threshold: Soglia di ampiezza per rilevare il silenzio
            
        Returns:
            Path del file WAV registrato
        """
        if max_duration is None:
            max_duration = AudioConfig.DURATION
        
        try:
            self.log(f"Avvio registrazione con rilevamento silenzio (max {max_duration}s, threshold={silence_threshold})...")
            self.is_recording = True
            
            frames = []
            silence_frames = 0
            max_silence_frames = int(AudioConfig.SAMPLE_RATE * 1.5)  # 1.5 secondi di silenzio
            max_frames = int(max_duration * AudioConfig.SAMPLE_RATE)
            
            # Calibrazione iniziale - misura il rumore di fondo
            self.log("Calibrazione rumore di fondo...", "info")
            initial_frames = []
            with sd.InputStream(
                samplerate=AudioConfig.SAMPLE_RATE,
                channels=AudioConfig.CHANNELS,
                blocksize=AudioConfig.CHUNK_SIZE,
                dtype=np.int16
            ) as stream:
                # Raccogliere 0.5 secondi per calibrazione
                for _ in range(int(0.5 * AudioConfig.SAMPLE_RATE / AudioConfig.CHUNK_SIZE)):
                    chunk, _ = stream.read(AudioConfig.CHUNK_SIZE)
                    initial_frames.append(chunk)
            
            # Calcola RMS medio dei frame iniziali
            calibration_rms = np.sqrt(np.mean(
                np.concatenate(initial_frames, axis=0).astype(np.float32) ** 2
            ))
            self.log(f"Livello background: {calibration_rms:.6f}", "info")
            
            # Usa una soglia più intelligente: 2x il background noise
            adaptive_threshold = max(calibration_rms * 2, 0.005)
            self.log(f"Soglia adattiva: {adaptive_threshold:.6f}", "info")
            
            # Stream di registrazione
            with sd.InputStream(
                samplerate=AudioConfig.SAMPLE_RATE,
                channels=AudioConfig.CHANNELS,
                blocksize=AudioConfig.CHUNK_SIZE,
                dtype=np.int16
            ) as stream:
                self.log("▶ Registrazione in corso... parla adesso!", "info")
                has_detected_audio = False
                
                while len(frames) < max_frames and self.is_recording:
                    # Leggi chunk
                    chunk, _ = stream.read(AudioConfig.CHUNK_SIZE)
                    frames.append(chunk)
                    
                    # Calcola RMS (ampiezza) del chunk
                    rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
                    
                    # Se c'è audio sopra la soglia
                    if rms > adaptive_threshold:
                        if not has_detected_audio:
                            self.log("🎙 Audio rilevato, continuo la registrazione...", "info")
                            has_detected_audio = True
                        silence_frames = 0
                    else:
                        # Silenzio rilevato
                        if has_detected_audio:
                            silence_frames += AudioConfig.CHUNK_SIZE
                            if silence_frames > max_silence_frames:
                                self.log("⏹ Silenzio rilevato, stop registrazione", "info")
                                break
            
            # Combina i frame
            audio_data = np.concatenate(frames, axis=0) if frames else np.array([], dtype=np.int16)
            
            output_file = AudioConfig.PC_RECORDING_FILE
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Salva il file
            sf.write(str(output_file), audio_data, AudioConfig.SAMPLE_RATE)
            
            self.is_recording = False
            self.recording_data = audio_data
            
            duration_recorded = len(audio_data) / AudioConfig.SAMPLE_RATE
            self.log(f"✓ Registrazione completata: {output_file} ({duration_recorded:.2f}s, {len(audio_data)} samples)", "info")
            
            return output_file
            
        except Exception as e:
            self.is_recording = False
            self.log(f"✗ Errore nella registrazione: {str(e)}", "error")
            raise
    
    def stop_recording(self):
        """Ferma la registrazione"""
        self.is_recording = False
        self.log("Registrazione interrotta dall'utente", "info")
    
    def get_last_recording(self) -> Path:
        """Restituisce il path dell'ultima registrazione"""
        return AudioConfig.PC_RECORDING_FILE
    
    def list_microphones(self) -> list:
        """Elenca i microfoni disponibili sul PC"""
        try:
            devices = sd.query_devices()
            microphones = []
            
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    microphones.append({
                        'index': i,
                        'name': device['name'],
                        'channels': device['max_input_channels']
                    })
            
            return microphones
        except Exception as e:
            self.log(f"Errore nel listare microfoni: {str(e)}", "error")
            return []
    
    def set_microphone(self, device_index: int):
        """
        Imposta il microfono da utilizzare.
        
        Args:
            device_index: Indice del dispositivo (da list_microphones())
        """
        try:
            sd.default.device = device_index
            self.log(f"Microfono impostato su: {sd.query_devices(device_index)['name']}", "info")
        except Exception as e:
            self.log(f"Errore nell'impostare il microfono: {str(e)}", "error")
            raise


# Istanza globale del registratore
_recorder = None

def get_pc_recorder(logger=None) -> PCMicrophoneRecorder:
    """Singleton per il registratore PC"""
    global _recorder
    if _recorder is None:
        _recorder = PCMicrophoneRecorder(logger)
    return _recorder
