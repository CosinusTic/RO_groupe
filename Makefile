## Step 1 ##
drone_recon: # Generate eulerian graph (non-oriented) for the whole city => kiki
	python3 drone/generate_eulerian_paths.py

snow: # Apply snow for all neighborhoods (generate .csv) => kiki
	python3 drone/drone_generate_snow.py

compare: # Compare oriented and non-oriented graphs 
	python3 drone/check_integrity.py

## Step 2 ##
vehicle_recon_oriented: # Generate eulerian graph (oriented) for the 5 neighborhoods => Nathan
	python3 vehicle/generate_eulerian_paths_oriented.py

render_unified: # Render HTML file from 5 neighborhoods from eulerized oriented graph => Nathan
	python3 vehicle/render_graph_oriented_unified.py

render_unified_snow: # Render HTML file from 5 neighborhoods with snow overhead (wait)
	python3 drone/render_unified_snow.py

simulate: # Launch sinulation (juju)
	python3 vehicle/simulation.py

report: # => Generate visual rendering from report => lolo (generate matplotlib reports to compare iterations, analyse one iteration over time, etc)
