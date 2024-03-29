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
        mode = input('Choose which segment of dataset: [eval / balanced / unbalanced / all]\n')
        proc.trim_audio(mode)
    if args.examine:
        proc.examine_trimmed_audio(2, 48000)  # stereo 48k
    if args.label:
        kwargs = dict()
        if args.folder:
            kwargs['target_dir'] = args.folder
        if args.revert:
            kwargs['revert'] = args.revert
        proc.manual_labeler(args.label, **kwargs)
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

TODO: autolabeler - store and label automatically the files with argument entered labels. Also,
it would be great to ensure that an argument with the non-desirable labels would be input as well,
and the method would filter out any audio with this label.
"""
