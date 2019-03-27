import argparse

class CLIManager():

    @classmethod
    def __init__(cls):
        parser = argparse.ArgumentParser(
            prog='audioset-download-tool',
            description='Tool developed for flexibly downloading subsets of the Google AudioSet'
        )

        parser.add_argument('name', 
                            nargs='+', 
                            help='Class name to be searched in the audio set')
        parser.add_argument('--output-csv', 
                            help='Outputs filtered csv files at the files directory', dest='output', action='store_true')
        parser.add_argument('-d', '--download',
                            help='Initiate downloading the audioset.',
                            choices=['all','eval','balanced', 'unbalanced'])
        parser.add_argument('-a', '--proc-audio',
                            help='Initiate audio postprocessing',
                            dest='postprocess_audio',
                            action='store_true')
        parser.add_argument('-p','--play-mode',
                            help='Modifies audio postprocessing. '
                                 'If set to "silent", postprocessing will carry out without playing the segments. '
                                 'If set to "play" will only play the segment without storing it.',
                            choices=['silent','play'])
        parser.add_argument('--print-df',
                            help='Outputs each of the filtered dataframes to the terminal',
                            dest='print',
                            action='store_true')
        parser.add_argument('--run_unstable',
                            help='Run unstable functions',
                            dest='unstable',
                            action='store_true')
        parser.add_argument('--examine',
                            help='Runs trimmed files examination',
                            choices=['all','eval','balanced', 'unbalanced'])
        parser.add_argument('-l', '--label',
                            help='Applies label to files in folder',
                            action='store')
        parser.add_argument('-f', '--folder',
                            help='Only applicable with --label. Receives the path of the folder to be labeled.',
                            action='store')
        parser.add_argument('-r', '--revert',
                            help='Only applicable with --label. When the option is passed, reverts all labels applied.',
                            action='store_true')
        parser.add_argument('-v', '--verbose',
                            help='Outputs verbose',
                            action='store_true')

        cls.args = parser.parse_args()

        if cls.args.verbose:
            print(cls.args)
            