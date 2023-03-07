import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any

import yaml
import pandas as pd
from pyannote.core import Annotation
from pyannote.audio.utils.preprocessors import DeriveMetaLabels
from pyannote.database import FileFinder, get_protocol, ProtocolFile
from pyannote.database.protocol.protocol import Preprocessor
from pyannote.database.util import load_rttm, LabelMapper
from pyannote.audio.utils.metric import MacroAverageFMeasure


class ProcessorChain:

    def __init__(self, preprocessors: List[Preprocessor], key: str):
        self.procs = preprocessors
        self.key = key

    def __call__(self, file: ProtocolFile):
        file_cp: Dict[str, Any] = abs(file)
        for proc in self.procs:
            out = proc(file_cp)
            file_cp[self.key] = out

        return out


CLASSES = {"babytrain": {'classes': ["MAL", "FEM", "CHI", "KCHI"],
                         'unions': {"SPEECH": ["MAL", "FEM", "CHI", "KCHI"]},
                         'intersections': {}}
           }


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Evaluate VTC with fscore')
    parser.add_argument("-p", "--protocol", type=str,
                        default="X.SpeakerDiarization.BBT2",
                        help="Pyannote database")
    parser.add_argument("--apply_folder", type=Path,
                        required=True,
                        help="Path to the inference files")
    parser.add_argument("--classes", choices=CLASSES.keys(),
                        default="babytrain",
                        type=str, help="Model architecture")
    parser.add_argument("--report_path", type=Path, required=True,
                        help="Path to report csv")
    return parser.parse_args(argv)


def _get_protocol(classes, protocol):
    classes_kwargs = CLASSES[classes]
    vtc_preprocessor = DeriveMetaLabels(**classes_kwargs)
    preprocessors = {
        "audio": FileFinder(),
        "annotation": vtc_preprocessor
    }
    if classes == "babytrain":
        with open(Path(__file__).parent / "data/babytrain_mapping.yml") as mapping_file:
            mapping_dict = yaml.safe_load(mapping_file)["mapping"]
        preprocessors["annotation"] = ProcessorChain([
            LabelMapper(mapping_dict, keep_missing=True),
            vtc_preprocessor
        ], key="annotation")
    return get_protocol(protocol, preprocessors=preprocessors)


def score_vtc(
        classes: str,
        protocol: str,
        apply_folder: str,
        report_path: str
):
    protocol = _get_protocol(classes, protocol)

    annotations: Dict[str, Annotation] = {}
    for filepath in apply_folder.glob("*.rttm"):
        rttm_annots = load_rttm(filepath)
        annotations.update(rttm_annots)

    metric = MacroAverageFMeasure()

    for file in protocol.test():
        if file["uri"] not in annotations:
            continue
        inference = annotations[file["uri"]]
        metric(file["annotation"], inference, file["annotated"])

    df: pd.DataFrame = metric.report(display=True)
    report_path.parent.mkdir(parents=True, exist_ok=True) 
    df.to_csv(report_path)


if __name__ == '__main__':
    args = sys.argv[1:]
    args = parse_args(args)

    score_vtc(args.classes, args.protocol, args.apply_folder, args.report_path)