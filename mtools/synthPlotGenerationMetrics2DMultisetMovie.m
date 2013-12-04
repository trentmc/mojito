function mv = synthPlotGenerationMetrics2DMovie(datasetss, metric1, metric2, format)
%function mv = synthPlotGenerationMetrics2DMovie(datasetss, metric1, metric2, format)
%
% @description
%  
%  Creates a movie in which each frame is a 2d scatterplot of 2 metrics.
%
% @arguments
% 
%  datasetss -- cell-list of data datasets -- each set of items in the list 
%               will get its own frame
%  metric1 -- string -- will be plotted on x-axis
%  metric2 -- string -- will be plotted on y-axis
%  format -- -- passed onto plot() call, should be a cell list of the same
%               size as the datasetss
%
% @return
% 
%  mv -- a matlab movie -- 
%
% @exceptions
%
% @notes
%
    default_formats={'b.','r.','g.','c.','m.','y.', ...
                     'b*','r*','g*','c*','m*','y*', ...
                     'bo','ro','go','co','mo','yo', ...
                     'bx','rx','gx','cx','mx','yx'};
    
    nb_frames=length(datasetss{1});
    
    if nargin == 3
        format=default_formats;
    end
    
    max_x=-1e20;
    min_x=1e20;
    max_y=-1e20;
    min_y=1e20;
    for datasetsx = datasetss
        datasets=datasetsx{1};
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
    end


    for i=1:nb_frames
        clf;
        axis([min_x max_x min_y max_y]);
        hold on;
        j=1;
        
        for datasetsx = datasetss
            datasets=datasetsx{1};
            
            if i>length(datasets)
                continue
            end

            synthPlotGenerationMetrics2D(datasets{i}, metric1, metric2, format{j});
            
            j=j+1;
        end
        xlabel(metric1);
        ylabel(metric2);
        grid on;
        
        title(['Frame ' num2str(i)]);
        
        mv(i)=getframe();
    end