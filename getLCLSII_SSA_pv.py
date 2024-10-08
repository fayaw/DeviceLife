def getLCLSII_SSA_pv(LinacSection, Cryomodule, Cavity):
    """
    LinacSection: LCLSII linac section, 0, 1, 2, 3
    CryoModule: cryomodule ID
    Cavity: 1 - 8
    """
    
    # Validate inputs
    if not isinstance(LinacSection, int):
        raise TypeError("LinacSection must be an integer")
    if not isinstance(Cryomodule, int):
        raise TypeError("Cryomodule must be an integer")
    if not isinstance(Cavity, int):
        raise TypeError("Cavity must be an integer")

    # Validate LinacSection and Cryomodule and Cavity
    if LinacSection not in [0, 1, 2, 3]:
        raise ValueError("LinacSection must be 0, 1, 2, or 3")
    
    if LinacSection == 0 and Cryomodule != 1:
        raise ValueError("For LinacSection 0, Cryomodule must be 1")
    elif LinacSection == 1 and Cryomodule not in [2, 3]:
        raise ValueError("For LinacSection 1, Cryomodule must be 2 or 3")
    elif LinacSection == 2 and not (4 <= Cryomodule <= 15):
        raise ValueError("For LinacSection 2, Cryomodule must be between 4 and 15")
    elif LinacSection == 3 and not (16 <= Cryomodule <= 35):
        raise ValueError("For LinacSection 3, Cryomodule must be between 16 and 35")
    
    if not (1 <= Cavity <= 8):
        raise ValueError("Cavity must be between 1 and 8")
    
    # Create PVs
    ssa_header = ""

    if Cryomodule < 10:
        ssa_header = f'ACCL:L{LinacSection}B:0{Cryomodule}{Cavity}0:SSA'
    else:
        ssa_header = f'ACCL:L{LinacSection}B:{Cryomodule}{Cavity}0:SSA'

    drv_ps_volt = []       # ps voltage for driver
    drv_ps_cur = []        # ps current for driver
    drv_pwr_mW = []        # driver output power in mW

    amp_ps_volt = []       # ps voltage
    amp_ps_cur = []        # ps current
    amp_pwr = []       # power for each amp
    ssa_fwd_pwr = f'{ssa_header}:FwdPwr' # total forward power
    ssa_ref_pwr = f'{ssa_header}:RefPwr' # total reflected power

    # temperature and cooling
    temp_cooling = {
        'HSink': [],    # heatsink temperature
        'CltrAir': [],  # cooler air temperature
        'PSAir': [],    # power supply air temperature
        'HeatExcInAir': [],     # heat exchanger inlet air temperature
        'LCWIn': [],    # LCW cooling water inlet temperature
        'LCWOut': [],    # LCW cooling water outlet temperature
        'LCWFlowRate': [],  # LCW cooling water flow rate
        'FanSpeed': []  # fan speed
    }
    temp_cooling['HSink'].append(f'{ssa_header}:DA_HSTemp')
    temp_cooling['CltrAir'].append(f'{ssa_header}:CtrlAirTemp')
    temp_cooling['PSAir'].append(f'{ssa_header}:PSAirTemp')
    temp_cooling['HeatExcInAir'].append(f'{ssa_header}:HXInAirTemp')
    temp_cooling['LCWIn'].append(f'{ssa_header}:LCWInTemp')
    temp_cooling['LCWOut'].append(f'{ssa_header}:LCWOutTemp')
    temp_cooling['LCWFlowRate'].append(f'{ssa_header}:LCWOutFlow')

    temp_cooling['FanSpeed'].append(f'{ssa_header}:CtrlFanSpeed')
    temp_cooling['FanSpeed'].append(f'{ssa_header}:DA_FanSpeed')
    temp_cooling['FanSpeed'].append(f'{ssa_header}:HXFan4Speed')

    for k in range(1, 4):
        # for driver
        if k == 1:
            drv_ps_volt.append(f'{ssa_header}:DA_PS1_V')
            drv_ps_volt.append(f'{ssa_header}:DA_PS2_V')
            drv_ps_cur.append(f'{ssa_header}:DA_I1')
            drv_ps_cur.append(f'{ssa_header}:DA_I2')
            drv_pwr_mW.append(f'{ssa_header}:DrvPwr_mW')

        # for amp
        amp_ps_volt.append(f'{ssa_header}:FA{k}_PS1_V')
        amp_ps_volt.append(f'{ssa_header}:FA{k}_PS2_V')

        temp_cooling['HSink'].append(f'{ssa_header}:FA{k}_HSTemp')
        temp_cooling['FanSpeed'].append(f'{ssa_header}:FA{k}_FanSpeed')
        temp_cooling['FanSpeed'].append(f'{ssa_header}:PSFan{k}Speed')
        temp_cooling['FanSpeed'].append(f'{ssa_header}:HXFan{k}Speed')

        for cur in range(1, 9):
            amp_ps_cur.append(f'{ssa_header}:FA{k}_I{cur}')
            if k == 3 and cur == 4:
                break

        for pwr in range(1, 5):
            amp_pwr.append(f'{ssa_header}:FA{k}_Pwr{pwr}')
            if k == 3 and pwr == 2:
                break

    pvs = {
        'drv': {
            'volt': drv_ps_volt,
            'cur': drv_ps_cur,
            'pwr': drv_pwr_mW
        },
        'amp': {
            'volt': amp_ps_volt,
            'cur': amp_ps_cur,
            'pwr': amp_pwr
        },
        'pwr': {
            'fwd': ssa_fwd_pwr,
            'ref': ssa_ref_pwr
        },
        'temp_cooling': temp_cooling
    }

    return pvs