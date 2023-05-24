import json
from glob import glob
import os.path
import shutil
import numpy as np
import pandas as pd

# get nifti and json (assumes $SUBDIR/$FILES)
niiDir = r'C:\Users\je5rz\Documents\project\NICU\NII'
df = pd.DataFrame(columns=['sub','date','nifti','json','prefix'])
nifti = glob(os.path.join(niiDir,"*","*.nii*"))
for f in nifti:
    idx = int(df.shape[0])
    df.loc[idx,'nifti'] = f
    # prefix
    df.loc[idx, 'prefix'] = os.path.basename(f).replace('.nii.gz','').replace('.nii','')
    # sub and date (from filename)
    part = os.path.basename(f).split('_')
    df.loc[idx, 'sub'] = part[0]
    for p in part[2:-1]:
        if len(p) == 14 and p.isnumeric():
            df.loc[idx, 'date'] = p
    # json
    f = f.replace('.nii.gz','.json').replace('.nii','.json')
    if os.path.isfile(f):
        df.loc[idx,'json'] = f

# create visit names from unqiue dates
df_scan = df.loc[:,['sub','date']].drop_duplicates().copy().sort_values(by=['sub','date'])
prev_sub = None
for i, row in df_scan.iterrows():
    if row['sub'] != prev_sub:
        scan = 1
    else:
        scan = scan + 1    
    df_scan.loc[i,'scan'] = f'scan{scan}'
    
# deid
def json_filter(data):
    ret = False
    if 'Modality' in data and data['Modality'] == 'MR':
        if 'BodyPartExamined' in data:
            ret = True
    return ret

deid = pd.read_csv(r'C:\Users\je5rz\Documents\GitHub\uva-mri-deid\scripts\dicom_anon_fields.csv') # dicomheader fields (+ json sidecar)
# output
outDir = r'C:\Users\je5rz\Documents\project\NICU\NII_DEID'
if not os.path.isdir(outDir):
    os.makedirs(outDir)

# loop over files
for i, row in df.iterrows():
    filename = row['json']
    # remove json fields as defined in "deid"
    with open(row['json'], 'r') as f:
        data = json.load(f)
    for key in deid['name']:
        data.pop(key, None)
    # check if keeping this data
    if json_filter(data):
        # make new subject directory
        subDir = os.path.join(outDir,row['sub'])
        if not os.path.isdir(subDir):
            os.makedirs(subDir)
        # rename (remove date)
        if sum(df_scan['sub']==row['sub']) > 1: # include scan# if more than one per sub
            scan = df_scan.loc[df_scan['date']==row['date'],'scan'].values[0]
            prefix = row['prefix'].replace(f'_{row["date"]}_',f'_{scan}_')
        else:
             prefix = row['prefix'].replace(f'_{row["date"]}_','_')
        # write json
        jsonFile = os.path.join(subDir, prefix + '.json')
        with open(jsonFile, 'w') as f:
            f.write(json.dumps(data, indent=4))
        # copy nifti
        _, ext = os.path.splitext(df.loc[0,'nifti'])
        if ext == '.gz':
            ext = '.nii.gz'
        niftiFile = os.path.join(subDir, prefix + ext)
        shutil.copyfile(row['nifti'], niftiFile)
        print(f'{i+1}/{df.shape[0]}\t{prefix}')
    else:
        print(f'OMITTING:\t{row["prefix"]}')