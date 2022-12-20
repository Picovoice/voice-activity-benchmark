#
# Copyright 2021-2022 Picovoice Inc.
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

from dataset import *
from engine import *
from mixer import create_test_files, AudioLabels, DEFAULT_FRAME_LEN

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)


def run_threshold(pcm, labels, engine_type, threshold, access_key):
    detector = Engine.create(engine_type, threshold=threshold, access_key=access_key)

    frame_length = detector.frame_length()
    num_frames = pcm.size // frame_length

    num_detect_frames = 0
    num_silence_frames = 0
    num_true_detects = 0
    num_false_alarms = 0

    for i in range(num_frames):
        frame = pcm[(i * frame_length):((i + 1) * frame_length)]
        label_idx = round((i * frame_length) / DEFAULT_FRAME_LEN)

        is_speech_truth = int(labels[label_idx])
        is_speech = detector.process(frame, '%d-%d' % (i, frame_length))

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

    false_alarm_rate = num_false_alarms / num_silence_frames
    true_detect_rate = num_true_detects / num_detect_frames

    logging.info(
        '[%s - %.4f] tdr: %f far: %f' % (engine_type.value, threshold, true_detect_rate, false_alarm_rate))

    return true_detect_rate, false_alarm_rate


def run(engine_type, speech_path, label_path, access_key):
    pcm, sample_rate = soundfile.read(speech_path, dtype=np.int16)
    assert sample_rate == Dataset.sample_rate()

    with open(label_path, 'r') as f:
        labels = f.read().strip('\n ').split('\n')

    res = list()
    threshold_info = Engine.threshold_info(engine_type)
    for threshold in np.arange(threshold_info.min, threshold_info.max + threshold_info.step, threshold_info.step):
        res.append((threshold, run_threshold(pcm, labels, engine_type, threshold, access_key)))

    return res


def save(results):
    for engine, result in results:
        path = os.path.join(os.path.dirname(__file__), 'benchmark_%s.csv' % engine.value)
        with open(path, 'w') as f:
            for threshold in sorted(result.keys()):
                true_detect_rate, false_alarm_rate = result[threshold]
                f.write('%f, %f\n' % (true_detect_rate, false_alarm_rate))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--librispeech_dataset_path', required=True)
    parser.add_argument('--demand_dataset_path', required=True)
    parser.add_argument('--engine', choices=[x.value for x in Engines])
    parser.add_argument('--access_key', default=None)

    args = parser.parse_args()

    access_key = args.access_key

    speech_dataset = Dataset.create(Datasets.LIBRI_SPEECH, args.librispeech_dataset_path)
    logging.info('loaded librispeech dataset with %d examples' % speech_dataset.size())

    noise_dataset = Dataset.create(Datasets.DEMAND, args.demand_dataset_path)
    logging.info('loaded demand dataset with %d examples' % noise_dataset.size())

    speech_path = os.path.join(os.path.dirname(__file__), 'benchmark_speech.wav')
    label_path = os.path.join(os.path.dirname(__file__), 'benchmark_labels.txt')

    if not os.path.exists(speech_path) or not os.path.exists(label_path):
        create_test_files(
            speech_path=speech_path,
            label_path=label_path,
            speech_dataset=speech_dataset,
            noise_dataset=noise_dataset)

    res = run(
        engine_type=Engines(args.engine),
        speech_path=speech_path,
        label_path=label_path,
        access_key=access_key)

    with open(os.path.join(os.path.dirname(__file__), f'benchmark_{args.engine}.csv'), 'w') as f:
        for threshold, (true_detect_rate, false_alarm_raet) in res:
            f.write(f"{true_detect_rate}, {false_alarm_raet}\n")


if __name__ == '__main__':
    main()
