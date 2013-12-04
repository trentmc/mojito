function synthPlotGenerationMetrics2D(data, metric1, metric2, format)
%function synthPlotGenerationMetrics2D(data, metric1, metric2, format)
%
% @description
%  
%  Plots one generation's worth of data, for 2 metrics, in a 2d scatterplot
%
% @arguments
% 
%  data -- -- 
%  metric1 -- string -- will be plotted on x-axis
%  metric2 -- string -- will be plotted on y-axis
%  format -- -- passed onto plot() call
%
% @return
% 
%  <<nothing>>
%
% @exceptions
%
% @notes
%

    if nargin == 3
        format='.';
    end
    
    metric1_idx = synthFindHeaderInDataset(data,metric1);
    metric2_idx = synthFindHeaderInDataset(data,metric2);
    
    if metric1_idx==0
        disp(['Metric ' metric1 ' not found in dataset'])
    end
    
    if metric2_idx==0
        disp(['Metric ' metric2 ' not found in dataset'])
    end
    [xdata,p]=sort(data.data(:,metric1_idx));
    ydata=data.data(p,metric2_idx);
    plot(xdata, ydata,format);
    
    xlabel(metric1);
    ylabel(metric2);
    grid on;
    
