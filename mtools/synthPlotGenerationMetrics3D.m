function synthPlotGenerationMetrics3D(data, metric1, metric2, metric3, format)
%function synthPlotGenerationMetrics3D(data, metric1, metric2, metric3, format)
%
% @description
%  
%  Plots one generation's worth of data, for 3 metrics, in a 3d plot
%
% @arguments
% 
%  data -- -- 
%  metric1 -- string -- will be plotted on x-axis
%  metric2 -- string -- will be plotted on y-axis
%  metric3 -- string -- will be plotted on z-axis
%  format -- -- passed onto plot3() call
%
% @return
% 
%  <<nothing>>
%
% @exceptions
%
% @notes
%
    if nargin == 4
        format='.';
    end
    
    metric1_idx=synthFindHeaderInDataset(data,metric1);
    metric2_idx=synthFindHeaderInDataset(data,metric2);
    metric3_idx=synthFindHeaderInDataset(data,metric3);
    
    if metric1_idx==0
        disp(['Metric ' metric1 ' not found in dataset'])
    end
    
    if metric2_idx==0
        disp(['Metric ' metric2 ' not found in dataset'])
    end
    
    if metric3_idx==0
        disp(['Metric ' metric3 ' not found in dataset'])
    end
    
    plot3(data.data(:, metric1_idx), data.data(:, metric2_idx), data.data(:, metric3_idx),format);
    
    xlabel(metric1);
    ylabel(metric2);
    zlabel(metric3);
    grid on;
    
