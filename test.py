from data_retriever import DataRetriever
from data_report import *
from getLCLSII_SSA_pv import getLCLSII_SSA_pv

def main():
    from IPython import embed
    
    # Example usage for LCLSII SSA PVs

    # Get the PVs for LinacSection 2, Cryomodule 4, Cavity 1
    pvNames = getLCLSII_SSA_pv(2, 4, 1)    

    # Flatten the dict pvNames values into a list
    pvNamesFlat = []
    for key, value in pvNames.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, list):
                    pvNamesFlat.extend(sub_value)
                else:
                    pvNamesFlat.append(sub_value)
        elif isinstance(value, list):
            pvNamesFlat.extend(value)
        else:
            pvNamesFlat.append(value)
   

    # Create a DataRetriever object
    obj = DataRetriever(webServer='LCLS', pvNames=pvNamesFlat, startTime='06/26/2024 08:08:08', endTime='06/27/2024 08:08:08', duration_hour=24)

    # set base_pv to the forward power
    obj.set_base_pv(base_pv = pvNames['pwr']['fwd'], val_range = (10, 5000))
    


    alignSettings = obj.get_property('alignSetup')
    alignSettings['base_pv'] = pvNames['pwr']['fwd']



    plt.ion() # Turn on interactive mode, plot will show up immediately and not block the code
    obj.getHistory()
    obj.alignHistory()
    
    print(f"Start Time: {obj.get_property('startTime')}")
    print(f"Duration (hours): {obj.get_property('duration_hour')}")
    print(f"Web Server: {obj.get_property('webServer')}")
    print(f"PV Names: {obj.get_property('pvNames')}")
    print(f"Synchronized Data Duration (hours): {obj._DataRetriever__synData.attrs['duration_hour']:.1f}")

    #plot_time_synData (obj.get_property('synData'))
    #plot_normalized_synData(obj.get_property('synData'))
    #plot_scatter_moving_window(obj.get_property('synData'))


    embed() # Start an IPython session after the code execution


if __name__ == "__main__":
    main()

