function synthPlotGenerationMarkMetrics2D(data, metric1, metric2, indexes, format)
%function synthPlotGenerationMarkMetrics2D(data, metric1, metric2, indexes, format)
%
% @description
%  
%  Plots only the specified individuals on a 2d scatterplot
%
%  Usefull to mark individuals that meet certain criteria
%
% @arguments
% 
%  data -- -- 
%  metric1 -- string -- will be plotted on x-axis
%  metric2 -- string -- will be plotted on y-axis
%  indexes -- vector -- the indexes to plot
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

    if nargin == 4
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
    tmpx=data.data(indexes,metric1_idx);
    tmpy=data.data(indexes,metric2_idx);
    
    [xdata,p]=sort(tmpx);
    ydata=tmpy(p);
    
    plot(xdata, ydata,format);

    
