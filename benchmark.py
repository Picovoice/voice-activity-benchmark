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

import argparse
import logging
import multiprocessing
import soundfile

from dataset import *
from engine import *
from mixer import create_test_files, AudioLabels


logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)


access_key = None


def run_threshold(pcm, speech_frames, engine_type, threshold):
    detector = Engine.create(engine_type, threshold=threshold, access_key=access_key)

    frame_length = detector.frame_length()
    num_frames = pcm.size // frame_length

    num_detect_frames = 0
    num_silence_frames = 0
    num_true_detects = 0
    num_false_alarms = 0

    for i in range(num_frames):
        frame = pcm[(i * frame_length):((i + 1) * frame_length)]
        speech_frame = ((i * frame_length) + (frame_length // 2)) // 512

        is_speech_truth = int(speech_frames[speech_frame])
        is_speech = detector.process(frame, f'{i}-{frame_length}')

        if is_speech_truth == AudioLabels.VOICE.value:
            num_detect_frames += 1
        elif is_speech_truth == AudioLabels.SILENCE.value:
            num_silence_frames += 1

        if is_speech and is_speech_truth == AudioLabels.VOICE.value:
            num_true_detects += 1
        elif is_speech and is_speech_truth == AudioLabels.SILENCE.value:
            num_false_alarms += 1

        if i % (num_frames // 100) == 0:
            logging.debug(f"{engine_type} {threshold} {i}/{num_frames}")

    detector.release()

    pcm_length_frames = pcm.size / detector.frame_length()
    false_alarm_rate = num_false_alarms / num_silence_frames
    true_detect_rate = num_true_detects / num_detect_frames

    logging.info(
        '[%s - %.4f] tdr: %f far: %f' % (engine_type.value, threshold, true_detect_rate, false_alarm_rate))

    return true_detect_rate, false_alarm_rate


def run(engine_type, speech_path, label_path):
    pcm, sample_rate = soundfile.read(speech_path, dtype=np.int16)
    assert sample_rate == Dataset.sample_rate()

    speech_frames = list()
    with open(label_path, 'r') as f:
        for line in f.readlines():
            speech_frames.append(line.strip('\n'))

    threshold_info = Engine.threshold_info(engine_type)
    threshold = threshold_info.min

    res = dict()
    while threshold <= threshold_info.max:
        res[threshold] = run_threshold(pcm, speech_frames, engine_type, threshold)
        threshold += threshold_info.step

    return engine_type, res


def save(results):
    for engine, result in results:
        path = os.path.join(os.path.dirname(__file__), 'cobra_%s.csv' % (engine.value))
        with open(path, 'w') as f:
            for threshold in sorted(result.keys()):
                true_detect_rate, false_alarm_rate = result[threshold]
                f.write('%f, %f\n' % (true_detect_rate, false_alarm_rate))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--access_key', required=True)
    parser.add_argument('--librispeech_dataset_path', required=True)
    parser.add_argument('--demand_dataset_path', required=True)

    args = parser.parse_args()

    global access_key
    access_key = args.access_key

    speech_dataset = Dataset.create(Datasets.LIBRI_SPEECH, args.librispeech_dataset_path)
    logging.info('loaded librispeech dataset with %d examples' % speech_dataset.size())

    noise_dataset = Dataset.create(Datasets.DEMAND, args.demand_dataset_path)
    logging.info('loaded demand dataset with %d examples' % noise_dataset.size())

    speech_path = os.path.join(os.path.dirname(__file__), 'cobrabm_speech.wav')
    label_path = os.path.join(os.path.dirname(__file__), 'cobrabm_labels.txt')
    create_test_files(
        speech_path=speech_path,
        label_path=label_path,
        speech_dataset=speech_dataset,
        noise_dataset=noise_dataset)

    with multiprocessing.Pool() as pool:
        save(pool.starmap(run, [(x, speech_path, label_path) for x in Engines]))

if __name__ == '__main__':
    main()
