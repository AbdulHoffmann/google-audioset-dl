import os
import string
import re
import wave
import shutil
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
        self.export_dir = os.path.join(os.path.abspath(self.audioset_dl.audios_directory), 'trimmed_files')
        self.selected_dir = os.path.join(os.path.abspath(self.audioset_dl.audios_directory), 'selected_files')
        self.logger = Logger(self.audioset_dl)

    def clean(self):
        warning_file = os.path.join(self.audioset_dl.support_files_directory, "warnings.log")
        if os.path.exists(warning_file):
            os.remove(warning_file)

    def trim_audio(self, download_mode):
        if CLIManager.args.verbose:
            print('Opening input file from:', os.path.abspath(self.audioset_dl.support_files_directory))

        gen_log_name = '{}_generated_audios.log'.format(download_mode)
        self.clean()

        if self.audioset_dl.audio_files_list:
            for audio_name in self.audioset_dl.audio_files_list:
                self.run_trim(re.search(r'\".+\"', audio_name), gen_log_name)
        else:
            with open(
                    os.path.join(os.path.abspath(self.audioset_dl.support_files_directory), gen_log_name)
            ) as audio_names:
                for audio_name in audio_names:
                    self.run_trim(re.search(r'".+"', audio_name.rstrip('\n')).group().strip('"'), gen_log_name)

    def run_trim(self, audio_name, audios_logfile):
        print('\nLooking into \'' + audio_name + '\'...\n')

        def to_milliseconds(sec_num):
            return sec_num * 1e3

        try:
            for filename, df in self.audioset_dl.get_filtered_df(audios_logfile).items():
                assert not (df.duplicated().any()), "Duplicate rows found in data."
                mask = df.index[df['name'].isin([audio_name])]
                if not (mask.empty):
                    row = df.loc[mask].squeeze()
                    if row.ndim != 1:
                        self.logger.warn(
                            f'Found files with coinciding names: \'{row.iloc[0]["name"]}\'.Only the last instance which appears in the dataframe will be downloaded and processed.'
                        )
                        row = row.iloc[-1]
                    start_ms = to_milliseconds(row['start_seconds'])
                    end_ms = to_milliseconds(row['end_seconds'])
                    print(f'Start Time: {row["start_seconds"]}')
                    print(f'End Time: {row["end_seconds"]}')
                    print(f'Duration: {row["end_seconds"] - row["start_seconds"]}\n')
                    audio = AudioSegment.from_wav(os.path.join(
                        self.audioset_dl.audios_directory,
                        filename.replace('.csv', ''),
                        audio_name
                    ))
                    trimmed_audio = audio[start_ms:end_ms + 1]
                    if CLIManager.args.play_mode != "play":
                        self.export_audio(trimmed_audio, row, filename)
                    if CLIManager.args.play_mode != "silent":
                        pydub.playback.play(trimmed_audio)

        except FileNotFoundError as e:
            print(e)

    def export_audio(self, audio_file, audio_info, subdir_name, format_='.wav'):
        for attempt in range(10):
            try:
                subdir_name = subdir_name.replace('.csv', '')
                audio_file.export(
                    os.path.join(self.export_dir, subdir_name, audio_info["name"].replace('.csv', '')),
                    format=format_.lstrip('.')
                )
            except FileNotFoundError:
                print("Directory Tree apparently doesn't exist. Creating it...\n")
                os.makedirs(os.path.join(self.export_dir, subdir_name))
            else:
                break

    def examine_trimmed_audio(self, desired_channels_number, desired_samplerate_number):
        def print_caracteristics():
            print(f'\nExamining File: "{file_}"')
            print(f"\nNumber of Channels: {audio.getnchannels()}")
            print(f"Sampling Rate: {audio.getframerate()}")
            print(f"Numer of Audio Frames: {audio.getnframes()}")
            print(f"Compression Type: {audio.getcompname()}\n")

        def clean_selected_folder():
            if os.path.exists(self.selected_dir):
                shutil.rmtree(self.selected_dir)
            os.mkdir(self.selected_dir)

        def select_audios(channels_number, samplerate_number):
            """
            Place the best audios from the trimmed files in a separated file
            """
            if audio.getnchannels() == channels_number and audio.getframerate() >= samplerate_number:
                shutil.copy2(
                    os.path.join(audios_path, file_),
                    os.path.join(self.audioset_dl.audios_directory, self.selected_dir, file_)
                )
                print_caracteristics()

        assert CLIManager.args.examine, "examine_trimmed_audio method has no input."

        if CLIManager.args.examine == 'all':
            folders = ('balanced_train_segments', 'eval_segments', 'unbalanced_train_segments')
        if CLIManager.args.examine == 'eval':
            folders = ('eval_segments',)
        if CLIManager.args.examine == 'balanced':
            folders = ('balanced_train_segments',)
        if CLIManager.args.examine == 'unbalanced':
            folders = ('unbalanced_train_segments',)

        clean_selected_folder()

        for folder in folders:
            audios_path = os.path.join(self.export_dir, folder)
            for file_ in os.listdir(audios_path):
                with wave.open(os.path.join(audios_path, file_), 'rb') as audio:
                    # print_caracteristics()
                    select_audios(desired_channels_number, desired_samplerate_number)

    def manual_labeler(self, label: str, target_dir=None, revert=False):
        """
        As 25.03.19 this function's objective is to label the title of files to be used in training. Since the problem
        supposed to be solved is binary, the classes are mutually exclusive.
        Encode:
        1: Positive class (Audio contains an Emergency Vehicle in it)
        0: Negative class (Audio doesn't contain an Emergency Vehicle in it)
        """
        if target_dir is None:
            target_dir = self.selected_dir
        for idx, (dir_path, subdirs, filenames) in enumerate(os.walk(target_dir)):
            if idx == 0:
                print(f"folders under '{os.path.basename(dir_path)}' which will be also affected:\n")
                for dir_ in subdirs:
                    print(dir_)
                print("\n", end="")
                confirm = input('confirm? [y]/n\n')
                if confirm.lower() == 'n' or confirm.lower() == 'no':
                    raise SystemExit
            if revert:
                for filename in filenames:
                    new_filename = re.sub(f'__{label}__', '', filename)
                    os.rename(os.path.join(dir_path, filename), os.path.join(dir_path, new_filename))
            else:
                for filename in filenames:
                    try:
                        h1, h2 = filename.rsplit('.', 1)
                        new_filename = h1 + f'__{label}__.' + h2
                        os.rename(os.path.join(dir_path, filename), os.path.join(dir_path, new_filename))
                    except ValueError:
                        print('File with no extension found.')
                        raise SystemExit
