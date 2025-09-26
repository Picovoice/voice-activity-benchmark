# Voice Activity Benchmark

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/Picovoice/voice-activity-benchmark/blob/master/LICENSE)

Made in Vancouver, Canada by [Picovoice](https://picovoice.ai)

The purpose of this benchmarking framework is to provide a scientific comparison between different voice activity
engines in terms of accuracy metrics. While working on [Cobra](https://github.com/Picovoice/Cobra),
we noted that there is a need for such a tool to empower customers to make data-driven decisions.


# Data

[LibriSpeech](http://www.openslr.org/12/) (test_clean portion) is used as the voice dataset.
It can be downloaded from [OpenSLR](http://www.openslr.org/resources/12/test-clean.tar.gz).

In order to simulate real-world situations, the data is mixed with noise (at 0dB SNR). For this purpose, we use the
[DEMAND](https://pubs.aip.org/asa/poma/article/19/1/035081/838946/The-Diverse-Environments-Multi-channel-Acoustic) dataset, which has noise recording in 18 different
environments (e.g. kitchen, office, traffic, etc.). Recordings containing distinct voice data are filtered out.
It can be downloaded from [Kaggle](https://www.kaggle.com/datasets/aanhari/demand-dataset).


# Voice Activity Engines

Three voice-activity engines are used:
- [py-webrtcvad](https://github.com/wiseman/py-webrtcvad) (Python bindings to the WEBRTC VAD),
which can be installed using [PyPI](https://pypi.org/project/webrtcvad/).
- [Cobra](https://github.com/Picovoice/Cobra), which is included as submodules in this repository.
- [Silero VAD](https://github.com/snakers4/silero-vad), which can be installed using [PyPI](https://pypi.org/project/silero-vad/). Version 5.1.


# Metric

We measured the accuracy of the voice activity engines using false positive and true positive rates.
The false positive rate is measured as the number of false positive frames detected over the total number of non-voice frames.
Likewise, true positive rate is measured as the number of true positive frames detected over the total number of voice-frames.
Using these definitions, we plot a receiver operating characteristic curve which can be used to characterize performance differences between engines.


# Usage

### Prerequisites

The benchmark has been developed on Ubuntu 18.04 with Python 3.8. Clone the repository using

```bash
git clone https://github.com/Picovoice/voice-activity-benchmark.git
```

Make sure the Python packages in the [requirements.txt](requirements.txt) are properly installed for your Python
version as Python bindings are used for running the engines.

### Running the Benchmark

Usage information can be retrieved via

```bash
python benchmark.py -h
```

The runtime benchmark for C is contained in the [runtime](runtime) folder. Use the following commands to build and run the runtime benchmark:
```bash
git clone --recursive https://github.com/Picovoice/cobra.git runtime/cobra
cmake -S runtime -B runtime/build && cmake --build runtime/build
./runtime/build/cobra_runtime -l {COBRA_LIBRARY_PATH} -a {ACCESS_KEY} -w {TEST_WAVFILE_PATH}
```

The runtime benchmark for Python can be run with the following command:
```bash
python3 -m runtime.runtime_test --wav_path {TEST_WAVFILE_PATH} --engine {"Cobra" | "Silero" | "WebRTC"} --access_key {ACCESS_KEY}
```

# Results

## Accuracy

Below is the result of running the benchmark framework. The plots below shows the receiver operating characteristic curve
of different engines. The top shows the overall graph. The bottom shows the top-left corner with a minimum true-positive rate of 50% and a maximum false-positive rate of 5%. The plots were generated with a signal-to-noise ratio of 0dB.

![](doc/img/summary.png)
![](doc/img/zoomed.png)


## Runtime

On a Raspberry Pi Zero, Cobra measured a realtime factor of `0.05`, or about `5%` CPU usage.
On a laptop with an Intel(R) Core(TM) i7-1185G7, Cobra measured a realtime factor of `0.0006`.
On an Ubuntu 22.04 machine with AMD CPU (`AMD Ryzen 9 5900X (12) @ 3.70GHz`), the following RTFs were recorded:
![](doc/img/rtf.png)

