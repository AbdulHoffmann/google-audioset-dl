import argparse
import os
import csv
import json
import youtube_dl

class CLIManager():

    @classmethod
    def __init__(cls):
        parser = argparse.ArgumentParser(prog='audioset-download-tool', description='Tool developed for flexibly downloading subsets of the Google AudioSet')
        parser.add_argument('name', nargs='+' , help='Class name to be searched in the audio set')
        parser.add_argument('--output-csv', dest='output', action='store_true')
        parser.add_argument('--download', action='store_true')
        # parser.add_argument('--format', help='Select output format for the audios')

        cls.args = parser.parse_args()
        print(cls.args)


class AudioSetDownloader():

    def __init__(self):
        self.csv_files = ('balanced_train_segments.csv', 'eval_segments.csv', 'unbalanced_train_segments.csv')
        self.ids = list()
        self.child_ids = list()
        self.filtered_list = list()

    def deserialize_json(self, filepath='support_files/ontology.json'):
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

    def filter_description_csvs(self, files_directory='google_audioset'):
        csv_data = []
        for filename in self.csv_files:
            with open(os.path.join(os.path.abspath(files_directory), filename)) as csvfile:
                csv_data.append(csv.reader(csvfile, quotechar='"', skipinitialspace=True))
                [next(csv_data[-1]) for _ in range(3)] # ignore header
                for row in csv_data[-1]:
                    for id_ in row[3].split(','):
                        for ids in self.child_ids:
                            if id_ in ids:
                                self.filtered_list.append(row)
            self.serialize_filtered_csvs(self.filtered_list, filename)

    def serialize_filtered_csvs(self, filtered_rows: list, filename: str, files_directory='filtered_audioset'):
        with open(os.path.join(os.path.abspath(files_directory), filename), 'w', newline='') as csvfile:
            filtered_csv = csv.writer(csvfile)
            for row in filtered_rows:
                filtered_csv.writerow(row)
            print('Finished saving .csv file %s' % filename)

    def youtube_dl_interface(self):

        def open_filtered_description_csvs(self, files_directory='filtered_audioset'):
            csv_data = []
            for filename in self.csv_files:
                with open(os.path.join(os.path.abspath(files_directory), filename)) as csvfile:
                    csv_data.append(csv.reader(csvfile, quotechar='"', skipinitialspace=True))
                    for row in csv_data[-1]:
                        yield row[0]

        class MyLogger(object):
            nonlocal watch_url
            error_list = []

            def debug(self, msg):
                pass

            def warning(self, msg):
                pass

            @classmethod
            def error(cls, msg):
                with open("audio_files/Errors.log", "a+") as text_file:
                    print(f"Error on file with url: {watch_url}", file=text_file)
                print(msg)


        def my_hook(dict):
            if dict['status'] == 'finished':
                print("Done downloading '{}', now converting...".format(dict['filename']))
            else:
                progress = round((dict['downloaded_bytes'] / dict['total_bytes'])*100, 1)
                print('Progress: {}%'.format(progress))

        for watch_url in open_filtered_description_csvs(self):
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
                'logger': MyLogger(),
                'progress_hooks': [my_hook],
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download(['https://www.youtube.com/watch?v=' + watch_url])


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