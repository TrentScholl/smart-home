import logging
import voluptuous as vol

from homeassistant.components.tts import Provider, PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv

import site
import importlib
import pkg_resources

_LOGGER = logging.getLogger(__name__)
REQUIREMENTS = ['grpcio==1.11.0', 'google-api-core==1.1.1', 'google-auth==1.4.1', 'google-cloud-texttospeech==0.1.0']

CONF_VOICE_NAME = 'voice_name'
CONF_SPEAKING_RATE = 'speaking_rate'
CONF_PITCH = 'pitch'
CONF_ENCODING = 'encoding'
CONF_INPUT = 'input'

SUPPORTED_OPTIONS = [
    CONF_VOICE_NAME,
    CONF_SPEAKING_RATE,
    CONF_PITCH,
    CONF_ENCODING,
    CONF_INPUT
]

SUPPORTED_ENCODINGS = ['LINEAR16', 'MP3', 'OGG_OPUS']

SUPPORTED_VOICE_NAMES = ['nl-NL-Standard-A', 'en-AU-Standard-A', 'en-AU-Standard-B', 'en-AU-Standard-C',
                        'en-AU-Standard-D', 'en-GB-Standard-A', 'en-GB-Standard-B', 'en-GB-Standard-C',
                        'en-GB-Standard-D', 'en-US-Wavenet-A', 'en-US-Wavenet-B', 'en-US-Wavenet-C',
                        'en-US-Wavenet-D', 'en-US-Wavenet-E', 'en-US-Wavenet-F', 'en-US-Standard-B',
                        'en-US-Standard-C', 'en-US-Standard-D', 'en-US-Standard-E', 'fr-FR-Standard-C',
                        'fr-FR-Standard-D', 'fr-CA-Standard-A', 'fr-CA-Standard-B', 'fr-CA-Standard-C',
                        'fr-CA-Standard-D', 'de-DE-Standard-A', 'de-DE-Standard-B', 'ja-JP-Standard-A',
                        'pt-BR-Standard-A', 'es-ES-Standard-A', 'sv-SE-Standard-A', 'tr-TR-Standard-A']

SUPPORTED_INPUTS = ['text', 'ssml']

ENCODING_EXTENSIONS = {
    'LINEAR16': 'wav',
    'MP3': 'mp3',
    'OGG_OPUS': 'ogg'
}

DEFAULT_ENCODING = 'MP3'

DEFAULT_VOICE_NAME = 'en-US-Wavenet-E'

DEFAULT_SPEAKING_RATE = 1.0

DEFAULT_PITCH = 0.0

DEFAULT_INPUT = 'text'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_VOICE_NAME, default=DEFAULT_VOICE_NAME): vol.In(SUPPORTED_VOICE_NAMES),
    vol.Optional(CONF_SPEAKING_RATE, default=DEFAULT_SPEAKING_RATE): vol.All(vol.Coerce(float), vol.Range(-20.0, 20.0)),
    vol.Optional(CONF_PITCH, default=DEFAULT_PITCH): vol.All(vol.Coerce(float), vol.Range(-20.0, 20.0)),
    vol.Optional(CONF_ENCODING, default=DEFAULT_ENCODING): vol.In(SUPPORTED_ENCODINGS),
    vol.Optional(CONF_INPUT, default=DEFAULT_INPUT): vol.In(SUPPORTED_INPUTS),
})

def get_engine(hass, config):
    # pylint: disable=import-error
    from google.oauth2 import service_account

    credentials = service_account.Credentials.from_service_account_file(hass.config.path('google-cloud.json'))

    from google.cloud import texttospeech

    google_cloud_tts_client = texttospeech.TextToSpeechClient(credentials=credentials)

    return GoogleCloudSpeechProvider(google_cloud_tts_client, config)

class GoogleCloudSpeechProvider(Provider):
    def __init__(self, google_cloud_tts_client, config):
        self.client = google_cloud_tts_client
        self.config = config
        self.name = 'Google Cloud TTS'

    @property
    def supported_languages(self):
        return 'None'

    @property
    def supported_options(self):
        """Return list of supported options."""
        return SUPPORTED_OPTIONS

    def get_tts_audio(self, message, language=None, options=None):
        from google.cloud import texttospeech

        if self.config[CONF_INPUT] == "ssml":
            input_text = texttospeech.types.SynthesisInput(ssml=message)
        else:
            input_text = texttospeech.types.SynthesisInput(text=message)

        voice = texttospeech.types.VoiceSelectionParams(name=self.config[CONF_VOICE_NAME])

        audio_config = texttospeech.types.AudioConfig(
            speaking_rate=self.config[CONF_SPEAKING_RATE],
            pitch=self.config[CONF_PITCH],
            audio_encoding=self.config[CONF_ENCODING])

        resp = self.client.synthesize_speech(input_text, voice, audio_config)

        return (ENCODING_EXTENSIONS[self.config[CONF_ENCODING]], resp.audio_content)
