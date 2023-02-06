# AWGGUI_IMP.py
# Author: Richard McManus

import hdawg
import time
import PySimpleGUI as sg
import os.path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Set global values
deviceIds = ['dev8310', 'dev8259'] # HDAWG serial numbers
sampleRates = ['2.4 Gsps','1.2 Gsps','600 Msps','300 Msps','150 Msps', '100 Msps'] # Minimum Sample Rate is 100 Msps; Sample Rates do not need to be discrete
primary_device_id = deviceIds[0]
secondaryDeviceIds = deviceIds
secondaryDeviceIds.append('None') # Allow user to use only primary device
secondary_device_id = deviceIds[2] # Set one device to default
waveCounts = ['Infinite'] 
wave_count = waveCounts[0] # Set default waveCounts to infinite, can specify integer number of waves in GUI
triggers = ['Level','Rising','Falling','Both','None'] # Triggers defined in HDAWG Manual, index is used to set node
trigger = triggers[4] # Default trigger is 'None'
triggerChannels = [1,2,3,4,5,6,7,8] # List of trigger channels
trigger_channel = triggerChannels[0] # Default Trigger Channel is 1
units = ['GHz', 'MHz', 'kHz', 'Hz'] # List of frequency units
firstTime = True

def create_plot(array): # Function that generates preview plot from 2D array using matplotlib.pyplot
    numCols = len(array[0]) # Number of waves to be plotted
    ax = plt.gca()
    ax.cla()    # Clear the current axes
    ax.grid()   # Enable Grid
    plt.figure(facecolor = '#ebeded')   # Set color of figure
    for i in range(numCols):    # Create zero order hold plot of each column
        current_color = ['b', 'g', 'r', 'c', 'm','y','k']   # Vary Colors of each wave
        plt.step(np.linspace(0,len(array[:,i]),len(array[:,i]), endpoint = False), array[:,i], color=current_color[i%7], marker='o',
            markersize = 1, linewidth = 0.75) # Plot
    plt.title(os.path.basename(filename), fontsize=8) # Title plot with name of csv file
    plt.tick_params(axis='both', labelsize=4)   
    plt.xlabel('Index', fontsize=6)
    plt.ylabel('Magnitude', fontsize=6)
    plt.grid(True)
    return plt.gcf()    

def create_interp_array(filename, frequency, sampleRate):   # Function that loads a csv file and interpolates sample points to achieve desired frequency from specified sample rate
    array = np.loadtxt(filename, delimiter=",") # Load csv file into array
    numCols = len(array[0]) # 2 columns in your example
    magnitude = [] # Initialize list for y coordinates
    for i in range(numCols): # Interpolate each column/waveform
        time = np.linspace(0, len(array[:,i]), int(sampleRate/frequency), endpoint = True)
        magnitude.append(np.interp(time,np.linspace(0,len(array[:,i]),len(array[:,i]), endpoint = False),array[:,i]))
    magnitude = np.transpose(magnitude)
    return magnitude # Return interpolated 2D array

def compute_frequency(frequency): # Function that converts converts GUI inputs into frequency float
    freqUnits = values["-FREQUENCY UNITS-"]
    global frequencyFlag    # Initialize flag for empty frequency drop down
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
            sg.popup('Error!', 'Frequency must be less than sample rate.')
        else:
            frequency = temp_frequency
    return frequency

def compute_sample_rate():
    if values["-SAMPLE RATE-"] == '100 Msps':    # Hardcoded value for minimum sample rate
        print(values["-SAMPLE RATE-"])
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

file_list_column = [    # Left half of GUI structure

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

# ---- Generate Window ----
window = sg.Window("AWG GUI", layout, finalize=True, element_justification='center',resizable=True)

# ----- Initialize Global Veriables needed for event loop -----
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
    event, values = window.read() # Read values from window
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
    
    if event == "-SECONDARY DEVICE ID-":
        secondary_device_id = values["-SECONDARY DEVICE ID-"]
    
    if event == "-WAVE COUNT-":
        wave_count = compute_wave_count(wave_count)
    
    if event == "-TRIGGER-":
        trigger = triggers.index(values["-TRIGGER-"])
    
    # Updates plot
    if event == "-UPDATE-":
        sampleRate = compute_sample_rate()
        frequency = compute_frequency(frequency)
        if fig_agg != None:
            fig_agg.get_tk_widget().forget()
            # del fig_agg
            fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, create_plot(create_interp_array(filename,compute_frequency(frequency),compute_sample_rate())))
        else:
            sg.popup('Select File.', 'File must be selected to update graph.')
    
    # Generates sequence and sends to HDAWGs 
    if event == "-GENERATE-":
        # Updates input values
        wave_count = compute_wave_count(wave_count)
        primary_device_id = values["-PRIMARY DEVICE ID-"]
        secondary_device_id = values["-SECONDARY DEVICE ID-"]
        trigger = triggers.index(values["-TRIGGER-"])
        trigger_channel = values["-TRIGGER CHANNEL-"]
        sampleRate = compute_sample_rate()
        frequency = compute_frequency(frequency)

        if fig_agg == None: # Plot has not been generated
            sg.popup('Select File.', 'File must be selected to generate waveforms.')

        elif frequencyFlag == True: # Frequency is not specified
            sg.popup('Error!', 'Frequency is not specified.',
                'Please input frequency and try again.')

        elif waveCountFlag == True: # Wave count is not an integer or 'Infinite'
            sg.popup('Error!', 'User defined wave count must be an integer.',
                'Please redefine wavecount and try again.')

        elif primary_device_id == secondary_device_id:  # Cannot specify device to be primary and secondary
            sg.popup('Error!', 'A device cannot be both primary and secondary.',
                'Please respecify device ids and try again.')

        elif 2 * frequency >= sampleRate:   # Warn user aliasing will occur
            sg.popup('Warning!',
                'Ensure the sample rate is at least twice the frequency to prevent aliasing.')

        else:   # No flags raised
            if window["-GENERATE-"].get_text() == 'Generate':   # Current event is to generate and program
                array = create_interp_array(filename,compute_frequency(frequency),compute_sample_rate())
                primary_daq, primary_device = hdawg.configure_api(primary_device_id)    # Establish connection to local server Zurich LabOne API
                channel_grouping = 0    # Initialize channel grouping to 1 x 8 (cores x channels)
                
                if secondary_device_id != None:
                    channel_grouping = -1   # Set channel grouping to mds
                
                if primary_daq != None:
                    primary_exp_setting = hdawg.generate_settings(primary_device, array, sampleRate, use = 'primary',
                        trigger = trigger, trigger_channel = trigger_channel, channel_grouping = channel_grouping)  # Generate list of settings 
                    hdawg.set_awg_settings(primary_daq, primary_exp_setting)    # Program HDAWG with settings
                    primary_awgModule = hdawg.initiate_AWG(primary_daq, primary_device) # Initialize awgModule 
                
                if secondary_device_id != 'None':
                    secondary_daq, secondary_device = hdawg.configure_api(secondary_device_id)  # Establish connection to the same local server using Zurich LabOne API
                    if secondary_daq != None:   
                        secondary_exp_setting = hdawg.generate_settings(secondary_device, array, sampleRate, use = 'secondary',
                            trigger = trigger, trigger_channel = trigger_channel, channel_grouping = channel_grouping)  # Generate list of settings 
                        hdawg.set_awg_settings(secondary_daq, secondary_exp_setting)    # Program HDAWG with settings
                        mds = hdawg.initiate_mds(primary_daq, primary_device, secondary_device) # Initialize multi-device sync (mds) module
                        mds_program = hdawg.generate_mds_program(array, mds, primary_awgModule, # Generate program for mds module
                            trigger = trigger, trigger_channel = trigger_channel, count = wave_count)   
                        hdawg.run_awg_program(primary_daq, primary_device, primary_awgModule, mds_program)  # Program primary HDAWG with mds program
                    
                    else:
                        primary_awg_program = hdawg.generate_awg_program(array, primary_awgModule, use = 'primary', # Generate program for single HDAWG
                        trigger = trigger, trigger_channel = trigger_channel, count = wave_count)
                        hdawg.run_awg_program(primary_daq, primary_device, primary_awgModule, primary_awg_program)  # Program single HDAWG with awg program
                    window["-GENERATE-"].update('Stop!', button_color = 'white on red') # Switch button to 'Stop!'
                    window["-GENERATION PROMPT-"].update('AWG is generating waveforms.')
            
            else:
                hdawg.awg_reset(primary_daq, primary_device)    # Turn off enable 
                if secondary_daq != None:
                    hdawg.awg_reset(secondary_daq, secondary_device)    # Turn off enable
                window["-GENERATE-"].update('Generate', button_color = 'white on green')    # Switch button to 'Generate'
                window["-GENERATION PROMPT-"].update('')
        #sg.popup('Error Generating Waveforms!', 'AWG with Device ID, ' + primary_device_id + ', did not connect.', 'Please Try Again.')
    
    elif event == "-FILE LIST-":  # A file was chosen from the listbox
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
