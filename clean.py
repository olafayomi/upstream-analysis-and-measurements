    # Sort Probes by RTT values
    valve_min_rtt = valve_min_rtt_df['Min RTT'].tolist()
    valve_min_rtt_range = []
    for min_rtt in valve_min_rtt:
        if min_rtt <= 10.0:
            valve_min_rtt_range.append(10)

        if (min_rtt > 10.0) and (min_rtt <= 20.0): 
            valve_min_rtt_range.append(20)

        if (min_rtt > 20.0) and (min_rtt <= 30.0):
            valve_min_rtt_range.append(30)

        if (min_rtt > 30.0) and (min_rtt <= 40.0):
            valve_min_rtt_range.append(40)

        if (min_rtt > 40.0) and (min_rtt <= 50.0):
            valve_min_rtt_range.append(50)

        if (min_rtt > 50.0) and (min_rtt <= 60.0):
            valve_min_rtt_range.append(60)

        if (min_rtt > 60.0) and (min_rtt <= 70.0):
            valve_min_rtt_range.append(70)

        if (min_rtt > 70.0) and (min_rtt <= 80.0): 
            valve_min_rtt_range.append(80)

        if (min_rtt > 80.0) and (min_rtt <= 90.0):
            valve_min_rtt_range.append(90)

        if (min_rtt > 90.0) and (min_rtt <= 100.9):
            valve_min_rtt_range.append(100)

        if min_rtt >= 101.0:
            valve_min_rtt_range.append(101)
    
    s = pd.Series(valve_min_rtt_range, name='MinRTT')
    df = pd.DataFrame(s)
    min_stats_df = df.groupby('MinRTT')['MinRTT'].agg('count').pipe(pd.DataFrame).rename(columns={'MinRTT': 'Probes'})
    print("Sum of the number of probes grouped into Min RTT range: %s" % (sum(min_stats_df['Probes'])))
    min_stats_df['pdf'] = min_stats_df['Probes'] / sum(min_stats_df['Probes'])
    min_stats_df['cdf'] = min_stats_df['pdf'].cumsum()
    min_stats_df['Percentage of probes in RTT values'] = (min_stats_df['Probes']/min_stats_df['Probes'].sum()) * 100
    min_stats_df['Cumulative percentage for RTT'] = min_stats_df['Percentage of probes in RTT values'].cumsum()
    min_stats_df['Reversed cumulative percentage for RTT'] = min_stats_df.loc[::-1, 'Percentage of probes in RTT values'].cumsum()[::-1]
    print(tabulate(min_stats_df, headers='keys', tablefmt='pretty'))

    min_stats_df = min_stats_df.reset_index()

    valve_max_rtt = valve_max_rtt_df['Max RTT'].tolist()
    valve_max_rtt_range = []
    for min_rtt in valve_max_rtt:
        if min_rtt <= 10.0:
            valve_max_rtt_range.append(10)

        if (min_rtt > 10.0) and (min_rtt <= 20.0): 
            valve_max_rtt_range.append(20)

        if (min_rtt > 20.0) and (min_rtt <= 30.0):
            valve_max_rtt_range.append(30)

        if (min_rtt > 30.0) and (min_rtt <= 40.0):
            valve_max_rtt_range.append(40)

        if (min_rtt > 40.0) and (min_rtt <= 50.0):
            valve_max_rtt_range.append(50)

        if (min_rtt > 50.0) and (min_rtt <= 60.0):
            valve_max_rtt_range.append(60)

        if (min_rtt > 60.0) and (min_rtt <= 70.0):
            valve_max_rtt_range.append(70)

        if (min_rtt > 70.0) and (min_rtt <= 80.0): 
            valve_max_rtt_range.append(80)

        if (min_rtt > 80.0) and (min_rtt <= 90.0):
            valve_max_rtt_range.append(90)

        if (min_rtt > 90.0) and (min_rtt <= 100.9):
            valve_max_rtt_range.append(100)

        if min_rtt >= 101.0:
            valve_max_rtt_range.append(101)
    
    s = pd.Series(valve_max_rtt_range, name='MaxRTT')
    df = pd.DataFrame(s)
    max_stats_df = df.groupby('MaxRTT')['MaxRTT'].agg('count').pipe(pd.DataFrame).rename(columns={'MaxRTT': 'Probes'})
    print("Sum of the number of probes grouped into Min RTT range: %s" % (sum(max_stats_df['Probes'])))
    max_stats_df['pdf'] = max_stats_df['Probes'] / sum(max_stats_df['Probes'])
    max_stats_df['cdf'] = max_stats_df['pdf'].cumsum()
    max_stats_df['Percentage of probes in RTT values'] = (max_stats_df['Probes']/max_stats_df['Probes'].sum()) * 100
    max_stats_df['Cumulative percentage for RTT'] = max_stats_df['Percentage of probes in RTT values'].cumsum()
    max_stats_df['Reversed cumulative percentage for RTT'] = max_stats_df.loc[::-1, 'Percentage of probes in RTT values'].cumsum()[::-1]
    print(tabulate(max_stats_df, headers='keys', tablefmt='pretty'))

    max_stats_df = max_stats_df.reset_index()

    fig, ax = plt.subplots()
    ax.plot(min_stats_df['MinRTT'], min_stats_df['cdf'],
            label="Minimum RTT", color="blue")
    ax.plot(max_stats_df['MaxRTT'], max_stats_df['cdf'],
            label="Maximum RTT", color="red")
    plt.title("CDF of minimum and maximum RTT values of 1699 probes to Valve server IP address")
    plt.xlabel("RTT values across probes")
    plt.ylabel("CDF")
    plt.legend(fontsize=15)
    plt.show(block=True)

