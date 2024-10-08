from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import numpy as np
from urllib.request import urlopen
import pandas as pd
import matplotlib.pyplot as plt

# Example usage:
# obj = DataRetriever(pvNames=['PV1', 'PV2'], endTime='06/05/2023 08:08:08', duration_hour=4.0)

class DataRetriever:
    def __init__(self, pvNames: List[str] = None, webServer: str = 'LCLS', 
                 endTime: str = '06/05/2023 08:08:08', 
                 duration_hour: float = 4.0, startTime: str = None, 
                 alignSetup: Dict[str, Any] = None):
        """
        Initializes the DataRetriever class with optional input parameters.

        Parameters:
        - pvNames (List[str]): List of PV names.
        - webServer (str): Server for fetching data.
        - endTime (str): End time for data collection in 'MM/DD/YYYY HH:MM:SS' format.
        - duration_hour (float): Duration of the data window in hours.
        - startTime (str): Start time for data collection in 'MM/DD/YYYY HH:MM:SS' format.
        - alignSetup (Dict[str, Any]): Configuration for alignment settings.

        Example:
        obj = DataRetriever(pvNames=['PV1', 'PV2'], endTime='12/11/2022 06:40:00', duration_hour=6)
        """
        
        # Default values
        if isinstance(pvNames, str):
            pvNames = [pvNames]
        self.__pvNames = pvNames or ['GUN:GUNB:100:FWD:PWR', 'GUN:GUNB:100:DFACT', 'GUN:GUNB:100:REV1:PWR']
        # Set up alignment configuration with default values if not provided
        self.__alignSetup = alignSetup or {
            'base_id': 0,                   # Index of the base PV in the pvNames list
            'base_pv': self.__pvNames[0],     # Base PV name
            'val_range': [[1e3, 1e5]],        # Valid range for the base PV values
            'disTimeAddBack_sec': 1,        # Time interval (in seconds) to add back for discontinuities in the base PV
            'dtResample_sec': 1,            # Resample time interval (in seconds)
            'Trim': True                    # Whether to trim out-of-range data (True to trim, False to keep)
        }
        
        # Calculate missing time parameter based on provided inputs
        if endTime is None and startTime and duration_hour:
            start_time_dt = datetime.strptime(startTime, '%m/%d/%Y %H:%M:%S')
            end_time_dt = start_time_dt + timedelta(hours=duration_hour)
            endTime = end_time_dt.strftime('%m/%d/%Y %H:%M:%S')
        elif startTime is None and endTime and duration_hour:
            end_time_dt = datetime.strptime(endTime, '%m/%d/%Y %H:%M:%S')
            start_time_dt = end_time_dt - timedelta(hours=duration_hour)
            startTime = start_time_dt.strftime('%m/%d/%Y %H:%M:%S')
        elif duration_hour is None and startTime and endTime:
            start_time_dt = datetime.strptime(startTime, '%m/%d/%Y %H:%M:%S')
            end_time_dt = datetime.strptime(endTime, '%m/%d/%Y %H:%M:%S')
        if startTime and endTime and duration_hour:
            start_time_dt = datetime.strptime(startTime, '%m/%d/%Y %H:%M:%S')
            end_time_dt = datetime.strptime(endTime, '%m/%d/%Y %H:%M:%S')
            if abs((end_time_dt - start_time_dt).total_seconds() / 3600 - duration_hour) > 1e-6:
                raise ValueError("The provided endTime, startTime, and duration_hour do not match the condition: duration_hour = endTime - startTime.")


        webServer = webServer.upper()
        if webServer == 'LCLS':
            self.__webServer = 'http://lcls-archapp.slac.stanford.edu/retrieval/data/getData.json?pv='
        elif webServer == 'SSRL':
            self.__webServer = 'http://spear-arch1.slac.stanford.edu/retrieval/data/getData.json?pv='
        else:
            raise ValueError('Invalid web server. Please choose either "LCLS" or "SSRL".')
               
        self.__endTime = datetime.strptime(endTime, '%m/%d/%Y %H:%M:%S')
        self.__duration_hour = duration_hour
        self.__startTime = datetime.strptime(startTime, '%m/%d/%Y %H:%M:%S') if startTime else None
        self.__rawData = []
        self.__synData = []

    def set_base_pv(self, base_pv: str, base_id: int = 0, 
                        val_range: List[List[float]] = [[1e3, 1e5]], 
                        disTimeAddBack_sec: int = 1, dtResample_sec: int = 1, 
                        Trim: bool = True):
        """
        Set the base PV for alignment and update the alignSetup dictionary.

        Parameters:
        - base_pv (str): The name of the base PV to set.
        - base_id (int): The index of the base PV in the pvNames list.
        - val_range (List[List[float]]): Valid range for the base PV values.
        - disTimeAddBack_sec (int): Time interval (in seconds) to add back for discontinuities in the base PV.
        - dtResample_sec (int): Resample time interval (in seconds).
        - Trim (bool): Whether to trim out-of-range data (True to trim, False to keep).
        """
           
        if base_pv:
            if base_pv not in self.__pvNames:
                raise ValueError(f"The base PV '{base_pv}' is not in the list of PV names.")
                base_id = self.__pvNames.index(base_pv)
        elif base_id is not None:
            if base_id < 0 or base_id >= len(self.__pvNames):
                raise ValueError(f"The base ID '{base_id}' is out of range.")
                base_pv = self.__pvNames[base_id]
        else:
            raise ValueError("Either base_pv or base_id must be provided.")

        # convert val_range to a list if it is a tuple
        if isinstance(val_range, tuple):
            val_range = list(val_range)

        # Convert val_range to a list of lists if it is not already in that format    
        if isinstance(val_range, list) and len(val_range) == 2 and not isinstance(val_range[0], list):
            val_range = [val_range]

        self.__alignSetup['base_pv'] = base_pv
        self.__alignSetup['base_id'] = base_id
        self.__alignSetup['val_range'] = val_range
        self.__alignSetup['disTimeAddBack_sec'] = disTimeAddBack_sec
        self.__alignSetup['dtResample_sec'] = dtResample_sec
        self.__alignSetup['Trim'] = Trim 
                        
            
    def set_property(self, *args, **kwargs):
        """
        Set the property of the DataRetriever instance.

        Parameters:
        - property_name (str): The name of the property to set.
        - value (Any): The value to set for the property.
        """
        
        if len(args) == 2:
            property_name, value = args
        else:
            if len(args) == 1 and isinstance(args[0], dict):
                kwargs = args[0]
                for key, value in kwargs.items():
                    self.set_property(key, value)                
                return
            else:
                raise ValueError("Invalid arguments. Expected either a property name and value, or a dictionary of properties and values.")
        
        if hasattr(self, f"_{self.__class__.__name__}__{property_name}"):
            if property_name == 'pvNames' and isinstance(value, str):
                value = [value]
                self.__pvNames = value
            if property_name in ['endTime', 'startTime']:
                value = datetime.strptime(value, '%m/%d/%Y %H:%M:%S')
                if property_name == 'startTime':
                    self.__startTime = value
                    self.__endTime = value + timedelta(hours=self.__duration_hour)
                elif property_name == 'endTime':
                    self.__endTime = value
                    self.__startTime = value - timedelta(hours=self.__duration_hour)
            if property_name == 'duration_hour':
                if not isinstance(value, (int, float)):
                    raise ValueError("duration_hour must be a number")
                else:
                    self.__duration_hour = value
                    self.__startTime = self.__endTime - timedelta(hours=value)             
            if property_name == 'alignSetup':
                if not isinstance(value, dict):
                    raise ValueError("alignSetup must be a dictionary")
                required_keys = ['base_id', 'base_pv', 'val_range', 'disTimeAddBack_sec', 'dtResample_sec', 'Trim']
                for key in required_keys:
                    if key not in value:
                        raise ValueError(f"alignSetup dictionary must contain the key '{key}'")
                self.__alignSetup = value
        else:
            raise AttributeError(f"'DataRetriever' object has no attribute '{property_name}'")
        
        if kwargs:
            for key, value in kwargs.items():
                self.set_property(key, value)

    def get_property(self, property_name: str) -> Any:
        """
        Get the property of the DataRetriever instance.

        Parameters:
        - property_name (str): The name of the property to get.

        Returns:
        - Any: The value of the property.
        """
        if hasattr(self, f"_{self.__class__.__name__}__{property_name}"):
            return getattr(self, f"_{self.__class__.__name__}__{property_name}")
        else:
            raise AttributeError(f"'DataRetriever' object has no attribute '{property_name}'")

    def getHistory(self):
        """
        Fetch historical data for the specified PVs within a time range.

        This method retrieves historical data for each PV in the pvNames list
        over the specified duration ending at endTime. The data is stored in
        the rawData attribute.

        Example:
        obj.getHistory()
        """
        import concurrent.futures

        startTime = (self.__endTime - timedelta(hours=self.__duration_hour)).strftime('%m/%d/%Y %H:%M:%S')
        timeRange = [startTime, self.__endTime.strftime('%m/%d/%Y %H:%M:%S')]
        self.__rawData = []

        # Initialize progress tracking
        total_pvs = len(self.__pvNames)
        progress = 0

        # parallelize the data retrieval with ThreadPoolExecutor   
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_pv = {executor.submit(self.get_history, pv): pv for pv in self.__pvNames}
            for i, future in enumerate(concurrent.futures.as_completed(future_to_pv)):
                pv = future_to_pv[future]
                data, error = future.result()
                self.__rawData.append(data)
                if error:
                    print(error)

                # Update progress with progress bar
                progress = (i + 1) / total_pvs
                bar_length = 40
                block = int(round(bar_length * progress))
                progress_bar = f"[{'#' * block + '-' * (bar_length - block)}]"
                print(f"Progress: {round(progress * 100)}% {progress_bar} - [{pv}]")

        
        # Convert raw data to pandas DataFrame and associate with PV names
        raw_data_dict = {pv: pd.DataFrame(data) for pv, data in zip(self.__pvNames, self.__rawData)}
        self.__rawData = raw_data_dict

    def get_history(self, pv_name: str):
        """
        Fetch historical data for a given PV name and time range.

        Parameters:
        - pv_name (str): The name of the PV.

        Returns:
        - List[Dict[str, Any]]: Historical data containing timestamps and values.
        """
        timeformat = '%Y-%m-%dT%H:%M:%S.%fZ'
        timeDiff_sec = 7*3600 # EPICS time has 7 hour delay, due to UTC time and pacific time difference
        rawData = []
        time_range = [(self.__startTime).strftime(timeformat), self.__endTime.strftime(timeformat)]
        url = f'{self.__webServer}{pv_name}&from={time_range[0]}&to={time_range[1]}'
        
        try:
            with urlopen(url) as req:
                data = json.load(req)
                secs = np.array([x['secs'] + x['nanos']/1e9 for x in data[0]['data']]) + timeDiff_sec                
                vals = np.array([x['val'] for x in data[0]['data']])
                
                # Interpolate data at startTime and endTime with the nearest data point
                start_time_ts = self.__startTime.timestamp()
                end_time_ts = self.__endTime.timestamp()

                # Find the nearest data point for startTime
                start_index = np.searchsorted(secs, start_time_ts, side='left')
                if start_index == 0:
                    start_val = vals[0]
                else:
                    start_val = vals[start_index - 1]

                # Find the nearest data point for endTime
                end_index = np.searchsorted(secs, end_time_ts, side='right')
                if end_index == len(secs):
                    end_val = vals[-1]
                else:
                    end_val = vals[end_index]                                  

                # Add interpolated points to secs and vals
                secs = np.insert(secs, start_index, start_time_ts)
                vals = np.insert(vals, start_index, start_val)
                secs = np.insert(secs, end_index + 1, end_time_ts)
                vals = np.insert(vals, end_index + 1, end_val)
                
                # Sort secs from small to large and corresponding sort vals
                sorted_indices = np.argsort(secs)
                secs = secs[sorted_indices]
                vals = vals[sorted_indices]
                
                # Filter out data points that are out of the specified time range
                valid_indices = (secs >= self.__startTime.timestamp()) & (secs <= self.__endTime.timestamp())
                secs = secs[valid_indices]
                vals = vals[valid_indices]
                
                rawData = {'secs': secs, 'vals': vals}
                return rawData, None
        except Exception as e:             
                return {}, f"Warning: The PV {pv_name} is not valid! Error: {e}"

    def alignHistory(self, getHistory: bool = True):
        """
        Align historical data based on the alignment settings.

        This method aligns the historical data based on the alignment settings
        provided in alignSetup. If getHistory is True, it fetches historical
        data before alignment when there is no rawData available.

        Example:
        obj.alignHistory()
        """
        
        if getHistory and not self.__rawData:
            print("No raw data available, fetching data...")
            self.getHistory()

        self.__synData = {'startTime': None, 'relTime': [], 'vals': [], 'duration_hour': None}
        
        timeRange = self.__rawData[self.__alignSetup['base_pv']]['secs']  # Time reference

        # Convert to relative time
        relTime = (timeRange - timeRange.iloc[0])  # in seconds
        
        if not self.__alignSetup['Trim']:
            # No Trim
            time_cum = relTime  # Cumulated time
            idt = np.arange(len(timeRange))      # idt: index of data to keep
        else:
            # Cut off out of range data
            idt = []
            for val_range in self.__alignSetup['val_range']:
                idt_k = (self.__rawData[self.__alignSetup['base_pv']]['vals'] >= val_range[0]) & \
                    (self.__rawData[self.__alignSetup['base_pv']]['vals'] <= val_range[1])
                if len(idt) == 0:
                    idt = idt_k
                else:
                    idt += idt_k
            # Sort and remove duplicates
            idt = np.where(idt)[0]
            idt = np.unique(np.sort(idt))

            if len(idt) == 0:
                print('All data are out of range!')
                return

            # Adjust time for cut off
            diff_idt = 1 + np.where(np.diff(idt) > 1)[0]  # Find where it was cut
            time_inv = np.append(0, np.diff(relTime[idt]))  # reltime in seconds
            # remove discontinuity by adding back time as defined in alignSetup
            time_inv[diff_idt] = self.__alignSetup['disTimeAddBack_sec'] 
            time_cum = np.cumsum(time_inv)

        # log the syncrhonized start time
        if len(diff_idt) == 0:
            # all data are in range
            self.__synData['startTime'] = datetime.fromtimestamp(self.__rawData[self.__alignSetup['base_pv']]['secs'].iloc[0])
        else:
            self.__synData['startTime'] = datetime.fromtimestamp(self.__rawData[self.__alignSetup['base_pv']]['secs'].iloc[diff_idt[0]])

        self.__synData['relTime'] = time_cum

        # Align data to the baseID with nearest data point
        self.__synData['vals'] = np.zeros((len(self.__pvNames), len(time_cum)))  # Initialize 2D array

        for i, pv in enumerate(self.__pvNames):
            raw_data = self.__rawData[pv]
            if pv == self.__alignSetup['base_pv']:
                self.__synData['vals'][i, :] = raw_data['vals'].iloc[idt]
            else:
                if len(raw_data['secs']) == 1:
                    # Only one data point -- bad
                    print(f"Warning: Only one data point for PV {pv} -- and will fill with same data")
                    self.__synData['vals'][i, :] = np.full(len(idt), raw_data['vals'].iloc[0])
                else:
                    self.__synData['vals'][i, :] = np.interp(relTime[idt], 
                              (raw_data['secs'] - raw_data['secs'].iloc[0]), 
                              raw_data['vals'], 
                              left=np.nan, right=np.nan)

        self.__synData['vals'] = self.__synData['vals'][:, :len(relTime)]  # Ensure the array dimensions match

        # Resample the data with time interval = dtResample_sec
        # check to do resample
        
        reSample = np.arange(time_cum[0], time_cum[-1], self.__alignSetup['dtResample_sec'])
        if len(self.__synData['relTime']) == 0:
            print("Error: 'relTime' is empty. Ensure 'relTime' is properly initialized before interpolation.")
            return

        self.__synData['vals'] = np.array([np.interp(reSample, self.__synData['relTime'], 
                                                   self.__synData['vals'][i, :], 
                                                   left=np.nan, right=np.nan) 
                                         for i in range(self.__synData['vals'].shape[0])])
        self.__synData['relTime'] = reSample
        

        # Convert synchronized data to pandas DataFrame and associate with PV names
        syn_data_dict = {pv: self.__synData['vals'][i, :] for i, pv in enumerate(self.__pvNames)}
        self.__synData = pd.DataFrame(syn_data_dict, index=self.__synData['relTime'])       
        self.__synData.attrs['duration_hour'] = time_cum[-1] / 3600        
        # Add description to say index is relative time after trim
        self.__synData.attrs['description'] = 'Index is relative time in seconds after trim.'
        print(f"Total time of data in hours: {time_cum[-1] / 3600:.1f}")
        
                
    def pltHistory(self, pvNames: List[str] = None, plot_raw: bool = True, figNum: int = 1):
        """
        Plot historical data for the specified PVs.

        Parameters:
        - pvNames (List[str]): List of PV names to plot.
        - plot_raw (bool): Whether to plot raw data (True) or aligned data (False).
        - figNum (int): Figure number for the plot.

        Example:
        obj.pltHistory()
        """
        if pvNames is None:
            pvNames = self.__pvNames
        else:
            pvNames = [pv for pv in self.__pvNames if pv in pvNames]

        plt.ion()

        if plot_raw:  # Plot raw data
            if not self.__rawData:
                print('No raw data available!')
                return

            plt.figure(figNum)
            for pv in pvNames:
                if pv in self.__rawData:
                    data = self.__rawData[pv]
                    plt.plot([datetime.fromtimestamp(ts) for ts in data['secs']], data['vals'], label=pv)
            plt.title(f"Start Time: {self.__startTime}, Duration: {self.__duration_hour:.1f} hours")
            plt.legend(pvNames)
            plt.grid()
            plt.show()  # Add this line to display the plot
        else:  # Plot aligned data
            if self.__synData.empty:
                print('No aligned data available!')
                return

            plt.figure(figNum)
            for pv in pvNames:
                plt.plot(self.__synData.index / 3600, self.__synData[pv], label=pv)
            plt.xlabel('Relative Time [hours]')
            plt.legend(pvNames)
            plt.grid()
            plt.show(block=False)  # Add this line to display the plot
 

def main():
    # Example usage from LCLS2
    obj = DataRetriever(webServer='LCLS', endTime='09/28/2023 18:00:00', duration_hour=4)
    # Change duration and endTime using set_property
    obj.set_property({'duration_hour':6, 'endTime':'09/28/2023 07:00:00'})
       
    plt.ion() # Turn on interactive mode, plot will show up immediately and not block the code
    obj.getHistory()
    obj.alignHistory()
    
    print(f"Start Time: {obj.get_property('startTime')}")
    print(f"Duration (hours): {obj.get_property('duration_hour')}")
    print(f"Web Server: {obj.get_property('webServer')}")
    print(f"PV Names: {obj.get_property('pvNames')}")
    print(f"Synchronized Data Duration (hours): {obj._DataRetriever__synData.attrs['duration_hour']:.1f}")
    
    
    #plt.ion()
    obj.pltHistory()
    obj.pltHistory(plot_raw=False, figNum=2)
    
  
    
    # Example usage from SSRL
    obj2 = DataRetriever(webServer='SSRL', pvNames='GUN:FilamentVolt', endTime='06/05/2023 08:08:08', duration_hour=4.0)
    obj2.getHistory()
    print(f"Start Time: {obj2.get_property('startTime')}")
    print(f"Duration (hours): {obj2.get_property('duration_hour')}")
    print(f"Web Server: {obj2.get_property('webServer')}")
    print(f"PV Names: {obj2.get_property('pvNames')}")
    


if __name__ == "__main__":
    main()