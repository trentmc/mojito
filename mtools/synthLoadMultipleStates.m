function [metrics, scaled,unscaled] = synthLoadMultipleStates(problem, base_dir, generations)
%function data_per_gen = synthLoadMultipleStates(problem, base_dir, generations)
%
% @description
%  
%  Creates a list of data, where each entry is from a different generation.
%  Looks in pickled state files: base_dir/state_genXXXX.db where XXXX
%  is the generation number.
%
% @arguments
% 
%  problem -- int -- specifies problem, e.g. 51
%  base_dir -- string -- where the data is
%  generations -- list of int -- (optional) what generations to look at.  Usually 
%    given in ascending order. if missing, all states found are loaded.
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
%  The output of this can be readily used by synthPlotGenerationMetrics2DMovie
%

    metrics={};
    scaled={};
    unscaled={};
    
    silently_stop=0;
    if nargin==2
        silently_stop=1;
        generations=[1:9999];
    end
    
    i = 1;
    for generation = generations
        state_file=['state_gen' sprintf('%04d',generation) '.db'];
        % check if the state exists
        if size(dir([base_dir '/' state_file]),1) == 0
            if silently_stop==1
                disp(['Loaded ' num2str(i) ' states'])
                break
            else
                disp(['Cannot find state file: ' base_dir '/' state_file]);
                continue
            end
        end
            
        cmd=['./summarize_db.py ' num2str(problem) ' ' base_dir '/' state_file ' None temp_metrics temp_points'];
        system(cmd);
        metrics{i} = synthImportMetrics('temp_metrics');
        [scaled{i}, unscaled{i}] = synthImportPoints('temp_points');
        i = i + 1;
    end
