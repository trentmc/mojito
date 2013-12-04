function values_list = synthListHeaderValues(data)
%function values_list = synthListHeaderValues(data)
%
% @description
%  
%   Return a list of header values found in 'data'
%
% @arguments
% 
%   data -- data -- 
%
% @return
% 
%   values_list -- list of header_value -- 
%
% @exceptions
%
% @notes
%
  
    values_list=[];
    for i=1:length(data.header)
        values_list=[values_list ...
                     '['  num2str(i)  ': '  cell2mat(data.header{i})  ']' 10];
    end
    
