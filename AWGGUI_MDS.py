# AWGGUI_MDS.py
# Author: Richard McManus

import hdawg
import mds
import time
import PySimpleGUI as sg
import os.path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from sys import platform

if platform == "linux" or platform == "linux2":
    dpi = 40
elif platform == "darwin":
    dpi = 40
elif platform == "win32" or platform == "win64":
    dpi = 80

# Set global values
deviceIds = ['dev8310', 'dev8259'] # HDAWG serial numbers
secondaryDeviceIds = ['dev8310', 'dev8259', 'None'] # HDAWG serial numbers
sampleRates = ['2.4 Gsps','1.2 Gsps','600 Msps','300 Msps','150 Msps', '100 Msps'] # Minimum Sample Rate is 100 Msps; Sample Rates do not need to be discrete
primary_device_id = deviceIds[0]
secondary_device_id = secondaryDeviceIds[1] # Set one device to default
waveCounts = ['Infinite'] 
wave_count = waveCounts[0] # Set default waveCounts to infinite, can specify integer number of waves in GUI
triggers = ['Level','Rising','Falling','Both','None'] # Triggers defined in HDAWG Manual, index is used to set node
trigger = triggers[4] # Default trigger is 'None'
triggerChannels = [1,2,3,4,5,6,7,8] # List of trigger channels
trigger_channel = triggerChannels[0] # Default Trigger Channel is 1
units = ['GHz', 'MHz', 'kHz', 'Hz'] # List of frequency units
sampleRate = 2.4e9
firstTime = True

def create_plot(array): # Function that generates preview plot from 2D array using matplotlib.pyplot
    numCols = len(array[0]) # Number of waves to be plotted
    ax = plt.gca()
    ax.cla()    # Clear the current axes
    ax.grid()   # Enable Grid
    plt.figure(figsize=(8, 6.5), dpi=dpi, facecolor = '#25292E')
    for i in range(numCols):    # Create zero order hold plot of each column
        current_color = ['b', 'g', 'r', 'c', 'm','y','k']   # Vary Colors of each wave
        plt.step(np.linspace(0,len(array[:,i]),len(array[:,i]), endpoint = False), array[:,i], color=current_color[i%7], marker='o',
            markersize = 1, linewidth = 0.75) # Plot
    plt.title(os.path.basename(filename), fontsize=18, color='white') # Title plot with name of csv file
    plt.tick_params(axis='both', labelsize=10, color='white', labelcolor='white')   
    plt.xlabel('Index', fontsize=14, color='white')
    plt.ylabel('Magnitude', fontsize=14, color='white')
    plt.grid(True)
    return plt.gcf()    

def create_interp_array(filename, frequency, sampleRate):   # Function that loads a csv file and interpolates sample points to achieve desired frequency from specified sample rate
    array = np.loadtxt(filename, delimiter=",") # Load csv file into array
    numCols = len(array[0])
    magnitude = [] # Initialize list for y coordinates
    for i in range(numCols): # Interpolate each column/waveform
        time = np.linspace(0, len(array[:,i]), int(sampleRate/frequency), endpoint = True)
        magnitude.append(np.interp(time,np.linspace(0,len(array[:,i]),len(array[:,i]), endpoint = False),array[:,i]))
    magnitude = np.transpose(magnitude)
    return magnitude # Return interpolated 2D array

def compute_frequency(frequency): # Function that converts converts GUI inputs into frequency float
    freqUnits = values["-FREQUENCY UNITS-"]
    global frequencyFlag    # Initialize flag for empty frequency drop down
    global aliasingFlag # Initialize flag for aliasing drop down
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
        temp_frequency = float(values["-FREQUENCY-"]) * multiplier # Compute non-scientific number frequency
        global sampleRate
        if temp_frequency > sampleRate: # Compare frequency specified to current sample rate
            aliasingFlag = True
            sg.popup('Error!', 'Frequency must be less than sample rate.')
        else:
            aliasingFlag = False
            frequency = temp_frequency
    return frequency

def compute_sample_rate():
    if values["-SAMPLE RATE-"] == '100 Msps':    # Hardcoded value for minimum sample rate
        return 100e6
    else:
        baseRate = 2.4e9
        return baseRate/(2**sampleRates.index(values["-SAMPLE RATE-"])) # Calculate sample rate by dividing by 2^n

def compute_wave_count(wave_count):
    global waveCountFlag    # Initialize flag for wave count input not being an integer
    temp_wave_count = values["-WAVE COUNT-"]    
    if temp_wave_count == waveCounts[0]:    # If wave count is infinite
        waveCountFlag = False
        wave_count = temp_wave_count
    else:
        try:
            wave_count = int(temp_wave_count)   # If wave count is an int, use int
            waveCountFlag = False
        except:
            waveCountFlag = True # Raise waveCountFlag if wave count input is not an int
    return wave_count

def draw_figure(canvas, figure): # Initializes figure for plot
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

sg.theme('Dark Grey 14')

file_list_column = [    # Left half of GUI structure
    [   
        sg.Column([
            [sg.Image('Logos.png')],
            [sg.HSeparator()],
            [
                sg.Text("Folder"),  
                sg.In(size=(25, 1), enable_events=True, key="-FOLDER-"),
                sg.FolderBrowse()
            ],
            [sg.Listbox(values=[], enable_events=True, size=(40, 10), key="-FILE LIST-")]
        ], element_justification='center')
    ],
    [   
        sg.Column([
            [sg.Text("Sample Rate")],
            [sg.Text("Frequency")],
        ], element_justification='left'),
        sg.Column([
            [sg.Combo(
                sampleRates, enable_events=True, size=(15,1),readonly=True,
                default_value=sampleRates[0], key="-SAMPLE RATE-")],
            [
                sg.In(1, enable_events=True, size=(17,1), key="-FREQUENCY-"),
                sg.Combo(units, enable_events=True, size=(4,1), readonly=True,
                    default_value = units[1], key="-FREQUENCY UNITS-")]
        ], element_justification='left')
    ],
    [sg.VPush()],
    [sg.Button('Update Graph', key="-UPDATE-",expand_x = True,
        expand_y = True)
    ],
    [sg.Text("")],
    [sg.VPush()],
    [
        sg.Column([
            [sg.Text("Leader Device ID")],
            [sg.Text("Follower Device ID")],
            [sg.Text("Wave Count")],
        ], element_justification='left'),
        sg.Column([
            [sg.Combo(
                deviceIds, enable_events=True, size=(15,1), readonly=True,
                default_value=deviceIds[0], key="-PRIMARY DEVICE ID-")
            ],
            [sg.Combo(
                secondaryDeviceIds, enable_events=True, size=(15,1),readonly=True,
                default_value=secondaryDeviceIds[1], key="-SECONDARY DEVICE ID-")
            ],
            [sg.Combo(
                waveCounts, enable_events=True, size=(15,1),
                default_value=waveCounts[0], key="-WAVE COUNT-")
            ],
        ], element_justification='left')
    ],
    [
        sg.Column([
            [sg.Text("Enable Trigger")]
        ], element_justification='left'),
        sg.Column([
            [sg.Combo(
                triggers, enable_events=True, size=(8,1), readonly = True,
                default_value=triggers[4], key="-ENABLE TRIGGER-"),
                sg.Text("Channel"),
                sg.Combo(triggerChannels, enable_events=True, size=(4,1), readonly=True,
                    default_value = triggerChannels[0], key="-ENABLE TRIGGER CHANNEL-")
            ]
        ], element_justification='left')
    ],
    [sg.VPush()],
    [sg.Button('Program', button_color='white on green', key="-PROGRAM-",size=(30,1),expand_x = True,
        expand_y = True)
    ],
    [sg.Text("",key="-PROGRAM PROMPT-",expand_x = True,
        expand_y = True, justification = 'center')],
    [sg.Button('Enable Output', button_color='white on green', key="-ENABLE-",size=(30,1),expand_x = True,
        expand_y = True, visible=False)],
    [sg.Text("",key="-ENABLE PROMPT-",expand_x = True,
        expand_y = True, justification = 'center')],
]

plot_column = [
    [sg.Canvas(size=(640, 520), key='-CANVAS-')],
    [sg.VPush()],
    [sg.HSeparator()],
    [sg.Output(size=(100, 10))]
]

sequence_column = [
        [
            sg.Text('Leader: ', size=(5,1), font = ("Helvetica", 15), expand_x = True, justification = 'right'),
            sg.Text(primary_device_id, enable_events=True, size=(5,1),
                font = ("Helvetica", 15), key="-PRIMARY SEQUENCE LABEL-", expand_x = True, justification = 'left')
        ],
         [
            sg.Text('Follower: ', size=(5,1), font = ("Helvetica", 15), expand_x = True, justification = 'right'),
            sg.Text(secondary_device_id, enable_events=True, size=(5,1),
                font = ("Helvetica", 15), key="-SECONDARY SEQUENCE LABEL-", expand_x = True, justification = 'left')
        ],
        [sg.HSeparator()],
        [sg.Text(enable_events=True, size=(100,40),
            background_color='#1E2125', key="-SEQUENCE-", justification = 'left')]          
]

tab1_layout = [  
    [
        sg.Column(file_list_column),
        sg.VSeperator(),
        sg.Column(plot_column, element_justification='center')
    ]
]

tab2_layout = [  
    [
        sg.Column(sequence_column, element_justification='center'),
    ]
]

# ----- Full layout -----
layout = [
    [
        sg.TabGroup([
            [
                sg.Tab('Control Panel', tab1_layout),
                sg.Tab('Sequences', tab2_layout, element_justification='center'),
            ]
        ])
    ]
]

# ---- Program Window ----
window = sg.Window("AWG GUI by Richard McManus (2023)", layout, finalize=True,
    element_justification='center', resizable=True)

# ----- Initialize Global Veriables needed for event loop -----
frequency = 1e6
sampleRate = 2.4e9
filename = None
fig_agg = None
frequencyFlag = False
aliasingFlag = False
waveCountFlag = False
primary_daq = None
primary_device = None
primary_awgModule = None
secondary_daq = None
secondary_device = None

# Specify path
path = os.path.join(os.getcwd(), 'Waves')

# Check whether the specified
# path exists or not
pathExists = os.path.exists(path)

if pathExists:
    window["-FOLDER-"].update(path)
    window.write_event_value("-FOLDER-", path)
    
# Run the Event Loop
while True:

    event, values = window.read(timeout = 100) # Read values from window
    if event == "Exit" or event == sg.WIN_CLOSED:
        break

    # If Folder name was filled in, make a list of files in the folder
    if event == "-FOLDER-":
        folder = values["-FOLDER-"]
        try:
            # Get list of files in folder
            file_list = os.listdir(folder)
        except:
            file_list = []

        fnames = [ # Only lists files with type .csv
            f
            for f in file_list
            if os.path.isfile(os.path.join(folder, f))
            and f.lower().endswith((".csv"))
        ]
        window["-FILE LIST-"].update(fnames)

    if event == "-PRIMARY DEVICE ID-":
        primary_device_id = values["-PRIMARY DEVICE ID-"]
        window["-PRIMARY SEQUENCE LABEL-"].update(primary_device_id)
    
    if event == "-SECONDARY DEVICE ID-":
        secondary_device_id = values["-SECONDARY DEVICE ID-"]
        window["-SECONDARY SEQUENCE LABEL-"].update(secondary_device_id)
    
    if event == "-WAVE COUNT-":
        wave_count = compute_wave_count(wave_count)
    
    if event == "-ENABLE TRIGGER-":
        enable_trigger = triggers.index(values["-ENABLE TRIGGER-"])

    if event == "-SAMPLE RATE-":
        sampleRate = compute_sample_rate()

    # Updates plot
    if event == "-UPDATE-":
        sampleRate = compute_sample_rate()
        frequency = compute_frequency(frequency)
        if aliasingFlag == False and frequencyFlag == False:
            if fig_agg != None:
                fig_agg.get_tk_widget().forget()
                # del fig_agg
                fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, create_plot(create_interp_array(filename,compute_frequency(frequency),compute_sample_rate())))
            else:
                sg.popup('Select File.', 'File must be selected to update graph.')

    # Programs sequence and sends to HDAWGs 
    if event == "-PROGRAM-":
        if window["-PROGRAM-"].get_text() == 'Program':   # Current event is to generate and program
            # Updates input values
            wave_count = compute_wave_count(wave_count)
            primary_device_id = values["-PRIMARY DEVICE ID-"]
            secondary_device_id = values["-SECONDARY DEVICE ID-"]
            enable_trigger = triggers.index(values["-ENABLE TRIGGER-"])
            enable_trigger_channel = values["-ENABLE TRIGGER CHANNEL-"]
            sampleRate = compute_sample_rate()
            frequency = compute_frequency(frequency)

            if fig_agg == None: # Plot has not been generated
                sg.popup('Select File.', 'File must be selected to generate waveforms.')
                
            elif waveCountFlag == True: # Wave count is not an integer or 'Infinite'
                sg.popup('Error!', 'User defined wave count must be an integer.',
                    'Please redefine wavecount and try again.')

            elif primary_device_id == secondary_device_id:  # Cannot specify device to be primary and secondary
                sg.popup('Error!', 'A device cannot be both primary and secondary.',
                    'Please respecify device ids and try again.')

            elif 2 * frequency >= sampleRate:   # Warn user aliasing will occur
                sg.popup('Warning!',
                    'Ensure the sample rate is at least twice the frequency to prevent aliasing.')

            elif frequencyFlag == False and aliasingFlag == False:   # No flags raised
                    print('Programming... Please Wait.')
                    window.refresh() 
                    print('Interpolating Waveform Array...')   
                    window.refresh() 
                    array = create_interp_array(filename,compute_frequency(frequency),compute_sample_rate())
                    daq = mds.configure_api()    # Establish connection to local server Zurich LabOne API
                    channel_grouping = -1    # Initialize channel grouping to mds
                    if daq != None:
                        print('Generating settings for ' + primary_device_id)
                        primary_exp_setting = mds.generate_settings(primary_device_id, array, sampleRate, use = 'primary',
                            trigger = enable_trigger, trigger_channel = enable_trigger_channel, channel_grouping = channel_grouping)  # Generate list of settings 
                        window.refresh()
                        mds.set_awg_settings(daq, primary_exp_setting)    # Program HDAWG with settings
                        primary_awgModule = hdawg.initiate_AWG(daq, primary_device_id) # Initialize awgModule                            
                        
                        if secondary_device_id != 'None':
                            print('Generating settings for ' + secondary_device_id)
                            window.refresh() 
                            secondary_exp_setting = mds.generate_settings(secondary_device_id, array, sampleRate, use = 'secondary',
                                channel_grouping = channel_grouping)  # Generate list of settings 
                            hdawg.set_awg_settings(daq, secondary_exp_setting)    # Program HDAWG with settings
                            secondary_awgModule = hdawg.initiate_AWG(daq, secondary_device_id) # Initialize awgModule 
                        
                    print('Initiating Multi-Device Sync Module')
                    mds.initiate_mds(daq, primary_device_id, secondary_device_id)
                    window.refresh()                        
                    mds_program = mds.generate_mds_program(array, primary_awgModule, # Generate program for mds
                        trigger = enable_trigger, trigger_channel = enable_trigger_channel, count = wave_count)
                    
                    window["-SEQUENCE-"].update(mds_program)
        #                     # hdawg.run_awg_program(primary_daq, primary_device, primary_awgModule, primary_awg_program)  # Program single HDAWG with awg program
        #                     # window.refresh()
        #                 window["-PROGRAM-"].update('Reset!', button_color = 'white on red') # Switch button to 'Reset!'
        #                 window["-PROGRAM PROMPT-"].update('Programming Successful.')
        #                 window["-ENABLE-"].update(visible=True) # Show Enable Button
            
        # else:
        #     hdawg.awg_reset(daq, primary_device_id)    # Turn off enable 
        #     window["-PRIMARY SEQUENCE-"].update('')
        #     window.refresh()
        #     if secondary_device_id != None:
        #         hdawg.awg_reset(daq, secondary_device_id)    # Turn off enable
        #         window.refresh()
        #         window["-SECONDARY SEQUENCE-"].update('')
        #     window["-PROGRAM-"].update('Program', button_color = 'white on green')    # Switch button to 'Program'
        #     window["-PROGRAM PROMPT-"].update('')
        #     window["-ENABLE-"].update('Enable Output', button_color = 'white on green', visible=False) # Switch button to 'Enable Output!'
        #     window["-ENABLE PROMPT-"].update('')

        #sg.popup('Error Generating Waveforms!', 'AWG with Device ID, ' + primary_device_id + ', did not connect.', 'Please Try Again.')
    
    if event == "-ENABLE-":
        if window["-PROGRAM-"].get_text() == 'Program':   # AWGs are not programed
            sg.popup('Error!',
                'AWGs are not programmed.', 'Please program AWGs and then enable output.')
        else:
            if window["-ENABLE-"].get_text() == 'Enable Output':   # Current event is to generate and program
                if secondary_daq != None:
                    hdawg.awg_enable(secondary_daq, secondary_device) 
                    window.refresh()
                    time.sleep(0.1)
                if primary_daq != None:
                    hdawg.awg_enable(primary_daq, primary_device) 
                    window.refresh()
                window["-ENABLE-"].update('Disable Output!', button_color = 'white on red') # Switch button to 'Disable Output!'
                window["-ENABLE PROMPT-"].update('Output Enabled.')
                time.sleep(0.2)
            else:
                if secondary_daq != None:
                    hdawg.awg_disable(secondary_daq, secondary_device) 
                    window.refresh()
                if primary_daq != None:
                    hdawg.awg_disable(primary_daq, primary_device)
                    window.refresh()
                window["-ENABLE-"].update('Enable Output', button_color = 'white on green') # Switch button to 'Enable Output!'
                window["-ENABLE PROMPT-"].update('')
                
    if primary_awgModule != None and window["-PROGRAM-"].get_text() != 'Program':
       if hdawg.awg_get_enable(primary_awgModule) != 1 and window["-ENABLE-"].get_text() != 'Enable Output':
            print("Sequence Complete")
            window.refresh()
            window["-ENABLE-"].update('Enable Output', button_color = 'white on green') # Switch button to 'Enable Output!'
            window["-ENABLE PROMPT-"].update('')

    if event == "-FILE LIST-":  # A file was chosen from the listbox
        if bool(values["-FILE LIST-"]):
            filename = os.path.join(    # Specify chosen file
                values["-FOLDER-"], values["-FILE LIST-"][0]
            )
            
            if fig_agg == None: # Generate and populate plot
                fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, create_plot(create_interp_array(filename,compute_frequency(frequency),compute_sample_rate())))
            
            else: # Clear and update plot
                fig_agg.get_tk_widget().forget()    
                # del fig_agg
                fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, create_plot(create_interp_array(filename,compute_frequency(frequency),compute_sample_rate())))

window.close()
