import psutil

### get running simulator ###

def get_running_processes():
    process_list = []
    
    for process in psutil.process_iter(['pid', 'name']):
        process_list.append(process.info)

    return process_list

def check_simulator(process_name, simulator_lists):
    for simulator, names in simulator_lists.items():
        if process_name.lower() in names:
            return simulator
    return None

def auto_scan_simulators():
    simulator_list = []
    simulator_lists = {
        'BlueStacks 5': ['hd-player.exe'], # 此处并不能区分蓝叠中国版和国际版，但结束进程和启动模拟器可以自动区分
        '夜神模拟器': ['nox.exe'],
        'MuMu 12': ['mumuplayer.exe'],
        '雷电模拟器': ['dnplayer.exe'],
        '逍遥模拟器': ['MEmu.exe']
        # 添加其他模拟器的名称和对应进程名
    }

    running_processes = get_running_processes()

    for process in running_processes:
        process_name = process['name'].lower()
        simulator = check_simulator(process_name, simulator_lists)
        
        if simulator:
            simulator_list.append(simulator)

    return simulator_list

### End get running simulator ###