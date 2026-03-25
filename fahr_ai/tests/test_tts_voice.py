import unittest
import asyncio
import base64
from unittest.mock import patch, MagicMock
from fahr_ai.modules.tts_voice import TTSVoiceAgent

class TestTTSVoiceAgent(unittest.TestCase):
    def setUp(self):
        # Mock KPipeline to match your snippet's behavior
        self.pipeline_patcher = patch('kokoro.KPipeline')
        self.mock_kpipeline = self.pipeline_patcher.start()
        
        # Setup mock generator with same output format as your snippet
        self.mock_generator = MagicMock()
        self.mock_generator.__next__.return_value = (0, 0, b'mock_audio_data')
        self.mock_kpipeline.return_value.return_value = self.mock_generator
        
        self.agent = TTSVoiceAgent()
        
    def tearDown(self):
        self.pipeline_patcher.stop()
    
    def run_async(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)
    
    def test_voice_output(self):
        """Test exact behavior from your snippet"""
        result = self.run_async(self.agent.run({
            'outputType': 'voice',
            'history': [
                {'type': 'human', 'content': 'Hello'},
                {'type': 'ai', 'content': 'Test response'}
            ]
        }))
        
        # Verify same pipeline call as your snippet
        self.mock_kpipeline.assert_called_once_with(lang_code='en')
        self.mock_kpipeline.return_value.assert_called_once_with(
            'Test response', 
            voice='en_default'
        )
        
        # Verify output format
        self.assertEqual(result['status'], 'success')
        audio_data = base64.b64decode(result['output']['audio_data'])
        self.assertEqual(audio_data, b'mock_audio_data')
        self.assertEqual(result['output']['sample_rate'], 24000)
    
    def test_non_voice_output(self):
        result = self.run_async(self.agent.run({
            'outputType': 'text',
            'history': []
        }))
        self.assertEqual(result['status'], 'skipped')

def manual_test():
    """Direct port of your working snippet into agent format"""
    from IPython.display import display, Audio
    
    print("=== MANUAL TEST (Matches your snippet exactly) ===")
    agent = TTSVoiceAgent(voice_profile='af_heart')  # Matching your voice
    
    # Your exact text
    text = '''
    [Kokoro](/kˈOkəɹO/) is an open-weight TTS model... 
    '''
    
    # Simulate agent processing
    state = {
        'outputType': 'voice',
        'history': [
            {'type': 'human', 'content': 'Prompt'},
            {'type': 'ai', 'content': text}
        ]
    }
    
    result = asyncio.run(agent.run(state))
    audio_data = base64.b64decode(result['output']['audio_data'])
    
    # Display exactly like your snippet
    display(Audio(data=audio_data, rate=24000, autoplay=True))
    print("Output:", result['output'].keys())  # Show available keys

if __name__ == "__main__":
    unittest.main()
    # manual_test()  # Uncomment to run your snippet-equivalent test