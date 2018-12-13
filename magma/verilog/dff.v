module DFF_width_${width}_pipe_depth_${pipe_depth}_retime_status_${retime_status} (
  input [${width - 1} : 0] data_in, 
  input clk, reset, en, 
  output [${width - 1} : 0] data_out
 );
   
  /* synopsys dc_tcl_script_begin
  set_ungroup [current_design] true
  set_flatten true -effort high -phase true -design [current_design]
  // https://solvnet.synopsys.com/dow_retrieve/G-2012.03/manpages/syn2/set_dont_retime.html
  % if retime_status == 1:
  set_dont_retime [current_design] false 
  set_optimize_registers true -design [current_design]
  % else:
  set_dont_retime [current_design] true
  set_optimize_registers false -design [current_design]
  % endif
  */
 
  % if pipe_depth > 0:
  DW_pl_reg #(
    .stages(${pipe_depth + 1}),
    .in_reg(0),
    .out_reg(0),
    .width(${width}),
    .rst_mode(0)
  ) dff (
    .data_in(data_in), 
    .clk(clk), 
    .data_out(data_out), 
    .rst_n(!reset), 
    .enable({${pipe_depth}{en}})
  );
  % else:
  assign data_out = data_in & (~{${width}{reset}});
  %endif
endmodule
