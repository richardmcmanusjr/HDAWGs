# AWGGUI_IMP.py

import hdawg
import time
import PySimpleGUI as sg
import os.path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# cwd = os.getcwd()
# fname = 'notredame.png'
#
# with open('{}/{}'.format(cwd, fname)) as fh:
#     image1 = fh.read()

# First the window layout in 2 columns

deviceIds = ['dev8310', 'dev8259']
sampleRates = ['2.4 GHz','1.2 GHz','600 MHz','300 MHz','150 MHz', '100 MHz'] #Minimum Sample Rate is 100 MHZ
# ,'75 MHz','37.5 MHz','18.75 MHz','9.4 MHz','4.5 MHz','2.34 MHz','1.2 MHz','586 kHz','293 kHz']
primary_device_id = deviceIds[0]
secondaryDeviceIds = deviceIds
secondaryDeviceIds.append('None')
secondary_device_id = deviceIds[2]
waveCounts = ['Infinite']
wave_count = waveCounts[0]
triggers = ['Level','Rising','Falling','Both','None']
trigger = triggers[4]
triggerChannels = [1,2,3,4,5,6,7,8]
trigger_channel = triggerChannels[0]
units = ['GHz', 'MHz', 'kHz', 'Hz']
firstTime = True

def create_plot(array):
    numCols = len(array[0]) # 2 columns in your example
    ax = plt.gca()
    ax.cla()                        # Clear the current axes
    ax.grid()
    plt.figure(facecolor = '#ebeded')
    for i in range(numCols):
        current_color = ['b', 'g', 'r', 'c', 'm','y','k']
        plt.step(np.linspace(0,len(array[:,i]),len(array[:,i]), endpoint = False), array[:,i], color=current_color[i%7], marker='o',
            markersize = 1, linewidth = 0.75)
    plt.title(os.path.basename(filename), fontsize=8)
    plt.tick_params(axis='both', labelsize=4)
    plt.xlabel('Index', fontsize=6)
    plt.ylabel('Magnitude', fontsize=6)
    plt.grid(True)
    return plt.gcf()

def create_interp_array(filename, frequency, sampleRate):
    array = np.loadtxt(filename, delimiter=",")
    numCols = len(array[0]) # 2 columns in your example
    magnitude = []
    for i in range(numCols):
        time = np.linspace(0, len(array[:,i]), int(sampleRate/frequency), endpoint = True)
        magnitude.append(np.interp(time,np.linspace(0,len(array[:,i]),len(array[:,i]), endpoint = False),array[:,i]))
    magnitude = np.transpose(magnitude)
    return magnitude

def compute_frequency(frequency):
    freqUnits = values["-FREQUENCY UNITS-"]
    global frequencyFlag
    if freqUnits == 'GHz':
        multiplier = 1e9
    elif freqUnits == 'MHz':
        multiplier = 1e6
    elif freqUnits == 'kHz':
        multiplier = 1e3
    else:
        multiplier = 1
    if values["-FREQUENCY-"] == '':
        frequencyFlag = True
    else:
        frequencyFlag = False
        temp_frequency = float(values["-FREQUENCY-"]) * multiplier
        global sampleRate
        if temp_frequency > sampleRate:
            sg.popup('Error!', 'Frequency must be less than sample rate.')
        else:
            frequency = temp_frequency
    return frequency

def compute_sample_rate():

    if values["-SAMPLE RATE-"] == '100 MHz':
        print(values["-SAMPLE RATE-"])
        return 100e6
    else:
        baseRate = 2.4e9
        return baseRate/(2**sampleRates.index(values["-SAMPLE RATE-"]))

def compute_wave_count(wave_count):
    global waveCountFlag
    temp_wave_count = values["-WAVE COUNT-"]
    if temp_wave_count == waveCounts[0]:
        waveCountFlag = False
        wave_count = temp_wave_count
    else:
        try:
            wave_count = int(temp_wave_count)
            waveCountFlag = False
        except:
            waveCountFlag = True
    return wave_count
def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

file_list_column = [

    # [sg.Image(data=image1, key="-IMAGE")]
    [
        sg.Text("Folder"),
        sg.In(size=(25, 1), enable_events=True, key="-FOLDER-"),
        sg.FolderBrowse(),
    ],
    [
        sg.Listbox(
            values=[], enable_events=True, size=(40, 20), key="-FILE LIST-"
        )
    ],
    [
        sg.Text("Sample Rate"),
        sg.Combo(
            sampleRates, enable_events=True, size=(15,1),readonly=True,
            default_value=sampleRates[0], key="-SAMPLE RATE-"),
    ],
    [
        sg.Text("Frequency    "),
        sg.In(1, enable_events=True, size=(17,1), key="-FREQUENCY-"),
        sg.Combo(units, enable_events=True, size=(4,1), readonly=True,
            default_value = units[1], key="-FREQUENCY UNITS-")
    ],
    [sg.VPush()],
    [sg.Button('Update Graph', key="-UPDATE-",size=(30,1),expand_x = True,
        expand_y = True)
    ],
    [sg.Text("")],
    [sg.VPush()],
    [
        sg.Text("Primary Device ID         "),
        sg.Combo(
            deviceIds, enable_events=True, size=(15,1),readonly=True,
            default_value=deviceIds[0], key="-PRIMARY DEVICE ID-"
        )
    ],
    [
        sg.Text("Secondary Device ID     "),
        sg.Combo(
            secondaryDeviceIds, enable_events=True, size=(15,1),readonly=True,
            default_value=secondaryDeviceIds[2], key="-SECONDARY DEVICE ID-"
        )
    ],
    [
        sg.Text("Wave Count                 "),
        sg.Combo(
            waveCounts, enable_events=True, size=(15,1),
            default_value=waveCounts[0], key="-WAVE COUNT-"
        )
    ],
        [
        sg.Text("Trigger "),
        sg.Combo(
            triggers, enable_events=True, size=(8,1), readonly = True,
            default_value=triggers[4], key="-TRIGGER-"
        ),
        sg.Text("Trigger Channel  "),
        sg.Combo(triggerChannels, enable_events=True, size=(4,1), readonly=True,
            default_value = triggerChannels[0], key="-TRIGGER CHANNEL-")
    ],
    [sg.VPush()],
    [sg.Button('Generate', button_color='white on green', key="-GENERATE-",size=(30,1),expand_x = True,
        expand_y = True)
    ],
    [sg.Text("",key="-GENERATION PROMPT-",expand_x = True,
        expand_y = True, justification = 'center')]
]

# ----- Full layout -----
layout = [
    [
        sg.Column(file_list_column),
        sg.VSeperator(),
        sg.Canvas(size=(650, 650), key='-CANVAS-'),
    ]
]

window = sg.Window("AWG GUI", layout, finalize=True, element_justification='center',resizable=True)
frequency = 1e6
sampleRate = 2.4e9
filename = None
fig_agg = None
frequencyFlag = False
waveCountFlag = False
primary_daq = None
primary_device = None
secondary_daq = None
secondary_device = None
# Run the Event Loop
while True:
    event, values = window.read()
    if event == "Exit" or event == sg.WIN_CLOSED:
        break
    # Folder name was filled in, make a list of files in the folder
    if event == "-FOLDER-":
        folder = values["-FOLDER-"]
        try:
            # Get list of files in folder
            file_list = os.listdir(folder)
        except:
            file_list = []

        fnames = [
            f
            for f in file_list
            if os.path.isfile(os.path.join(folder, f))
            and f.lower().endswith((".csv"))
        ]
        window["-FILE LIST-"].update(fnames)
    if event == "-PRIMARY DEVICE ID-":
        primary_device_id = values["-PRIMARY DEVICE ID-"]
    if event == "-SECONDARY DEVICE ID-":
        secondary_device_id = values["-SECONDARY DEVICE ID-"]
    if event == "-WAVE COUNT-":
        wave_count = compute_wave_count(wave_count)
    if event == "-TRIGGER-":
        trigger = triggers.index(values["-TRIGGER-"])
    if event == "-UPDATE-":
        sampleRate = compute_sample_rate()
        frequency = compute_frequency(frequency)
        if fig_agg != None:
            fig_agg.get_tk_widget().forget()
            # del fig_agg
            fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, create_plot(create_interp_array(filename,compute_frequency(frequency),compute_sample_rate())))
        else:
            sg.popup('Select File.', 'File must be selected to update graph.')
    if event == "-GENERATE-":
        wave_count = compute_wave_count(wave_count)
        primary_device_id = values["-PRIMARY DEVICE ID-"]
        secondary_device_id = values["-SECONDARY DEVICE ID-"]
        trigger = triggers.index(values["-TRIGGER-"])
        trigger_channel = values["-TRIGGER CHANNEL-"]
        sampleRate = compute_sample_rate()
        frequency = compute_frequency(frequency)
        if fig_agg == None:
            sg.popup('Select File.', 'File must be selected to generate waveforms.')
        elif frequencyFlag == True:
            sg.popup('Error!', 'Frequency is not specified.',
                'Please input frequency and try again.')
        elif waveCountFlag == True:
            sg.popup('Error!', 'User defined wave count must be an integer.',
                'Please redefine wavecount and try again.')
        elif primary_device_id == secondary_device_id:
            sg.popup('Error!', 'A device cannot be both primary and secondary.',
                'Please respecify device ids and try again.')
        elif 2 * frequency >= sampleRate:
            sg.popup('Warning!',
                'Ensure the sample rate is at least twice the frequency to prevent aliasing.')
        else:
            if window["-GENERATE-"].get_text() == 'Generate':
                array = create_interp_array(filename,compute_frequency(frequency),compute_sample_rate())
                primary_daq, primary_device = hdawg.configure_api(primary_device_id)
                channel_grouping = 0
                if secondary_device_id != None:
                    channel_grouping = -1
                if primary_daq != None:
                    primary_exp_setting = hdawg.generate_settings(primary_device, array, sampleRate, use = 'primary',
                        trigger = trigger, trigger_channel = trigger_channel, channel_grouping = channel_grouping)
                    hdawg.set_awg_settings(primary_daq, primary_exp_setting)
                    primary_awgModule = hdawg.initiate_AWG(primary_daq, primary_device)
                if secondary_device_id != 'None':
                    secondary_daq, secondary_device = hdawg.configure_api(secondary_device_id)
                    if secondary_daq != None:
                        secondary_exp_setting = hdawg.generate_settings(secondary_device, array, sampleRate, use = 'secondary',
                            trigger = trigger, trigger_channel = trigger_channel, channel_grouping = channel_grouping)
                        hdawg.set_awg_settings(secondary_daq, secondary_exp_setting)
                        mds = hdawg.initiate_mds(primary_daq, primary_device, secondary_device)
                        mds_program = hdawg.generate_mds_program(array, mds, primary_awgModule,
                            trigger = trigger, trigger_channel = trigger_channel, count = wave_count)
                        hdawg.run_awg_program(primary_daq, primary_device, primary_awgModule, mds_program)
                    else:
                        primary_awg_program = hdawg.generate_awg_program(array, primary_awgModule, use = 'primary',
                        trigger = trigger, trigger_channel = trigger_channel, count = wave_count)
                        hdawg.run_awg_program(primary_daq, primary_device, primary_awgModule, primary_awg_program)
                    window["-GENERATE-"].update('Stop!', button_color = 'white on red')
                    window["-GENERATION PROMPT-"].update('AWG is generating waveforms.')
            else:
                hdawg.awg_reset(primary_daq, primary_device)
                if secondary_daq != None:
                    hdawg.awg_reset(secondary_daq, secondary_device)
                window["-GENERATE-"].update('Generate', button_color = 'white on green')
                window["-GENERATION PROMPT-"].update('')
        #sg.popup('Error Generating Waveforms!', 'AWG with Device ID, ' + primary_device_id + ', did not connect.', 'Please Try Again.')
    elif event == "-FILE LIST-":  # A file was chosen from the listbox
        if bool(values["-FILE LIST-"]):
            filename = os.path.join(
                values["-FOLDER-"], values["-FILE LIST-"][0]
            )
            if fig_agg == None:
                fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, create_plot(create_interp_array(filename,compute_frequency(frequency),compute_sample_rate())))
            else:
                fig_agg.get_tk_widget().forget()
                # del fig_agg
                fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, create_plot(create_interp_array(filename,compute_frequency(frequency),compute_sample_rate())))

window.close()
