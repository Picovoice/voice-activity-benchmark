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

import os

import matplotlib.pyplot as plt
from matplotlib.ticker import (AutoMinorLocator, MultipleLocator)

from engine import Engines


def plot_roc_chart(save_to_file=None):
    engine_true_detects = dict([(e.value, [1]) for e in Engines])
    engine_false_alarms = dict([(e.value, [1]) for e in Engines])

    for engine in Engines:
        engine = engine.value
        file_name = os.path.join(os.path.dirname(__file__), 'benchmark_%s.csv' % engine)
        if not os.path.exists(file_name):
            print(f"WARNING: {file_name} does not exist. Skipping engine {engine}")
            continue

        with open(file_name, 'r') as f:
            for line in f.readlines():
                true_detect, false_alarm = [float(x) for x in line.strip('\n').split(', ')]
                engine_true_detects[engine].append(true_detect)
                engine_false_alarms[engine].append(false_alarm)

        engine_true_detects[engine].append(0)
        engine_false_alarms[engine].append(0)

    fig, ax = plt.subplots()
    for engine in Engines:
        engine = engine.value
        ax.plot(engine_false_alarms[engine], engine_true_detects[engine])

    ax.plot(ax.get_xlim(), ax.get_ylim(), ls="--", c=".3")

    ax.legend([e.value for e in Engines])

    ax.set_title('ROC for VAD Engines')
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")

    ax.set_ylim(0, 1)
    ax.set_xlim(0, 1)

    ax.xaxis.set_major_locator(MultipleLocator(0.1))
    ax.yaxis.set_major_locator(MultipleLocator(0.1))
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.grid(which='major', color='#CCCCCC', linestyle='--')
    ax.grid(which='minor', color='#CCCCCC', linestyle=':')

    fig.tight_layout()

    if save_to_file is not None:
        plt.savefig(save_to_file)
        print(f'ROC chart saved to {save_to_file}')
    else:
        plt.show()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('save_to_file_name', nargs='?', default=None, help='Save the plot to a file instead of showing it (optional)')
    args = parser.parse_args()
    plot_roc_chart(args.save_to_file_name)
