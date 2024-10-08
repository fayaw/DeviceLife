import pandas as pd
import matplotlib.pyplot as plt

# Assuming synData is your DataFrame
# synData = pd.read_csv('your_data.csv')  # Example of loading data

def plot_scatter_moving_window(synData, pv_x=None, pv_y=None, window_hours=1, marker='+', layout=(1, 4), normalize=True):
    """
    Plots scatter plots of pv_x vs pv_y using a moving time window in subplots.

    Parameters:
    synData (pd.DataFrame): The DataFrame containing the data.
    pv_x (str): The PV to plot on the x-axis. If None, uses the first PV.
    pv_y (list): List of PVs to plot on the y-axis. If None, uses all PVs except pv_x.
    window_hours (int): The size of the moving time window in hours. Default is 1 hour.
    marker (str): The marker style for the scatter plot. Default is '+'.
    layout (tuple): Tuple specifying the layout of the subplots (rows, cols). Default is (1, 4).
    normalize (bool): Whether to normalize the data. Default is True.
    """
    if pv_x is None:
        pv_x = synData.columns[0]

    if pv_y is None:
        pv_y = synData.columns.drop(pv_x).tolist()

    if normalize:
        synData = synData.apply(lambda x: (x - x.min()) / (x.max() - x.min()), axis=0)

    window_size = window_hours * 3600  # the data is in seconds
    rows, cols = layout
    total_plots = rows * cols

    # Calculate the number of plots needed
    number_of_plots = int(synData.index[-1]// window_size) + 1
    total_plots = min(total_plots, number_of_plots)

    if total_plots <= cols:
        cols = total_plots
        rows = 1

    fig, axes = plt.subplots(rows, cols, figsize=(15, 4))
    axes = axes.flatten()  # Flatten the axes array for easy iteration

    for i in range(total_plots):
        start_time = synData.index[0] + i * window_size
        end_time = min(start_time + window_size, synData.index[-1])
        window_data = synData[(synData.index >= start_time) & (synData.index <= end_time)]

        if window_data.empty:
            break

        for pv in pv_y:
            if pv in synData.columns and pv_x in synData.columns:
                axes[i].scatter(window_data[pv_x], window_data[pv], marker=marker, label=pv)
                axes[i].set_xlabel(pv_x)
                axes[i].set_title(f'{start_time/3600}-{end_time/3600:.1f} hours')
                if i == 0:
                    axes[i].legend()
                axes[i].grid(True)
            else:
                print(f'PV {pv} or {pv_x} not found in the DataFrame.')

    plt.tight_layout()

    # Hide any unused subplots
    for j in range(total_plots, len(axes)):
        fig.delaxes(axes[j])
    plt.show()

# Example usage:
# plot_scatter_moving_window(synData)
# plot_scatter_moving_window(synData, pv_x='PV1', pv_y=['PV2', 'PV3'], window_hours=2, num_plots=6, layout=(2, 3))

def plot_normalized_synData(synData, pvs=None, legend=True, legend_labels=None):
    """
    Plots the normalized data (0 to 1) for the selected PVs from the synData DataFrame in a single plot.
    If no PVs are selected, plots all PVs.

    Parameters:
    synData (pd.DataFrame): The DataFrame containing the data.
    pvs (list): List of PVs to plot. If None, plots all PVs.
    legend (bool): Whether to display the legend. Default is True.
    legend_labels (list): List of labels for the legend. If None, uses PV names.
    """
    if pvs is None:
        pvs = synData.columns.tolist()

    plt.figure(figsize=(10, 6))

    for pv in pvs:
        if pv in synData.columns:
            normalized_data = (synData[pv] - synData[pv].min()) / (synData[pv].max() - synData[pv].min())
            plt.plot(synData.index/3600, normalized_data, label=pv)
        else:
            print(f'PV {pv} not found in the DataFrame.')

    if legend:
        if legend_labels is None:
            legend_labels = pvs
        plt.legend(legend_labels)

    plt.xlabel('relTime [hours]')
    plt.ylabel('Normalized Value')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Example usage:
# pvs_to_plot = ['PV1', 'PV2', 'PV3']
# plot_normalized_synData(synData, pvs_to_plot)
# plot_normalized_synData(synData)  # This will plot all PVs

def subplot_time_synData(synData, pvs=None, layout=(1, 4)):
    """
    Plots the selected PVs from the synData DataFrame in a subplot style.
    If no PVs are selected, plots all PVs.

    Parameters:
    synData (pd.DataFrame): The DataFrame containing the data.
    pvs (list): List of PVs to plot. If None, plots all PVs.
    layout (tuple): Tuple specifying the layout of the plots (rows, cols).
    """
    rows, cols = layout
    total_plots = cols * rows

    if pvs is None:
        # Plot all PVs if none are specified        
        pvs = synData.columns.tolist()

    # Limit the number of plots to total_plots
    num_pvs = min(len(pvs), total_plots)

    # Adjust the layout if there are fewer PVs than cols
    if num_pvs <= cols:
        cols = num_pvs
        rows = 1
        total_plots = num_pvs
   
    fig, axes = plt.subplots(rows, cols, figsize=(15, 4))
    axes = axes.flatten()  # Flatten the axes array for easy iteration

    for i in range(total_plots):
        if i >= num_pvs:
            break  # No more PVs to plot

        pv = pvs[i]
        if pv in synData.columns:
            axes[i].plot(synData.index/3600, synData[pv], label=pv)
            axes[i].set_ylabel(pv)
            if i // cols == rows - 1:  # Only show xlabel if it's in the last row
                axes[i].set_xlabel('relTime [hours]')
        else:
            print(f'PV {pv} not found in the DataFrame.')

    # Hide any unused subplots
    for j in range(i + 1, total_plots):
        fig.delaxes(axes[j])

    plt.tight_layout()     
    plt.show()

# Example usage:
# pvs_to_plot = ['PV1', 'PV2', 'PV3']
# subplot_time_synData(synData, pvs_to_plot)
# subplot_time_synData(synData)  # This will plot all PVs