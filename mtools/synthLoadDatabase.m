function [metrics, scaled,unscaled] = synthLoadDatabase(problem, filename)
%function data_per_gen = synthLoadDatabase(problem, filename)
%
% @description
%  
%  Loads a database file
%
% @arguments
% 
%  problem -- int -- specifies problem, e.g. 51
%  filename -- string -- where the data is
%
% @return
% 
%  metrics -- cell-list of 'metrics_at_gen' -- each item is for a different state
%   (generation), with indices 1,2,...,length(generations)
%  scaled -- cell-list of 'scaled_points_at_gen' -- each item is for a different state
%   (generation), with indices 1,2,...,length(generations)
%  unscaled -- cell-list of 'unscaled_poitns_at_gen' -- each item is for a different state
%   (generation), with indices 1,2,...,length(generations)
%
% @exceptions
%
% @notes
%
%  The output of this can be readily used by synthPlotGenerationMetrics2D
%

if size(dir(filename),1)==0
    disp(['Cannot find file: ' filename]);
    return
end
            
cmd=['./summarize_db.py ' num2str(problem) ' ' filename ' None temp_metrics temp_points'];
system(cmd);
metrics = synthImportMetrics('temp_metrics');
[scaled, unscaled] = synthImportPoints('temp_points');

