function idx = synthFindHeaderInDataset(data, header)
%function idx = synthFindHeaderInDataset(data, header)
%
% @description
%
%  Searches through data.header{idx} for each idx
%  until one matches the input 'header', and returns index.
%
% @arguments
%
%  data -- -- has attribute header{}
%  header -- string --
%
% @return
% 
%  idx -- int -- index of 'header' in data.header{}
%
% @exceptions
%
% @notes
%

    for i = 1:length(data.header)
        if strcmpi(data.header{i}, header)
            idx = i;
            return
        end
    end
    idx=0;
    
