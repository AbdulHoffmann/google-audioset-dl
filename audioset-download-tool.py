import argparse
import os
import csv
import json
import re

import youtube_dl
import pandas as pd
from pydub import AudioSegment
import pydub.playback

class CLIManager():

    @classmethod
    def __init__(cls):
        parser = argparse.ArgumentParser(prog='audioset-download-tool', description='Tool developed for flexibly downloading subsets of the Google AudioSet')
        parser.add_argument('name', nargs='+' , help='Class name to be searched in the audio set')
        parser.add_argument('--output-csv', help='Outputs filtered csv files at the files directory', dest='output', action='store_true')
        parser.add_argument('--download', help='Initiate downloading the audioset', action='store_true')
        parser.add_argument('--audio', help='Initiate audio postprocessing', dest='postprocess_audio' , action='store_true')
        parser.add_argument('--print-df', help='Outputs each of the dataframes to the terminal', dest='postprocess_audio', dest='print', action='store_true')
        parser.add_argument('--run_unstable', help='Run unstable functions', dest='unstable' , action='store_true')
        parser.add_argument('-v','--verbose', help='Outputs verbose', action='store_true')

        cls.args = parser.parse_args()

        if cls.args.verbose:
            print(cls.args)


class AudioSetDownloader():

    def __init__(self):
        self.csv_files = ('balanced_train_segments.csv', 'eval_segments.csv', 'unbalanced_train_segments.csv')
        self.ids = list()
        self.child_ids = list()
        self.filtered_list = list()
        self.audio_files_list = list()
        self.csv_output_directory = 'filtered_audioset'
        self.audios_directory = 'audio_files'
        self.support_files_directory = 'support_files'

    def deserialize_json(self, filepath=None):
        if not(filepath):
            filepath = '{}/ontology.json'.format(self.support_files_directory)
        try:
            with open(os.path.abspath(filepath)) as json_file:
                self.json_data = json.load(json_file)

        except json.JSONDecodeError:
            print('Please, check the integrity of "ontology.json"')

    def get_child_ids(self, subset_names: list):
        for name in subset_names:
            for i in self.json_data:
                if name.lower() == i['name'].lower():
                    self.child_ids.append(i['child_ids'])

    def get_ids(self, subset_names: list):
        for name in subset_names:
            for i in self.json_data:
                if name.lower() == i['name'].lower():
                    self.ids.append(i['id'])

    def deserialize_google_csvs(self, files_directory='google_audioset'):
        csv_data = []
        for filename in self.csv_files:
            with open(os.path.join(os.path.abspath(files_directory), filename)) as csvfile:
                csv_data.append(csv.reader(csvfile, quotechar='"', skipinitialspace=True))
                [next(csv_data[-1]) for _ in range(3)] # ignore header
                yield {filename: list(csv_data[-1])}

    def filter_description_csvs(self):
        for gen in self.deserialize_google_csvs():
            filename, content = (tuple(gen.keys())[0], gen.get(tuple(gen.keys())[0]))
            for row in content:
                if CLIManager.args.verbose:
                    print([i for i in row])
                for id_ in row[3].split(','):
                    for ids in self.child_ids:
                        if id_ in ids:
                            self.filtered_list.append(row)
            self.serialize_filtered_csvs(self.filtered_list, filename, self.csv_output_directory)

    def serialize_filtered_csvs(self, filtered_rows: list, filename: str, files_directory):
        with open(os.path.join(os.path.abspath(files_directory), filename), 'w', newline='') as csvfile:
            filtered_csv = csv.writer(csvfile)
            for row in filtered_rows:
                filtered_csv.writerow(row)
            print('Finished saving .csv file %s' % filename)

    def deserialize_filtered_csvs(self):
        inter_list = []
        for filename in self.csv_files:
            with open(os.path.join(os.path.abspath(self.csv_output_directory), filename)) as csvfile:
                csv_data = csv.reader(csvfile, quotechar='"', skipinitialspace=True)
                inter_list.append([row for row in csv_data])
        return {filename: pd.DataFrame(content, columns=['ytid', 'start_seconds', 'end_seconds', 'positive_labels']) for filename, content in zip(self.csv_files, inter_list)}

    def add_name_column_to_df(self):
        # f_csv_n, f_csv_c = zip(*self.deserialize_filtered_csvs().items()) # filtered_csv_name and filtered_csv_content
        f_csv = self.deserialize_filtered_csvs() # filtered_csvs
        for f_csv_n, df in f_csv.items():
            pass

    def youtube_dl_interface(self):
        def open_filtered_description_csvs(files_directory): # TODO: merge this function with the deserialize_filtered_csvs method
            csv_data = []
            for filename in self.csv_files:
                with open(os.path.join(os.path.abspath(files_directory), filename)) as csvfile:
                    csv_data.append(csv.reader(csvfile, quotechar='"', skipinitialspace=True))
                    for row in csv_data[-1]:
                        yield row[0]

        def clean():
            try:
                os.remove(os.path.join(os.path.abspath(self.support_files_directory), "errors.log"))
            except Exception as e:
                print(e)
            try:
                os.remove(os.path.join(os.path.abspath(self.support_files_directory), "generated_audios.log"))
            except Exception as e:
                print(e)

        class MyLogger(object):

            @classmethod
            def __init__(cls, watch_url):
                cls.error_list = []
                cls.watch_url = watch_url

            def debug(self, msg):
                pass

            def warning(self, msg):
                pass

            @classmethod
            def error(cls, msg):
                with open(self.support_files_directory + "/errors.log", "a+") as log_file:
                    print(f"Error on file with url: {cls.watch_url}", file=log_file)
                print(msg)

        def store_audio_filenames(self):
            with open(self.support_files_directory + "/generated_audios.log", "a+") as log_file:
                print(watch_url + ', ' + self.audio_files_list[-1], file=log_file)

        def my_hook(dict, extension='.wav'):
            if dict['status'] == 'finished':
                self.audio_files_list.append(dict['filename'].split('/')[1])
                print("Done downloading '{}', now converting...".format(self.audio_files_list[-1]))
                self.audio_files_list[-1] = re.sub(r'\..{3}$', '', self.audio_files_list[-1]) + extension
                store_audio_filenames(self)
            else:
                progress = round((dict['downloaded_bytes'] / dict['total_bytes'])*100, 1)
                print('Progress: {}%'.format(progress))

        clean()

        for watch_url in open_filtered_description_csvs(self.csv_output_directory):
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'outtmpl': 'audio_files/%(title)s.%(ext)s',
                'prefer_ffmpeg': True,
                'ignoreerrors': True,
                'logger': MyLogger(watch_url),
                'progress_hooks': [my_hook],
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download(['https://www.youtube.com/watch?v=' + watch_url])

    def postprocess_audio(self):
        print(os.path.abspath(self.support_files_directory))

        def run_postprocess(audio_name):
                print('\nbeginning ' + audio_name + '...\n')
                audio = AudioSegment.from_wav(os.path.join(self.audios_directory, audio_name))

                # ten_seconds = 10 * 1000
                last_5_seconds = audio[-5000:]
                pydub.playback.play(last_5_seconds)

        if self.audio_files_list:
            for audio_name in self.audio_files_list:
                run_postprocess(audio_name)
        else:
            with open(os.path.join(os.path.abspath(self.support_files_directory), 'generated_audios.log')) as audio_names:
                for audio_name in audio_names:
                    run_postprocess(audio_name.rstrip('\n'))


if __name__ == '__main__':

    args = CLIManager().args
    audio = AudioSetDownloader()
    audio.deserialize_json()
    audio.get_ids(args.name)
    print(f'id found: {audio.ids}')
    audio.get_child_ids(args.name)
    print(f'child ids found: {audio.child_ids}')

    if args.output:
        audio.filter_description_csvs()
    if args.download:
        audio.youtube_dl_interface()
    if args.postprocess_audio:
        audio.postprocess_audio()
    if args.postprocess_audio:
        audio.postprocess_audio()
    if args.print:
        for k, df in audio.deserialize_filtered_csvs().items():
            print(k)
            print(df)
    if args.unstable:
        audio.add_name_column_to_df()
