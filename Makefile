recon_euler: # Generate eulerian graph
	python3 drone/generate_eulerian_paths.py

snow: # Apply snow for all neighborhoods
	python3 drone/drone_generate_snow.py

render_snow: # Generate .png under each neighborhoods
	python3 drone/render_snow.py

render_unified: # Generate .png for all neighborhoods
	python3 drone/render_unified.py

render_unified_snow: # Generate .png with snow for all neighborhoods
	python3 drone/render_unified_with_snow.py

simulate:
	python3 vehicle/simulation.py
