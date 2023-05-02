# create FileSet and write DICOMDIR from existig set of DICOM files (AEMRI study)

from pathlib import Path
import os
from glob import glob
from pydicom.fileset import FileSet
from pydicom import dcmread
import time

#   python C:\\Users\\Public\\PST\\Scripts\ipython3.exe
#   robocopy C:\Users\je5rz\Documents\AEMRI\DEID\FORPACS Z:\ResearchData\BrainTransfer\DEID\FORPACS /S /Z /MT /R:10 /W:1


deidDir = Path(os.path.join('C:\\','Users','je5rz','Documents','AEMRI','DEID','RSNA'))
outDir = Path(os.path.join('C:\\','Users','je5rz','Documents','AEMRI','DEID','FORPACS'))

fs = FileSet()
fs.Study = 'AEMRI'

lastStudy=None
lastPatient=None
lastTime = time.perf_counter()

i = 0
# loop over dicom files (should all start with I), add to FileSet
for dicom in deidDir.rglob('I*'):
    if dicom.is_file():
        try:
            d = dcmread(dicom)
            d.StudyTime = '000000' # required
            # name based on AEMRI directories
            d.StudyID = dicom.parents[2].name
            d.PatientID = '_'.join(d.StudyID.split('_')[:-1])
            d.PatientName = d.PatientID
            study_n = int(d.StudyID.split('_')[-1])
            # only add first 10 studies
            if study_n <= 10:
                fs.add(d)
                i = i + 1
            # print info for each new series
            if lastStudy is None or d.StudyID != lastStudy:
                newTime = time.perf_counter()
                lastStudy = d.StudyID
                print(f'{dicom.parents[2].name}\t{round(newTime-lastTime,1)} secs')
                lastTime = newTime

        except KeyboardInterrupt:
            break
        except:
            print(f'ERROR\t{dicom}')

# write FileSet
if not outDir.is_dir():
    outDir.mkdir()
fs.write(outDir)
