from cli_manager import CLIManager
from audioset_download_tool import AudioSetDownloader
from audio_postprocessor import AudioProcessor

if __name__ == '__main__':

    args = CLIManager().args
    downl = AudioSetDownloader()
    proc = AudioProcessor(downl)
    downl.deserialize_json()
    downl.get_ids(args.name)
    print(f'id found: {downl.ids}')
    downl.get_child_ids(args.name)
    print(f'child ids found: {downl.child_ids}\n')

    if args.output:
        downl.filter_description_csvs()
    if args.download:
        downl.youtube_dl_interface(CLIManager.args.download)
    if args.postprocess_audio:
        proc.trim_audio()
        # proc.test()
    if args.print:
        for k, df in downl.get_filtered_df().items():
            print('\n', k)
            print(df, '\n')
    if args.unstable:
        pass

"""
FIXME: Take out duplicates for good:

Looking into Bone County SD 2011 Interceptor Pursuit - GTA SA.wav...


Video Name: 25    Bone County SD 2011 Interceptor Pursuit - GTA ...
26    Bone County SD 2011 Interceptor Pursuit - GTA ...
Name: name, dtype: object
Start Time: 25     60.0
26    180.0
Name: start_seconds, dtype: float64
End Time: 25     70.0
26    190.0
Name: end_seconds, dtype: float64
Duration: 25    10.0
26    10.0
dtype: float64

Traceback (most recent call last):
  File "main.py", line 21, in <module>
    proc.trim_audio()
  File "/home/ahoffmann/Projects/abdul-masters-project/audioset-download-tool/audio_postprocessor.py", line 29, in trim_audio
    self.run_trim(re.search(r'".+"', audio_name.rstrip('\n')).group().strip('"'))
  File "/home/ahoffmann/Projects/abdul-masters-project/audioset-download-tool/audio_postprocessor.py", line 50, in run_trim
    trimmed_audio = audio[start_ms:end_ms+1]
  File "/home/ahoffmann/anaconda3/envs/audioset-download-tool/lib/python3.7/site-packages/pydub/audio_segment.py", line 305, in __getitem__
    start = min(start, len(self))
  File "/home/ahoffmann/anaconda3/envs/audioset-download-tool/lib/python3.7/site-packages/pandas/core/generic.py", line 1479, in __nonzero__
    .format(self.__class__.__name__))
ValueError: The truth value of a Series is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all().

FIXME: Verify consistency of data (names, timestamps, etc.)

Video Name: V8 Powerboat on fire with explosion.wav             (5quD8nDBLnU)
Start Time: 150.0 -----> should be 60
End Time: 160.0 -------> should be 70
Duration: 10.0

according to the filtered balanced csv

"""
