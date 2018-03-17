import pandas as pd
import numpy as np
import backend
import dataviz_funcs as dvf

# process the data and save the graph for every team in the team_names list
for team_name in dvf.team_names:
    team_results = dvf.heatmap_pipeline(team_name)
