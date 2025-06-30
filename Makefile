## Step 1 ##
drone_recon: # Generate eulerian graph (non-oriented) for the whole city => kiki
	python3 drone/generate_eulerian_paths.py

snow: # Apply snow for all neighborhoods (generate .csv) => kiki
	python3 drone/drone_generate_snow.py

compare: # Compare oriented and non-oriented graphs 
	python3 drone/check_integrity.py

render:
	python3 rendering/render.py

render_snow:
	python3 rendering/render_snow.py

## Step 2 ##
vehicle_recon_oriented: # Generate eulerian graph (oriented) for the 5 neighborhoods => Nathan
	python3 vehicle/generate_eulerian_paths_oriented.py

render_unified: # Render HTML file from 5 neighborhoods from eulerized oriented graph => Nathan
	python3 rendering/render_oriented.py

render_unified_snow: # Render HTML file from 5 neighborhoods with snow overhead (Nathan)
	python3 rendering/render_oriented_snow.py


simulate: # Launch sinulation (juju)
	python3 vehicle/simulation.py

report_graph:
	python3 reports/graphical_output/compares_types_graph.py

report_table: 
	python3 reports/graphical_output/compares_types_table.py

clean:
	rm -rf ./resources/*.html
	rm -rf ./resources/*/*.csv
