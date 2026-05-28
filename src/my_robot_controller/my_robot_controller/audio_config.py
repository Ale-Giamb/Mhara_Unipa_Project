"""
Configurazione per la gestione dell'input audio.
Consente di scegliere tra:
- Microfono del robot Pepper
- Microfono del PC
"""

import os
from enum import Enum
from pathlib import Path

class AudioSource(Enum):
    """Sorgenti audio disponibili"""
    PEPPER_MICROPHONE = "pepper"  # Microfono di Pepper (default)
    PC_MICROPHONE = "pc"           # Microfono del PC

class AudioConfig:
    """
    Configurazione centralizzata per l'audio.
    Carica le impostazioni da variabili d'ambiente o file di configurazione.
    """
    
    # Sorgente audio predefinita
    DEFAULT_SOURCE = AudioSource.PC_MICROPHONE
    
    # Configurazione directory per file audio
    AUDIO_DIR = Path(os.path.expanduser("~/Scrivania/mhara_env/MHARA_Unipa/src/audio"))
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    # File audio temporaneo per registrazioni del PC
    PC_RECORDING_FILE = AUDIO_DIR / "recording.wav"
    
    # Parametri audio
    SAMPLE_RATE = 16000  # Hz (16 kHz)
    CHANNELS = 1         # Mono
    DURATION = 10        # Secondi massimi di registrazione
    CHUNK_SIZE = 1024    # Dimensione chunk per streaming
    
    # Formato audio
    AUDIO_FORMAT = "wav"
    
    def __init__(self, audio_source: AudioSource = None):
        """
        Inizializza la configurazione audio.
        
        Args:
            audio_source: Sorgente audio (PEPPER_MICROPHONE o PC_MICROPHONE)
                         Se None, usa DEFAULT_SOURCE
        """
        self.audio_source = audio_source or self.load_from_env()
        
    @classmethod
    def load_from_env(cls) -> AudioSource:
        """Carica la sorgente audio dalle variabili d'ambiente"""
        source = os.getenv("AUDIO_SOURCE", "pepper").lower()
        
        if source == "pc":
            return AudioSource.PC_MICROPHONE
        elif source == "pepper":
            return AudioSource.PEPPER_MICROPHONE
        else:
            # Fallback alla sorgente predefinita
            return cls.DEFAULT_SOURCE
    
    @classmethod
    def set_source_from_env(cls, source: str):
        """
        Imposta la sorgente audio tramite variabile d'ambiente.
        
        Usage:
            os.environ["AUDIO_SOURCE"] = "pc"
            AudioConfig.set_source_from_env("pc")
        """
        os.environ["AUDIO_SOURCE"] = source.lower()
    
    def get_source_name(self) -> str:
        """Restituisce il nome della sorgente audio attuale"""
        if self.audio_source == AudioSource.PEPPER_MICROPHONE:
            return "Microfono Pepper"
        else:
            return "Microfono PC"
    
    def is_pepper_source(self) -> bool:
        """Verifica se la sorgente è il microfono di Pepper"""
        return self.audio_source == AudioSource.PEPPER_MICROPHONE
    
    def is_pc_source(self) -> bool:
        """Verifica se la sorgente è il microfono del PC"""
        return self.audio_source == AudioSource.PC_MICROPHONE
    
    def switch_source(self, source: AudioSource):
        """Cambia la sorgente audio"""
        self.audio_source = source
        os.environ["AUDIO_SOURCE"] = source.value
    
    @classmethod
    def to_pepper(cls):
        """Cambio rapido a microfono Pepper"""
        cls.set_source_from_env("pepper")
    
    @classmethod
    def to_pc(cls):
        """Cambio rapido a microfono PC"""
        cls.set_source_from_env("pc")
    
    def __repr__(self) -> str:
        return f"AudioConfig(source={self.get_source_name()})"


# Istanza globale di configurazione audio
audio_config = AudioConfig()
