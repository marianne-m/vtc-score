# vtc-score

This repository gives you an easy way to score VTC inferences.

## Setup

This requires the pyannote version on branch develop of the repo git@github.com:bootphon/pyannote-audio/.

```bash
git clone git@github.com:marianne-m/vtc-score.git
cd vtc-score/

# create a venv (tested on python3.8)
python3.8 -m venv venv/
. venv/bin/activate

# or create a conda env
conda create -n vtc_score python=3.8
conda activate vtc_score

pip install -r requirements.txt
```

## Usage

Set the `PYANNOTE_DATABASE_CONFIG` environment variable before launching the score command :

```bash
PYANNOTE_DATABASE_CONFIG=/scratch2/mkhentout/test-alice/ALICE/voice-type-classifier/pyannote_tmp_config/tmp_data/database.yml
```

To score VTC inferences, run :

```bash
python main.py --apply_path path/to/vtc/inferences --report_path path/to/fscore/report.csv
```
