How to use it
---

1. Verify python 3 installation and ffmpeg
3. `python3 main.py <ontology_class_names>` just outputs ids and child ids
1. `python3 main.py <ontology_class_names> --output-csv` saves filtered csv files
5. `python3 main.py <ontology_class_names> --download` downloads the audio files contained in the csv filtered files. The option accepts the following values: `all`, `balanced`, `unbalanced`, `eval`
6. `python3 main.py <ontology_class_names> --proc-audio` postprocesses the audio, saving the trimmed version on (by default) `./audio_files/trimmed_files`. If instead `-pa` is used, it will only play the sections without actually saving them

Next Steps
---

+ Get channels from each audio
+ Control Sampling, Encoding and Channels

+ Pydub docs:
  + [github](https://github.com/jiaaro/pydub/)
  + [pydub: AudioSegment](https://media.readthedocs.org/pdf/audiosegment/stable/audiosegment.pdf)
  + [pydoc](https://www.pydoc.io/pypi/pydub-0.9.5/)
  + [pydoc api](https://www.pydoc.io/pypi/pydub-0.9.5/autoapi/audio_segment/index.html)
  + [github api](https://github.com/jiaaro/pydub/blob/master/API.markdown)

_check out the [librosa](https://librosa.github.io/) library as well_