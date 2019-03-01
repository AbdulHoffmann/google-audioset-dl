from cli_manager import CLIManager
from audioset_download_tool import AudioSetDownloader
from audio_postprocessor import AudioProcessor
import pandas as pd

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
    if args.print:
        for k, df in downl.get_filtered_df().items():
            pd.set_option("display.max_rows", 300)
            print('\n', k)
            print(df, '\n')
            input('\nPress any key to continue...\n')
    if args.unstable:
        pass

"""
FIXME: Known error, if titles are exactly the same. Only downloading and processing the last one.

FIXME: if child ids are empty, download actual ids.
"""
