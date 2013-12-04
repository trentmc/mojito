function [scaled, unscaled] = synthImportPoints(base_filename)
%function [scaled, unscaled] = synthImportPoints(base_filename)
%
% @description
%  
%   Imports a scaled point and an unscaled_point from a file
%   specified by base_filename.  Expects these files:
%     base_filename.unscaled.hdr -- ascii list of unscaled variable names
%     base_filename.scaled.hdr   -- ascii list of scaled variable names
%     base_filename.unscaled.val -- ascii list of unscaled variable values
%     base_filename.scaled.val   -- ascii list of scaled variable values
%
% @arguments
% 
%   base_filename -- string -- 
%
% @return
% 
%  scaled -- point --
%  unscaled -- point -- 
%
% @exceptions
%
% @notes
%
%   A 'point' here has two attributes:
%    header -- cell-list of string -- 1st entry holds 'IND_ID', while
%      subsequent entries hold variable names
%    data -- list of floats -- each float here corresponds to a value in the 
%      header
%
  
    scaled_header_fn=[base_filename '.unscaled.hdr'];
    unscaled_header_fn=[base_filename '.scaled.hdr'];
    scaled_values_fn=[base_filename '.scaled.val'];
    unscaled_values_fn=[base_filename '.unscaled.val'];
    
    % now read in the scaled values
        
    tmpvals=load(scaled_values_fn);
    
    % we assume that there are as many header entries as there are values
    
    cols=size(tmpvals,2);
    
    formatstring='';
    for i=1:cols
            formatstring=[formatstring '%s'];
    end
   
    % read in the headers
    fid=fopen(scaled_header_fn,'r');
    hdr = textscan(fid,formatstring,'delimiter',',');
    fclose(fid);
    
    scaled=[];
    scaled.header=hdr;
    scaled.data=tmpvals;

    % now read in the unscaled values    
    tmpvals=load(unscaled_values_fn);
    
    % we assume that there are as many header entries as there are values
    
    cols=size(tmpvals,2);
    
    formatstring='';
    for i=1:cols
            formatstring=[formatstring '%s'];
    end
   
    % read in the headers
    fid=fopen(unscaled_header_fn,'r');
    hdr = textscan(fid,formatstring,'delimiter',',');
    fclose(fid);
    
    unscaled=[];
    unscaled.header=hdr;
    unscaled.data=tmpvals;
