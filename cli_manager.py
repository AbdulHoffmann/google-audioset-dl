import argparse

class CLIManager():

    @classmethod
    def __init__(cls):
        parser = argparse.ArgumentParser(prog='audioset-download-tool', description='Tool developed for flexibly downloading subsets of the Google AudioSet')
        parser.add_argument('name', 
                            nargs='+', 
                            help='Class name to be searched in the audio set')
        parser.add_argument('--output-csv', 
                            help='Outputs filtered csv files at the files directory', dest='output', action='store_true')
        parser.add_argument('-d', '--download',
                            help='Initiate downloading the audioset. Possible values are "all", "balanced", "unbalanced" or "eval"',
                            choices=['all','eval','balanced', 'unbalanced'])
        parser.add_argument('-a', '--proc-audio',
                            help='Initiate audio postprocessing',
                            dest='postprocess_audio',
                            action='store_true')
        parser.add_argument('-p','--play-mode',
                            help='Only runs the audios without exporting the trimmed audio. Possible values are "silent", "normal", "play"',
                            choices=['silent','play'])
        parser.add_argument('--print-df',
                            help='Outputs each of the filtered dataframes to the terminal',
                            dest='print',
                            action='store_true')
        parser.add_argument('--run_unstable',
                            help='Run unstable functions',
                            dest='unstable',
                            action='store_true')
        parser.add_argument('-v','--verbose',
                            help='Outputs verbose',
                            action='store_true')

        cls.args = parser.parse_args()

        if cls.args.verbose:
            print(cls.args)
            