import textwrap
import numpy as np
import os
import zhinst.core
import zhinst.utils
import time

def configure_api(
    server_host: str = 'localhost',
    server_port: int = 8004,
    apilevel: int = 6
):
    try:
        # Settings
        # Call a zhinst utility function that returns:
        # - an API session `daq` in order to communicate with devices via the data server.
        # - the device ID string that specifies the device branch in the server's node hierarchy.
        # - the device's discovery properties.
        daq = zhinst.core.ziDAQServer(server_host, server_port, apilevel)
        return daq
    except:
        return None

def generate_settings(
    device, array, sampleRate, use = 'primary', awg_range = 1.2, 
    amplitude = 1.2, trigger = 4, trigger_channel = 1, channel_grouping = -1
):
    numCols = int(len(array[0])) # 2 columns in your example
    
    reference_clock_source = 1

    exp_setting = [
        ["/%s/awgs/0/outputs/0/modulation/mode" % device, 0],
        ["/%s/awgs/0/time" % device, 0],
        ["/%s/awgs/0/userregs/0" % device, 0],
        ["/%s/system/clocks/sampleclock/freq" % device, sampleRate],
        ["/%s/system/clocks/referenceclock/source" % device, reference_clock_source],
        ["/%s/system/awg/channelgrouping" % device, channel_grouping],
        ["/%s/triggers/out/0/delay" % device , 0]
    ]

    if trigger >= 0 and trigger < 4:
        exp_setting.append(["/%s/awgs/0/auxtriggers/0/channel" % device, trigger_channel - 1])
        exp_setting.append(["/%s/awgs/0/auxtriggers/0/slope" % device, trigger])

    if use == 'primary':
        for i in range(min(numCols,8)):
            exp_setting.append(["/%s/sigouts/%d/on" % (device, i), 1])
            exp_setting.append(["/%s/sigouts/%d/range" % (device, i), awg_range])
            exp_setting.append(["/%s/awgs/0/outputs/%d/amplitude" % (device, i), amplitude])

    if use != 'primary' and numCols > 8:
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

def initiate_mds(daq, device_1, device_2):
    mds = daq.multiDeviceSyncModule()
    mds.set("group", 0)
    mds.set("recover", 0)
    mds.set("recover", 1)
    mds.execute()
    mds.set("devices", device_1 + ',' + device_2)
    mds.set("start", 1)
    time.sleep(0.2)
    message = None
    while mds.getInt("/status") != -1 and mds.getInt("/status") != 2:
        temp_message = mds.getString("/message")
        if  temp_message != message:
            message = temp_message
            print(message)
        time.sleep(0.1)

    if mds.getInt("/status") == -1:
        print("Synchronization failed.")
        print(mds.getString("/message"))

    if mds.getInt("/status") == 2:
        print(
            "Synchronization successful."
        )

    # Wait for the mds
    time.sleep(0.2)
    return mds

def generate_mds_program(array, awgModule, trigger = 4, trigger_channel = 1, count = 'Infinite'):
    data_dir = awgModule.getString("directory")
    wave_dir = os.path.join(data_dir, "awg", "waves")
    if not os.path.isdir(wave_dir):
        # The data directory is created by the AWG module and should always exist. If this exception
        # is raised, something might be wrong with the file system.
        raise Exception(
            f"AWG module wave directory {wave_dir} does not exist or is not a directory"
        )

    mds_program = textwrap.dedent(
        """\
        var run = 1;
        """
    )

    numCols = int(len(array[0])) 

    for i in range(1, numCols+1):
        csv_file = os.path.join(wave_dir, "wave" + str(i) + ".csv")
        np.savetxt(csv_file, array[:, i-1])
        mds_program = mds_program + textwrap.dedent(
            """\
            wave w""" + str(i) + """ = "wave""" + str(i) + """";
            """
        )

    if trigger >= 0 and trigger < 4:
        mds_program = mds_program + textwrap.dedent(
            """\
            waitDigTrigger(""" + str(trigger_channel) + """);
            """
        )

    # if count == "Infinite":
    #     mds_program = mds_program + textwrap.dedent(
    #         """\
    #         while(run){
    #         playWave("""
    #     )
    # else:
    #     mds_program = mds_program + textwrap.dedent(
    #         """\
    #         repeat(""" + str(count) + """){
    #         playWave("""
    #     )
    # for i in range(1, numCols + 1):
    #     if i != numCols:
    #         mds_program = mds_program + textwrap.dedent(
    #             str(i) + ", w" + str(i) + ", "
    #         )

    #     else:
    #         mds_program = mds_program + textwrap.dedent(
    #             str(i) + ", w" + str(i) + """);
    #             """
    #         )
    #         mds_program = mds_program + textwrap.dedent(
    #             """\
    #             }
    #             """
    #         )
    # print(mds_program)
    return mds_program

def run_mds_program(daq, device_1, device_2, awgModule, awg_program):
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
            "Compilation successful with no warnings, will upload the program to the HDAWG."
        )
    if awgModule.getInt("compiler/status") == 2:
        print(
            "Compilation successful with warnings, will upload the program to the HDAWG."
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
        print("Upload to the HDAWG successful.")
    if awgModule.getInt("elf/status") == 1:
        raise Exception("Upload to the HDAWG failed.")

    return awgModule.getInt("elf/status")
