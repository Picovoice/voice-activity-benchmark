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

from enum import Enum

import numpy as np
import soundfile

from dataset import Dataset

DEFAULT_SAMPLERATE = 16000
DEFAULT_FRAME_LEN = 512
SILENCE_SEC = 20
SILENCE_SAMPLES = DEFAULT_FRAME_LEN * ((SILENCE_SEC * DEFAULT_SAMPLERATE) // DEFAULT_FRAME_LEN)
SILENCE_FRAMES = SILENCE_SAMPLES // DEFAULT_FRAME_LEN


class AudioLabels(Enum):
    SILENCE = 0
    UNKNOWN = 1
    VOICE = 2


def _max_abs(x):
    return max(np.max(x), np.abs(np.min(x)))


def _mix_noise(speech_parts, noise_dataset):
    speech_length = sum(len(x) for x in speech_parts)

    noise_parts = list()
    while sum(x.size for x in noise_parts) < speech_length:
        x = noise_dataset.random(dtype=np.float32)
        noise_parts.append(x / _max_abs(x))

    res = np.concatenate(noise_parts)[:speech_length]

    start_index = 0
    for speech_part in speech_parts:
        end_index = start_index + len(speech_part)
        speech_scale = 1 / _max_abs(speech_part) if _max_abs(speech_part) > 0 else 0
        res[start_index:end_index] += speech_part * speech_scale
        start_index = end_index

    return res


def _energy_detect_speech_frames(pcm, voice_threshold=1e-2, silence_threshold=5e-4, radius=5):
    pcm = np.copy(pcm)
    pcm[0] = 0
    pcm[1:] = pcm[1:] - 0.97 * pcm[:-1]

    pcm = pcm[DEFAULT_FRAME_LEN:]

    num_frames = pcm.size // DEFAULT_FRAME_LEN
    frames = pcm[:num_frames * DEFAULT_FRAME_LEN].reshape((num_frames, DEFAULT_FRAME_LEN)).astype(np.float64)
    powers = (frames ** 2).sum(axis=1)
    powers /= powers.max()

    labels = np.ones_like(powers, dtype=np.int16) * AudioLabels.UNKNOWN.value
    labels[np.where(powers >= voice_threshold)] = AudioLabels.VOICE.value
    labels[np.where(powers <= silence_threshold)] = AudioLabels.SILENCE.value

    for x in range(len(labels)):
        if labels[x] == AudioLabels.VOICE.value:
            for y in range(radius):
                if x + y < len(labels):
                    if labels[x + y] != AudioLabels.VOICE.value:
                        labels[x + y] = AudioLabels.UNKNOWN.value
                if x - y >= 0:
                    if labels[x - y] != AudioLabels.VOICE.value:
                        labels[x - y] = AudioLabels.UNKNOWN.value

    return labels


def _assemble_speech(speech_dataset):
    speech_parts = list()
    speech_frames = list()

    silence_pcm = np.array([np.int16(0)] * SILENCE_SAMPLES)
    silence_frames = np.array([np.int16(0)] * SILENCE_FRAMES)

    for idx in range(0, speech_dataset.size()):
        pcm = speech_dataset.get(idx)
        if len(pcm) % DEFAULT_FRAME_LEN:
            pcm = pcm[:-(len(pcm) % DEFAULT_FRAME_LEN)]
        detected_speech_frames = _energy_detect_speech_frames(pcm=pcm)
        pcm = pcm[DEFAULT_FRAME_LEN:]
        assert len(pcm) == (len(detected_speech_frames) * DEFAULT_FRAME_LEN)
        speech_parts.append(pcm)
        speech_frames = np.append(speech_frames, detected_speech_frames)

        speech_parts.append(silence_pcm)
        speech_frames = np.append(speech_frames, silence_frames)

    return speech_parts, speech_frames


def create_test_files(
        speech_path,
        label_path,
        speech_dataset,
        noise_dataset):
    speech_parts, speech_frames = _assemble_speech(speech_dataset)
    speech = _mix_noise(speech_parts, noise_dataset)
    speech /= _max_abs(speech)

    soundfile.write(speech_path, speech, samplerate=Dataset.sample_rate())

    with open(label_path, 'w') as f:
        for frame_label in speech_frames:
            f.write('%d\n' % frame_label)
