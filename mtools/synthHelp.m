%synthHelp.m
% Run this script to see what the useful mtools are.

h = [];
h = [h '\n'];
h = [h 'Usage: synthHelp\n'];
h = [h '\n'];
h = [h 'TOOLS AVAILABLE:\n'];
h = [h '\n'];

h = [h '==========================\n'];
h = [h 'High-level data extraction\n'];
h = [h '==========================\n'];
h = [h 'datasets = synthLoadMultipleStates(problem, base_dir, generations)\n'];
h = [h '\n'];

h = [h '==========================\n'];
h = [h 'Visualize extracted data\n'];
h = [h '==========================\n'];
h = [h '     synthPlotGenerationMetrics2D(data, metric1, metric2, format) \n'];
h = [h '     synthPlotGenerationMetrics3D(data, metric1, metric2, metric3, format)\n'];
h = [h 'mv = synthPlotGenerationMetrics2DMovie(datasets, metric1, metric2, format)\n'];
h = [h '\n'];

h = [h '==========================\n'];
h = [h 'Low-level data extraction\n'];
h = [h '==========================\n'];
h = [h '       values_list = synthListHeaderValues(data)\n'];
h = [h '[scaled, unscaled] = synthImportPoints(base_filename)\n'];
h = [h '      metric_point = synthImportMetrics(base_filename)\n'];
h = [h '               idx = synthFindHeaderInDataset(data, header)\n'];
h = [h '\n'];

fprintf(h)
