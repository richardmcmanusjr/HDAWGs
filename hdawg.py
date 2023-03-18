import textwrap
import numpy as np
import os
import zhinst.utils
import time

def rotateWave(arr,d,n):
    temp_arr = arr[d:n]
    temp_arr = np.append(temp_arr,arr[0:d])
    return temp_arr

def configure_api(
    device_id,
    server_host: str = "localhost",
    server_port: int = 8004,
):
    try:
        # Settings
        apilevel = 6  # The API level supported by this example.
        # Call a zhinst utility function that returns:
        # - an API session `daq` in order to communicate with devices via the data server.
        # - the device ID string that specifies the device branch in the server's node hierarchy.
        # - the device's discovery properties.
        (daq, device, _) = zhinst.utils.create_api_session(
            device_id, apilevel, server_host=server_host, server_port=server_port
        )
        zhinst.utils.api_server_version_check(daq)

        # Create a base configuration: Disable all available outputs, awgs, demods, scopes,...
        zhinst.utils.disable_everything(daq, device)

        # 'system/awg/channelgrouping' : Configure how many independent sequencers
        #   should run on the AWG and how the outputs are grouped by sequencer.
        #   0 : 4x2 with HDAWG8; 2x2 with HDAWG4.
        #   1 : 2x4 with HDAWG8; 1x4 with HDAWG4.
        #   2 : 1x8 with HDAWG8.
        # Configure the HDAWG to use one sequencer for each pair of output channels
        daq.setInt(f"/{device}/system/awg/channelgrouping", 2)

        return daq, device
    except:
        return None, None

def generate_settings(
    device, array, sampleRate, use = 'primary', awg_range = 1.2, 
    amplitude = 1.2, trigger = '4', trigger_channel = 1, channel_grouping = 0
):
    numCols = int(len(array[0])) # 2 columns in your example
    
    if use == 'primary':
        reference_clock_source = 1
    else:
        reference_clock_source = 0
    # print(numCols)
    exp_setting = [
        ["/%s/awgs/0/outputs/0/modulation/mode" % device, 0],
        ["/%s/awgs/0/time" % device, 0],
        ["/%s/awgs/0/userregs/0" % device, 0],
        ["/%s/system/clocks/sampleclock/freq" % device, sampleRate],
        ["/%s/system/clocks/referenceclock/source" % device, reference_clock_source],
        ["/%s/system/awg/channelgrouping" % device, channel_grouping]
    ]

    if trigger >= 0 and trigger < 4:
        exp_setting.append(["/%s/awgs/0/auxtriggers/0/channel" % device, trigger_channel - 1])
        exp_setting.append(["/%s/awgs/0/auxtriggers/0/slope" % device, trigger])

    if reference_clock_source == 1:
        for i in range(min(numCols,8)):
            exp_setting.append(["/%s/sigouts/%d/on" % (device, i), 1])
            exp_setting.append(["/%s/sigouts/%d/range" % (device, i), awg_range])
            exp_setting.append(["/%s/awgs/0/outputs/%d/amplitude" % (device, i), amplitude])

    if reference_clock_source == 0 and numCols > 8:
        for i in range(min(numCols - 8, 16)):
            exp_setting.append(["/%s/sigouts/%d/on" % (device, i), 1])
            exp_setting.append(["/%s/sigouts/%d/range" % (device, i), awg_range])
            exp_setting.append(["/%s/awgs/0/outputs/%d/amplitude" % (device, i), amplitude])
    # print(exp_setting)
    #  generate_settings('dev8259',[[0,1,2,3]],100)
    return exp_setting

def set_awg_settings(daq, exp_setting):
    daq.set(exp_setting)
    # Ensure that all settings have taken effect on the device before continuing.
    daq.sync()

def initiate_AWG(daq, device):
    awgModule = daq.awgModule()
    awgModule.set("device", device)
    awgModule.set("index", 0)
    awgModule.execute()
    return awgModule

def generate_awg_program(array, awgModule, use = 'primary', trigger = '4', trigger_channel = 1, marker = None, count = 'Infinite', seq_clk_offset = 0, sample_clk_offset = 0):
    data_dir = awgModule.getString("directory")
    wave_dir = os.path.join(data_dir, "awg", "waves")
    if not os.path.isdir(wave_dir):
        # The data directory is created by the AWG module and should always exist. If this exception
        # is raised, something might be wrong with the file system.
        raise Exception(
            f"AWG module wave directory {wave_dir} does not exist or is not a directory"
        )

    awg_program = textwrap.dedent(
        """\
        var run = 1;
        """
    )

    numCols = int(len(array[0])) 

    index = None
    offset = None
    if use == 'primary':
        sample_clk_offset = 0
        index = min(8,numCols)
        offset = - 1
    else:
        index = min(8,numCols - 8)
        offset = 7
    for i in range(1, index + 1, 1):
        csv_file = os.path.join(wave_dir, "wave" + str(i) + ".csv")
        current_wave = array[:, i + offset]
        if sample_clk_offset != 0:
            current_wave = rotateWave(current_wave, int(sample_clk_offset), len(current_wave))            
        np.savetxt(csv_file, current_wave)
        awg_program = awg_program + textwrap.dedent(
            """\
            wave w""" + str(i) + """ = "wave""" + str(i) + """";
            """
        )

    if trigger >= 0 and trigger < 4:
        awg_program = awg_program + textwrap.dedent(
            """\
            while(run){
            waitDigTrigger(""" + str(trigger_channel) + """);
            """
        )

    if marker != None:
        marker_binary = list('0b0000')
        marker_binary[6 - marker] = '1'
        marker_binary = ''.join(marker_binary)
        awg_program = awg_program + textwrap.dedent(
        """\
        setTrigger(""" + marker_binary + """);
        wait(""" + str(seq_clk_offset) + """);
        setTrigger(0);
        """
        )

    if count == "Infinite":
        awg_program = awg_program + textwrap.dedent(
            """\
            while(run){
            playWave("""
        )
    else:
        awg_program = awg_program + textwrap.dedent(
            """\
            repeat(""" + str(count) + """){
            playWave("""
        )
    for i in range(1, index + 1,1):
        if i != index:
            awg_program = awg_program + textwrap.dedent(
                str(i) + ", w" + str(i) + ", "
            )

        else:
            awg_program = awg_program + textwrap.dedent(
                str(i) + ", w" + str(i) + """);
                """
            )
            awg_program = awg_program + textwrap.dedent(
                """\
                }
                """
            )
    if trigger >= 0 and trigger < 4:
        awg_program = awg_program + textwrap.dedent(
            """\
            }
            """
            )
    return awg_program

def run_awg_program(daq, device, awgModule, awg_program):
    # Transfer the AWG sequence program. Compilation starts automatically.
    awgModule.set("compiler/sourcestring", awg_program)
    # Note: when using an AWG program from a source file (and only then), the compiler needs to
    # be started explicitly with awgModule.set('compiler/start', 1)
    while awgModule.getInt("compiler/status") == -1:
        time.sleep(0.1)

    if awgModule.getInt("compiler/status") == 1:
        # compilation failed, raise an exception
        raise Exception(awgModule.getString("compiler/statusstring"))

    if awgModule.getInt("compiler/status") == 0:
        print(
            "Compilation successful with no warnings, will upload the program to device " + device
        )
    if awgModule.getInt("compiler/status") == 2:
        print(
            "Compilation successful with warnings, will upload the program to device " + device
        )
        print("Compiler warning: ", awgModule.getString("compiler/statusstring"))

    # Wait for the waveform upload to finish
    time.sleep(0.2)
    i = 0
    while (awgModule.getDouble("progress") < 1.0) and (
        awgModule.getInt("elf/status") != 1
    ):
        print(f"{i} progress: {awgModule.getDouble('progress'):.2f}")
        time.sleep(0.2)
        i += 1
    print(f"{i} progress: {awgModule.getDouble('progress'):.2f}")
    if awgModule.getInt("elf/status") == 0:
        print("Upload to device " + device + " successful.")
    if awgModule.getInt("elf/status") == 1:
        raise Exception("Upload to device " + device + "failed.")
    
    return awgModule.getInt("elf/status")

def awg_enable(daq, device):
    daq.setInt(f"/{device}/awgs/0/enable", 1)
    print('Device ' + device + ' enabled.')

def awg_get_enable(awgModule):
    return awgModule.getInt("awg/enable")

def awg_disable(daq, device):
    daq.setInt(f"/{device}/awgs/0/enable", 0)
    print('Device ' + device + ' disabled.')

def awg_reset(daq, device):
    exp_setting = [["/%s/AWGS/0/RESET" % device, 1]]
    set_awg_settings(daq, exp_setting)
    print("Device %s program cleared" % device)

def awg_waveform_playing(daq, device):
    return daq.getInt("/{device}/AWGS/n/WAVEFORM/PLAYING")
    
