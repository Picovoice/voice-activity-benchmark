#
# Copyright 2021 Picovoice Inc.
#
# You may not use this file except in compliance with the license.
# A copy of the license is located in the "LICENSE" file accompanying this source.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#

from collections import namedtuple
from enum import Enum

import numpy as np

from mixer import DEFAULT_SAMPLERATE


ThresholdInfo = namedtuple('ThresholdInfo', 'min, max, step')

class Engines(Enum):
    COBRA = 'Cobra'
    SILERO = 'Silero'
    WEBRTC = 'WebRTC'

engine_create_map = {
    Engines.COBRA: lambda threshold, access_key, **kwargs: CobraEngine(threshold, access_key),
    Engines.SILERO: lambda threshold, **kwargs: SileroEngine(threshold),
    Engines.WEBRTC: lambda threshold, **kwargs: WebRTCEngine(threshold),
}

threshold_info_map = {
    Engines.COBRA: ThresholdInfo(0.0, 1.0, 0.001),
    Engines.SILERO: ThresholdInfo(0.0, 1.0, 0.001),
    Engines.WEBRTC: ThresholdInfo(0, 3, 1),
}


class Engine(object):
    def process(self, pcm, frame_key):
        raise NotImplementedError()

    def frame_length(self):
        raise NotImplementedError()

    def release(self):
        raise NotImplementedError()

    def __str__(self):
        return self.__class__.__name__

    @staticmethod
    def threshold_info(engine_type):
        if engine_type in threshold_info_map:
            return threshold_info_map[engine_type]
        else:
            raise ValueError("no threshold range for '%s'", engine_type.value)

    @staticmethod
    def create(engine, threshold, **kwargs):
        if engine in engine_create_map:
            return engine_create_map[engine](threshold, **kwargs)
        else:
            raise ValueError("cannot create engine of type '%s'", engine.value)


class CobraEngine(Engine):
    _cache = dict()

    def __init__(self, threshold, access_key):
        import pvcobra
        self._cobra = pvcobra.Cobra(access_key=access_key, library_path=pvcobra.LIBRARY_PATH)
        self._threshold = threshold

    def process(self, pcm, frame_key):
        assert pcm.dtype == np.int16

        if frame_key in self._cache:
            voice_probability = self._cache[frame_key]
        else:
            voice_probability = self._cobra.process(pcm)
            self._cache[frame_key] = voice_probability

        return voice_probability >= self._threshold

    def frame_length(self):
        return self._cobra.frame_length

    def release(self):
        self._cobra.delete()


class SileroEngine(Engine):
    _cache = dict()

    def __init__(self, threshold):
        from silero_vad import load_silero_vad
        self._model = load_silero_vad(onnx=True)
        self._threshold = threshold
        import torch
        self._torch = torch

    def process(self, pcm, frame_key):
        assert pcm.dtype == np.int16

        if frame_key in self._cache:
            voice_probability = self._cache[frame_key]
        else:
            pcm_float = pcm.astype(np.float32) / 32768.0
            voice_probability = self._model(self._torch.from_numpy(pcm_float), DEFAULT_SAMPLERATE).item()
            self._cache[frame_key] = voice_probability

        return (voice_probability >= self._threshold)

    def frame_length(self):
        assert DEFAULT_SAMPLERATE in (16000, 8000)
        return 512 if DEFAULT_SAMPLERATE == 16000 else 256

    def release(self):
        del self._model


class WebRTCEngine(Engine):
    _FRAME_SEC = 0.03

    def __init__(self, threshold):
        import webrtcvad
        self._vad = webrtcvad.Vad(int(threshold))

    def process(self, pcm, frame_key):
        assert pcm.dtype == np.int16

        return self._vad.is_speech(pcm.tobytes(), DEFAULT_SAMPLERATE)

    def frame_length(self):
        return int((DEFAULT_SAMPLERATE * self._FRAME_SEC))

    def release(self):
        del self._vad
