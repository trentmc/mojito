figure
hold on
synthPlotGenerationMetrics2D(metrics_cpu1{5},'gain','pwrnode','rx:')
synthPlotGenerationMetrics2D(metrics_cpu1{10},'gain','pwrnode','bx:')

synthPlotGenerationMetrics2D(metrics_cpu2{5},'gain','pwrnode','ro:')
synthPlotGenerationMetrics2D(metrics_cpu2{10},'gain','pwrnode','o:')

synthPlotGenerationMetrics2D(metrics_end,'gain','pwrnode','k-')
synthPlotGenerationMetrics2D(metrics_bigrun,'gain','pwrnode','c-')

xlabel('Gain (dB)');
ylabel('Power (W)');

title('Multi-cpu, multi-enviromental point optimization result for ssViAmp1');
legend('CPU1 - Generation 5', ...
       'CPU1 - Generation 10', ...
       'CPU2 - Generation 5', ...
       'CPU2 - Generation 10', ...
       'CPU1+CPU2 - Gen 20', ...
       'Front w/o Env. Points');

% mark some points
pidx_is_pmos=synthFindHeaderInDataset(unscaled_bigrun,'input_is_pmos');
pidx_chosen_part=synthFindHeaderInDataset(unscaled_bigrun,'chosen_part_index');
pidx_chosen_load_part=synthFindHeaderInDataset(unscaled_bigrun,'load_part_index');

figure
hold on
synthPlotGenerationMetrics2D(metrics_bigrun,'gain','pwrnode','c-')

% is the input a pmos?
crit=[];
c.function=@synthTestIndEqual;
c.arguments=[pidx_is_pmos 1];
crit{1}=c;

pmos_idxs=synthFindComplyingInds(unscaled_bigrun, crit);

synthPlotGenerationMarkMetrics2D(metrics_bigrun,'gain','pwrnode',pmos_idxs,'mx');

% nmos?
c.function=@synthTestIndEqual;
c.arguments=[pidx_is_pmos 0];
crit{1}=c;

nmos_idxs=synthFindComplyingInds(unscaled_bigrun, crit);

synthPlotGenerationMarkMetrics2D(metrics_bigrun,'gain','pwrnode',nmos_idxs,'bx');

% folded?
c.function=@synthTestIndTwoEqual;
c.arguments=[pidx_is_pmos pidx_chosen_part];
crit{1}=c;

folded_idxs=synthFindComplyingInds(unscaled_bigrun, crit);

synthPlotGenerationMarkMetrics2D(metrics_bigrun,'gain','pwrnode',folded_idxs,'ro');

% resistor load?
c.function=@synthTestIndEqual;
c.arguments=[pidx_chosen_load_part 1];
crit{1}=c;

resistorload_idxs=synthFindComplyingInds(unscaled_bigrun, crit);

synthPlotGenerationMarkMetrics2D(metrics_bigrun,'gain','pwrnode',resistorload_idxs,'go');

title('Multi-cpu result for ssViAmp1');
legend('Front', ...
       'PMOS input', ...
       'NMOS input', ...
       'Folded Cascode', ...
       'Uncascoded Load' ...
       );
