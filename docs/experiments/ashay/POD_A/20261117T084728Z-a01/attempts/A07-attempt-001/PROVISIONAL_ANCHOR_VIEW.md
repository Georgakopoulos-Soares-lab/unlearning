# Provisional predeclared AUROC anchor display

All40candidate/task/representation/policy cells below use seed42 and the predeclared layer16 (17th block)/final_norm anchors. This is not a best-layer or best-seed selection. Values remain producer-complete, independently unverified pending A08. Intervals are pointwise paired exact/RC-group bootstrap conditional on fitted heads. The complete five-metric,26-representation,three-seed join is TASK_LAYER_SEED_VIEW.csv; it retains full precision and all adverse/flat effects.

| Candidate | Task | Hook | Policy | AUROC [95% CI] | Minus base [95% CI] | Minus R1 [95% CI] |
|---|---|---|---|---:|---:|---:|
| R4 | gue_tf_0 | decoder.layers.16 | independent_refit | 0.825178 [0.789147, 0.861190] | -0.004797 [-0.035096, 0.026376] | 0.023558 [-0.008617, 0.056428] |
| R4 | gue_tf_0 | decoder.layers.16 | fixed_original_base | 0.651226 [0.600995, 0.695574] | -0.178749 [-0.228837, -0.130018] | 0.006432 [-0.046722, 0.061480] |
| R4 | gue_tf_0 | decoder.final_norm | independent_refit | 0.705340 [0.660109, 0.749089] | 0.025666 [-0.032666, 0.086001] | 0.063738 [0.004825, 0.124654] |
| R4 | gue_tf_0 | decoder.final_norm | fixed_original_base | 0.480620 [0.427147, 0.533411] | -0.199053 [-0.262016, -0.137569] | 0.036040 [-0.037955, 0.106667] |
| R4 | gue_prom_core_all | decoder.layers.16 | independent_refit | 0.874992 [0.845592, 0.904567] | 0.058124 [0.026849, 0.092223] | 0.028429 [-0.000078, 0.058456] |
| R4 | gue_prom_core_all | decoder.layers.16 | fixed_original_base | 0.669337 [0.622852, 0.715897] | -0.147531 [-0.198198, -0.095689] | 0.075520 [0.017714, 0.131349] |
| R4 | gue_prom_core_all | decoder.final_norm | independent_refit | 0.869957 [0.840497, 0.900748] | 0.108573 [0.070237, 0.150233] | 0.096670 [0.064950, 0.128960] |
| R4 | gue_prom_core_all | decoder.final_norm | fixed_original_base | 0.748291 [0.706201, 0.789237] | -0.013093 [-0.052640, 0.025376] | 0.202573 [0.146047, 0.261716] |
| R4 | gue_prom_300_all | decoder.layers.16 | independent_refit | 0.980072 [0.968393, 0.989072] | 0.025681 [0.011260, 0.042119] | 0.016434 [0.005389, 0.028911] |
| R4 | gue_prom_300_all | decoder.layers.16 | fixed_original_base | 0.739986 [0.696263, 0.780906] | -0.214405 [-0.257989, -0.172181] | 0.177066 [0.106199, 0.244354] |
| R4 | gue_prom_300_all | decoder.final_norm | independent_refit | 0.950576 [0.930174, 0.967166] | 0.113664 [0.081124, 0.146625] | 0.116686 [0.083147, 0.151179] |
| R4 | gue_prom_300_all | decoder.final_norm | fixed_original_base | 0.911849 [0.886630, 0.936220] | 0.074937 [0.037879, 0.111835] | 0.633234 [0.574527, 0.690834] |
| R4 | gue_splice_reconstructed | decoder.layers.16 | independent_refit | 0.774303 [0.735823, 0.809100] | -0.013559 [-0.047972, 0.019167] | 0.052198 [0.017141, 0.084529] |
| R4 | gue_splice_reconstructed | decoder.layers.16 | fixed_original_base | 0.631743 [0.593487, 0.669769] | -0.156119 [-0.197187, -0.116789] | 0.128584 [0.078350, 0.178363] |
| R4 | gue_splice_reconstructed | decoder.final_norm | independent_refit | 0.636111 [0.596829, 0.676052] | 0.002277 [-0.039081, 0.045960] | 0.043243 [-0.008853, 0.093992] |
| R4 | gue_splice_reconstructed | decoder.final_norm | fixed_original_base | 0.550882 [0.512699, 0.588459] | -0.082951 [-0.126502, -0.037875] | 0.007630 [-0.044378, 0.058931] |
| R4 | gue_mouse_0 | decoder.layers.16 | independent_refit | 0.900840 [0.874140, 0.925874] | 0.023893 [-0.002498, 0.051201] | 0.066748 [0.036348, 0.099621] |
| R4 | gue_mouse_0 | decoder.layers.16 | fixed_original_base | 0.769466 [0.727654, 0.810244] | -0.107481 [-0.148623, -0.067695] | 0.172397 [0.131410, 0.215338] |
| R4 | gue_mouse_0 | decoder.final_norm | independent_refit | 0.840748 [0.806041, 0.873727] | 0.230092 [0.179188, 0.281172] | 0.182214 [0.130341, 0.232183] |
| R4 | gue_mouse_0 | decoder.final_norm | fixed_original_base | 0.760443 [0.717153, 0.798795] | 0.149786 [0.097210, 0.201813] | 0.132183 [0.078327, 0.187104] |
| R6 | gue_tf_0 | decoder.layers.16 | independent_refit | 0.830219 [0.794404, 0.864066] | 0.000244 [-0.029547, 0.031513] | 0.028600 [-0.006924, 0.062261] |
| R6 | gue_tf_0 | decoder.layers.16 | fixed_original_base | 0.684363 [0.637009, 0.726727] | -0.145611 [-0.192330, -0.100040] | 0.039569 [-0.018806, 0.094511] |
| R6 | gue_tf_0 | decoder.final_norm | independent_refit | 0.747430 [0.704124, 0.788767] | 0.067756 [0.015897, 0.119870] | 0.105828 [0.049926, 0.162779] |
| R6 | gue_tf_0 | decoder.final_norm | fixed_original_base | 0.502559 [0.453307, 0.553096] | -0.177114 [-0.248048, -0.106818] | 0.057979 [-0.011594, 0.124329] |
| R6 | gue_prom_core_all | decoder.layers.16 | independent_refit | 0.850623 [0.816898, 0.882796] | 0.033755 [0.001844, 0.067577] | 0.004059 [-0.025866, 0.033610] |
| R6 | gue_prom_core_all | decoder.layers.16 | fixed_original_base | 0.629891 [0.580313, 0.676884] | -0.186977 [-0.241185, -0.128450] | 0.036074 [-0.026680, 0.097525] |
| R6 | gue_prom_core_all | decoder.final_norm | independent_refit | 0.822148 [0.786803, 0.858348] | 0.060764 [0.019658, 0.102562] | 0.048862 [0.013799, 0.084524] |
| R6 | gue_prom_core_all | decoder.final_norm | fixed_original_base | 0.700116 [0.657496, 0.744747] | -0.061268 [-0.104411, -0.016097] | 0.154398 [0.088480, 0.221805] |
| R6 | gue_prom_300_all | decoder.layers.16 | independent_refit | 0.976593 [0.964674, 0.986059] | 0.022202 [0.008479, 0.039002] | 0.012955 [0.002976, 0.024141] |
| R6 | gue_prom_300_all | decoder.layers.16 | fixed_original_base | 0.808362 [0.769099, 0.846298] | -0.146029 [-0.185397, -0.106198] | 0.245441 [0.185531, 0.300864] |
| R6 | gue_prom_300_all | decoder.final_norm | independent_refit | 0.954131 [0.934221, 0.970816] | 0.117220 [0.085536, 0.152229] | 0.120241 [0.087786, 0.154665] |
| R6 | gue_prom_300_all | decoder.final_norm | fixed_original_base | 0.900542 [0.874164, 0.926071] | 0.063630 [0.030574, 0.098061] | 0.621927 [0.558972, 0.683369] |
| R6 | gue_splice_reconstructed | decoder.layers.16 | independent_refit | 0.806882 [0.770139, 0.840346] | 0.019020 [-0.014105, 0.050800] | 0.084776 [0.050329, 0.120615] |
| R6 | gue_splice_reconstructed | decoder.layers.16 | fixed_original_base | 0.667171 [0.630839, 0.704795] | -0.120691 [-0.159343, -0.083157] | 0.164012 [0.117532, 0.211518] |
| R6 | gue_splice_reconstructed | decoder.final_norm | independent_refit | 0.616920 [0.576949, 0.654428] | -0.016913 [-0.057261, 0.024059] | 0.024052 [-0.028991, 0.076471] |
| R6 | gue_splice_reconstructed | decoder.final_norm | fixed_original_base | 0.554077 [0.515457, 0.593659] | -0.079757 [-0.125005, -0.031602] | 0.010825 [-0.033902, 0.054754] |
| R6 | gue_mouse_0 | decoder.layers.16 | independent_refit | 0.906992 [0.880717, 0.930395] | 0.030046 [0.004738, 0.056773] | 0.072901 [0.042363, 0.103714] |
| R6 | gue_mouse_0 | decoder.layers.16 | fixed_original_base | 0.755695 [0.712976, 0.797686] | -0.121252 [-0.164805, -0.079795] | 0.158626 [0.115854, 0.203068] |
| R6 | gue_mouse_0 | decoder.final_norm | independent_refit | 0.748855 [0.706616, 0.790170] | 0.138198 [0.074488, 0.200899] | 0.090321 [0.035094, 0.143205] |
| R6 | gue_mouse_0 | decoder.final_norm | fixed_original_base | 0.769847 [0.728080, 0.808380] | 0.159191 [0.102072, 0.217130] | 0.141588 [0.085289, 0.198622] |
