import os
import csv
import json
import re

from cli_manager import CLIManager
import youtube_dl
import pandas as pd
import numpy as np

class AudioSetDownloader():

    def __init__(self):
        self.csv_files = ('balanced_train_segments.csv', 'eval_segments.csv', 'unbalanced_train_segments.csv')
        self.ids = list()
        self.child_ids = list()
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
        for filename in self.csv_files:
            with open(os.path.join(os.path.abspath(files_directory), filename)) as csvfile:
                csv_data = csv.reader(csvfile, quotechar='"', skipinitialspace=True)
                [next(csv_data) for _ in range(3)] # ignore header
                yield (filename, list(csv_data))

    def filter_description_csvs(self):
        for gen in self.deserialize_google_csvs():
            filtered_list = []
            filename, content = gen
            for row in content:
                if CLIManager.args.verbose:
                    print([i for i in row])
                for id_ in row[3].split(','):
                    for ids in self.child_ids:
                        if id_ in ids:
                            filtered_list.append(row)
            self.serialize_filtered_csvs(filtered_list, filename, self.csv_output_directory)

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
        return {filename: pd.DataFrame(content, columns=['ytid', 'start_seconds', 'end_seconds', 'positive_labels']) for filename, content in zip(self.csv_files, inter_list, )}

    def add_name_column_to_filtered_df(self, audios_logfile='generated_audios.log'):
        def build_name_series(csv_data, df):
            my_list = [np.nan] * df.shape[0]
            for line in csv_data:
                for k, v in df['ytid'].iteritems():
                    if v == line[0]:
                        my_list[k] = line[1]
            return pd.Series(my_list)

        f_csv = self.deserialize_filtered_csvs()
        with open(os.path.join(os.path.abspath(self.support_files_directory), audios_logfile)) as csvfile:
            csv_data = tuple(csv.reader(csvfile, quotechar='"', skipinitialspace=True))
            csv_data = set((tuple(line) for line in csv_data))
            for f_csv_name, df in f_csv.items():
                df['start_seconds'] = pd.to_numeric(df['start_seconds'])
                df['end_seconds'] = pd.to_numeric(df['end_seconds'])
                name_series = build_name_series(csv_data, df)
                # name_series = pd.Series([row[1]  if row[0] in df['ytid'].values else np.nan for row in csv_data])
                # name_series = pd.Series((line[1] if row == line[0] else np.nan for line in csv_data for row in df['ytid']))
                # mask = pd.Series(df['ytid'].isin((row[0] for row in csv_data)))
                df = df.assign(name=name_series).drop_duplicates(('ytid', 'start_seconds', 'end_seconds'))
                if CLIManager.args.verbose:
                    print('\n' + f_csv_name)
                    print(name_series, '\n')
                yield (f_csv_name, df)

    def get_filtered_df(self):
        return {k: v for k, v in self.add_name_column_to_filtered_df()}

    def youtube_dl_interface(self, download_mode):
        def open_filtered_description_csvs(files_directory, download_mode='all'): # TODO: merge this function with the deserialize_filtered_csvs method
            csv_data = []
            if download_mode == 'balanced':
                csv_files = ('balanced_train_segments.csv',)
            elif download_mode == 'unbalanced':
                csv_files = ('unbalanced_train_segments.csv',)
            elif download_mode == 'eval':
                csv_files = ('eval_segments.csv',)
            elif download_mode == 'all':
                csv_files = self.csv_files

            for filename in csv_files:
                self.subdir_audio_files = re.sub(r'\.csv$', '', filename)
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

        def store_audio_filenames():
            with open(self.support_files_directory + "/generated_audios.log", "a+") as log_file:
                print(watch_url + ', "' + self.audio_files_list[-1] + '"', file=log_file)

        def my_hook(dict, extension='.wav'):
            if dict['status'] == 'finished':
                self.audio_files_list.append(dict['filename'].split('/')[-1])
                print("Done downloading '{}', now converting...".format(self.audio_files_list[-1]))
                self.audio_files_list[-1] = re.sub(r'\.(?:.{3}|webm)$', '', self.audio_files_list[-1]) + extension
                store_audio_filenames()
            else:
                progress = round((dict['downloaded_bytes'] / dict['total_bytes'])*100, 1)
                print('Progress: {}%'.format(progress))

        clean()

        for watch_url in open_filtered_description_csvs(self.csv_output_directory, download_mode):
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'outtmpl': 'audio_files/' + self.subdir_audio_files + '/%(title)s.%(ext)s',
                'prefer_ffmpeg': True,
                'ignoreerrors': True,
                'logger': MyLogger(watch_url),
                'progress_hooks': [my_hook],
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download(['https://www.youtube.com/watch?v=' + watch_url])
