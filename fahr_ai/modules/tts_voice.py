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
import requests
import logging
import  os 

os.environ['NO_PROXY'] = '10.254.115.17, 10.254.140.69'
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSVoiceProcessor():
    """TTS agent with HTTP endpoint fallback to local processing"""
    
    def __init__(self, endpoint_url: str = "http://10.254.140.69:443/api/tts/convert", timeout: int = 30):
        self.endpoint_url = endpoint_url
        self.timeout = timeout
        
        # Initialize local TTS models (lazy loading)
        self._kokoro_tts = None
        self._xtts_v2_tts = None
        self._avatar_profiles = None
        self._device = "cuda" if torch.cuda.is_available() else "cpu"

    def _load_local_models(self):
        """Lazy load local TTS models only when needed"""
        if self._avatar_profiles is None:
            with open("./configs/avatar_profiles.json", "r") as f:
                self._avatar_profiles = json.load(f)

        if self._kokoro_tts is None:
            self._kokoro_tts = KPipeline(lang_code='a')
            
        if self._xtts_v2_tts is None:
            self._xtts_v2_tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self._device)

    def run(self, text: str, avatarId: int = 0, messageId: str = None) -> Dict:
        """
        Main method that tries HTTP endpoint first, then falls back to local processing
        """
        # First, try the HTTP endpoint
        try:
            result = self._try_http_endpoint(text, avatarId, messageId)
            if result['status'] == 'success':
                logger.info("Successfully processed via HTTP endpoint")
                return result
        except Exception as e:
            # logger.warning(f"HTTP endpoint failed: {str(e)}, falling back to local processing")
            pass

        # Fallback to local processing
        logger.info("Using local TTS processing")
        return self._process_locally(text, avatarId)

    def _try_http_endpoint(self, text: str, avatarId: int, messageId: str = None) -> Dict:
        """Try to process TTS via HTTP endpoint"""
        # Load avatar profiles to get gender and language info
        if self._avatar_profiles is None:
            with open("./configs/avatar_profiles.json", "r") as f:
                self._avatar_profiles = json.load(f)
        
        avatar_prof = self._avatar_profiles["profiles"].get(str(avatarId), self._avatar_profiles["profiles"]["0"])
        
        payload = {
            "avaterId": avatarId,
            "messageId": messageId or f"msg_{avatarId}_{hash(text) % 10000}",
            "text": text,
            "gender": avatar_prof.get("gender", "female"),
            "language": avatar_prof.get("language", "en")
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            self.endpoint_url,
            json=payload,
            headers=headers,
            timeout=self.timeout
        )
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Check if the response contains the expected audio data
            if 'audio_base64' in response_data:
                return {
                    'status': 'success',
                    'output': response_data,
                    'source': 'http_endpoint'
                }
            else:
                raise Exception(f"Invalid response format from endpoint: {response_data}")
        else:
            raise Exception(f"HTTP {response.status_code}: {response.text}")

    def _process_locally(self, text: str, avatarId: int) -> Dict:
        """Fallback local processing using original logic"""
        try:
            # Load models if not already loaded
            self._load_local_models()
            
            avatar_prof = self._avatar_profiles["profiles"].get(str(avatarId), self._avatar_profiles["profiles"]["0"])
            language = avatar_prof.get("language", "en")
            model_name = avatar_prof.get("model", "kokoro")
            gender = avatar_prof.get("gender", "female")
            voice = avatar_prof.get("avaterName", "af_heart")
            
            if model_name == "kokoro":
                base64_audio = self._process_kokoro(text, voice)
            elif model_name == "xtts_v2":
                base64_audio = self._process_xtts_v2(text, voice)
            else:
                raise Exception(f"Unknown model: {model_name}")
            
            return {
                'status': 'success',
                'output': {
                    "audio_base64": base64_audio,
                    "content_type": "wav"
                },
                'source': 'local_processing'
            }
            
        except Exception as e:
            return {
                'status': 'error', 
                'message': str(e),
                'source': 'local_processing'
            }
        
    def _process_kokoro(self, text: str, speaker: str) -> str:
        """Process text using Kokoro TTS"""
        generator = self._kokoro_tts(text, voice=speaker)

        all_audio = []            
        for _, _, audio in generator:
            all_audio.append(audio)

        if all_audio:
            full_audio = torch.cat(all_audio, dim=0).cpu().numpy()
            
            audio_buffer = io.BytesIO()
            sf.write(audio_buffer, full_audio, 24000, format='WAV')
            audio_buffer.seek(0)
            
            base64_audio = base64.b64encode(audio_buffer.read()).decode('utf-8')
            return base64_audio
        else:
            raise Exception("No audio generated from Kokoro")

    def _process_xtts_v2(self, text: str, speaker: str) -> str:
        """Process text using XTTS v2"""
        audio = self._xtts_v2_tts.tts(
            text=text,
            speaker=speaker,
            language="ar"
        )
        
        if isinstance(audio, torch.Tensor):
            audio = audio.cpu().numpy()
        
        sample_rate = self._xtts_v2_tts.synthesizer.output_sample_rate
        
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, audio, sample_rate, format='WAV')
        audio_buffer.seek(0)
        
        base64_audio = base64.b64encode(audio_buffer.read()).decode('utf-8')
        return base64_audio

    def set_endpoint_url(self, url: str):
        """Update the endpoint URL"""
        self.endpoint_url = url

    def set_timeout(self, timeout: int):
        """Update the request timeout"""
        self.timeout = timeout

if __name__ == "__main__":
    # Example usage
    text_en = '''
        [Kokoro](/kˈOkəɹO/) is an open-weight TTS model with 82 million parameters. 
        Despite its lightweight architecture, it delivers comparable quality to larger models while being significantly faster
        and more cost-efficient. With Apache-licensed weights, [Kokoro](/kˈOkəɹO/) 
        can be deployed anywhere from production environments to personal projects.
    '''
    text_ar = '''   
        هي خدمة تُقدَّم للجهات الاتحادية أو المحلية المعنية بالمتاحف والآثار،
        وتهدف إلى تسجيل القطع الأثرية القادمة من دول أخرى
        من أجل منحها الحصانة والحماية القانونية طوال فترة وجودها داخل الدولة،
        وذلك لأغراض مثل العرض المؤقت، البحث، أو التبادل الثقافي
    '''
    
    # Initialize with custom endpoint and timeout
    ttsagent = TTSVoiceProcessor(
        endpoint_url="http://10.254.140.69:443/api/tts/convert",
        timeout=30
    )
    
    # Process English text
    print("Processing English text...")
    en_result = ttsagent.run(text_en, avatarId=2, messageId="msg_en_123")
    # print(f"English processing status: {en_result['status']}")
    # if en_result['status'] == 'success':
    #     print(f"English processed via: {en_result.get('source', 'unknown')}")
    # else:
    #     print(f"English processing error: {en_result.get('message', 'unknown error')}")
    
    # Process Arabic text
    print("\nProcessing Arabic text...")
    ar_result = ttsagent.run(text_ar, avatarId=0, messageId="msg_ar_123")
    print(f"Arabic processing status: {ar_result['status']}")
    if ar_result['status'] == 'success':
        print(f"Arabic processed via: {ar_result.get('source', 'unknown')}")
    else:
        print(f"Arabic processing error: {ar_result.get('message', 'unknown error')}")

    # Save audio files if successful
    if en_result['status'] == 'success':
        decoded_audio = base64.b64decode(en_result["output"]["audio_base64"])
        with open('en_decoded_audio.wav', 'wb') as f:
            f.write(decoded_audio)
        print("English Audio file saved as 'en_decoded_audio.wav'")

    if ar_result['status'] == 'success':
        decoded_audio = base64.b64decode(ar_result["output"]["audio_base64"])
        with open('ar_decoded_audio.wav', 'wb') as f:
            f.write(decoded_audio)
        print("Arabic Audio file saved as 'ar_decoded_audio.wav'")