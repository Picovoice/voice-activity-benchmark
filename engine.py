#
# Copyright 2021-2025 Picovoice Inc.
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
import pvcobra
import webrtcvad

from mixer import DEFAULT_SAMPLERATE


class Engines(Enum):
    WEBRTC = 'WebRTC'
    COBRA = 'Cobra'


ThresholdInfo = namedtuple('ThresholdInfo', 'min, max, step')


class Engine(object):
    def process(self, pcm, frame_key):
        raise NotImplementedError()

    def release(self):
        raise NotImplementedError()

    def __str__(self):
        raise NotImplementedError()

    @staticmethod
    def threshold_info(engine_type):
        if engine_type is Engines.COBRA:
            return ThresholdInfo(0.0, 1.0, 0.005)
        elif engine_type is Engines.WEBRTC:
            return ThresholdInfo(0, 3, 1)
        else:
            raise ValueError("no threshold range for '%s'", engine_type.value)

    @staticmethod
    def create(engine, threshold, **kwargs):
        if engine is Engines.COBRA:
            if "access_key" not in kwargs:
                TypeError("Cobra missing kwarg 'access_key'")
            return CobraEngine(threshold, kwargs['access_key'])
        elif engine is Engines.WEBRTC:
            return WebRTCEngine(threshold)
        else:
            ValueError("cannot create engine of type '%s'", engine.value)


class CobraEngine(Engine):
    cache = dict()

    def __init__(self, threshold, access_key):
        self._cobra = pvcobra.create(access_key=access_key)
        self._threshold = threshold

    def process(self, pcm, frame_key):
        assert pcm.dtype == np.int16

        if frame_key in self.cache:
            voice_probability = self.cache[frame_key]
        else:
            voice_probability = self._cobra.process(pcm)
            self.cache[frame_key] = voice_probability

        return voice_probability >= self._threshold

    def frame_length(self):
        return self._cobra.frame_length

    def release(self):
        self._cobra.delete()

    def __str__(self):
        return 'Cobra'


class WebRTCEngine(Engine):
    _FRAME_SEC = 0.03

    def __init__(self, threshold):
        self._vad = webrtcvad.Vad(int(threshold))

    def process(self, pcm, frame_key):
        assert pcm.dtype == np.int16

        return self._vad.is_speech(pcm.tobytes(), DEFAULT_SAMPLERATE)

    def frame_length(self):
        return int((DEFAULT_SAMPLERATE * self._FRAME_SEC))

    def release(self):
        pass

    def __str__(self):
        return 'WebRTC'
