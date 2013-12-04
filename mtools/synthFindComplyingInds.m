function idxs = synthFindComplyingInds(data, criteria)
%function idxs = synthFindComplyingInds(data, criteria)
%
% @description
%
%  Searches through data.data for individuals that match the specified
%  citeria.
%
% @arguments
%
%  data -- -- 
%  criteria -- string --
%
% @return
% 
%  idx -- int -- indexes of the found individuals
%
% @exceptions
%
% @notes
%
%  criteria is a cell array containing one or more criterion
%  a criterion is a struct that looks like this:
%   c.function=@f
%   c.arguments
%
%   f is a function that gets the current individual as input
%   along with c.arguments. This function should return 0 if an individual
%   does not meet the criterion.
%

nb_inds=size(data.data,1);

nb_tests=size(criteria,1);

passfail=zeros(1,nb_inds);

for i=1:nb_inds
    ind=data.data(i,:);
    passfail(i)=1;
    for j=1:nb_tests
        c=criteria{j};
        passfail(i)=passfail(i) & feval(c.function,ind,c.arguments);
    end
end

idxs=unique((1:nb_inds).*passfail);
if size(idxs)>0
    if idxs(1) == 0
        idxs=idxs(2:end);
    end
end