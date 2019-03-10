import os
import string
import re

from audioset_download_tool import AudioSetDownloader
from cli_manager import CLIManager
from pydub import AudioSegment
import pydub.playback


class Logger():

    def __init__(self, audioset_dl: AudioSetDownloader):
        self.audioset_dl = audioset_dl

    def info(self):
        pass

    def warn(self, msg):
        print('\nWarning:', msg, '\n')
        with open(os.path.join(self.audioset_dl.support_files_directory, "warnings.log"), "a+") as log_file:
                print(msg, file=log_file)

    def error(self):
        pass


class AudioProcessor():

    def __init__(self, audioset_dl: AudioSetDownloader):
        self.audioset_dl = audioset_dl
        self.export_dir = os.path.join(os.path.abspath('audio_files'), 'trimmed_files')
        self.logger = Logger(self.audioset_dl)

    def clean(self):
        warning_file = os.path.join(self.audioset_dl.support_files_directory, "warnings.log")
        if os.path.exists(warning_file):
            os.remove(warning_file)

    def trim_audio(self):
        if CLIManager.args.verbose:
            print('Opening input file from:', os.path.abspath(self.audioset_dl.support_files_directory))

        self.clean()

        if self.audioset_dl.audio_files_list:
            for audio_name in self.audioset_dl.audio_files_list:
                self.run_trim(re.search(r'\".+\"', audio_name))
        else:
            with open(os.path.join(os.path.abspath(self.audioset_dl.support_files_directory), 'generated_audios.log')) as audio_names:
                for audio_name in audio_names:
                    self.run_trim(re.search(r'".+"', audio_name.rstrip('\n')).group().strip('"'))

    def run_trim(self, audio_name):
        print('\nLooking into \'' + audio_name + '\'...\n')

        def to_milliseconds(sec_num):
            return sec_num * 1e3

        try:
            for filename, df in self.audioset_dl.get_filtered_df().items():
                assert not(df.duplicated().any()), "Duplicate rows found in data."
                mask = df.index[df['name'].isin([audio_name])]
                if not(mask.empty):
                    row = df.loc[mask].squeeze()
                    if row.ndim != 1:
                        self.logger.warn(f'Found files with coinciding names: \'{row.iloc[0]["name"]}\'. Only the last instance which appears in the dataframe will be downloaded and processed.')
                        row = row.iloc[-1]
                    start_ms = to_milliseconds(row['start_seconds'])
                    end_ms = to_milliseconds(row['end_seconds'])
                    print(f'Start Time: {row["start_seconds"]}')
                    print(f'End Time: {row["end_seconds"]}')
                    print(f'Duration: {row["end_seconds"] - row["start_seconds"]}\n')
                    audio = AudioSegment.from_wav(os.path.join(self.audioset_dl.audios_directory, filename.replace('.csv', ''), audio_name))
                    trimmed_audio = audio[start_ms:end_ms+1]
                    if CLIManager.args.play_mode != "play":
                        self.export_audio(trimmed_audio, row, filename)
                    if CLIManager.args.play_mode != "silent":
                        pydub.playback.play(trimmed_audio)

        except FileNotFoundError as e:
            print(e)

    def export_audio(self, audio_file, audio_info, subdir_name, format_='.wav'):    # TODO: Further study ffpmeg and understand possibilities regarding sampling, encoding and channels using the parameters
        for attempt in range(10):
            try:
                subdir_name = subdir_name.replace('.csv', '')
                audio_file.export(os.path.join(self.export_dir, subdir_name, audio_info["name"].replace('.csv', '')), format=format_.lstrip('.'))
            except FileNotFoundError:
                print("Directory Tree apparently doesn't exist. Creating it...\n")
                os.makedirs(os.path.join(self.export_dir, subdir_name))
            else:
                break
