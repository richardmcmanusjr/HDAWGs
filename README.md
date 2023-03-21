# HDAWGs
A python GUI that utilizes Zurich Instruments's LabOne Python API to remotely synchronize and program two HDAWG8s from a single .CSV waveform file.

## Control Panel
- Browse for waveform folder
- Load waveforms from .csv file
- Specify: 
  - primary and secondary devices
  - sample rate and frequency of playback
  - duration of playback
  - triggers
    - sync trigger between devices
    - enable trigger to initiate playback

<p align="center">
<img src="https://github.com/richardmcmanusjr/HDAWGs/blob/main/Control Panel.png">
</p>

## Sequences Tab
- Displays primary and secondary sequences
  - Generated from control panel configuration
  - Uploaded to HDAWGs via Zurich’s Python LabOne API

<p align="center">
<img src="https://github.com/richardmcmanusjr/HDAWGs/blob/main/Sequences.png">
</p>

## Settings Tab
- Configures delay compensation
  - Sample Clock Offset rotates secondary device wave array
    - Sample Rate Dependent
    - Discrete values of 1/(sample rate)
      - 0.4167 ns for 2.4 Gsps
  - Sequence Clock Offset delays primary device sequence
    - Discrete values of 3.33 ns
  - Total Sync Offset = Sequence Clock Offset - Sample Rate Offset

<p align="center">
<img src="https://github.com/richardmcmanusjr/HDAWGs/blob/main/Settings.png">
</p>
