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
        parser.add_argument('--format', help='Select output format for the audios')

        cls.args = parser.parse_args()
        print(cls.args)


class AudioSetDownloader():

    def __init__(self):
        self.csv_files = ('balanced_train_segments.csv', 'eval_segments.csv', 'unbalanced_train_segments.csv')
        self.ids = list()
        self.child_ids = list()
        self.csv_data = list()

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
        filtered_list = []
        for filename in self.csv_files:
            with open(os.path.join(os.path.abspath(files_directory), filename)) as csvfile:
                self.csv_data.append(csv.reader(csvfile, quotechar='"', skipinitialspace=True))
                [next(self.csv_data[-1]) for _ in range(3)] # ignore header
                for row in self.csv_data[-1]:
                    for id_ in row[3].split(','):
                        for ids in self.child_ids:
                            if id_ in ids:
                                filtered_list.append(row)
            self.serialize_filtered_csvs(filtered_list, filename)

    def serialize_filtered_csvs(self, filtered_rows: list, filename: str, files_directory='filtered_audioset'):
        with open(os.path.join(os.path.abspath(files_directory), filename), 'w', newline='') as csvfile:
            filtered_csv = csv.writer(csvfile)
            for row in filtered_rows:
                filtered_csv.writerow(row)
            print('Finished saving .csv file %s' % filename)


if __name__ == '__main__':
    CLIManager()
    audio = AudioSetDownloader()
    audio.deserialize_json()
    audio.get_ids(CLIManager.args.name)
    audio.get_child_ids(CLIManager.args.name)
    audio.filter_description_csvs()
    print(f'id found: {audio.ids}')
    print(f'child ids found: {audio.child_ids}')