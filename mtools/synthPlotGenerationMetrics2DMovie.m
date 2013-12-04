function mv = synthPlotGenerationMetrics2DMovie(datasets, metric1, metric2, format)
%function mv = synthPlotGenerationMetrics2DMovie(datasets, metric1, metric2, format)
%
% @description
%  
%  Creates a movie in which each frame is a 2d scatterplot of 2 metrics.
%
% @arguments
% 
%  datasets -- cell-list of data -- each item in the list will get its own
%              frame
%  metric1 -- string -- will be plotted on x-axis
%  metric2 -- string -- will be plotted on y-axis
%  format -- -- passed onto plot() call
%
% @return
% 
%  mv -- a matlab movie -- 
%
% @exceptions
%
% @notes
%
    if nargin == 3
        format='.';
    end
    
    i=1;
    max_x=-1e20;
    min_x=1e20;
    max_y=-1e20;
    min_y=1e20;
    
    for data = datasets
        metric1_idx = synthFindHeaderInDataset(data{1},metric1);
        metric2_idx = synthFindHeaderInDataset(data{1},metric2);
        
        if metric1_idx==0
            disp(['Metric ' metric1 ' not found in dataset'])
        end
        
        if metric2_idx==0
            disp(['Metric ' metric2 ' not found in dataset'])
        end
        max_x=max(max_x,max(data{1}.data(:,metric1_idx)));
        min_x=min(min_x,min(data{1}.data(:,metric1_idx)));
        
        max_y=max(max_y,max(data{1}.data(:,metric2_idx)));
        min_y=min(min_y,min(data{1}.data(:,metric2_idx)));
    end
    
    for data=datasets
        synthPlotGenerationMetrics2D(data, metric1, metric2, format);
        
        axis([min_x max_x min_y max_y])
        
        title(['Frame ' num2str(i)]);
        
        mv(i)=getframe();
        i=i+1;
    end
