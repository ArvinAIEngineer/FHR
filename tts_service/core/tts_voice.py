import base64
from typing import Dict
from kokoro import KPipeline
import soundfile as sf
import torch
import io
from typing import List, Literal 
import numpy as np
from TTS.api import TTS
import json
import sys
# Add the current directory to sys.path
sys.path.append("./")
class TTSVoiceProcessor():
    """Pure in-memory TTS agent matching your working snippet"""
    
    def __init__(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        with open("./configs.json", "r") as f:
            self.avatar_profiles: dict = json.load(f)

        # init tts models
        self.Kokoro_tts = KPipeline(lang_code='a')
        self.xtts_v2_tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

    def run(self, text: str, avatarId:int = 0) -> Dict:

        avatar_prof =  self.avatar_profiles["profiles"].get(str(avatarId), "0")
        language = avatar_prof.get("language", "en")
        model_name = avatar_prof.get("model", "kokoro")
        gender = avatar_prof.get("gender", "female")
        voice = avatar_prof.get("avaterName", "af_heart")
        try:       
            if model_name == "kokoro":
                base64_audio = self.process_kokoro(text, voice)
            elif model_name == "xtts_v2":
                base64_audio = self.process_xtts_v2(text, voice)                
            
            return {
                'status': 'success',
                'output': {
                    "audio_base64": base64_audio,
                    "content_type": "wav"
                }
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
        
    def process_kokoro(self, text:str, speaker:str, ):
        # Generate audio using same pipeline logic
        generator = self.Kokoro_tts(text, voice=speaker)

        # Create a list to store all audio chunks
        all_audio = []            
        # Collect all audio chunks
        for _, _, audio in generator:
            all_audio.append(audio)

        # Concatenate all audio chunks into a single array
        if all_audio:
            full_audio = torch.cat(all_audio, dim=0).cpu().numpy()
            
            # Convert audio to WAV format in memory
            audio_buffer = io.BytesIO()
            sf.write(audio_buffer, full_audio, 24000, format='WAV')
            audio_buffer.seek(0)
            
            # Convert to base64
            base64_audio = base64.b64encode(audio_buffer.read()).decode('utf-8')
        return base64_audio

    def process_xtts_v2(self, text:str, speaker:str):        
        # Generate audio in memory (returns numpy array)
        audio = self.xtts_v2_tts.tts(
            text=text,
            speaker=speaker,
            language="ar"
        )
        
        # Convert to numpy array if it's not already
        if isinstance(audio, torch.Tensor):
            audio = audio.cpu().numpy()
        
        # Get sample rate from the model
        sample_rate = self.xtts_v2_tts.synthesizer.output_sample_rate
        
        # Convert audio to WAV format in memory
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, audio, sample_rate, format='WAV')
        audio_buffer.seek(0)
        
        # Convert to base64
        base64_audio = base64.b64encode(audio_buffer.read()).decode('utf-8')
        
        return base64_audio
    
if __name__ == "__main__":
   
    # Example usage
    text_en = '''
        [Kokoro](/kˈOkəɹO/) is an open-weight TTS model with 82 million parameters. 
        Despite its lightweight architecture, it delivers comparable quality to larger models while being significantly faster
        and more cost-efficient. With Apache-licensed weights, [Kokoro](/kˈOkəɹO/) 
        can be deployed anywhere from production environments to personal projects.
    '''
    text_ar = '''   
        هي خدمة تُقدَّم للجهات الاتحادية أو المحلية المعنية بالمتاحف والآثار،
        وتهدف إلى تسجيل القطع الأثرية القادمة من دول أخرى
        من أجل منحها الحصانة والحماية القانونية طوال فترة وجودها داخل الدولة،
        وذلك لأغراض مثل العرض المؤقت، البحث، أو التبادل الثقافي
    '''
    ttsagent = TTSVoiceProcessor()
    en_base64_audio = ttsagent.run(text_en, 2)
    ar_base64_audio = ttsagent.run(text_ar, 0)

    # If you want to save the base64 string to a file
    # with open('audio_base64.txt', 'w') as f:
    #     f.write(base64_audio)
    
    print("Base64 audio generated successfully!")
    # print(ar_base64_audio["message"])
    # If you want to decode and save the audio file for testing
    if en_base64_audio:
        decoded_audio = base64.b64decode(en_base64_audio["output"]["audio_base64"])
        with open('en_decoded_audio.wav', 'wb') as f:
            f.write(decoded_audio)
        print("English Audio file saved as 'en_decoded_audio.wav'")

    if ar_base64_audio["status"] == "success":
        decoded_audio = base64.b64decode(ar_base64_audio["output"]["audio_base64"])
        with open('ar_decoded_audio.wav', 'wb') as f:
            f.write(decoded_audio)
        print("Arabic Audio file saved as 'ar_decoded_audio.wav'")
