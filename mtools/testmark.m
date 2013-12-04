% tries to mark some specific points

i=1;

% is the input a pmos?
c.function=@synthTestIndEqual;
ipmx=synthFindHeaderInDataset(unscaled_cpu1{1},'input_is_pmos');
c.arguments=[ipmx 1];
crit{i}=c;
i=i+1;

idxs=synthFindComplyingInds(unscaled_end, crit);

synthPlotGenerationMarkMetrics2D(metrics_end,'gain','pwrnode',idxs,'yo');
